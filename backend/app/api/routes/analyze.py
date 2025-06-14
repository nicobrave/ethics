from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import asyncio
import time
import uuid
from datetime import datetime
import logging

from app.models.analysis import AnalysisRequest, AnalysisResponse, AnalysisResult
from app.services.scraper import WebScraper
from app.services.ai_analyzer import AIAnalyzer
from app.services.cache import CacheService
from app.utils.validators import validate_url

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory store for demo (replace with Redis/DB in production)
analysis_store = {}

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_website(request: AnalysisRequest):
    """Analyze a website for ethical AI practices"""
    try:
        # Validate URL
        url_str = str(request.url)
        if not validate_url(url_str):
            raise HTTPException(status_code=400, detail="Invalid URL provided")
        
        # Check cache first
        cache_key = f"analysis:{url_str}:{request.deep_scan}"
        cached_result = await CacheService.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached result for {url_str}")
            return AnalysisResponse(success=True, data=cached_result)
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting analysis {analysis_id} for {url_str}")
        
        # Step 1: Scrape website
        async with WebScraper() as scraper:
            scraped_data = await scraper.scrape_website(url_str, request.deep_scan)
        
        # Step 2: AI Analysis
        analyzer = AIAnalyzer()
        ai_analysis = await analyzer.analyze_ethics(scraped_data)
        
        # Step 3: Create result
        analysis_time = time.time() - start_time
        
        result = AnalysisResult(
            id=analysis_id,
            url=url_str,
            timestamp=datetime.utcnow(),
            analysis_time=analysis_time,
            **ai_analysis
        )
        
        # Store result (cache for 1 hour)
        await CacheService.set(cache_key, result, expire=3600)
        analysis_store[analysis_id] = result
        
        logger.info(f"Analysis {analysis_id} completed in {analysis_time:.2f}s")
        
        return AnalysisResponse(success=True, data=result)
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return AnalysisResponse(
            success=False,
            error=f"Analysis failed: {str(e)}"
        )

@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get analysis result by ID"""
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return AnalysisResponse(success=True, data=analysis_store[analysis_id])

# ... existing code ... 