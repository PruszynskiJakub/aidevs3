import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Union

import requests
from dotenv import load_dotenv

load_dotenv()


class AgentTool(ABC):
    """Base class for all agent tools"""

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
                - url (str): The API endpoint URL
                - method (str): HTTP method to use
                - payload (dict, optional): Data to send with the request
        
        Returns:
            dict: API response parsed as JSON
            
        Raises:
            ValueError: If required parameters are missing or invalid
            requests.RequestException: If API request fails
        """
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

        # Prepare request parameters
        url = params["url"]

        # Prepare request kwargs
        request_kwargs = {}

        # Add payload for appropriate methods
        if method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH]:
            payload = params.get("payload", {})
            request_kwargs['json'] = payload

        try:
            response = requests.request(method.value, url, **request_kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error making API call: {e}")
            return None


# Example of how to use it to fetch questions
if __name__ == "__main__":
    api_tool = MakeApiCallTool()

    # Recreating the original fetch_questions functionality
    base_url = os.getenv('AG3NTS_HQ_URL')
    api_key = os.getenv('AG3NTS_API_KEY')

    questions = api_tool.execute({
        "url": f"{base_url}/data/{api_key}/softo.json",
        "method": "GET",
    })

    if questions:
        print("Fetched questions:")
        for question_id, question in questions.items():
            print(f"{question_id}: {question}")
