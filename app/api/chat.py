"""
UniVR Chatbot - Chat API Endpoints
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.univr_agent import UniVRAgent
from app.services.store_manager import StoreManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize the agent (singleton)
agent = UniVRAgent()


class ChatRequest(BaseModel):
    """Chat request schema."""
    message: str
    domain: Optional[str] = None  # If None, uses generic agent (no RAG)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response schema."""
    response: str
    sources: list[dict] = []
    domain: Optional[str] = None


class DomainInfo(BaseModel):
    """Domain information schema."""
    domain: str
    display_name: str
    document_count: int


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the chatbot and get a response.
    
    If domain is provided, uses RAG with that domain's documents.
    If domain is None, uses generic Gemini (no RAG).
    """
    try:
        logger.info(f"Chat request: domain={request.domain}, message={request.message[:50]}...")
        
        # Get response from the agent
        result = await agent.chat(
            message=request.message,
            domain=request.domain
        )
        
        return ChatResponse(
            response=result["response"],
            sources=result.get("sources", []),
            domain=request.domain
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domains", response_model=list[DomainInfo])
async def get_domains():
    """Get list of available domains (from existing stores)."""
    try:
        store_manager = StoreManager()
        stores = await store_manager.list_stores()
        
        return [
            DomainInfo(
                domain=store.domain,
                display_name=store.display_name,
                document_count=store.document_count
            )
            for store in stores
        ]
    except Exception as e:
        logger.error(f"List domains error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/welcome")
async def get_welcome_message():
    """Get a welcome message for new users."""
    # Fetch available domains dynamically
    try:
        store_manager = StoreManager()
        stores = await store_manager.list_stores()
        domain_names = [store.domain for store in stores]
    except Exception:
        domain_names = []
    
    return {
        "message": "👋 Benvenuto! Welcome to the University of Verona Chatbot!",
        "available_domains": domain_names,
        "suggestions": [
            "What scholarships are available for international students?",
            "What are the tuition fees for the upcoming semester?",
            "How do I apply for the Right to Education program?",
            "What documents do I need for admission?",
            "When is the application deadline?"
        ]
    }


@router.get("/suggestions/{domain}")
async def get_domain_suggestions(domain: str):
    """
    Generate suggested questions for a specific domain.
    
    Uses Gemini with File Search to analyze documents and suggest relevant questions.
    """
    try:
        # Use the agent to generate suggestions based on document content
        result = await agent.chat(
            message="""Based on the documents in this knowledge base, generate exactly 5 specific, 
            helpful questions that a student might want to ask. 
            Return ONLY the questions, one per line, without numbering or bullet points.
            Make them specific to the actual content available, not generic questions.
            Questions should be in the same language as the documents (Italian or English).""",
            domain=domain
        )
        
        # Parse the response into individual questions
        response_text = result.get("response", "")
        questions = [
            q.strip() 
            for q in response_text.strip().split("\n") 
            if q.strip() and len(q.strip()) > 10
        ][:5]  # Limit to 5 questions
        
        # Fallback if parsing fails
        if not questions:
            questions = [
                "What information is available in this section?",
                "What are the key deadlines I should know about?",
                "What documents are required?",
                "Who can I contact for more information?",
                "What are the eligibility requirements?"
            ]
        
        return {
            "domain": domain,
            "suggestions": questions
        }
        
    except Exception as e:
        logger.error(f"Error generating suggestions for {domain}: {e}")
        # Return fallback suggestions on error
        return {
            "domain": domain,
            "suggestions": [
                "What information is available in this section?",
                "What are the key deadlines I should know about?",
                "What documents are required?",
                "Who can I contact for more information?",
                "What are the eligibility requirements?"
            ]
        }

