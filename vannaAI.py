import psycopg2
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
from vanna.ollama.ollama import Ollama

# Custom Vanna class with ChromaDB and Ollama
class MyVanna(ChromaDB_VectorStore, Ollama):
    def __init__(self, config):
        if not isinstance(config, dict) or "model" not in config:
            raise ValueError("config must include at least {'model': '<ollama_model>'}")
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)

# Vanna config
config = {
    'model': 'llama3',                    # Make sure this model is available in Ollama
    'ollama_host': 'http://localhost:11434',
    'dialect': 'postgres'                # Force SQL generation for PostgreSQL
}

vn = MyVanna(config=config)

# PostgreSQL connection
DB_CONFIG = {
    'dbname': 'pharma_db',
    'user': 'postgres',
    'password': 'Beast@0987',
    'host': 'localhost',
    'port': '5432'
}

# Extract schema from PostgreSQL
def get_postgres_schema():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """)
    rows = cur.fetchall()
    conn.close()

    ddl = ""
    for table, col, dtype in rows:
        ddl += f"{table}: {col} ({dtype})\n"
    return ddl

# Load schema into Vanna
schema = get_postgres_schema()
vn.train(ddl=schema)

# OPTIONAL: Seed Vanna with correct SQL and context
vn.train(sql="""
    SELECT c.name AS category, SUM(s.quantity * p.price) AS total_revenue
    FROM sales s
    JOIN products p ON s.product_id = p.product_id
    JOIN categories c ON p.category_id = c.category_id
    WHERE s.sale_date >= CURRENT_DATE - INTERVAL '3 months'
    GROUP BY c.name;
""")
vn.train(documentation="This query shows total revenue grouped by category for the last 3 months.")

# SQL execution function
def run_sql(query):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(query)
    results = cur.fetchall()
    conn.close()
    return results

# SQL generation prompt
prompt = "Show total sales revenue grouped by category for the last 3 months"
sql = vn.generate_sql(prompt)
print("\nGenerated SQL:\n", sql)

# Run and print results
try:
    results = run_sql(sql)
    print("\nQuery Results:")
    for row in results:
        print(row)
except Exception as e:
    print("\nError running SQL:", e)

# Connect Vanna to PostgreSQL explicitly for browser UI
vn.connect_to_postgres(
    dbname=DB_CONFIG['dbname'],
    user=DB_CONFIG['user'],
    password=DB_CONFIG['password'],
    host=DB_CONFIG['host'],
    port=DB_CONFIG['port']
)

# Run on Browser
from vanna.flask import VannaFlaskApp
try:    
    print(" Initializing Vanna Flask app...")
    app = VannaFlaskApp(vn)
    print("Starting Flask server...")
    app.run()
except Exception as e:
    print(f"Error starting Flask app: {e}")