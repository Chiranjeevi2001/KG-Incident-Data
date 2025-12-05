from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, Neo4jError, ConfigurationError
from dotenv import load_dotenv
import os
import time
import sys
from typing import Optional, Tuple


load_dotenv(".env", override=True)

def _require(value: Optional[str], name: str) -> str:
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


URI: str = _require(os.getenv("NEO4J_URI"), "NEO4J_URI")
USERNAME: str = _require(os.getenv("NEO4J_USERNAME"), "NEO4J_USERNAME")
PASSWORD: str = _require(os.getenv("NEO4J_PASSWORD"), "NEO4J_PASSWORD")
DATABASE: str = os.getenv("NEO4J_DATABASE") or "neo4j"


AUTH = (USERNAME, PASSWORD)

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    summary = driver.execute_query("""
    CREATE (a:Person {name: $name})
    CREATE (b:Person {name: $friendName})
    CREATE (a)-[:KNOWS]->(b)
    """,
    name="Alice", friendName="David",
    database_="neo4j",
    ).summary
    print("Created {nodes_created} nodes in {time} ms.".format(
        nodes_created=summary.counters.nodes_created,
        time=summary.result_available_after
    ))