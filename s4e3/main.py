import json
import logging
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Union, List

import requests
from dotenv import load_dotenv

load_dotenv()


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
    optional_params = {
        "include_links_summary": "Boolean to include links summary in response (default: True)"
    }

    def execute(self, params: Dict[str, Any]) -> Union[Dict, None]:
        """
        Scrapes web content using Jina API.
        
        Args:
            params (dict): Dictionary containing:
                - url (str): The webpage URL to scrape
                - include_links_summary (bool, optional): Include links summary
        
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
            "X-With-Links-Summary": str(params.get("include_links_summary", True)).lower()
        }

        try:
            response = requests.get(
                f"https://r.jina.ai/{params['url']}",
                headers=headers
            )
            response.raise_for_status()

            result = response.json()
            self.logger.info(f"Web scraping successful: {response.status_code}")
            return result
        except requests.RequestException as e:
            self.logger.error(f"Error scraping web content: {e}")
            return None


class Agent:
    """Agent that can understand tasks and execute tools"""

    def __init__(self, available_tools: List[AgentTool], llm_service):
        """
        Initialize the agent with tools and LLM service
        
        Args:
            available_tools (List[AgentTool]): List of tools available to the agent
            llm_service: OpenAiService instance for LLM interactions
        """
        self.tools = {tool.name: tool for tool in available_tools}
        self.llm_service = llm_service
        self.memory = {}
        self.current_context = {}

    async def run(self, task_description: str) -> Any:
        """
        Main entry point for task execution. Creates execution plan and handles the execution flow.
        
        Args:
            task_description (str): Description of the task to perform
            
        Returns:
            Any: Result of the task execution
            
        Raises:
            Exception: If task execution fails
        """
        try:
            # Create execution plan
            execution_plan = await self.plan(task_description)

            # Execute each step in the plan
            for step in execution_plan['plan']:
                result = await self.execute(step)

                # Update context with result
                self.current_context[step['step']] = result

                # Extract required information
                if result:
                    await self._extract_information(
                        result,
                        execution_plan['required_information']
                    )

            return self.memory
            
        except Exception as e:
            print(f"Error executing task: {e}")
            raise

    async def plan(self, task_description: str) -> Dict[str, Any]:
        """
        Creates a multi-step execution plan for the given task.
        
        Args:
            task_description (str): Description of the task to perform
            
        Returns:
            dict: Contains execution plan with steps and required information
        """
        prompt = f"""Given the following task description, create a plan of actions and determine which tools to use.
        Available tools:
        {self._format_tools_for_prompt()}
        
        Task description: {task_description}
        Current context: {self.current_context}
        Previous findings: {self.memory}
        
        <rules>
        1. Keep any placeholders in the format [[PLACEHOLDER_NAME]] exactly as they are - do not modify or replace them.
        </rules>        
        
        Respond in the following JSON format:
        {{
            "_thinking": "Describe your thought process here about how you're approaching this task, what considerations you're making, and why you're choosing specific steps",
            "plan": [
                {{
                    "step": "description of the step",
                    "tool_name": "name of the tool to use", 
                    "parameters": {{
                        parameters to pass to the tool
                    }}
                }}
            ],
            "required_information": [
                "list of information we need to extract to complete the task: {task_description}"
            ]
        }}
        """

        response = await self.llm_service.completion(
            messages=[
                {"role": "system", "content": prompt},
            ],
            response_format={"type": "json_object"}
        )
        
        print(response.choices[0].message.content)

        try:
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    async def execute(self, step: Dict[str, Any]) -> Any:
        """
        Executes a single step from the execution plan.
        
        Args:
            step (dict): Step information containing tool_name and parameters
            
        Returns:
            Any: Result of the tool execution
        """
        tool_name = step['tool_name']
        parameters = step['parameters']

        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool = self.tools[tool_name]
        return tool.execute(parameters)

    async def _extract_information(self, content: Any, required_info: List[str]):
        """Extract specific information from content"""
        prompt = f"""
        From the following content, extract information about: {required_info}
        
        Content: {content}
        
        Respond with only the relevant information in JSON format.
        """

        response = await self.llm_service.completion(
            messages=[
                {"role": "system", "content": prompt},
            ],
            response_format={"type": "json_object"}
        )

        extracted_info = json.loads(response.choices[0].message.content)
        self.memory.update(extracted_info)

    def _format_tools_for_prompt(self) -> str:
        """Formats the available tools into a string for the prompt"""
        tool_descriptions = []
        for tool in self.tools.values():
            desc = f"Tool: {tool.name}\n"
            desc += f"Description: {tool.description}\n"
            desc += "Required parameters:\n"
            for param, param_desc in tool.required_params.items():
                desc += f"- {param}: {param_desc}\n"
            if hasattr(tool, 'optional_params'):
                desc += "Optional parameters:\n"
                for param, param_desc in tool.optional_params.items():
                    desc += f"- {param}: {param_desc}\n"
            tool_descriptions.append(desc)
        return "\n".join(tool_descriptions)


# Example usage
if __name__ == "__main__":
    import asyncio
    from services import OpenAiService

    async def main():
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create available tools
        api_tool = MakeApiCallTool()
        web_scrape_tool = WebScrapeTool()

        # Create LLM service and agent
        llm_service = OpenAiService()
        agent = Agent([api_tool, web_scrape_tool], llm_service)

        # Example task
        task = """Fetch the questions data from the [[AG3NTS_HQ_URL]]/data/[[AG3NTS_API_KEY]]/softo.json using the API key. 
        Then answer the questions in the data with the content available on under this url https://softo.ag3nts.org."""

        result = await agent.run(task)
        if result:
            print(result)

    asyncio.run(main())
