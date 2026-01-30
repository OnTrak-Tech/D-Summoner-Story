"""
Google Gemini API Client
Provides AI-powered text generation using the Gemini API.
Replaces Bedrock for cost-efficiency and performance.
"""

import json
import os
import logging
from typing import Any, Dict, Optional
import urllib.request
import urllib.parse
import urllib.error

logger = logging.getLogger(__name__)


class GeminiAPIError(Exception):
    """Custom exception for Gemini API errors"""
    pass


class GeminiClient:
    """
    Google Gemini API client for text generation.
    
    Uses the Gemini API via REST for lightweight integration
    without requiring heavy SDK dependencies.
    """
    
    # Default model - gemini-1.5-flash is cost-effective for text generation
    DEFAULT_MODEL = "gemini-1.5-flash"
    API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key. If not provided, will be fetched from SSM.
        """
        self._api_key = api_key
        self._cached_key = None
        
    @property
    def api_key(self) -> str:
        """Get API key, fetching from SSM if needed."""
        if self._api_key:
            return self._api_key
            
        if self._cached_key:
            return self._cached_key
            
        # Fetch from SSM Parameter Store
        from shared.aws_clients import get_ssm_client
        
        ssm = get_ssm_client()
        ssm_path = os.environ.get('SSM_PATH_PREFIX', '/summoner-story/dev')
        
        try:
            response = ssm.get_parameter(
                Name=f"{ssm_path}/gemini-api-key",
                WithDecryption=True
            )
            self._cached_key = response['Parameter']['Value']
            return self._cached_key
        except Exception as e:
            logger.error(f"Failed to get Gemini API key from SSM: {e}")
            raise GeminiAPIError(f"Failed to retrieve Gemini API key: {e}")
    
    def generate_content(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> str:
        """
        Generate text content using Gemini API.
        
        Args:
            prompt: The input prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Creativity level (0.0 - 1.0)
            model: Model to use (default: gemini-1.5-flash)
            
        Returns:
            Generated text content
        """
        model = model or self.DEFAULT_MODEL
        url = f"{self.API_BASE}/{model}:generateContent"
        
        params = urllib.parse.urlencode({"key": self.api_key})
        full_url = f"{url}?{params}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
                "topP": 0.95,
                "topK": 40
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                full_url,
                data=data,
                headers={
                    'Content-Type': 'application/json'
                },
                method='POST'
            )
            
            logger.debug(f"Calling Gemini API with model {model}")
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode())
                
            # Extract generated text from response
            candidates = result.get("candidates", [])
            if not candidates:
                raise GeminiAPIError("No response candidates from Gemini API")
                
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            
            if not parts:
                raise GeminiAPIError("No content parts in Gemini response")
                
            generated_text = parts[0].get("text", "")
            
            logger.info(f"Gemini generated {len(generated_text)} characters")
            return generated_text
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            logger.error(f"Gemini API HTTP error {e.code}: {error_body}")
            raise GeminiAPIError(f"Gemini API error {e.code}: {error_body}")
            
        except urllib.error.URLError as e:
            logger.error(f"Gemini API connection error: {e.reason}")
            raise GeminiAPIError(f"Gemini API connection error: {e.reason}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini API response: {e}")
            raise GeminiAPIError(f"Invalid response from Gemini API: {e}")
    
    def generate_json(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.5
    ) -> Any:
        """
        Generate JSON content using Gemini API.
        
        Args:
            prompt: The input prompt (should request JSON output)
            max_tokens: Maximum tokens to generate
            temperature: Creativity level (lower for JSON)
            
        Returns:
            Parsed JSON object
        """
        # Add JSON instruction to prompt
        json_prompt = f"{prompt}\n\nRespond ONLY with valid JSON, no markdown or additional text."
        
        response = self.generate_content(
            prompt=json_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Clean up response - remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first line (```json or ```) and last line (```)
            lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            cleaned = "\n".join(lines)
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Gemini JSON response: {e}")
            # Return the raw text if JSON parsing fails
            return response


# Singleton instance
_gemini_client = None


def get_gemini_client() -> GeminiClient:
    """Get singleton Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
