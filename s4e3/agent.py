import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from agent_tools import AgentTool


@dataclass
class ContextEntry:
    """Represents a single context entry from tool execution"""
    tool_name: str
    step_description: str
    parameters: Dict[str, Any]
    timestamp: datetime
    related_info: Dict[str, Any]


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
        self.context_history: List[ContextEntry] = []
        self.current_task: Optional[str] = None
        self.key_findings: List[str] = []

    async def run(self, task_description: str) -> Any:
        """
        Main entry point for task execution. Plans and executes one step at a time,
        evaluating progress after each step.

        Args:
            task_description (str): Description of the task to perform

        Returns:
            Any: Result of the task execution
        """
        self.current_task = task_description
        max_steps = 25  # Safety limit to prevent infinite loops
        step_count = 0

        try:
            while step_count < max_steps:
                # 1. Plan next step
                next_step = await self._plan_next_step(task_description)
                if not next_step['plan']:
                    print("No more steps needed - task complete")
                    break

                # 2. Execute the step
                print(f"Executing step {step_count}: {next_step['plan'][0]['step']}")
                result = await self.execute(next_step['plan'][0])

                # 3. Create and store context entry
                context_entry = ContextEntry(
                    tool_name=next_step['plan'][0]['tool_name'],
                    step_description=next_step['plan'][0]['step'],
                    parameters=next_step['plan'][0]['parameters'],
                    # result=result,
                    timestamp=datetime.now(),
                    related_info={}
                )

                # 4. Extract and evaluate information
                if result:
                    extracted_info = await self._extract_information(
                        result,
                        next_step['required_information']
                    )
                    context_entry.related_info = extracted_info['key_findings']
                    
                self.context_history.append(context_entry)

                # 5. Evaluate progress and decide whether to continue
                if next_step['plan'][0]['tool_name'] == 'final_answer':
                    return result

                step_count += 1

            return self.key_findings

        except Exception as e:
            print(f"Error executing task: {e}")
            raise

    async def _plan_next_step(self, task_description: str) -> Dict[str, Any]:
        """
        Plans the next single step based on current context and task description.
        """
        formatted_context = self._format_context_for_prompt()
        formatted_tools = self._format_tools_for_prompt()
        key_findings_str = json.dumps(self.key_findings, indent=2)

        prompt = f"""Given the task description, current context, and key findings, determine the SINGLE NEXT STEP to take.
        
        Available tools:
        {formatted_tools}
        
        Task description: {task_description}
        
        Current Context:
        {formatted_context}
        
        Key Findings:
        {key_findings_str}
                
        <rules>
        1. Plan only ONE next step that brings us closer to completing the task
        2. Keep any placeholders in the format [[PLACEHOLDER_NAME]]
        3. Consider the context history to avoid redundant operations
        4. Use ONLY the tools and parameters listed in the 'Available tools' section
        5. Base your decision on factual information from the key findings and context
        6. Do not introduce any information or assumptions not present in the provided data
        </rules>
        
        Respond in the following JSON format:
        {{
            "_thinking": "Explain why this specific step is the best next action, referencing key findings or context",
            "plan": [
                {{
                    "step": "description of the single next step",
                    "tool_name": "exact name of the tool to use from the available tools",
                    "parameters": {{
                        "param1": "value1",
                        "param2": "value2"
                    }}
                }}
            ],
            "required_information": [
                "list of specific information we need to extract from this step's result"
            ]
        }}
        """

        response = await self.llm_service.completion(
            messages=[{"role": "system", "content": prompt}],
            response_format={"type": "json_object"}
        )

        print("Next step plan:")
        print(response.choices[0].message.content)

        return json.loads(response.choices[0].message.content)

    async def _evaluate_progress(self, task_description: str) -> Dict[str, Any]:
        """
        Evaluates whether the current context and findings are sufficient to complete the task.
        """
        formatted_context = self._format_context_for_prompt()

        prompt = f"""Evaluate whether we have gathered enough information to complete the task.
        
        Task description: {task_description}
        
        Current Context:
        {formatted_context}
        
        Key findings so far: {self.key_findings}
        
        Respond in the following JSON format:
        {{
            "task_completed": true/false,
            "reasoning": "Detailed explanation of why the task is complete or what's missing",
            "missing_elements": ["List of any missing information or steps needed"],
            "confidence_score": 0.0-1.0
        }}
        """

        response = await self.llm_service.completion(
            messages=[{"role": "system", "content": prompt}],
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

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

    def _format_context_for_prompt(self) -> str:
        """Formats the context history into a readable string for the prompt"""
        if not self.context_history:
            return "No previous context available."

        context_entries = []
        for entry in self.context_history:
            context_str = (
                f"Step: {entry.step_description}\n"
                f"Tool Used: {entry.tool_name}\n"
                f"Parameters: {json.dumps(entry.parameters, indent=2)}\n"
                f"Related Information: {json.dumps(entry.related_info, indent=2)}\n"
                f"Timestamp: {entry.timestamp.isoformat()}\n"
                "---"
            )
            context_entries.append(context_str)

        return "\n".join(context_entries)

    async def _extract_information(self, content: Any, required_info: List[str]) -> Dict[str, Any]:
        """Extract specific information from content and return it"""
        prompt = f"""
        Analyze the following content and extract key information based on:
        1. The required information: {required_info}
        2. Information relevant to the current task: {self.current_task}
        3. Key findings crucial to complete the task: {self.key_findings}
        4. Information that might be useful for future steps
        5. Results and outcomes of actions taken

        Content: {content}

        Consider:
        - Direct answers to required information
        - Task progress indicators
        - Dependencies or prerequisites discovered
        - Action outcomes and their implications
        - Any constraints or limitations identified
        - If the content is the part of the main objective of the task then paste it without any formatting in key_findings

        Respond with a JSON object containing:
        {{
            "_thinking": "Explain the reasoning behind the extracted information",
            "related_directly_to_main_objective": "true/false",
            "key_findings": [
                "concise bullet list of information we need to extract to complete the task, if it is related to the main objective then paste {content} it without any formatting"
            ]
        }}
        
        """

        response = await self.llm_service.completion(
            messages=[
                {"role": "system", "content": prompt},
            ],
            response_format={"type": "json_object"}
        )
        print("Extracted information:")
        print(response.choices[0].message.content)

        extracted_info = json.loads(response.choices[0].message.content)
        # Update memory with structured information
        # if isinstance(extracted_info['key_findings'], dict):
        #     self.memory.update({
        #         'key_findings': {**self.memory.get('key_findings', {}), **extracted_info['key_findings']},
        #     })
        # else:
        #     self.memory['key_findings'] = extracted_info['key_findings']

        self.key_findings.extend(extracted_info['key_findings'])

        
        return extracted_info

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

    async def refine(self) -> Tuple[Dict[str, Any], List[str]]:
        """
        Analyzes current context and memory against the objective to identify gaps
        and determine next steps.

        Returns:
            Tuple[Dict[str, Any], List[str]]: Contains analysis results and identified gaps
        """
        if not self.current_task:
            raise ValueError("No active task to refine")

        formatted_context = self._format_context_for_prompt()

        prompt = f"""Analyze the current context and progress towards the following objective.
        
        Objective: {self.current_task}
        
        Context History:
        {formatted_context}
        
        Current Findings: {self.memory}
        
        Analyze the situation and respond in the following JSON format:
        {{
            "analysis": {{
                "progress": "Description of progress made so far",
                "key_findings": ["List of important discoveries"],
                "missing_information": ["Information gaps that need to be filled"],
                "inconsistencies": ["Any contradictions or unclear points in the data"],
                "suggested_actions": ["Specific actions to take next"]
            }},
            "confidence_score": "0-1 score indicating confidence in current findings",
            "requires_additional_context": true/false
        }}
        """

        response = await self.llm_service.completion(
            messages=[
                {"role": "system", "content": prompt},
            ],
            response_format={"type": "json_object"}
        )

        analysis_result = json.loads(response.choices[0].message.content)

        # Update memory with analysis
        self.memory['latest_analysis'] = {
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis_result
        }

        return (
            analysis_result,
            analysis_result['analysis']['missing_information']
        )
