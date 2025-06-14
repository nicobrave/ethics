from datetime import datetime
from fastapi import APIRouter
import sys
import psutil
import asyncio

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    } 