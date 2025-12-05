import os
from langchain_community.graphs import Neo4jGraph
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_community.chat_models import ChatOCIGenAI
from langchain_core.prompts import PromptTemplate
from src.config import (
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE,
    OCI_CONFIG_PROFILE, OCI_COMPARTMENT_ID, OCI_GENAI_ENDPOINT
)

URI = NEO4J_URI
USERNAME = NEO4J_USERNAME
PASSWORD = NEO4J_PASSWORD
DATABASE = NEO4J_DATABASE
AUTH_TYPE = "API_KEY"

COMPARTMENT_ID = OCI_COMPARTMENT_ID
ENDPOINT = OCI_GENAI_ENDPOINT

print("OCI Compartment:", OCI_COMPARTMENT_ID)
print("OCI Endpoint:", OCI_GENAI_ENDPOINT)
print("OCI Config Profile:", OCI_CONFIG_PROFILE)

def get_llm(temperature=0):
    """
    Initialize OCI Gen AI Chat Model.
    """
    return ChatOCIGenAI(
        model_id="ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyasebknceb4ekbiaiisjtu3fj5i7s4io3ignvg4ip2uyma", 
        provider="openai",
        service_endpoint=ENDPOINT,
        compartment_id=COMPARTMENT_ID,
        model_kwargs={"temperature": temperature, "max_tokens": 512}
    )

def get_graph():
    """
    Initialize Neo4j Graph connection.
    """
    return Neo4jGraph(
        url=URI,
        username=USERNAME,
        password=PASSWORD,
        database=DATABASE
    )

def get_cypher_qa_chain(llm, graph, verbose=True, top_k=10):
    """
    Create Graph Cypher QA Chain.
    """
    
    cypher_generation_template = """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
The question is:
{question}"""

    CYPHER_GENERATION_PROMPT = PromptTemplate(
        input_variables=["schema", "question"], 
        template=cypher_generation_template
    )

    return GraphCypherQAChain.from_llm(
        llm,
        graph=graph,
        verbose=verbose,
        cypher_prompt=CYPHER_GENERATION_PROMPT,
        top_k=top_k,
        allow_dangerous_requests=True
    )

def get_vector_store():
    """
    Initialize Neo4j Vector Store.
    """
    from langchain_community.vectorstores import Neo4jVector
    from langchain_community.embeddings import OCIGenAIEmbeddings
    
    embeddings = OCIGenAIEmbeddings(
        model_id="cohere.embed-multilingual-v3.0",
        service_endpoint=ENDPOINT,
        truncate="NONE",
        compartment_id=COMPARTMENT_ID,
        auth_profile=OCI_CONFIG_PROFILE,
        auth_type=AUTH_TYPE
    )
    
    return Neo4jVector.from_existing_graph(
        embedding=embeddings,
        url=URI,
        username=USERNAME,
        password=PASSWORD,
        index_name="passage_embeddings",
        node_label="Passage",
        text_node_properties=["text"],
        embedding_node_property="embedding",
    )

class RAGPipeline:
    def __init__(self):
        self.llm = get_llm()
        self.graph = get_graph()
        # Refresh schema
        self.graph.refresh_schema()
        self.chain = get_cypher_qa_chain(self.llm, self.graph)
        try:
            self.vector_store = get_vector_store()
            print("Vector store initialized.")
        except Exception as e:
            print(f"Vector store initialization failed: {e}")
            self.vector_store = None

    def query(self, question: str):
        # Simple routing logic: check if question asks for "similar" or "description"
        # Ideally, use an Agent or RouterChain
        if self.vector_store and ("similar" in question.lower() or "passage" in question.lower()):
            print("Using Vector Search...")
            try:
                docs = self.vector_store.similarity_search(question, k=3)
                return "\n\n".join([d.page_content for d in docs])
            except Exception as e:
                return f"Vector search failed: {e}"
        
        try:
            return self.chain.invoke({"query": question})
        except Exception as e:
            return f"Error processing query: {e}"

if __name__ == "__main__":
    # Test run
    pipeline = RAGPipeline()
    response = pipeline.query("How many issues are there?")
    print(response)
