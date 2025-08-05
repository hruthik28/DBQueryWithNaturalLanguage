# Here's an ultra-detailed step-by-step guide to run Vanna AI locally with Ollama, PostgreSQL, and ChromaDB, complete with:

✅ Installation steps

🏗️ Database schema with sample data

💡 Schema extraction

🤖 Vanna training + query generation

🧪 SQL execution

🧰 Bonus: Troubleshooting tips

🔧 Prerequisites
|Tool	|Download Link|
|-------|-------------|
|Python 3.10+	|https://www.python.org/downloads/|
|PostgreSQL|	https://www.postgresql.org/download/|
|Ollama	|https://ollama.com/download|
|pgAdmin (optional GUI)	|https://www.pgadmin.org/download/

# 🪜 STEP 1: Install Python Libraries
Open terminal (or CMD) and run:

```bash
pip install vanna chromadb psycopg2-binary

OR 

pip install vanna[chromadb,ollama,postgres]
```

# 🪜 How to Set Up Ollama on Windows (via Official Installer)
## 🔗 Step 1: Download Ollama

- Go to https://ollama.com
- Click Download for Windows
- You’ll get an .exe installer

## ⚙️ Step 2: Install Ollama
- Run the .exe file
- Follow the on-screen installation instructions
-After install, Ollama will automatically open in the background as a system tray app
- ✅ Ollama for Windows runs using WSL2 (Windows Subsystem for Linux) under the hood.
    - If WSL2 is not installed, the installer will prompt you to install it.

## 🧠 Step 3: Run a Model
- After installation, open Command Prompt (or PowerShell) and run:

```bash
ollama run llama3
```
This will:
- Download the model (first-time only)
- Start a local chat session in the terminal
- You can try other models too:

```bash
ollama run mistral
ollama run gemma
ollama run codellama
```

To run the model on server/locally:
```bash
ollama serve
```

To check if model is up and running:
```bash
Get-Process | Where-Object { $_.ProcessName -like "*ollama*" }
```

To stop the model:
```bash
Stop-Process -Name "ollama" -Force
```

## 📜 Step 4: List Installed Models
```bash
ollama list
```
To see available models:
👉 https://ollama.com/library

## 🌐 Step 5: Use Ollama’s Local REST API
Once running, the API is accessible at:

```text
http://localhost:11434
```
You can send HTTP POST requests to it from apps using Java, Python, Postman, or curl.
```bash
# Try in powershell:
curl -Method POST http://localhost:11434/api/generate `
   -Headers @{ "Content-Type" = "application/json" } `
   -Body '{ "model": "llama3", "prompt": "Say hello!", "stream": false }'

# Response:
StatusCode        : 200
StatusDescription : OK
Content           : {"model":"llama3","created_at":"2025-08-04T17:07:40.6392257Z","response":"Hello there! It's nice
                    to meet you. Is there something I can help you with, or would you like to
                    chat?","done":true,"done_reas...
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 554
                    Content-Type: application/json; charset=utf-8
                    Date: Mon, 04 Aug 2025 17:07:40 GMT

                    {"model":"llama3","created_at":"2025-08-04T17:07:40.6392257Z","response":"He...
Forms             : {}
Headers           : {[Content-Length, 554], [Content-Type, application/json; charset=utf-8], [Date, Mon, 04 Aug 2025
                    17:07:40 GMT]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        : mshtml.HTMLDocumentClass
RawContentLength  : 554
```

## 🔁 Optional: Update Ollama
To update, simply run:
```bash
ollama update
```
## 📝 Notes
- Make sure WSL2 is installed and working
- GPU acceleration is not supported on Windows (yet)
- Ollama runs fully offline (after downloading the model)

# 🪜 STEP 3: Create PostgreSQL Database
1️⃣ Connect to PostgreSQL (CLI or pgAdmin)
Login using:
```bash
psql -U postgres
```
2️⃣ Create Database
```sql
CREATE DATABASE pharma_db;
```
# 🪜 STEP 4: Create Tables + Insert Sample Data
Use psql or pgAdmin to run:
```sql
-- Categories
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100)
);

INSERT INTO categories (category_name)
VALUES ('Painkillers'), ('Antibiotics'), ('Vitamins');

-- Products
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    category_id INT REFERENCES categories(category_id),
    price NUMERIC
);

INSERT INTO products (name, category_id, price)
VALUES 
('Paracetamol', 1, 20.00),
('Ibuprofen', 1, 30.00),
('Amoxicillin', 2, 50.00),
('Vitamin C', 3, 15.00);

-- Sales
CREATE TABLE sales (
    sale_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    quantity INT,
    sale_date DATE
);

INSERT INTO sales (product_id, quantity, sale_date)
VALUES 
(1, 100, CURRENT_DATE - INTERVAL '20 days'),
(2, 50, CURRENT_DATE - INTERVAL '10 days'),
(3, 80, CURRENT_DATE - INTERVAL '90 days'),
(4, 200, CURRENT_DATE - INTERVAL '5 days');

-- Customers
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    region VARCHAR(50)
);

INSERT INTO customers (name, region)
VALUES 
('Alice', 'North'),
('Bob', 'East'),
('Charlie', 'South');

-- Orders
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    sale_id INT REFERENCES sales(sale_id),
    customer_id INT REFERENCES customers(customer_id)
);

INSERT INTO orders (sale_id, customer_id)
VALUES 
(1, 1),
(2, 2),
(3, 3),
(4, 1);
```

# 🪜 STEP 5: Extract Schema for Training Vanna
get_schema() Python Function
```python
import psycopg2

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
```

# 🪜 STEP 6: Initialize Vanna AI with Ollama + ChromaDB
```python
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

# Load schema into Vanna
schema = get_postgres_schema()
vn.train(ddl=schema)
```

# 🪜 STEP 7: Ask a Question and Generate SQL
```python
prompt = "Show total sales revenue grouped by category for the last 3 months"
sql = vn.generate_sql(prompt)
print("Generated SQL:\n", sql)
```
Expected SQL output:
```sql
SELECT
    c.category_name,
    SUM(s.quantity * p.price) AS total_sales
FROM sales s
JOIN products p ON s.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id
WHERE s.sale_date >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY c.category_name
ORDER BY total_sales DESC;
```

# 🪜 STEP 8: Execute SQL on PostgreSQL
```python
# SQL execution function
def run_sql(query):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(query)
    results = cur.fetchall()
    conn.close()
    return results

# Run and print results
try:
    results = run_sql(sql)
    print("\nQuery Results:")
    for row in results:
        print(row)
except Exception as e:
    print("\nError running SQL:", e)
```

# 🪜 STEP 9: Run on browser using Flask 
```python
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
```

# 🧠 Try These Natural Language Prompts
|Question	|Expected Behavior|
|-----------|-----------------|
|"List all products with their categories"	|JOIN products + categories|
|"How many units sold by product name?"	|JOIN sales + products|
|"Who bought Vitamin C?"	|JOIN orders → sales → products → customers|
|"Sales in the North region last month"	|Complex joins + filter on customer region|

# 🧰 Troubleshooting
|Issue	|Fix|
|-------|---|
|psycopg2.OperationalError	|Check PostgreSQL username/password/host|
|Ollama not responding	|Ensure ollama run llama3 is running|
|SQL output is empty	|Check if sale_date falls in recent months|
|"Model not found"	|Run ollama pull llama3 before starting|
