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
    try:
        df = pd.DataFrame(data)
        
        if x not in df.columns or y not in df.columns:
            st.warning(f"Missing columns: {x} or {y}")
            return None
            
        if agg:
            df = df.groupby(x, as_index=False).agg({y: agg})
        
        chart_funcs = {
            "bar": px.bar,
            "line": px.line,
            "scatter": px.scatter,
            "pie": px.pie,
            "histogram": px.histogram
        }
        
        if viz_type not in chart_funcs:
            st.warning(f"Unsupported chart: {viz_type}")
            return None
            
        fig = chart_funcs[viz_type](df, x=x, y=y)
        fig.update_layout(
            margin=dict(l=20, r=20, t=30, b=20),
            height=400
        )
        return fig
        
    except Exception as e:
        st.error(f"Visualization error: {str(e)}")
        return None
def create_chart(vis_prams,df):
    chart = vis_prams['viz_type']
    x = df[vis_prams['x']]
    y = df[vis_prams['y']]
    fig = getattr(px,chart)
    fig = fig(df,x=x,y=y)
    st.plotly_chart(fig, use_container_width=True)

def format_database_response(response: Dict[str, Any]):
    if "error" in response:
        st.error(response["error"])
        return

    # Show explanation first
    st.markdown(response["explanation"])
    
    # Show visualization if available
    # if response.get("type") == "visualization":
    #     fig = create_visualization(
    #         response["data"],
    #         response["viz_type"],
    #         response["x"],
    #         response["y"],
    #         response.get("agg")
    #     )
    #     if fig:
    #         st.plotly_chart(fig, use_container_width=True)
    
    # Always show data table
    if response.get("data"):
        df = pd.DataFrame(response["data"])
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
    if response.get("type") == "visualization":
        create_chart(response,df)

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
