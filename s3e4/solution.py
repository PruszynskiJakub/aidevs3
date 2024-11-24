import asyncio
import json
import os
from dataclasses import dataclass
from typing import Set, List

import requests
from dotenv import load_dotenv

import api
from services import OpenAiService

# Load environment variables at the start
load_dotenv()


@dataclass
class SearchState:
    processed_names: Set[str] = None
    processed_cities: Set[str] = None
    unprocessed_names: Set[str] = None
    unprocessed_cities: Set[str] = None

    def __post_init__(self):
        self.processed_names = set()
        self.processed_cities = set()
        self.unprocessed_names = set()
        self.unprocessed_cities = set()

    def add_unprocessed_name(self, name: str):
        """Safely add name to unprocessed set"""
        if name and isinstance(name, str):
            self.unprocessed_names.add(name.strip())

    def add_unprocessed_city(self, city: str):
        """Safely add city to unprocessed set"""
        if city and isinstance(city, str):
            self.unprocessed_cities.add(city.strip())


class ResistanceTracker:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = os.getenv('AG3NTS_HQ_URL')  # Get base URL from env
        self.report_url = os.getenv('AG3NTS_HQ_URL_REPORT')  # Get report URL from env
        self.state = SearchState()
        self.openai_service = OpenAiService()  # Add OpenAI service

    def _make_api_request(self, endpoint: str, query: str) -> dict:
        """Make API request with error handling"""
        try:
            print(f"Making API request to {endpoint} with query: {query}")
            url = f"{self.base_url}/{endpoint}"
            payload = {
                "apikey": self.api_key,
                "query": query.upper()
            }
            response = requests.post(url, json=payload)
            # response.raise_for_status()
            print(f"API response: {response.text}")
            return response.json()
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            raise

    def search_person(self, name: str) -> List[str]:
        """Search for locations where a person was seen"""
        split = name.split(" ")
        response = self._make_api_request("people", split[0])
        if response.get('code') == 0:
            return response.get('message', '').split()
        return []

    def search_place(self, city: str) -> List[str]:
        """Search for people seen in a given city"""
        response = self._make_api_request("places", city)
        if response.get('code') == 0:
            return response.get('message', '').split()
        return []

    def get_initial_data(self) -> str:
        """Download and return the initial data file"""
        response = requests.get(f"{self.base_url}/dane/barbara.txt")
        print(response.text)
        return response.text

    async def extract_names_and_cities(self, text: str):
        """Extract names and cities using LLM"""
        try:
            prompt = [
                {
                    "role": "system",
                    "content": """You are an expert at extracting names and locations from Polish text.
                    Return the response as JSON with two arrays: 'names' for person names and 'cities' for city names.
                    Convert city names to basic Latin characters (without Polish diacritics).
                    Names should be in nominative case.
                    Example format:
                    {
                        "names": ["BARBARA", "JAN"],
                        "cities": ["KRAKOW", "WARSZAWA"]
                    }
                    Return pure JSON, nothing else, no extra formatting or ```.
                    """
                },
                {
                    "role": "user",
                    "content": text
                }
            ]

            response = await self.openai_service.completion(messages=prompt)
            print(f"LLM response: {response.choices[0].message.content}")
            try:
                extracted_data = json.loads(response.choices[0].message.content)
                if not isinstance(extracted_data,
                                  dict) or 'names' not in extracted_data or 'cities' not in extracted_data:
                    raise ValueError("Invalid response format from LLM")
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON response from LLM")

            # Add extracted data to our search state
            self.state.unprocessed_names.update(extracted_data.get('names', []))
            self.state.unprocessed_cities.update(extracted_data.get('cities', []))

        except Exception as e:
            print(f"Error in extract_names_and_cities: {e}")
            raise

    def report_location(self, city: str):
        """Report Barbara's location to the central system"""
        api.answer("loop", city)

        # return response.json()

    async def find_barbara(self, max_iterations: int = 10) -> str:
        """Find Barbara's location through iterative searching"""
        initial_data = self.get_initial_data()
        await self.extract_names_and_cities(initial_data)
        self.state.unprocessed_names.remove("BARBARA ZAWADZKA")
        self.state.unprocessed_cities.remove("KRAKOW")

        iteration = 0
        while iteration < max_iterations:
            # Process unprocessed names
            while self.state.unprocessed_names:
                name = self.state.unprocessed_names.pop()
                if name in self.state.processed_names:
                    continue

                locations = self.search_person(name)
                self.state.processed_names.add(name)

                for location in locations:
                    if location not in self.state.processed_cities:
                        self.state.unprocessed_cities.add(location)

            # Process unprocessed cities
            while self.state.unprocessed_cities:
                city = self.state.unprocessed_cities.pop()
                if city in self.state.processed_cities:
                    continue

                people = self.search_place(city)
                self.state.processed_cities.add(city)

                # Look for BARBARA in the list of people
                # We know that she is not present in Kraków
                if "BARBARA" in people and city != "KRAKOW":
                    return city

                for person in people:
                    if person not in self.state.processed_names:
                        self.state.unprocessed_names.add(person)

            if not (self.state.unprocessed_names or self.state.unprocessed_cities):
                break

            iteration += 1

        raise Exception("Barbara not found within maximum iterations")


async def main():
    try:
        api_key = os.getenv('AG3NTS_API_KEY')
        if not api_key:
            raise ValueError("API key not found in environment variables")

        tracker = ResistanceTracker(api_key)

        barbara_location = await tracker.find_barbara()
        print(f"Barbara found in: {barbara_location}")

        tracker.report_location(barbara_location)
        # print(f"Report response: {response}")

    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
