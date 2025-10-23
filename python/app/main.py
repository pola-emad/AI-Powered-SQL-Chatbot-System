from fastapi import FastAPI, Query
from sqlalchemy import create_engine, text
from openai import OpenAI
import pandas as pd
import json


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
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

EXTRA_HEADERS = {
    "HTTP-Referer": "https://iti-examination-system.com",
    "X-Title": "ITI Examination System"
}

# -----------------------
# Endpoints
# -----------------------

@app.get("/test-db")
def test_db():
    try:
        with engine.connect() as conn:
            result = conn.exec_driver_sql(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"
            )
            tables = [row[0] for row in result]
            return {"status": "connected", "tables": tables}
    except Exception as e:
        return {"status": "failed", "detail": str(e)}


@app.get("/test-openai")
def test_open_ai(prompt: str = Query("Say hello to the world")):
    try:
        completion = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1:free",
            messages=[
                #{"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return {"reply": completion.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}


@app.post("/chat")
def chat_with_database(user_prompt: str = Query(...)):
    try:
        # Step 1: Generate and execute SQL query first
        # Step 1: Ask model to generate SQL query only
        system_prompt = """
You are an assistant that converts natural language questions into safe, correct SQL SELECT queries for a Microsoft SQL Server database.

Rules:
- Use only SELECT statements. Never modify data (no INSERT, UPDATE, DELETE, DROP, ALTER, etc.).
- Do not use backticks or markdown formatting. Return plain SQL.
- Use the exact table and column names listed below (case-insensitive).
- Prefer INNER JOINs when linking related tables.
- Always generate readable results (e.g., combine F_Name and L_Name for full student names).
- If a question mentions "average", "count", "highest", etc., use aggregate functions properly.
- If unsure, return a reasonable best guess query that will not cause an error.

Database schema:
Tables and columns:
- Student(StudentID, F_Name, L_Name, Gender, Age, Email, Password, Faculty, DepartmentID, IntakeID, BranchID, TrackID)
- Intake(IntakeID, IntakeNumber, StartDate, EndDate)
- Branch(BranchID, BranchName, Location)
- Department(DepartmentID, DepartmentName)
- Track(TrackID, TrackName, Prerequisite1, Prerequisite2)
- Instructor(InstructorID, InstructorName, Gender, Age, Salary, Email, DepartmentID)
- Course(CourseID, CourseName, Duration_days, InstructorID, coursedescription)
- Track_Course(TrackID, CourseID)
- Student_Course(StudentID, CourseID, Attendance_Percent)
- Exam(ExamID, CourseID, InstructorID, ExamTitle, ExamDate, DurationMinutes, TotalMarks)
- Exam_Question(ExamID, QuestionID, OrderNo)
- Question(QuestionID, CourseID, QuestionText, QuestionType, QuestionLevel, Marks)
- Choice(ChoiceID, QuestionID, ChoiceText, IsCorrect)
- Student_Answer(AnswerID, StudentID, ExamID, QuestionID, AnswerText, IsCorrect)
- Exam_Result(ResultID, ExamID, StudentID, Score, Status, Percentage)
- Certification(CertificationID, CourseID, CertificationTitle, Povider)
- Student_Certificate(StudentID, CertificationID, IssueDate)
- Feedback(FeedbackID, StudentID, InstructorID, Rating, Comment, DateSubmitted)
- Graduate(GraduateID, StudentID, TrackID, GraduationDate, CompanyID, Hire_Date, Position, Salary)
- Company(CompanyID, CompanyName, CompanyType, Industry, CompanyLocation)
- Freelance_Project(ProjectID, ProjectTitle, Related_Field, Cost, Duration_Days)
- Student_Project(StudentID, ProjectID, CompletionDate, Rating)
- intake_track_branch(intakeid, trackid, branchid)
- Topic(TopicID, CourseID, TopicName)

When users ask questions like:
- “Give me the intake of student Ahmed Ali” → use F_Name + L_Name to match name and select IntakeNumber.
- “List students in intake 45” → join Student with Intake and filter by IntakeNumber.
- “Average score in math for PowerBI track” → join Exam_Result, Exam, Course, and Track.
Scenarios: the user might enter input in arabic or english, you need to understand the requst and extract the target tables and columns
and generate the correct SQL query.
Return only SQL .
"""


        completion = client.chat.completions.create(
            extra_headers=EXTRA_HEADERS,
            model="meta-llama/llama-4-maverick:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        sql_query = completion.choices[0].message.content.strip()
        
        # Safety checks
        clean_query = sql_query.strip().lower()
        clean_query = clean_query.replace("```sql", "").replace("```", "").strip()
        if not clean_query.startswith("select"):
            raise ValueError("Only SELECT statements are allowed.")

        # Execute SQL
        with engine.connect() as conn:
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            result = conn.execute(text(sql_query))
            rows = result.fetchall()
            columns = result.keys()
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=columns)
        
        # Step 2: Check for visualization request with enhanced column awareness
        viz_prompt = f"""
You are analyzing a database visualization request for an examination system.

Available columns from the query: {list(columns)}

Common column mappings:
- Track name is "TrackName"
- Course name is "CourseName"
- Student name combines "F_Name" and "L_Name"
- Exam scores are in "Score" or "Percentage"
- Dates appear as "ExamDate", "StartDate", "EndDate", etc.
- Counts often use "StudentID", "ExamID", etc.
- Ratings appear as "Rating"
- Financial data in "Salary", "Cost"

Determine if this is a visualization request. If yes, specify:
1. Chart type (bar, line, scatter, pie, histogram)
2. X-axis column (must exactly match one from available columns)
3. Y-axis column (must exactly match one from available columns)
4. Any grouping/aggregation needed (sum, mean, count)

Return strict JSON: {{"is_viz": true/false, "chart_type": "", "x": "", "y": "", "agg": ""}}
If columns don't match exactly, return {{"is_viz": false}}

User question: {user_prompt}
Available columns: {list(columns)}
"""

        viz_check = client.chat.completions.create(
            extra_headers=EXTRA_HEADERS,
            model="meta-llama/llama-4-maverick:free",
            messages=[
                {"role": "system", "content": "You analyze if text requests data visualization."},
                {"role": "user", "content": viz_prompt}
            ]
        )
        
        viz_params = json.loads(viz_check.choices[0].message.content)
        
        # Generate natural language response
        nl_prompt = f"""Given this query result, provide a clear, natural language summary.
        Question: {user_prompt}
        Columns: {list(columns)}
        Data preview: {df.head(3).to_dict(orient='records')}
        Total rows: {len(df)}
        
        Format your response in a professional but friendly tone.
        Be concise and highlight key insights.
        Don't mention the columns or data preview explicitly.
        """
        
        explanation = client.chat.completions.create(
            extra_headers=EXTRA_HEADERS,
            model="meta-llama/llama-4-maverick:free",
            messages=[
                {"role": "system", "content": "You are a helpful database assistant."},
                {"role": "user", "content": nl_prompt}
            ]
        )

        # After DataFrame creation, handle visualization
        if viz_params.get("is_viz", False):
            chart_data = {
                "type": "visualization",
                "viz_type": viz_params["chart_type"],
                "x": viz_params["x"],
                "y": viz_params["y"],
                "agg": viz_params.get("agg", None),
                "data": df.to_dict(orient="records"),
                "explanation": explanation.choices[0].message.content
            }
            return chart_data
            
        # Return normal query response if not visualization
        return {
            "type": "query_response",
            "explanation": explanation.choices[0].message.content,
            "data": df.to_dict(orient="records"),
            "columns": list(columns),
            "row_count": len(df)
        }

    except Exception as e:
        return {"error": str(e)}




