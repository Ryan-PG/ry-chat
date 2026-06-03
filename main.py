import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="LLM Chat", layout="wide")

st.title("💬 OpenAI / Ollama Chat")

# Sidebar
with st.sidebar:
    st.header("Settings")

    provider = st.selectbox(
        "Provider",
        ["OpenAI", "Ollama"]
    )

    if provider == "OpenAI":
        base_url = st.text_input(
            "Base URL",
            value="https://api.openai.com/v1"
        )
        api_key = st.text_input(
            "API Key",
            type="password"
        )
        default_model = "gpt-5"
    else:
        base_url = st.text_input(
            "Base URL",
            value="http://localhost:11434/v1"
        )
        api_key = st.text_input(
            "API Key",
            value="ollama",
            type="password"
        )
        default_model = "llama3.1"

    model = st.text_input(
        "Model",
        value=default_model
    )

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
prompt = st.chat_input("Type your message...")

if prompt:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()

        try:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
            )

            stream = client.chat.completions.create(
                model=model,
                messages=st.session_state.messages,
                stream=True,
            )

            full_response = ""

            for chunk in stream:
                delta = chunk.choices[0].delta.content

                if delta:
                    full_response += delta
                    placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": full_response,
                }
            )

        except Exception as e:
            st.error(str(e))