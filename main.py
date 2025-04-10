# Copyright (c) 2025 Chris Collins chris@hitorro.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
import logging
import traceback
import sys

from agent import run_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("math_agent")

app = FastAPI(
    title="Math Agent API",
    description="API for a LangGraph-based math agent with Ollama LLM",
    version="1.0.0",
)

class AgentRequest(BaseModel):
    query: str

class MessageResponse(BaseModel):
    type: str
    content: str
    name: Optional[str] = None

class AgentResponse(BaseModel):
    messages: List[MessageResponse]
    answer: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Math Agent API"}

@app.post("/agent", response_model=AgentResponse)
async def query_agent(request: AgentRequest, req: Request):
    """
    Endpoint to interact with the math agent.
    
    Args:
        request: The AgentRequest containing the user's query.
        req: The FastAPI request object for additional context.
    
    Returns:
        AgentResponse: The agent's response including all messages and the final answer.
    """
    logger.info(f"Received query: {request.query}")
    try:
        # Run the agent
        logger.info("Running agent with user query")
        result = run_agent(request.query)
        logger.info(f"Agent returned {len(result)} messages")
        
        # Convert the messages to a format compatible with the response model
        messages = []
        for msg in result:
            message_type = type(msg).__name__.replace("Message", "").lower()
            
            # Log the message content for debugging
            logger.debug(f"Message type: {message_type}, content: {msg.content[:100]}...")
            
            message = MessageResponse(
                type=message_type,
                content=msg.content,
            )
            
            # Add tool name if available
            if hasattr(msg, "name") and msg.name:
                message.name = msg.name
                logger.debug(f"Tool name: {msg.name}")
                
            messages.append(message)
        
        # Get the final answer (last AI message)
        final_answer = "No answer provided"
        for msg in reversed(result):
            if type(msg).__name__ == "AIMessage":
                final_answer = msg.content
                break
        
        logger.info("Successfully processed query and returning response")
        return AgentResponse(
            messages=messages,
            answer=final_answer
        )
    except Exception as e:
        error_detail = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        logger.error(f"Error processing query: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(error_detail))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Math Agent API server on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

