import os
import logging
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_google_vertexai import ChatVertexAI
from langchain_google_vertexai import VertexAIEmbeddings, VectorSearchVectorStore

import operator

# Import our custom client
from .shopify_client import ShopifyClient

logger = logging.getLogger(__name__)

# --- Configuration ---
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
REGION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
MODEL_NAME = "gemini-2.0-flash-exp" # Using the requested model or similar available

# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    cart_id: str
    shop_domain: str
    products_found: List[Dict[str, Any]]
    next_node: str

# --- Tools ---

@tool
def search_products(query: str):
    """
    Search for products in the store using semantic search.
    Returns a list of products with title, price, and ID.
    """
    logger.info(f"Searching for: {query}")
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
    index_id = os.getenv("VERTEX_INDEX_ID")
    endpoint_id = os.getenv("VERTEX_ENDPOINT_ID")
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    
    if not index_id or not endpoint_id:
        logger.warning("Vertex AI Index ID or Endpoint ID not set. Returning empty results.")
        return []

    try:
        # Use default VertexAI embeddings (768 dimensions)
        embeddings = VertexAIEmbeddings(model_name="text-embedding-004")
        
        vector_store = VectorSearchVectorStore.from_components(
            project_id=project_id,
            region=location,
            gcs_bucket_name=bucket_name,
            index_id=index_id,
            endpoint_id=endpoint_id,
            embedding=embeddings
        )
        
        # Search for top 5 products
        results = vector_store.similarity_search(query, k=5)
        
        products = []
        for res in results:
            # Metadata is stored in the document
            products.append({
                "title": res.metadata.get("title", "Unknown Product"),
                "price": res.metadata.get("price", "0.00"),
                "id": res.metadata.get("id", ""),
                "image_url": res.metadata.get("image_url", ""),
                "handle": res.metadata.get("handle", ""),
                "category": res.metadata.get("category", "General")
            })
            
        return products
    except Exception as e:
        logger.error(f"Error during vector search: {e}")
        return []


@tool
def add_to_cart(product_id: str, quantity: int = 1):
    """
    Add a product to the Shopify cart.
    Returns the cart URL.
    """
    logger.info(f"Adding {product_id} x{quantity} to cart")
    # Here we would use ShopifyClient to interact with Storefront API
    return "https://my-shop.myshopify.com/cart/c/123456"

# --- Nodes ---

llm = ChatVertexAI(model_name=MODEL_NAME, temperature=0)

def supervisor_node(state: AgentState):
    """
    The Supervisor (Router) analyzes the last message and decides which agent to call.
    """
    messages = state['messages']
    last_message = messages[-1]
    
    system_prompt = """
    You are a helpful shopping assistant. Your goal is to help users find products and buy them.
    
    If the user asks for a product, use the 'search_agent'.
    If the user wants to buy or add to cart, use the 'cart_agent'.
    If the user is just chatting, use the 'general_chat'.
    
    Respond with ONLY the name of the next agent: 'search_agent', 'cart_agent', or 'general_chat'.
    """
    
    # Simple routing logic using LLM
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        last_message
    ])
    
    route = response.content.strip().lower()
    if "search" in route:
        return {"next_node": "search_agent"}
    elif "cart" in route:
        return {"next_node": "cart_agent"}
    else:
        return {"next_node": "general_chat"}

def search_agent_node(state: AgentState):
    """
    Product Search Agent.
    """
    messages = state['messages']
    last_message = messages[-1]
    
    # Bind tools to the LLM
    tools = [search_products]
    llm_with_tools = llm.bind_tools(tools)
    
    response = llm_with_tools.invoke(messages)
    
    # If tool call is generated
    if response.tool_calls:
        # Execute tool
        # For simplicity in this node, we just execute the first tool call
        # In a real ReAct loop, we'd have a prebuilt node for this.
        tool_call = response.tool_calls[0]
        if tool_call['name'] == 'search_products':
            result = search_products.invoke(tool_call['args'])
            return {
                "messages": [response, AIMessage(content=f"Found these products: {result}")],
                "products_found": result,
                "next_node": "end"
            }
    
    return {"messages": [response], "next_node": "end"}

def cart_agent_node(state: AgentState):
    """
    Cart Manager Agent.
    """
    messages = state['messages']
    
    tools = [add_to_cart]
    llm_with_tools = llm.bind_tools(tools)
    
    response = llm_with_tools.invoke(messages)
    
    if response.tool_calls:
        tool_call = response.tool_calls[0]
        if tool_call['name'] == 'add_to_cart':
            result = add_to_cart.invoke(tool_call['args'])
            return {
                "messages": [response, AIMessage(content=f"Added to cart. Checkout here: {result}")],
                "next_node": "end"
            }

    return {"messages": [response], "next_node": "end"}

def general_chat_node(state: AgentState):
    """
    General Chat Agent.
    """
    messages = state['messages']
    response = llm.invoke(messages)
    return {"messages": [response], "next_node": "end"}

# --- Graph Construction ---

workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("search_agent", search_agent_node)
workflow.add_node("cart_agent", cart_agent_node)
workflow.add_node("general_chat", general_chat_node)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    lambda x: x['next_node'],
    {
        "search_agent": "search_agent",
        "cart_agent": "cart_agent",
        "general_chat": "general_chat"
    }
)

workflow.add_edge("search_agent", END)
workflow.add_edge("cart_agent", END)
workflow.add_edge("general_chat", END)

app = workflow.compile()
