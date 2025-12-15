from fastapi import FastAPI, Query
from sqlalchemy import create_engine, text
from openai import OpenAI
import pandas as pd
import json
import utils as u




app = FastAPI()

# -----------------------
# Database Configuration
# -----------------------
DB_SERVER = r"POLA-EMAD\DBENGINE_EXPRESS"
DB_NAME = "ITI_Examination_System"
DRIVER = "ODBC Driver 17 for SQL Server"

CONN_STR = (
    f"mssql+pyodbc://@{DB_SERVER}/{DB_NAME}"
    f"?trusted_connection=yes&driver={DRIVER.replace(' ', '+')}"
)

engine = create_engine(CONN_STR)

# -----------------------
# OpenRouter Configuration
# -----------------------
<<<<<<< HEAD
model=u.model
client = u.client

=======
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="API KEY"
)
>>>>>>> d3ebf8724dc0a6b5955a1a88931e641ae644c145

EXTRA_HEADERS = {
    "HTTP-Referer": "https://iti-examination-system.com",
    "X-Title": "ITI Examination System"
}

# -----------------------
# Helper Functions
# -----------------------
def get_completion_from_messages(messages, 
                                 model=model, 
                                 temperature=0, 
                                 max_tokens=500):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature, 
        max_tokens=max_tokens, 
        
        stop=["<｜begin▁of▁sentence｜>","```json","```"],
    )
    return response.choices[0].message.content

def get_sql_and_viz_request(user_prompt: str) -> dict:
    
    system_prompt = u.system_prompt

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": u.example_input_response_1}
        ]
        response = get_completion_from_messages(messages) # response is in json fromat {sqlquery:"",
                                                        # user visualization request:""}
        return json.loads(response)
    except json.JSONDecodeError:
        raise ValueError(f"Failed to parse LLM response as JSON\n",response)


# -----------------------
# Endpoints
# -----------------------


@app.post("/chat")
def chat_with_database(user_prompt: str = Query(...)):
    try:
        # Step 1: Get SQL query and viz request
        response = get_sql_and_viz_request(user_prompt) #json object
        sql_query = response.get("sqlquery", "").strip()
        viz_request = response.get("user visualization request", "")

        # Validate SQL
        if not sql_query.lower().startswith("select"):
            raise ValueError("Only SELECT statements are allowed")

        # Execute SQL
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = result.fetchall()
            columns = result.keys()
        
        df = pd.DataFrame(rows, columns=columns)
        
        # Handle visualization if requested
        viz_data = None
        if viz_request:
            viz_prompt = u.get_viz_prompt(columns=columns)
            messages = [
                {"role": "system", "content": viz_prompt},
                {"role": "user", "content": viz_request}
            ]
            viz_response = get_completion_from_messages(messages)
            
            try:
                viz_params = json.loads(viz_response)
                
                viz_data = {
                        "type": "visualization",
                        "viz_type": viz_params["chart_type"],
                        "x": viz_params["x"],
                        "y": viz_params["y"],
                        "agg": viz_params.get("agg"),
                    }
            except json.JSONDecodeError:
                viz_data = None

        # Generate explanation
        nl_prompt = f"explain briefly in natural language and friendly tone this data: {df.head(3).to_dict()} ({len(df)} total rows)"
        messages = [
            {"role": "system", "content": "Be concise and highlight key insights."},
            {"role": "user", "content": nl_prompt}
        ]
        explanation = get_completion_from_messages(messages)

        return {
            "type": "visualization" if viz_data else "query_response",
            "explanation": explanation,
            "data": df.to_dict(orient="records"),
            **(viz_data or {}),
            "columns": list(columns),
            "row_count": len(df)
        }

    except Exception as e:
        return {"error": str(e)}




