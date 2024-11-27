import json
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


class FinalAnswerTool(AgentTool):
    """Tool for preparing the final answer based on key findings"""

    name = "final_answer"
    description = """
    Prepares a final answer using the key findings and the original task description.
    """
    required_params = {
        "key_findings": "The key findings to base the final answer on",
        "task_description": "The original task description"
    }

    def __init__(self, llm_service):
        """
        Initialize the tool with LLM service

        Args:
            llm_service: Service for LLM interactions
        """
        super().__init__()
        self.llm_service = llm_service

    def execute(self, params: Dict[str, Any]) -> Union[str, None]:
        """
        Prepares the final answer using the key findings and an LLM.
        
        Args:
            params (dict): Dictionary containing:
                - key_findings (List[str]): The key findings to base the final answer on
                - task_description (str): The original task description

        Returns:
            str: The final answer based on the task description and key findings
            
        Raises:
            ValueError: If required parameters are missing
        """
        self.logger.info("Preparing final answer based on key findings using LLM")

        if not params.get("key_findings"):
            raise ValueError("Key findings parameter is required")
        if not params.get("task_description"):
            raise ValueError("Task description parameter is required")

        # Prepare the prompt for the LLM
        prompt = f"""
        Task Description: {params["task_description"]}

        Key Findings:
        {json.dumps(params["key_findings"], indent=2)}

        Based on the task description and the key findings provided, generate a final answer.
        The answer should directly address the task description and incorporate relevant key findings.

        Final Answer:
        """

        # Call the LLM service to generate the final answer
        try:
            response = self.llm_service.completion(
                messages=[{"role": "system", "content": prompt}],
                max_tokens=500
            )
            final_answer = response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"Error generating final answer with LLM: {e}")
            return None

        self.logger.info("Final answer prepared successfully using LLM")
        return final_answer
