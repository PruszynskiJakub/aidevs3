import logging
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Union, List

import requests


class AgentTool(ABC):
    """Base class for all agent tools"""

    name = "base_tool"
    description = "Base tool description"
    required_params = {}
    optional_params = {}

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def execute(self, params: dict) -> any:
        """Execute the tool with given parameters"""
        pass


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class MakeApiCallTool(AgentTool):
    """Generic tool for making API calls"""

    name = "make_api_call"
    description = """
    Makes an HTTP request to a specified API endpoint.
    Supports various HTTP methods and custom payloads.
    """
    required_params = {
        "url": "The API endpoint URL to call",
        "method": "HTTP method to use (GET, POST, PUT, DELETE, PATCH)"
    }
    optional_params = {
        "payload": "Data to send with the request (for POST, PUT, PATCH methods)",
    }

    def execute(self, params: Dict[str, Any]) -> Union[Dict, None]:
        """
        Makes an API call with the specified parameters.
        
        Args:
            params (dict): Dictionary containing:
                - url (str): The API endpoint URL (can contain [[PLACEHOLDER]] patterns)
                - method (str): HTTP method to use
                - payload (dict, optional): Data to send with the request
        
        Returns:
            dict: API response parsed as JSON
            
        Raises:
            ValueError: If required parameters are missing or invalid
            requests.RequestException: If API request fails
        """
        self.logger.info(f"Making API call to: {params.get('url')} with method: {params.get('method')}")

        # Validate required parameters
        if not params.get("url"):
            raise ValueError("URL parameter is required")
        if not params.get("method"):
            raise ValueError("Method parameter is required")

        # Parse and validate HTTP method
        try:
            method = HttpMethod(params["method"].upper())
        except ValueError:
            raise ValueError(f"Invalid HTTP method. Must be one of: {[m.value for m in HttpMethod]}")

        # Replace placeholders in URL
        url = params["url"]
        placeholders = self._extract_placeholders(url)
        for placeholder in placeholders:
            env_value = os.getenv(placeholder)
            if env_value is None:
                raise ValueError(f"Environment variable {placeholder} not found for placeholder [[{placeholder}]]")
            url = url.replace(f"[[{placeholder}]]", env_value)

        # Prepare request kwargs
        request_kwargs = {}

        # Add payload for appropriate methods
        if method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH]:
            payload = params.get("payload", {})
            request_kwargs['json'] = payload

        try:
            response = requests.request(method.value, url, **request_kwargs)
            response.raise_for_status()
            result = response.json()
            self.logger.info(f"API call successful: {response.status_code}")
            return result
        except requests.RequestException as e:
            self.logger.error(f"Error making API call: {e}")
            return None

    def _extract_placeholders(self, url: str) -> List[str]:
        """
        Extracts placeholder names from URL string.
        Example: "api/[[API_KEY]]/data" -> ["API_KEY"]
        """
        import re
        pattern = r'\[\[(.*?)\]\]'
        return re.findall(pattern, url)


class WebScrapeTool(AgentTool):
    """Tool for scraping web content using Jina API"""

    name = "web_scrape"
    description = """
    Scrapes web content from a given URL using Jina API.
    Returns the content with an optional summary including links.
    """
    required_params = {
        "url": "The URL of the webpage to scrape"
    }
    optional_params = {}

    def execute(self, params: Dict[str, Any]) -> Union[Dict, None]:
        """
        Scrapes web content using Jina API.
        
        Args:
            params (dict): Dictionary containing:
                - url (str): The webpage URL to scrape

        Returns:
            dict: Scraped content response
            
        Raises:
            ValueError: If required parameters are missing
            requests.RequestException: If scraping request fails
        """
        self.logger.info(f"Scraping web content from: {params.get('url')}")

        if not params.get("url"):
            raise ValueError("URL parameter is required")

        jina_api_key = os.getenv("JINA_API_KEY")
        if not jina_api_key:
            raise ValueError("JINA_API_KEY environment variable is required")

        headers = {
            "Authorization": f"Bearer {jina_api_key}",
            'Accept': 'application/json',
            "X-With-Links-Summary": "true"
        }

        try:
            response = requests.get(
                f"https://r.jina.ai/{params['url']}",
                headers=headers
            )
            response.raise_for_status()

            result = response.json()
            self.logger.info(f"Web scraping successful: {response.status_code}")
            return {
                "content": result.get("data")['content'],
            }
        except requests.RequestException as e:
            self.logger.error(f"Error scraping web content: {e}")
            return None
