# app/main.py
# ================================
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager
import os

from app.config import settings
from app.api.routes import analyze, health
from app.database.connection import init_db, close_db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("USANDO ENV FILE:", os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting AI Ethics Detector API...")
    await init_db()
    logger.info("✅ Database initialized")
    yield
    # Shutdown
    logger.info("🛑 Shutting down AI Ethics Detector API...")
    await close_db()

app = FastAPI(
    title="AI Ethics Detector API",
    description="API para analizar la ética de startups de IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(analyze.router, prefix="/api/v1", tags=["analysis"])

@app.get("/")
async def root():
    return {
        "service": "AI Ethics Detector API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

# ================================
# app/config.py
# ================================
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )

    # API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ethics_detector.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # App Config
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    
    # CORS and Security
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    ALLOWED_HOSTS: List[str] = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    MAX_CONCURRENT_ANALYSES: int = int(os.getenv("MAX_CONCURRENT_ANALYSES", "5"))
    
    # Scraping Config
    USER_AGENT: str = os.getenv("USER_AGENT", "EthicsDetector/1.0")
    SCRAPING_TIMEOUT: int = int(os.getenv("SCRAPING_TIMEOUT", "30"))
    MAX_PAGE_SIZE: str = os.getenv("MAX_PAGE_SIZE", "5MB")
    
settings = Settings()

# ================================
# app/models/analysis.py
# ================================
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EthicsCategory(str, Enum):
    ETHICAL = "ethical"
    WARNING = "warning" 
    DANGER = "danger"

class AnalysisRequest(BaseModel):
    url: HttpUrl
    deep_scan: bool = Field(default=False, description="Análisis profundo incluyendo términos de servicio")

class CriteriaScore(BaseModel):
    privacy: int = Field(ge=0, le=10)
    social_impact: int = Field(ge=0, le=10)
    transparency: int = Field(ge=0, le=10)
    fairness: int = Field(ge=0, le=10)

class RedFlag(BaseModel):
    severity: str = Field(description="low, medium, high")
    category: str = Field(description="privacy, social, transparency, etc.")
    description: str
    evidence: Optional[str] = None

class AnalysisResult(BaseModel):
    id: str
    url: str
    timestamp: datetime
    
    # Core Results
    overall_score: int = Field(ge=0, le=100)
    category: EthicsCategory
    title: str
    justification: str
    
    # Detailed Scores
    criteria_scores: CriteriaScore
    
    # Red Flags
    red_flags: List[RedFlag] = []
    
    # Technical Details
    analysis_time: float = Field(description="Tiempo de análisis en segundos")
    pages_analyzed: int
    content_length: int
    
    # AI Analysis Details
    ai_confidence: float = Field(ge=0, le=1)
    detected_patterns: List[str] = []

class AnalysisResponse(BaseModel):
    success: bool
    data: Optional[AnalysisResult] = None
    error: Optional[str] = None
    rate_limit_remaining: Optional[int] = None

# ================================
# app/services/scraper.py
# ================================
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
import asyncio
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import re

from app.config import settings

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.timeout = settings.SCRAPING_TIMEOUT * 1000  # Convert to ms
        
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()

    async def scrape_website(self, url: str, deep_scan: bool = False) -> Dict:
        """Scrape website content"""
        try:
            page = await self.browser.new_page()
            await page.set_extra_http_headers({
                'User-Agent': settings.USER_AGENT
            })
            
            # Navigate to main page
            logger.info(f"Scraping {url}")
            await page.goto(url, timeout=self.timeout, wait_until='networkidle')
            
            # Get main content
            content = await page.content()
            title = await page.title()
            
            # Extract text content
            soup = BeautifulSoup(content, 'html.parser')
            text_content = self._extract_text_content(soup)
            
            # Extract metadata
            metadata = self._extract_metadata(soup)
            
            result = {
                'url': url,
                'title': title,
                'content': text_content,
                'metadata': metadata,
                'pages_analyzed': 1,
                'content_length': len(text_content)
            }
            
            # Deep scan - get additional pages
            if deep_scan:
                additional_content = await self._deep_scan(page, url)
                result.update(additional_content)
            
            await page.close()
            return result
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            raise Exception(f"Failed to scrape website: {str(e)}")

    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
        
        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:50000]  # Limit content length

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata from HTML"""
        metadata = {}
        
        # Meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name') or tag.get('property')
            content = tag.get('content')
            if name and content:
                metadata[name] = content
        
        # Links to important pages
        important_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text().lower().strip()
            
            if any(keyword in href or keyword in text for keyword in 
                   ['privacy', 'terms', 'about', 'contact', 'policy']):
                important_links.append({
                    'text': text,
                    'href': link['href']
                })
        
        metadata['important_links'] = important_links
        return metadata

    async def _deep_scan(self, page: Page, base_url: str) -> Dict:
        """Perform deep scan of additional pages"""
        additional_content = {}
        pages_scanned = 1
        
        # Look for privacy policy and terms of service
        important_pages = ['privacy', 'terms', 'about']
        
        for page_type in important_pages:
            try:
                # Try to find and scrape the page
                page_content = await self._scrape_specific_page(page, base_url, page_type)
                if page_content:
                    additional_content[f'{page_type}_content'] = page_content
                    pages_scanned += 1
            except Exception as e:
                logger.warning(f"Could not scrape {page_type} page: {str(e)}")
        
        return {
            'additional_content': additional_content,
            'pages_analyzed': pages_scanned,
            'deep_scan_completed': True
        }

    async def _scrape_specific_page(self, page: Page, base_url: str, page_type: str) -> Optional[str]:
        """Scrape specific page type"""
        # Common URL patterns for different page types
        patterns = {
            'privacy': ['/privacy', '/privacy-policy', '/privacidad'],
            'terms': ['/terms', '/terms-of-service', '/terminos'],
            'about': ['/about', '/about-us', '/acerca']
        }
        
        for pattern in patterns.get(page_type, []):
            try:
                url = urljoin(base_url, pattern)
                await page.goto(url, timeout=10000)
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                return self._extract_text_content(soup)[:10000]  # Limit content
            except:
                continue
        
        return None

# ================================
# app/services/ai_analyzer.py
# ================================
import google.generativeai as genai
import json
import logging
from typing import Dict, Any, List
import asyncio
import re

from app.config import settings
from app.models.analysis import RedFlag, CriteriaScore, EthicsCategory

logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self):
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_client = None
    
    async def analyze_ethics(self, scraped_data: Dict) -> Dict[str, Any]:
        """Analyze ethics of scraped content"""
        try:
            # Prepare content for analysis
            analysis_content = self._prepare_content_for_analysis(scraped_data)
            
            # Get AI analysis
            if self.gemini_client:
                analysis = await self._analyze_with_gemini(analysis_content)
            else:
                raise Exception("No AI service available (Gemini API key not configured)")
            
            # Process and structure the analysis
            structured_analysis = self._structure_analysis(analysis, scraped_data)
            
            return structured_analysis
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            raise Exception(f"AI analysis failed: {str(e)}")

    def _prepare_content_for_analysis(self, scraped_data: Dict) -> str:
        """Prepare content for AI analysis"""
        content_parts = [
            f"Website: {scraped_data.get('url', 'Unknown')}",
            f"Title: {scraped_data.get('title', 'No title')}",
            f"Main content: {scraped_data.get('content', '')[:5000]}",  # Limit content
        ]
        
        # Add additional content if available
        additional = scraped_data.get('additional_content', {})
        for key, value in additional.items():
            content_parts.append(f"{key.replace('_', ' ').title()}: {value[:2000]}")
        
        # Add metadata
        metadata = scraped_data.get('metadata', {})
        if metadata:
            content_parts.append(f"Metadata: {json.dumps(metadata, indent=2)[:1000]}")
        
        return "\n\n".join(content_parts)

    async def _analyze_with_gemini(self, content: str) -> str:
        """Analyze content using Google Gemini"""
        prompt = """Eres un experto analista de ética en IA. Tu trabajo es evaluar startups de IA de manera objetiva y sin sesgos.

Analiza el siguiente contenido web y determina si la propuesta es ética o no. Considera:

1. PRIVACIDAD: ¿Cómo manejan los datos personales? ¿Hay transparencia?
2. IMPACTO SOCIAL: ¿Beneficia o perjudica a la sociedad? ¿Explota vulnerabilidades?
3. TRANSPARENCIA: ¿Es claro cómo funciona? ¿Ocultan información importante?
4. EQUIDAD: ¿Discrimina o es sesgado? ¿Es justo para todos los usuarios?

Responde ÚNICAMENTE con un objeto JSON válido que siga esta estructura:
{
    "overall_score": 0-100,
    "category": "ethical|warning|danger",
    "title": "Título descriptivo",
    "justification": "Explicación detallada de 2-3 párrafos",
    "criteria_scores": {
        "privacy": 0-10,
        "social_impact": 0-10,
        "transparency": 0-10,
        "fairness": 0-10
    },
    "red_flags": [
        {
            "severity": "low|medium|high",
            "category": "Privacidad|Impacto Social|Transparencia|Equidad",
            "description": "Descripción del problema",
            "evidence": "Evidencia específica del contenido"
        }
    ],
    "detected_patterns": ["patrón1", "patrón2"],
    "confidence": 0.0-1.0
}

Se ULTRA CRÍTICO y objetivo. Detecta patrones ocultos, dark patterns, lenguaje evasivo. No incluyas nada antes o después del JSON."""
        
        full_prompt = f"{prompt}\n\nContenido a analizar:\n{content}"

        try:
            response = await self.gemini_client.generate_content_async(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise

    def _structure_analysis(self, ai_response: str, scraped_data: Dict) -> Dict[str, Any]:
        """Structure AI response into our format"""
        try:
            # Gemini's JSON mode should return a clean JSON string.
            analysis_data = json.loads(ai_response)
            
            # Translate red flag categories
            translation_map = {
                "privacy": "Privacidad",
                "social_impact": "Impacto Social",
                "social": "Impacto Social",
                "transparency": "Transparencia",
                "fairness": "Equidad",
                "technical": "Técnico"
            }
            
            processed_flags = []
            for flag_data in analysis_data.get("red_flags", []):
                category_en = flag_data.get("category", "").lower().replace(" ", "_")
                flag_data["category"] = translation_map.get(category_en, flag_data.get("category", "General"))
                processed_flags.append(RedFlag(**flag_data))
            
            # Handle criteria scores
            criteria_scores_data = analysis_data.get("criteria_scores")
            if criteria_scores_data:
                # The AI returns english keys, we validate them directly.
                validated_criteria = CriteriaScore(**criteria_scores_data)
            else:
                # Provide default if AI response doesn't contain scores
                validated_criteria = CriteriaScore(privacy=5, social_impact=5, transparency=5, fairness=5)

            # Validate and structure the response
            structured = {
                "overall_score": max(0, min(100, analysis_data.get("overall_score", 50))),
                "category": analysis_data.get("category", "warning"),
                "title": analysis_data.get("title", "Análisis Completado"),
                "justification": analysis_data.get("justification", "Análisis no disponible"),
                "criteria_scores": validated_criteria,
                "red_flags": processed_flags,
                "detected_patterns": analysis_data.get("detected_patterns", []),
                "ai_confidence": analysis_data.get("confidence", 0.8),
                "pages_analyzed": scraped_data.get("pages_analyzed", 1),
                "content_length": scraped_data.get("content_length", 0)
            }
            
            return structured
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            # Fallback analysis
            return self._fallback_analysis(scraped_data)
        except Exception as e:
            logger.error(f"Error structuring analysis: {str(e)}")
            return self._fallback_analysis(scraped_data)

    def _fallback_analysis(self, scraped_data: Dict) -> Dict[str, Any]:
        """Fallback analysis when AI fails"""
        return {
            "overall_score": 50,
            "category": "warning",
            "title": "Análisis Limitado",
            "justification": "No se pudo completar el análisis completo. Se recomienda revisión manual.",
            "criteria_scores": CriteriaScore(privacy=5, social_impact=5, transparency=5, fairness=5),
            "red_flags": [RedFlag(
                severity="medium",
                category="technical",
                description="Análisis automático no disponible",
                evidence="Error en el procesamiento de IA"
            )],
            "detected_patterns": ["analysis_error"],
            "ai_confidence": 0.1,
            "pages_analyzed": scraped_data.get("pages_analyzed", 1),
            "content_length": scraped_data.get("content_length", 0)
        }

# ================================
# app/api/routes/analyze.py
# ================================
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

# ================================
# app/api/routes/health.py
# ================================
from fastapi import APIRouter
from datetime import datetime
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