import json
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Union, List

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
                - url (str): The API endpoint URL (can contain [[PLACEHOLDER]] patterns)
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
            return response.json()
        except requests.RequestException as e:
            print(f"Error making API call: {e}")
            return None

    def _extract_placeholders(self, url: str) -> List[str]:
        """
        Extracts placeholder names from URL string.
        Example: "api/[[API_KEY]]/data" -> ["API_KEY"]
        """
        import re
        pattern = r'\[\[(.*?)\]\]'
        return re.findall(pattern, url)


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

    async def run(self, task_description: str) -> Any:
        """
        Main method to run a task. Handles the execution flow and error handling.
        
        Args:
            task_description (str): Description of the task to perform
            
        Returns:
            Any: Result of the task execution
            
        Raises:
            Exception: If task execution fails
        """
        try:
            result = await self.execute_task(task_description)
            if result:
                print("Task executed successfully:")
                return result
            else:
                print("Task execution failed")
                return None
        except Exception as e:
            print(f"Error executing task: {e}")
            raise

    async def analyze_task(self, task_description: str) -> Dict[str, Any]:
        """
        Analyzes the task description and determines which tool to use and with what parameters
        
        Args:
            task_description (str): Description of the task to perform
            
        Returns:
            dict: Contains 'tool_name' and 'parameters' for the selected tool
        """
        prompt = f"""Given the following task description, determine which tool to use and what parameters to pass to it.
        Available tools:
        {self._format_tools_for_prompt()}
        
        Task description: {task_description}
        
        Respond in the following JSON format:
        {{
            "tool_name": "name of the tool to use",
            "parameters": {{
                // parameters to pass to the tool
            }}
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

    async def execute_task(self, task_description: str) -> Any:
        """
        Analyzes and executes the given task using appropriate tool
        
        Args:
            task_description (str): Description of the task to perform
            
        Returns:
            Any: Result of the tool execution
        """
        analysis = await self.analyze_task(task_description)
        tool_name = analysis['tool_name']
        parameters = analysis['parameters']

        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool = self.tools[tool_name]
        return tool.execute(parameters)


# Example usage
if __name__ == "__main__":
    import asyncio
    from services import OpenAiService

    async def main():
        # Create available tools
        api_tool = MakeApiCallTool()

        # Create LLM service and agent
        llm_service = OpenAiService()
        agent = Agent([api_tool], llm_service)

        # Example task
        task = """Fetch the questions data from the [[AG3NTS_HQ_URL]]/data/[[AG3NTS_API_KEY]]/softo.json using the API key"""

        result = await agent.run(task)
        if result:
            print(result)

    asyncio.run(main())
