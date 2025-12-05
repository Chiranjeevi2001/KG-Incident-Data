import json
import os
import time
from neo4j import GraphDatabase
from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE, DATA_FILE

URI = NEO4J_URI
USERNAME = NEO4J_USERNAME
PASSWORD = NEO4J_PASSWORD
DATABASE = NEO4J_DATABASE

def get_driver():
    return GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def clear_database(tx):
    tx.run("MATCH (n) DETACH DELETE n")

def create_constraints(tx):
    # Unique constraints
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Issue) REQUIRE i.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Issue) REQUIRE i.key IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (cat:Category) REQUIRE cat.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (per:Person) REQUIRE per.account_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Label) REQUIRE l.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:SlackChannel) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (pas:Passage) REQUIRE pas.id IS UNIQUE"
    ]
    for constraint in constraints:
        tx.run(constraint)

def ingest_data(tx, data):
    query = """
    UNWIND $data AS row
    
    // Create Issue
    MERGE (i:Issue {id: row.id})
    SET i.key = row.key,
        i.type = row.type,
        i.status = row.status,
        i.resolution = row.resolution,
        i.severity = row.severity,
        i.impact = row.impact,
        i.env_type = row.env_type,
        i.customer_env = row.customer_env,
        i.event_start = row.event_start,
        i.event_end = row.event_end,
        i.event_duration_ms = row.event_duration_ms,
        i.summary = row.summary,
        i.created = row.created,
        i.updated = row.updated,
        i.url = row.url
        
    // Create Product
    MERGE (p:Product {id: row.product.id})
    SET p.name = row.product.name
    MERGE (i)-[:HAS_PRODUCT]->(p)
    
    // Create Category
    MERGE (cat:Category {id: row.category.id})
    SET cat.name = row.category.name
    MERGE (i)-[:HAS_CATEGORY]->(cat)
    
    // Create Reporter
    MERGE (rep:Person {account_id: row.reporter.account_id})
    SET rep.display_name = row.reporter.display_name,
        rep.email = row.reporter.email
    MERGE (i)-[:REPORTED_BY]->(rep)
    
    // Create Assignee
    MERGE (assignee:Person {account_id: row.assignee.account_id})
    SET assignee.display_name = row.assignee.display_name,
        assignee.email = row.assignee.email
    MERGE (i)-[:ASSIGNED_TO]->(assignee)
    
    // Create Slack Channel
    FOREACH (sc IN CASE WHEN row.slack_channel IS NOT NULL THEN [row.slack_channel] ELSE [] END |
        MERGE (s:SlackChannel {id: sc.id})
        SET s.url = sc.url
        MERGE (i)-[:HAS_SLACK_CHANNEL]->(s)
    )
    
    // Create Components
    FOREACH (comp IN row.components |
        MERGE (c:Component {id: comp.id})
        SET c.name = comp.name
        MERGE (i)-[:HAS_COMPONENT]->(c)
    )
    
    // Create Labels
    FOREACH (lbl IN row.labels |
        MERGE (l:Label {id: lbl.id})
        SET l.name = lbl.name
        MERGE (i)-[:HAS_LABEL]->(l)
    )
    
    // Create Passages
    FOREACH (pas IN row.passages |
        MERGE (p:Passage {id: pas.id})
        SET p.source_type = pas.source_type,
            p.source_id = pas.source_id,
            p.text = pas.text,
            p.created = pas.created,
            p.url = pas.url
        MERGE (p)-[:FROM]->(i)
    )
    """
    tx.run(query, data=data)

def create_issue_links(tx, data):
    query = """
    UNWIND $data AS row
    MATCH (i:Issue {id: row.id})
    WITH i, row
    WHERE row.clones IS NOT NULL
    MATCH (target:Issue {key: row.clones})
    MERGE (i)-[:CLONES]->(target)
    """
    tx.run(query, data=data)

def main():
    if not os.path.exists(DATA_FILE):
        print(f"Data file {DATA_FILE} not found. Run generate_data.py first.")
        return

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    driver = get_driver()
    try:
        driver.verify_connectivity()
        print("Connected to Neo4j")
        
        with driver.session(database=DATABASE) as session:
            print("Clearing database...")
            session.execute_write(clear_database)
            
            print("Creating constraints...")
            session.execute_write(create_constraints)
            
            print(f"Ingesting {len(data)} incidents...")
            session.execute_write(ingest_data, data)
            
            print("Creating issue links...")
            session.execute_write(create_issue_links, data)
            
            # Verification count
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
            print(f"Graph construction complete. Total nodes: {count}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

def generate_embeddings(driver):
    print("Generating embeddings for Passages...")
    from langchain_community.embeddings import OCIGenAIEmbeddings
    from src.config import OCI_CONFIG_PROFILE, OCI_COMPARTMENT_ID, OCI_GENAI_ENDPOINT

    embeddings_model = OCIGenAIEmbeddings(
        model_id="cohere.embed-english-v3.0",
        service_endpoint=OCI_GENAI_ENDPOINT,
        compartment_id=OCI_COMPARTMENT_ID,
        auth_profile=OCI_CONFIG_PROFILE
    )

    with driver.session(database=DATABASE) as session:
        # Fetch all passages
        result = session.run("MATCH (p:Passage) RETURN p.id AS id, p.text AS text")
        passages = [{"id": record["id"], "text": record["text"]} for record in result]
        
        if not passages:
            print("No passages found.")
            return

        print(f"Found {len(passages)} passages. Generating embeddings...")
        
        # Batch process (optional, but good for large data)
        texts = [p["text"] for p in passages]
        try:
            embeddings = embeddings_model.embed_documents(texts)
            
            # Update graph
            for i, passage in enumerate(passages):
                session.run(
                    "MATCH (p:Passage {id: $id}) CALL db.create.setNodeVectorProperty(p, 'embedding', $embedding)",
                    id=passage["id"],
                    embedding=embeddings[i]
                )
            
            # Create Vector Index
            session.run("""
                CREATE VECTOR INDEX passage_embeddings IF NOT EXISTS
                FOR (p:Passage) ON (p.embedding)
                OPTIONS {indexConfig: {
                 `vector.dimensions`: 1024,
                 `vector.similarity_function`: 'cosine'
                }}
            """)
            print("Embeddings generated and vector index created.")
            
        except Exception as e:
            print(f"Failed to generate embeddings: {e}")

if __name__ == "__main__":
    main()
    # Re-open driver or pass it if we want to run this as part of main
    # For now, let's just run it separately or call it at the end of main if we refactor main to return driver or take a flag
    # But simpler: just create a new driver instance here or call it inside main
    
    # Refactoring main to call generate_embeddings
    driver = get_driver()
    try:
        generate_embeddings(driver)
    finally:
        driver.close()
