# GenAI SQL Query Generator

This project is a FastAPI-based application that generates SQL queries from natural language questions using LangChain, LangGraph, and an OpenAI LLM. It connects to a SQL Server database and processes questions to produce syntactically correct SQL queries.

---

## 📁 Project Structure

```
genai_project/
├── src/
│   ├── __init__.py              # Module initialization
│   ├── config.py                # Environment variable configuration
│   ├── logger.py                # Structured logging setup
│   ├── database.py              # Database connection initialization
│   ├── workflow.py              # LangGraph workflow for query generation
│   └── main.py                  # FastAPI application
├── .env                         # Environment variables
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

---

## ⚙️ Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd genai_project
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate        # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your OpenAI API key and database connection details.

5. **Run the application:**

   ```bash
   python -m src/main.py
   ```

   The API will be available at: [http://localhost:8000](http://localhost:8000)

---

## 📡 API Usage

* **Endpoint:** `POST /chat`
* **Request Body:**

  ```json
  {
    "question": "List all employees in the HR department"
  }
  ```
* **Response:**

  ```json
  {
    "query": "SELECT * FROM Employees WHERE Department = 'HR'"
  }
  ```

---

## 📝 Logging

Logs are stored in the `logs/` directory with daily rotation (max 5MB per file, 5 backups). Console output is colorized for better readability.

---

## 📦 Dependencies

* Python 3.9+
* FastAPI
* LangChain
* LangGraph
* PyODBC
* python-dotenv
* coloredlogs

---

## ⚠️ Notes

* Ensure the **SQL Server ODBC driver** is installed on your system.
* The application uses `gpt-4.1-mini` from OpenAI.
* You can update the model in `workflow.py` if needed.
* **Do not expose sensitive information** in the `.env` file publicly.
