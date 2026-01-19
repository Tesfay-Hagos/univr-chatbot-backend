"""
UniVR Chatbot - Main RAG Agent

Uses Gemini File Search for RAG capabilities to answer questions
about University of Verona announcements, scholarships, and services.

Supports multiple domains - each domain has its own File Search Store.
Falls back to generic Gemini (no RAG) if no domain is specified.
"""

import logging
from typing import Optional

from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, MODEL, STORE_PREFIX

logger = logging.getLogger(__name__)

# System instruction for the University chatbot
SYSTEM_INSTRUCTION = """You are the official University of Verona (Università degli Studi di Verona) AI Assistant.

Your role is to help students find accurate information about:
- Scholarships (Borse di Studio)
- Right to Education programs (Diritto allo Studio)
- Admission requirements and deadlines
- Tuition fees and payment options
- International student services

Guidelines:
1. Always provide accurate, helpful information based on the documents in your knowledge base.
2. If you don't find relevant information, clearly say so and suggest contacting the appropriate office.
3. Be friendly and professional in both Italian and English.
4. Include specific dates, deadlines, and requirements when available.
5. Cite the source documents when possible.

Important contacts:
- Student Services (Segreteria Studenti): segreteria.studenti@univr.it
- ESU Verona (scholarships): info@esu.vr.it
- International Office: international@univr.it

Respond in the same language as the user's question (Italian or English).
"""


class UniVRAgent:
    """
    University of Verona RAG Agent using Gemini File Search.
    
    Supports multiple domains - looks up the correct store based on domain.
    Falls back to generic Gemini if no domain specified or store not found.
    """
    
    def __init__(self):
        """Initialize the agent with Gemini client."""
        self.client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the Gemini client."""
        if not GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set. Agent will run in demo mode.")
            return
        
        try:
            self.client = genai.Client()
            logger.info("Gemini client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
    
    def _get_store(self, domain: str) -> types.FileSearchStore | None:
        """Retrieve a File Search Store by domain name."""
        if not self.client:
            return None
        
        display_name = f"{STORE_PREFIX}-{domain}"
        try:
            for store in self.client.file_search_stores.list():
                if store.display_name == display_name:
                    return store
        except Exception as e:
            logger.error(f"Error listing stores: {e}")
        return None
    
    def _build_tools(self, domain: Optional[str]) -> list:
        """Build the tools list for the agent based on domain."""
        tools = []
        
        if domain:
            store = self._get_store(domain)
            if store and store.name:
                file_search_tool = types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[store.name]
                    )
                )
                tools.append(file_search_tool)
                logger.debug(f"File Search tool configured with domain '{domain}': {store.name}")
            else:
                logger.warning(f"Store for domain '{domain}' not found. Using generic agent.")
        else:
            logger.debug("No domain specified. Using generic agent (no RAG).")
        
        return tools
    
    async def chat(self, message: str, domain: Optional[str] = None) -> dict:
        """
        Send a message and get a response from the agent.
        
        Args:
            message: The user's message
            domain: Optional domain to use for RAG (e.g., 'scholarships')
            
        Returns:
            dict with 'response' and 'sources'
        """
        # Demo mode if no API key or client
        if not self.client:
            return self._demo_response(message)
        
        try:
            # Build tools based on domain
            tools = self._build_tools(domain)
            
            # Add domain context to system instruction
            domain_context = ""
            if domain:
                domain_context = f"\n\nThe user is asking about: {domain}. Focus on this topic."
            
            config = types.GenerateContentConfig(
                tools=tools if tools else None,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False),
                temperature=0.7,
                system_instruction=SYSTEM_INSTRUCTION + domain_context,
            )
            
            # Create chat session
            chat = self.client.chats.create(
                model=MODEL,
                config=config,
            )
            
            # Send message and get response
            response = chat.send_message(message)
            
            # Extract sources from grounding metadata
            sources = []
            if response.candidates and response.candidates[0].grounding_metadata:
                gm = response.candidates[0].grounding_metadata
                if gm.grounding_chunks:
                    for i, chunk in enumerate(gm.grounding_chunks):
                        sources.append({
                            "index": i + 1,
                            "content": getattr(chunk, "content", "")[:200] + "..." if hasattr(chunk, "content") else ""
                        })
            
            return {
                "response": response.text or "I couldn't generate a response. Please try again.",
                "sources": sources
            }
            
        except Exception as e:
            logger.warning(f"Gemini API error, falling back to demo mode: {e}")
            return self._demo_response(message)
    
    def _demo_response(self, message: str) -> dict:
        """Provide a demo response when API key is not configured."""
        demo_responses = {
            "scholarship": """🎓 **Scholarship Information**

The University of Verona offers several scholarships for students:

1. **ESU Verona Scholarships** - Based on income (ISEE) and academic merit
   - Application deadline: Usually September
   - Contact: info@esu.vr.it

2. **University Merit Scholarships** - For outstanding academic performance
   
3. **International Student Scholarships** - Various programs available

⚠️ *Note: This is a demo response. Connect a Gemini API key and create domain stores for real data.*""",
            
            "tuition": """💰 **Tuition Fees Information**

Tuition at University of Verona varies by program and income:

- **First rate** (lowest income): ~€150-300/year
- **Standard rate**: ~€1,500-2,500/year
- **Full rate** (highest income): ~€2,500-3,500/year

Payment deadlines are typically in:
- First installment: October
- Second installment: March

⚠️ *Note: This is a demo response. Connect a Gemini API key and create domain stores for real data.*""",
            
            "default": """👋 **Welcome to the University of Verona Chatbot!**

I can help you with:
- 📚 Scholarship information
- 💰 Tuition fees and payment
- 📝 Admission requirements
- 🌍 International student services
- 📅 Important deadlines

⚠️ *Note: This is running in demo mode. To get real answers, please configure your Gemini API key and create domain stores.*"""
        }
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["scholarship", "borsa", "borse", "financial"]):
            return {"response": demo_responses["scholarship"], "sources": []}
        elif any(word in message_lower for word in ["tuition", "fee", "tasse", "payment", "cost"]):
            return {"response": demo_responses["tuition"], "sources": []}
        else:
            return {"response": demo_responses["default"], "sources": []}
