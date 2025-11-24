from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
from .agent import app as agent_app
from langchain_core.messages import HumanMessage
from .shopify_client import ShopifyClient
from .indexer import ProductIndexer
import os
import logging
import sys

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    cart_id: str = ""
    shop_domain: str = ""

class SyncRequest(BaseModel):
    shop_url: str
    api_token: str

async def sync_products_task(shop_url: str, api_token: str):
    logger.info(f"Starting sync for {shop_url}")
    try:
        client = ShopifyClient(shop_url=shop_url, access_token=api_token)
        indexer = ProductIndexer(shopify_client=client)
        
        # Use env vars or defaults
        index_endpoint_name = os.getenv("VERTEX_ENDPOINT_ID", "")
        deployed_index_id = os.getenv("VERTEX_INDEX_ID", "")
        
        if not index_endpoint_name or not deployed_index_id:
            logger.warning("VERTEX_ENDPOINT_ID or VERTEX_INDEX_ID not set. Skipping vector upload.")
            # We could still fetch products to verify Shopify connection
            products = await client.fetch_all_products()
            logger.info(f"Fetched {len(products)} products from Shopify (but skipped indexing).")
            return

        await indexer.ingest_products(index_endpoint_name, deployed_index_id)
        logger.info("Sync completed successfully.")
    except Exception as e:
        logger.error(f"Sync failed: {e}")

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint that invokes the LangGraph agent.
    """
    inputs = {
        "messages": [HumanMessage(content=request.message)],
        "cart_id": request.cart_id,
        "shop_domain": request.shop_domain,
        "products_found": []
    }
    
    try:
        # Invoke the graph
        # We iterate to get the final state
        final_state = agent_app.invoke(inputs)
        
        # Extract the last message content
        messages = final_state.get("messages", [])
        if not messages:
            return {"response": "I'm sorry, I didn't get that."}
            
        last_message = messages[-1]
        return {"response": last_message.content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync")
async def sync_endpoint(request: SyncRequest, background_tasks: BackgroundTasks):
    """
    Trigger product synchronization in the background.
    """
    background_tasks.add_task(sync_products_task, request.shop_url, request.api_token)
    return {"status": "accepted", "message": "Sync started in background"}

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Shop Agent Backend"}

