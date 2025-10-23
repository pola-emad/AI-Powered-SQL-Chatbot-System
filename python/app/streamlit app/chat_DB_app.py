import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from typing import Dict, Any

# Page config
st.set_page_config(
    page_title="ITI Examination System",
    page_icon="🎓",
    layout="wide",
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background: #f0f2f6;
    }
    .assistant-message {
        background: #ffffff;
    }
    .chat-header {
        text-align: center;
        padding: 2rem 0;
    }
    .st-emotion-cache-1y4p8pa {
        max-width: 100%;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []

def display_welcome():
    st.markdown("""
    <div class='chat-header'>
        <h1>🎓 ITI Examination System</h1>
        <p>Ask questions about students, courses, exams, and more...</p>
    </div>
    """, unsafe_allow_html=True)

def create_visualization(data, viz_type, x, y, agg=None):
    df = pd.DataFrame(data)
    
    # Validate columns exist
    if x not in df.columns or y not in df.columns:
        st.warning(f"Required columns not found in data. Looking for '{x}' and '{y}'")
        st.write("Available columns:", ", ".join(df.columns))
        return None
    
    try:
        if agg:
            df = df.groupby(x, as_index=False).agg({y: agg})
        
        chart_funcs = {
            "bar": px.bar,
            "line": px.line,
            "scatter": px.scatter,
            "pie": px.pie,
            "histogram": px.histogram
        }
        
        if viz_type in chart_funcs:
            fig = chart_funcs[viz_type](df, x=x, y=y)
            fig.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                height=400
            )
            return fig
        else:
            st.warning(f"Unsupported chart type: {viz_type}")
            return None
            
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")
        return None

def format_database_response(response: Dict[str, Any]):
    if "error" in response:
        st.error(response["error"])
        return

    # Display natural language explanation
    st.markdown(response["explanation"])
    
    if response.get("type") == "visualization":
        if not all(k in response for k in ["data", "viz_type", "x", "y"]):
            st.error("Missing required visualization parameters")
            return
            
        fig = create_visualization(
            response["data"],
            response["viz_type"],
            response["x"],
            response["y"],
            response.get("agg")
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # Always show data table as fallback
        df = pd.DataFrame(response["data"])
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={col: st.column_config.Column(
                width="medium"
            ) for col in df.columns}
        )
    elif response.get("data"):
        # Display data table if present
        df = pd.DataFrame(response["data"])
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={col: st.column_config.Column(
                width="medium"
            ) for col in df.columns}
        )

def main():
    initialize_session_state()
    display_welcome()

    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                format_database_response(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question about the examination system..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        "http://127.0.0.1:8000/chat",
                        params={"user_prompt": prompt}
                    )
                    response_data = response.json()
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response_data}
                    )
                    format_database_response(response_data)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
