import os
from typing import TypedDict, List, Tuple

import requests
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


class ExecuteQueryParams(TypedDict):
    query: str
    _thoughts: str


def execute_query(params: ExecuteQueryParams) -> str:
    params.pop('_thoughts', None)
    response = requests.get(
        url=f"{os.getenv('AG3NTS_HQ_URL')}/apidb",
        json={
            "task": "database",
            "apikey": os.getenv('AG3NTS_API_KEY'),
            "query": params['query']
        }
    )
    return response.json()['reply']


def get_mysql_data() -> Tuple[List[Tuple[int, str]], List[Tuple[int, int]]]:
    # Get users data
    users_query = ExecuteQueryParams(
        query="SELECT id, username FROM users",
        _thoughts=""
    )
    users_data = execute_query(users_query)
    print(users_data)
    users = [(row['id'], row['username']) for row in users_data]

    # Get connections data
    connections_query = ExecuteQueryParams(
        query="SELECT user1_id, user2_id FROM connections",
        _thoughts=""
    )
    connections_data = execute_query(connections_query)
    print(connections_data)
    connections = [(row['user1_id'], row['user2_id']) for row in connections_data]

    return users, connections


def setup_neo4j_database(uri: str, username: str, password: str, users: List[Tuple[int, str]],
                         connections: List[Tuple[int, int]]):
    print("Setting up Neo4j database...")
    print(users)
    print(connections)
    driver = GraphDatabase.driver(uri, auth=(username, password))

    with driver.session() as session:
        # Clear existing data
        session.run("MATCH (n) DETACH DELETE n")

        # Create users
        for user_id, name in users:
            session.run(
                "CREATE (p:Person {id: $id, name: $name})",
                id=user_id, name=name
            )

        # Create relationships
        for source_id, target_id in connections:
            session.run("""
                MATCH (a:Person {id: $source_id})
                MATCH (b:Person {id: $target_id})
                CREATE (a)-[:KNOWS]->(b)
            """, source_id=source_id, target_id=target_id)

    return driver


def find_shortest_path(driver: GraphDatabase.driver) -> str:
    with driver.session() as session:
        result = session.run("""
            MATCH p=shortestPath(
                (start:Person {name: 'Rafał'})-[:KNOWS*]-(end:Person {name: 'Barbara'})
            )
            RETURN [node in nodes(p) | node.name] as path
        """)

        path = result.single()['path']
        return ', '.join(path)


def submit_solution(path: str):
    response = requests.post(
        url=f"{os.getenv('AG3NTS_HQ_URL')}/report",
        json={
            "task": "connections",
            "apikey": os.getenv('AG3NTS_API_KEY'),
            "answer": path
        }
    )
    return response.json()


def main():
    # Neo4j connection details - adjust these according to your setup
    NEO4J_URI = "neo4j://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "neo4jlocal"

    # Get data from MySQL
    users, connections = get_mysql_data()

    # Setup Neo4j database and get driver
    driver = setup_neo4j_database(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, users, connections)

    try:
        # Find shortest path
        path = find_shortest_path(driver)

        # Submit solution
        result = submit_solution(path)
        print(f"Submission result: {result}")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
