import os
import logging
import re
from typing import List, Dict, Any
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
        """Concatenate product details into a single context string."""
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
        
        return f"Title: {title}\nDescription: {description}\nTags: {tags}\nVendor: {vendor}\nType: {product_type}\nPrice: {price}"

    async def ingest_products(self, index_endpoint_name: str, deployed_index_id: str):
        """
        Fetch products, generate embeddings, and upload to Vector Search.
        """
        logger.info("Starting product ingestion...")
        products = await self.shopify_client.fetch_all_products()
        
        if not products:
            logger.warning("No products found.")
            return

        texts = []
        metadatas = []
        ids = []

        for product in products:
            context = self.create_context_string(product)
            product_id = product.get("id")
            
            texts.append(context)
            ids.append(product_id)
            
            # Metadata for filtering/retrieval
            image_url = ""
            images = product.get("images", {}).get("edges", [])
            if images:
                image_url = images[0]["node"].get("url", "")

            metadatas.append({
                "id": product_id,
                "title": product.get("title"),
                "handle": product.get("handle"),
                "image_url": image_url,
                "context": context # Storing context in metadata for retrieval if needed, or just rely on vector store
            })

        logger.info(f"Generating embeddings for {len(texts)} products...")
        # Batch generation might be needed for 50k products, but for now we do simple list
        # In production, we should batch this (e.g., 100 at a time)
        
        # TODO: Implement batching for scalability
        embeddings = self.embeddings_model.embed_documents(texts)

        logger.info("Embeddings generated. Uploading to Vector Search...")
        
        # Note: Direct upload to Vector Search Index is usually done via IndexEndpoint
        # However, LangChain's VectorSearch wrapper is easier if we set it up.
        # For this custom implementation, we might want to use the raw aiplatform SDK or LangChain's vectorstore.
        
        # Let's use LangChain's VectorStore for simplicity if possible, or raw SDK.
        # Given the requirement for "Vertex AI Vector Search", let's assume we use the LangChain wrapper
        # pointing to an existing index.
        
        from langchain_google_vertexai import VectorSearchVectorStore
        
        vector_store = VectorSearchVectorStore.from_components(
            project_id=PROJECT_ID,
            region=REGION,
            gcs_bucket_name=os.getenv("GCS_BUCKET_NAME"),
            index_id=os.getenv("VERTEX_INDEX_ID"),
            endpoint_id=index_endpoint_name,
            embedding=self.embeddings_model
        )
        
        # Add texts
        vector_store.add_texts(texts=texts, metadatas=metadatas)
        
        logger.info("Ingestion complete.")
