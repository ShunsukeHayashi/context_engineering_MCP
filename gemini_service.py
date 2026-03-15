import logging
import os
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        
        # Initialize model with grounding capabilities
        self.model = genai.GenerativeModel(
            os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        logger.info("Gemini service initialized successfully")
    
    async def search_with_grounding(self, query: str, guides_data: List[Dict]) -> Dict[str, Any]:
        """
        Use Gemini's grounding to search through AI guides with semantic understanding
        """
        try:
            # Create context from guides data
            guides_context = "\n\n".join([
                f"Title: {guide['title']}\n"
                f"Publisher: {guide['publisher']}\n"
                f"Description: {guide['description']}\n"
                f"Topics: {', '.join(guide['topics'])}"
                for guide in guides_data
            ])
            
            prompt = f"""You are an AI assistant helping to search through AI guides. 
            Based on the following query and the available guides, provide the most relevant guides.
            
            Query: {query}
            
            Available Guides:
            {guides_context}
            
            Instructions:
            1. Analyze the query for intent and keywords
            2. Find guides that best match the query semantically
            3. Return a JSON response with:
               - matched_guides: Array of matching guide titles
               - relevance_scores: Object mapping titles to relevance scores (0-1)
               - search_reasoning: Brief explanation of why these guides match
            
            Respond only with valid JSON."""
            
            response = self.model.generate_content(prompt)
            
            # Parse the response
            import json
            result = json.loads(response.text)
            
            return {
                "success": True,
                "grounded_search": True,
                "results": result
            }
            
        except Exception as e:
            logger.error(f"Grounding search error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "grounded_search": True
            }
    
    async def analyze_guide_url(self, url: str) -> Dict[str, Any]:
        """
        Extract and analyze content from a guide URL using Gemini
        """
        try:
            # First, fetch the URL content
            import requests
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to fetch URL: {response.status_code}"
                }
            
            # For demonstration, we'll analyze the page content
            # In a real implementation, you'd parse PDFs, extract text, etc.
            prompt = f"""Analyze this AI guide URL and provide a comprehensive summary.
            
            URL: {url}
            Content Preview: {response.text[:2000]}
            
            Provide:
            1. Main topics covered
            2. Key takeaways
            3. Target audience
            4. Practical applications
            5. Prerequisites or recommended knowledge
            
            Format as JSON with these keys: topics, takeaways, audience, applications, prerequisites"""
            
            response = self.model.generate_content(prompt)
            
            import json
            analysis = json.loads(response.text)
            
            return {
                "success": True,
                "url": url,
                "analysis": analysis,
                "analyzed_with": os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
            }
            
        except Exception as e:
            logger.error(f"URL analysis error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    async def generate_guide_summary(self, guide: Dict) -> Dict[str, Any]:
        """
        Generate an enhanced summary of a guide using Gemini
        """
        try:
            prompt = f"""Create a comprehensive summary for this AI guide:
            
            Title: {guide['title']}
            Publisher: {guide['publisher']}
            Description: {guide['description']}
            Topics: {', '.join(guide['topics'])}
            
            Generate:
            1. Extended summary (2-3 paragraphs)
            2. Learning objectives
            3. Who should read this guide
            4. Estimated reading time
            5. Related guides or resources
            
            Format as JSON."""
            
            response = self.model.generate_content(prompt)
            
            import json
            summary = json.loads(response.text)
            
            return {
                "success": True,
                "guide_title": guide['title'],
                "enhanced_summary": summary
            }
            
        except Exception as e:
            logger.error(f"Summary generation error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "guide_title": guide.get('title', 'Unknown')
            }
    
    async def compare_guides(self, guide_titles: List[str], guides_data: List[Dict]) -> Dict[str, Any]:
        """
        Compare multiple guides and provide recommendations
        """
        try:
            # Filter guides by titles
            selected_guides = [g for g in guides_data if g['title'] in guide_titles]
            
            if not selected_guides:
                return {
                    "success": False,
                    "error": "No matching guides found"
                }
            
            guides_info = "\n\n".join([
                f"Guide {i+1}: {guide['title']}\n"
                f"Publisher: {guide['publisher']}\n"
                f"Description: {guide['description']}\n"
                f"Topics: {', '.join(guide['topics'])}"
                for i, guide in enumerate(selected_guides)
            ])
            
            prompt = f"""Compare these AI guides and provide insights:
            
            {guides_info}
            
            Provide:
            1. Key differences between the guides
            2. Overlapping content areas
            3. Recommended reading order
            4. Which guide is best for beginners vs advanced users
            5. Complementary aspects
            
            Format as JSON with keys: differences, overlaps, reading_order, audience_fit, complementary_aspects"""
            
            response = self.model.generate_content(prompt)
            
            import json
            comparison = json.loads(response.text)
            
            return {
                "success": True,
                "compared_guides": guide_titles,
                "comparison": comparison
            }
            
        except Exception as e:
            logger.error(f"Guide comparison error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
_gemini_service = None

def get_gemini_service() -> GeminiService:
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
