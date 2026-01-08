import logging
import os
from typing import Dict, List, Optional, Any, Union

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import time

from security_config import security_config, security_middleware, get_security_headers, log_security_event

# Load environment variables from .env file
load_dotenv()

# --- Configuration and Logging ---

APP_NAME = os.getenv("APP_NAME", "MCP AI Guides Server")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Data Source (Hardcoded for demonstration) ---

AI_GUIDES_DATA: List[Dict[str, Union[str, List[str]]]] = [
    {
        "title": "OpenAI: GPT Best Practices",
        "publisher": "OpenAI",
        "description": "Comprehensive guide on best practices for prompting and using GPT models effectively.",
        "topics": ["prompt engineering", "LLM usage", "AI best practices"],
        "download_url": "https://example.com/openai-gpt-best-practices.pdf"
    },
    {
        "title": "Google: Introduction to Generative AI",
        "publisher": "Google",
        "description": "An introductory course to generative AI concepts and applications.",
        "topics": ["generative AI", "AI fundamentals", "machine learning"],
        "download_url": "https://example.com/google-intro-gen-ai.pdf"
    },
    {
        "title": "Anthropic: Constitutional AI",
        "publisher": "Anthropic",
        "description": "Exploration of Constitutional AI for building safe and helpful AI systems.",
        "topics": ["AI safety", "AI ethics", "constitutional AI"],
        "download_url": "https://example.com/anthropic-constitutional-ai.pdf"
    },
    {
        "title": "OpenAI: AI Agent Construction Guidelines",
        "publisher": "OpenAI",
        "description": "A detailed guide on constructing robust and intelligent AI agents.",
        "topics": ["AI agents", "agent architecture", "AI development"],
        "download_url": "https://example.com/openai-ai-agents.pdf"
    },
    {
        "title": "Google: Enterprise AI Deployment Strategies",
        "publisher": "Google",
        "description": "Strategies and best practices for deploying AI solutions at enterprise scale.",
        "topics": ["enterprise AI", "AI deployment", "MLOps"],
        "download_url": "https://example.com/google-enterprise-ai.pdf"
    }
]

# --- Request/Response Models ---

class GuideComparisonRequest(BaseModel):
    guide_titles: List[str]

class GeminiSearchRequest(BaseModel):
    query: str
    use_grounding: bool = True

# --- FastAPI Application Instance ---

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="A centralized repository and search interface for a curated collection of free AI-related guides from OpenAI, Google, and Anthropic. Enhanced with Gemini AI for intelligent search and analysis."
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=security_config.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security middleware
@app.middleware("http")
async def security_middleware_handler(request: Request, call_next):
    """Security middleware for rate limiting and security headers"""
    start_time = time.time()
    
    # Get client ID for rate limiting
    client_id = security_middleware.get_client_id(request)
    
    # Check rate limiting
    if not await security_middleware.rate_limit_check(client_id):
        log_security_event(
            "rate_limit_exceeded",
            {"client_id": client_id, "path": request.url.path},
            "WARNING"
        )
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers=get_security_headers()
        )
    
    # Validate request size
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > security_config.max_request_size:
        log_security_event(
            "request_size_exceeded",
            {"client_id": client_id, "size": content_length},
            "WARNING"
        )
        return JSONResponse(
            status_code=413,
            content={"detail": "Request too large"},
            headers=get_security_headers()
        )
    
    # Process request
    response = await call_next(request)
    
    # Add security headers
    for header, value in get_security_headers().items():
        response.headers[header] = value
    
    # Log request for monitoring
    process_time = time.time() - start_time
    log_security_event(
        "api_request",
        {
            "client_id": client_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": process_time
        },
        "INFO"
    )
    
    return response

# Authentication dependency
async def verify_api_key(request: Request):
    """Verify API key for protected endpoints"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None  # Allow public access for most endpoints
    
    if not security_config.validate_api_key_format(api_key):
        log_security_event(
            "invalid_api_key_format",
            {"client_id": security_middleware.get_client_id(request)},
            "WARNING"
        )
        raise HTTPException(status_code=401, detail="Invalid API key format")
    
    # In a real implementation, you would validate against a database
    # For now, we'll accept any properly formatted key
    return {"api_key": api_key}

# --- Helper Functions ---

def _find_guide_by_title(title: str) -> Optional[Dict[str, Union[str, List[str]]]]:
    """Finds an AI guide by its exact title (case-insensitive for comparison)."""
    for guide in AI_GUIDES_DATA:
        if guide["title"].lower() == title.lower():
            return guide
    return None

# --- API Endpoints ---

@app.get("/health", summary="Health Check", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """Returns a simple status to indicate the server is running."""
    logger.info("Health check requested.")
    return {"status": "ok", "service": APP_NAME, "version": APP_VERSION}


@app.get(
    "/guides",
    response_model=List[Dict[str, Union[str, List[str]]]],
    summary="List all AI guides"
)
async def list_ai_guides() -> List[Dict[str, Union[str, List[str]]]]:
    """Lists all available AI guides with their titles, publishers, descriptions, and topics.

    Returns:
        A list of dictionaries, each representing an AI guide's metadata.
    """
    logger.info("Listing all AI guides.")
    return AI_GUIDES_DATA


@app.get(
    "/guides/search",
    response_model=List[Dict[str, Union[str, List[str]]]],
    summary="Search for AI guides"
)
async def search_ai_guides(query: str) -> List[Dict[str, Union[str, List[str]]]]:
    """Searches for AI guides based on keywords or topics in their title or description.

    Args:
        query: The keyword or topic to search for.

    Returns:
        A list of dictionaries for matching AI guides.
    """
    logger.info(f"Searching AI guides with query: '{query}'.")
    query_lower = query.lower()
    results = []
    for guide in AI_GUIDES_DATA:
        title_match = query_lower in guide["title"].lower()
        desc_match = query_lower in guide["description"].lower()
        topics_match = any(query_lower in topic.lower() for topic in guide.get("topics", []))

        if title_match or desc_match or topics_match:
            results.append(guide)
    return results


@app.get(
    "/guides/{title}",
    response_model=Dict[str, Union[str, List[str]]],
    summary="Get details of a specific AI guide"
)
async def get_ai_guide_details(title: str) -> Dict[str, Union[str, List[str]]]:
    """Retrieves the full details of a specific AI guide by its exact title.

    Args:
        title: The exact title of the AI guide.

    Returns:
        A dictionary containing the full details of the AI guide.

    Raises:
        HTTPException: If the AI guide is not found (status code 404).
    """
    logger.info(f"Fetching details for AI guide: '{title}'.")
    guide = _find_guide_by_title(title)
    if guide is None:
        logger.warning(f"AI guide not found: '{title}'.")
        raise HTTPException(status_code=404, detail="AI guide not found")
    return guide


@app.get(
    "/guides/{title}/download-url",
    response_model=Dict[str, str],
    summary="Get download URL for a specific AI guide"
)
async def get_ai_guide_download_url(title: str) -> Dict[str, str]:
    """Provides the direct download URL for a specific AI guide by its title.

    Args:
        title: The exact title of the AI guide.

    Returns:
        A dictionary containing the download URL.

    Raises:
        HTTPException: If the AI guide is not found (status code 404).
    """
    logger.info(f"Fetching download URL for AI guide: '{title}'.")
    guide = _find_guide_by_title(title)
    if guide is None:
        logger.warning(f"AI guide not found for download URL: '{title}'.")
        raise HTTPException(status_code=404, detail="AI guide not found")
    
    # The type hint `Union[str, List[str]]` on AI_GUIDES_DATA forces a check here
    download_url_value = guide.get("download_url")
    if isinstance(download_url_value, str):
        return {"download_url": download_url_value}
    else:
        logger.error(f"Download URL for '{title}' is not a string: {download_url_value}")
        raise HTTPException(status_code=500, detail="Download URL not available or malformed")


# --- Gemini-Enhanced Endpoints ---

@app.post(
    "/guides/search/gemini",
    response_model=Dict[str, Any],
    summary="Search guides using Gemini AI with grounding"
)
async def search_guides_with_gemini(request: GeminiSearchRequest) -> Dict[str, Any]:
    """Uses Gemini AI's grounding capabilities for intelligent semantic search across guides.
    
    Args:
        request: Search request with query and grounding option
        
    Returns:
        Search results with relevance scores and reasoning
    """
    try:
        from gemini_service import get_gemini_service
        gemini = get_gemini_service()
        
        logger.info(f"Gemini search requested: '{request.query}' (grounding: {request.use_grounding})")
        
        if request.use_grounding:
            result = await gemini.search_with_grounding(request.query, AI_GUIDES_DATA)
        else:
            # Fallback to regular search if grounding not requested
            guides = await search_ai_guides(request.query)
            result = {
                "success": True,
                "grounded_search": False,
                "results": {
                    "matched_guides": [g["title"] for g in guides],
                    "search_reasoning": "Standard keyword-based search"
                }
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Gemini search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gemini search failed: {str(e)}")


@app.get(
    "/guides/{title}/analyze",
    response_model=Dict[str, Any],
    summary="Analyze guide content using Gemini AI"
)
async def analyze_guide_with_gemini(title: str) -> Dict[str, Any]:
    """Analyzes a guide's content using Gemini AI to extract insights and summaries.
    
    Args:
        title: The exact title of the AI guide
        
    Returns:
        Enhanced analysis including summary, learning objectives, and recommendations
    """
    try:
        guide = _find_guide_by_title(title)
        if guide is None:
            raise HTTPException(status_code=404, detail="AI guide not found")
        
        from gemini_service import get_gemini_service
        gemini = get_gemini_service()
        
        logger.info(f"Analyzing guide with Gemini: '{title}'")
        result = await gemini.generate_guide_summary(guide)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gemini analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gemini analysis failed: {str(e)}")


@app.post(
    "/guides/analyze-url",
    response_model=Dict[str, Any],
    summary="Analyze guide content from URL using Gemini AI"
)
async def analyze_url_with_gemini(url: str = Query(..., description="URL of the guide to analyze")) -> Dict[str, Any]:
    """Fetches and analyzes content from a guide URL using Gemini AI.
    
    Args:
        url: URL of the guide to analyze
        
    Returns:
        Content analysis including topics, takeaways, and recommendations
    """
    try:
        from gemini_service import get_gemini_service
        gemini = get_gemini_service()
        
        logger.info(f"Analyzing URL with Gemini: '{url}'")
        result = await gemini.analyze_guide_url(url)
        
        return result
        
    except Exception as e:
        logger.error(f"URL analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"URL analysis failed: {str(e)}")


@app.post(
    "/guides/compare",
    response_model=Dict[str, Any],
    summary="Compare multiple guides using Gemini AI"
)
async def compare_guides_with_gemini(request: GuideComparisonRequest) -> Dict[str, Any]:
    """Compares multiple AI guides to identify differences, overlaps, and recommendations.
    
    Args:
        request: List of guide titles to compare
        
    Returns:
        Comprehensive comparison including differences, overlaps, and reading order
    """
    try:
        if len(request.guide_titles) < 2:
            raise HTTPException(status_code=400, detail="At least 2 guides required for comparison")
        
        if len(request.guide_titles) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 guides can be compared at once")
        
        from gemini_service import get_gemini_service
        gemini = get_gemini_service()
        
        logger.info(f"Comparing {len(request.guide_titles)} guides with Gemini")
        result = await gemini.compare_guides(request.guide_titles, AI_GUIDES_DATA)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Guide comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Guide comparison failed: {str(e)}")
