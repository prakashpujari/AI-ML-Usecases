"""
Simple Neo4j demo for the ML_OPS workspace.

What it does:
- Connects to a Neo4j instance (bolt://localhost:7687 by default)
- Creates a few `Person` and `Company` nodes and `WORKS_AT` relationships
- Runs a sample query to list coworkers at the same company

Configure connection via environment variables:
- NEO4J_URI (default: bolt://localhost:7687)
- NEO4J_USER (default: neo4j)
- NEO4J_PASSWORD (default: password)

Run:
    pip install -r src/requirements.txt
    python src\neo4j_demo.py

Note: Start Neo4j (Docker, Desktop, or server) before running this script.
"""

import os
import sys
from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")


def create_demo_graph(driver):
    """Create sample nodes and relationships for the demo.
    Existing nodes with the same `name` will be merged (using MERGE).
    """
    with driver.session() as session:
        session.run(
            """
            MERGE (alice:Person {name: $a_name})
            MERGE (bob:Person {name: $b_name})
            MERGE (carol:Person {name: $c_name})
            MERGE (acme:Company {name: $c1})
            MERGE (initech:Company {name: $c2})
            MERGE (alice)-[:WORKS_AT]->(acme)
            MERGE (bob)-[:WORKS_AT]->(acme)
            MERGE (carol)-[:WORKS_AT]->(initech)
            RETURN alice, bob, carol, acme, initech
            """,
            {
                "a_name": "Alice",
                "b_name": "Bob",
                "c_name": "Carol",
                "c1": "Acme Corp",
                "c2": "Initech",
            },
        )


def list_coworkers(driver, person_name):
    """Find coworkers of `person_name` (people who work at the same company).
    Returns a list of (coworker_name, company_name).
    """
    query = (
        "MATCH (p:Person {name: $name})-[:WORKS_AT]->(c:Company)<-[:WORKS_AT]-(coworker:Person) "
        "WHERE coworker.name <> $name "
        "RETURN coworker.name AS coworker, c.name AS company"
    )
    with driver.session() as session:
        result = session.run(query, {"name": person_name})
        return [(r["coworker"], r["company"]) for r in result]


def cleanup_demo_graph(driver):
    """Delete the demo nodes and relationships created by this script.
    Use with caution — this removes nodes with the demo company names.
    """
    with driver.session() as session:
        session.run(
            """
            MATCH (n)
            WHERE (n:Company AND n.name IN $companies) OR (n:Person AND n.name IN $people)
            DETACH DELETE n
            """,
            {"companies": ["Acme Corp", "Initech"], "people": ["Alice", "Bob", "Carol"]},
        )


def main():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    except Exception as e:
        print("Failed to create Neo4j driver:", e, file=sys.stderr)
        sys.exit(1)

    print("Connected to Neo4j at", NEO4J_URI)

    print("Creating demo graph...")
    create_demo_graph(driver)
    print("Demo graph created.")

    name = "Alice"
    coworkers = list_coworkers(driver, name)
    if coworkers:
        print(f"Coworkers of {name}:")
        for c_name, company in coworkers:
            print(f" - {c_name} at {company}")
    else:
        print(f"No coworkers found for {name}.")

    # Uncomment to clean up created demo nodes after verification
    # cleanup_demo_graph(driver)

    driver.close()


if __name__ == "__main__":
    main()
