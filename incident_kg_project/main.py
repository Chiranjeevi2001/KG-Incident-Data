import os
import sys
from src.pipeline import RAGPipeline
from src.config import PROJECT_ROOT

def main():
    print("Initializing RAG Pipeline...")
    try:
        pipeline = RAGPipeline()
        print("RAG Pipeline Ready!")
        print("Type 'exit' or 'quit' to stop.")
        
        while True:
            question = input("\nAsk a question: ")
            if question.lower() in ["exit", "quit"]:
                break
            
            if not question.strip():
                continue
                
            print("\nThinking...")
            response = pipeline.query(question)
            
            # Handle response format (it might be a dict or string depending on chain)
            if isinstance(response, dict):
                print(f"Answer: {response.get('result', response)}")
            else:
                print(f"Answer: {response}")
                
    except Exception as e:
        print(f"Failed to initialize pipeline: {e}")
        print("Please check your .env file and OCI configuration.")

if __name__ == "__main__":
    main()
