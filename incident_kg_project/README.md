# Incident Ticket Knowledge Graph RAG

This project builds a Knowledge Graph from dummy incident ticket data and provides a Natural Language Query interface using OCI Gen AI and Neo4j.

## Prerequisites

1.  **Python 3.8+**
2.  **Neo4j Database**:
    - Ensure you have a running Neo4j instance (AuraDB or Local).
    - Update `.env` with your connection details.
3.  **OCI Configuration**:
    - You need an Oracle Cloud Infrastructure (OCI) account.
    - Ensure you have a valid config profile (default: `DEFAULT`) in `~/.oci/config`.
    - Ensure you have access to OCI Gen AI service and the required models.

## Setup

1.  **Clone the repository** (if applicable) or navigate to the project directory.

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration**:
    - Create or update `.env` file with the following:
        ```env
        NEO4J_URI=bolt://localhost:7687
        NEO4J_USERNAME=neo4j
        NEO4J_PASSWORD=your_password
        NEO4J_DATABASE=neo4j
        
        # OCI Config (Optional if using default profile)
        OCI_CONFIG_PROFILE=DEFAULT
        OCI_COMPARTMENT_ID=ocid1.compartment.oc1..example...
        OCI_GENAI_ENDPOINT=https://inference.generativeai.us-chicago-1.oci.oraclecloud.com
        ```

## Usage

## Usage

### 1. Generate Dummy Data
Generate realistic dummy incident tickets in JSON format.
```bash
python3 src/generator.py
```
This will create `data/incidents.json`.

### 2. Build Knowledge Graph
Ingest the generated data into Neo4j.
```bash
python3 src/builder.py
```
This script clears the database (optional) and populates it with Issues, Components, Products, People, etc.

### 3. Run RAG Pipeline
Start the interactive QA session.
```bash
python3 main.py
```
You can now ask questions like:
- "How many issues are assigned to John Doe?"
- "List all high severity issues."
- "What components are affected by incident INC-1234?"

## Customization

- **Data Generation**: Modify `generate_data.py` to change the number of issues or schema.
- **RAG Pipeline**: Modify `rag_pipeline.py` to change the LLM model or prompt templates.
