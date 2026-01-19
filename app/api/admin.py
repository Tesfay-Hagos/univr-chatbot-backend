"""
UniVR Chatbot - Admin API Endpoints

Manage File Search Stores (domains) and documents.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.services.store_manager import StoreManager, StoreInfo

logger = logging.getLogger(__name__)

router = APIRouter()

# Data directory for uploaded files
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============ Schemas ============

class CreateStoreRequest(BaseModel):
    """Request to create a new store/domain."""
    domain: str
    description: str = ""


class CreateStoreResponse(BaseModel):
    """Response after creating a store."""
    success: bool
    domain: str
    store_name: str
    message: str


class UploadResponse(BaseModel):
    """Upload response schema."""
    success: bool
    filename: str
    domain: str
    message: str


class DocumentInfo(BaseModel):
    """Document information schema."""
    name: str
    display_name: str
    metadata: dict = {}


# ============ Store Management ============

@router.post("/stores", response_model=CreateStoreResponse)
async def create_store(request: CreateStoreRequest):
    """
    Create a new File Search Store for a domain.
    
    This creates a new RAG domain that can be used for document uploads and queries.
    """
    try:
        store_manager = StoreManager()
        store = await store_manager.create_store(request.domain, request.description)
        
        return CreateStoreResponse(
            success=True,
            domain=request.domain,
            store_name=store.name,
            message=f"Store for domain '{request.domain}' created successfully"
        )
    except Exception as e:
        logger.error(f"Create store error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stores", response_model=list[StoreInfo])
async def list_stores():
    """List all available stores/domains."""
    try:
        store_manager = StoreManager()
        stores = await store_manager.list_stores()
        return stores
    except Exception as e:
        logger.error(f"List stores error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stores/{domain}")
async def delete_store(domain: str):
    """Delete a store and all its documents."""
    try:
        store_manager = StoreManager()
        success = await store_manager.delete_store(domain)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Store '{domain}' not found")
        
        return {"success": True, "message": f"Store '{domain}' deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete store error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Document Management ============

@router.post("/stores/{domain}/upload", response_model=UploadResponse)
async def upload_document(
    domain: str,
    file: UploadFile = File(...)
):
    """
    Upload a document to a domain's File Search Store.
    
    If a document with the same filename exists, it will be replaced.
    """
    try:
        # Validate file type
        if not file.filename.endswith((".pdf", ".md", ".txt", ".docx")):
            raise HTTPException(
                status_code=400,
                detail="Only PDF, Markdown, TXT, and DOCX files are supported"
            )
        
        # Save the file locally
        file_path = DATA_DIR / file.filename
        content = await file.read()
        file_path.write_bytes(content)
        
        logger.info(f"Saved file: {file_path}")
        
        # Upload to File Search Store
        store_manager = StoreManager()
        result = await store_manager.upload_document(str(file_path), domain)
        
        return UploadResponse(
            success=True,
            filename=file.filename,
            domain=domain,
            message=f"Document '{file.filename}' uploaded to '{domain}' domain"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stores/{domain}/documents", response_model=list[DocumentInfo])
async def list_documents(domain: str):
    """List all documents in a domain's store."""
    try:
        store_manager = StoreManager()
        documents = await store_manager.list_documents(domain)
        return documents
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stores/{domain}/documents/{doc_name:path}")
async def delete_document(domain: str, doc_name: str):
    """Delete a document from a domain's store."""
    try:
        store_manager = StoreManager()
        success = await store_manager.delete_document(domain, doc_name)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"success": True, "message": "Document deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
