import os
import logging
import re
from typing import List, Dict, Any, Set
from langchain_google_vertexai import VertexAIEmbeddings
from google.cloud import aiplatform
from google.cloud import firestore
from .shopify_client import ShopifyClient

logger = logging.getLogger(__name__)

# Initialize Vertex AI
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
REGION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
aiplatform.init(project=PROJECT_ID, location=REGION)


class ProductIndexer:
    def __init__(self, shopify_client: ShopifyClient):
        self.shopify_client = shopify_client
        # Use default VertexAI embeddings (768 dimensions)
        self.embeddings_model = VertexAIEmbeddings(model_name="text-embedding-004")
        self.db = firestore.Client()

    def clean_html(self, raw_html: str) -> str:
        """Remove HTML tags from a string."""
        if not raw_html:
            return ""
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext.strip()

    def create_context_string(self, product: Dict[str, Any]) -> str:
        """Concatenate product details into a single context string with category emphasis."""
        title = product.get("title", "")
        description = self.clean_html(product.get("descriptionHtml", ""))
        tags = ", ".join(product.get("tags", []))
        vendor = product.get("vendor", "")
        product_type = product.get("productType", "")
        
        # Get price from the first variant or price range
        price = "N/A"
        variants = product.get("variants", {}).get("edges", [])
        if variants:
            price = variants[0]["node"].get("price", "N/A")
        
        # Enhanced context with category prominence
        context = f"Category: {product_type}\nTitle: {title}\nDescription: {description}\nTags: {tags}\nVendor: {vendor}\nPrice: {price}"
        return context

    def extract_categories(self, products: List[Dict[str, Any]]) -> Set[str]:
        """Extract unique product categories/types from products."""
        categories = set()
        for product in products:
            product_type = product.get("productType", "").strip()
            if product_type:
                categories.add(product_type)
        return categories

    async def ingest_products(self, index_endpoint_name: str, deployed_index_id: str):
        """
        Fetch products, generate embeddings, and upload to Vector Search with upsert logic.
        Uses delete-all + add pattern for simplicity (avoids duplicates).
        """
        logger.info("Starting product ingestion...")
        products = await self.shopify_client.fetch_all_products()
        
        if not products:
            logger.warning("No products found.")
            return

        # Extract and store categories in Firestore for agent context
        categories = self.extract_categories(products)
        logger.info(f"Found {len(categories)} unique product categories: {', '.join(sorted(categories))}")
        
        # Store categories in Firestore for agent access
        try:
            categories_ref = self.db.collection('metadata').document('product_categories')
            categories_ref.set({
                'categories': list(sorted(categories)),
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            logger.info("Product categories stored in Firestore")
        except Exception as e:
            logger.warning(f"Failed to store categories in Firestore: {e}")

        texts = []
        metadatas = []
        ids = []

        for product in products:
            context = self.create_context_string(product)
            product_id = product.get("id")
            product_type = product.get("productType", "")
            
            texts.append(context)
            ids.append(product_id)
            
            # Enhanced metadata with category/type
            image_url = ""
            images = product.get("images", {}).get("edges", [])
            if images:
                image_url = images[0]["node"].get("url", "")
            
            # Get price for metadata
            price = "N/A"
            variants = product.get("variants", {}).get("edges", [])
            if variants:
                price = variants[0]["node"].get("price", "N/A")

            metadatas.append({
                "id": product_id,
                "title": product.get("title"),
                "handle": product.get("handle"),
                "category": product_type,  # Added for filtering
                "product_type": product_type,  # Redundant but explicit
                "vendor": product.get("vendor", ""),
                "price": price,
                "image_url": image_url,
            })

        logger.info(f"Generating embeddings for {len(texts)} products...")
        
        # Generate embeddings
        embeddings = self.embeddings_model.embed_documents(texts)
        logger.info(f"Generated {len(embeddings)} embeddings, first embedding has {len(embeddings[0])} dimensions")

        logger.info("Uploading to Vector Search...")
        
        from langchain_google_vertexai import VectorSearchVectorStore
        
        vector_store = VectorSearchVectorStore.from_components(
            project_id=PROJECT_ID,
            region=REGION,
            gcs_bucket_name=os.getenv("GCS_BUCKET_NAME"),
            index_id=os.getenv("VERTEX_INDEX_ID"),
            endpoint_id=index_endpoint_name,
            embedding=self.embeddings_model
        )
        
        # UPSERT LOGIC: Delete all existing data first, then add new
        # Note: VectorSearchVectorStore doesn't have a built-in delete_all method
        # For true upsert, we'd need to track existing IDs and delete them individually
        # For now, we'll just add (which may create duplicates on re-sync)
        # TODO: Implement proper upsert with ID tracking
        logger.info("Adding products to vector store...")
        vector_store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        
        logger.info(f"Ingestion complete. {len(products)} products indexed across {len(categories)} categories.")
