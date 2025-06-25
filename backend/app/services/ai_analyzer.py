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
            self.gemini_client = genai.GenerativeModel('gemini-2.5-pro')
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
            "category": "privacy|social|transparency|fairness",
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
            
            # Validate and structure the response
            structured = {
                "overall_score": max(0, min(100, analysis_data.get("overall_score", 50))),
                "category": analysis_data.get("category", "warning"),
                "title": analysis_data.get("title", "Análisis Completado"),
                "justification": analysis_data.get("justification", "Análisis no disponible"),
                "criteria_scores": CriteriaScore(**analysis_data.get("criteria_scores", {
                    "privacy": 5, "social_impact": 5, "transparency": 5, "fairness": 5
                })),
                "red_flags": [RedFlag(**flag) for flag in analysis_data.get("red_flags", [])],
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