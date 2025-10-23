This project is a proof-of-concept AI chatbot that converts natural language into SQL queries, executes them on a SQL Server database, and returns human-readable results.
It bridges LLMs and relational databases in real time through an interactive Streamlit web interface powered by FastAPI on the backend.

🚀 Features

Converts natural language requests into SQL queries using an AI model (OpenAI / Llama via OpenRouter).

Executes validated queries directly on the connected SQL Server database.

Automatically formats and displays results in clean, readable text or tables.

End-to-end integration with FastAPI backend and Streamlit frontend.

Extensible structure for multi-model or multi-database support.

🧩 Tech Stack

Backend: Python, FastAPI, pyodbc

Frontend: Streamlit

Database: SQL Server

AI Models: OpenRouter (OpenAI, Llama)

Other: REST APIs, JSON handling, prompt engineering

⚙️ Setup Instructions

Clone the repository.

Install dependencies:

pip install -r requirements.txt


Configure your database credentials in the .env file.

Replace "API_KEY" with your actual OpenRouter or OpenAI key.

Run the backend:

uvicorn main:app --reload


Launch the Streamlit frontend:

streamlit run app.py


Open the app in your browser, and start chatting with your database.

🧠 Example Queries

“Give me the intake of student Ahmed Ali.”

“List all students in intake 45.”

“Show the highest-rated freelance projects.”

🛠️ Future Enhancements

Support for multiple databases (PostgreSQL, MySQL).

Enhanced security and query validation.

Custom dashboards and visualizations.

Conversational memory for contextual querying.
z<img width="1652" height="821" alt="Screenshot 2025-10-21 194916" src="https://github.com/user-attachments/assets/5282f0ba-9b94-4561-95b2-200675c1286d" />

<img width="1667" height="782" alt="Screenshot 2025-10-21 195013" src="https://github.com/user-attachments/assets/3e0b40a7-a1ff-4a91-a99a-45b8964f6d31" />

