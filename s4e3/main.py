import logging

from dotenv import load_dotenv

from agent import Agent
from agent_tools import FinalAnswerTool, MakeApiCallTool, WebScrapeTool

load_dotenv()

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

        llm_service = OpenAiService()
        
        # Create available tools
        api_tool = MakeApiCallTool()
        web_scrape_tool = WebScrapeTool()
        final_answer_tool = FinalAnswerTool(llm_service=llm_service)

        # Create agent
        agent = Agent([api_tool, web_scrape_tool, final_answer_tool], llm_service)

        # Example task
        task = """Fetch the questions data from the [[AG3NTS_HQ_URL]]/data/[[AG3NTS_API_KEY]]/softo.json using the API key. 
        Then answer the questions in the data with the content available on under this url https://softo.ag3nts.org. 
        If you cannot find the answer in the content, try to find it on relevant subpages.
        
        The expected output is a JSON object with the following structure:
        {
            "questionID like 01": "concise and specific answer to the first question",
            ...
            "questionID like n": "concise and specific answer to the n-th question"
        }
        """

        result = await agent.run(task)
        if result:
            print(result)

    asyncio.run(main())
