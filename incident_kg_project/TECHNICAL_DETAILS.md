# Technical Implementation Details

## Architecture

The project consists of three main components:
1.  **Data Generation**: Creates synthetic data mimicking Oracle Aconex Incident tickets.
2.  **Knowledge Graph**: Stores the data in a graph structure (Neo4j) to enable relationship-based queries.
3.  **RAG Pipeline**: Uses a Large Language Model (OCI Gen AI) to translate natural language questions into Cypher queries (Text2Cypher) and retrieve answers.

## Data Schema

### Nodes
- **Issue**: Represents an incident ticket. Properties: `key`, `summary`, `status`, `severity`, `impact`, etc.
- **Component**: System component affected.
- **Product**: Product the issue belongs to.
- **Category**: Issue category.
- **Person**: Reporter or Assignee.
- **Label**: Tags associated with the issue.
- **SlackChannel**: Related communication channel.
- **Passage**: Unstructured text (e.g., comments, descriptions) for potential vector search.

### Relationships
- `(:Issue)-[:HAS_COMPONENT]->(:Component)`
- `(:Issue)-[:HAS_PRODUCT]->(:Product)`
- `(:Issue)-[:HAS_CATEGORY]->(:Category)`
- `(:Issue)-[:REPORTED_BY]->(:Person)`
- `(:Issue)-[:ASSIGNED_TO]->(:Person)`
- `(:Issue)-[:HAS_LABEL]->(:Label)`
- `(:Issue)-[:HAS_SLACK_CHANNEL]->(:SlackChannel)`
- `(:Issue)-[:CLONES]->(:Issue)`
- `(:Passage)-[:FROM]->(:Issue)`

## Project Structure

- `src/generator.py`: Data generation script.
- `src/builder.py`: Knowledge Graph construction script.
- `src/pipeline.py`: RAG pipeline logic.
- `src/config.py`: Configuration management.
- `main.py`: Entry point.
- `data/`: Directory for generated data.

## Libraries & Tools

- **Neo4j**: Graph Database for storage.
- **LangChain**: Framework for building the RAG pipeline.
    - `GraphCypherQAChain`: Core component for Text2Cypher.
    - `Neo4jGraph`: Wrapper for Neo4j connection.
    - `ChatOCIGenAI`: Interface for OCI Gen AI models.
- **Faker**: Library for generating realistic dummy data.
- **OCI SDK**: Underlying SDK for Oracle Cloud Infrastructure.

## RAG Pipeline Logic

1.  **Initialization**:
    - Connects to Neo4j.
    - Initializes OCI Gen AI Chat Model (e.g., Command R+).
    - Refreshes graph schema to understand available types and properties.

2.  **Query Processing**:
    - User input is sent to the `GraphCypherQAChain`.
    - **Step 1 (Cypher Generation)**: LLM generates a Cypher query based on the user question and graph schema.
    - **Step 2 (Execution)**: The generated Cypher is executed against Neo4j.
    - **Step 3 (Answer Synthesis)**: The query results are passed back to the LLM to generate a natural language response.

## Customization Options

- **Path Length**: Can be controlled by modifying the Cypher generation prompt or using `return_direct` to get raw graph results.
- **Similarity Search**: Currently, the pipeline focuses on Graph QA (structured). For unstructured text search, vector embeddings on `Passage` nodes would be required, integrated via `Neo4jVector` in LangChain.
