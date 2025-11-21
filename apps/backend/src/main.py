from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from .agent import app as agent_app
from langchain_core.messages import HumanMessage

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    cart_id: str = ""
    shop_domain: str = ""

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

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Shop Agent Backend"}

