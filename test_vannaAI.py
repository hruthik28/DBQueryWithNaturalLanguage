import openai
from openai import OpenAI
from vanna.openai.openai_chat import OpenAI_Chat
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore

ollama_client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        config = config or {}
        config["model"] = config.get("model", "llama3")
        config["temperature"] = config.get("temperature", 0.7)
        config.setdefault("base_url", "http://localhost:11434/v1")
        config.setdefault("api_key", "ollama")
        # config = config or {}
        # config.setdefault("model", "llama3")
        # config.setdefault("base_url", "http://localhost:11434/v1")
        # config.setdefault("api_key", "ollama")  # placeholder for Ollama
        config.setdefault("temperature", 0.7)

        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, client=ollama_client, config=config)
        self.temperature = config["temperature"]
    
#vn = MyVanna(config={"embedding_model": "text-embedding-3-small"})

vn = MyVanna(config={
    "embedding_model": "text-embedding-3-small",  # optional if using default
    "model": "llama3",
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama",  # dummy; required by OpenAI-style interface
    "temperature": 0.7
})

vn.connect_to_postgres(host='localhost', dbname='testdb', user='postgres', password='password', port=5432)
# Train and prompt as usual
vn.train(ddl="CREATE TABLE customers (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), city VARCHAR(100), purchases INT);")
vn.train(question= "Show me details of Alice", sql="select * from customers where name='Alice'")
vn.train(documentation= "List all customers with more than 5 purchases")

print(vn.get_training_data())
print(vn.ask(question="List all customers in New York"))

from vanna.flask import VannaFlaskApp
try:    
    print(" Initializing Vanna Flask app...")
    app = VannaFlaskApp(vn)
    print("Starting Flask server...")
    app.run()
except Exception as e:
    print(f"Error starting Flask app: {e}")
