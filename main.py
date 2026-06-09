import streamlit as st
from openai import OpenAI

import dotenv
import os
dotenv.load_dotenv()

ollama_api_key = os.environ.get("OLLAMA_API_KEY")
nvidia_api_key = os.environ.get("NVIDIA_API_KEY")
openai_api_key = os.environ.get("OPENAI_API_KEY")

st.set_page_config(page_title="LLM Chat", layout="wide")

st.title("💬 OpenAI / Ollama Test Chat")

# Sidebar
with st.sidebar:
    st.header("Settings")

    provider = st.selectbox(
        "Provider",
        ["Ollama", "OpenAI", "NVIDIA"]
    )

    if provider == "OpenAI":
        base_url = st.text_input(
            "Base URL",
            value="https://api.openai.com/v1"
        )
        api_key = st.text_input(
            "API Key",
            type="password",
            value=openai_api_key if nvidia_api_key else ""
        )
        default_model = "gpt-5"
    elif provider == "NVIDIA":
        base_url = st.text_input(
            "Base URL",
            value="https://integrate.api.nvidia.com/v1"
        )
        api_key = st.text_input(
            "API Key",
            type="password",
            value=nvidia_api_key if nvidia_api_key else ""
        )
        default_model = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
    else:
        base_url = st.text_input(
            "Base URL",
            value="http://localhost:11434/v1"
        )
        api_key = st.text_input(
            "API Key",
            type="password",
            value=ollama_api_key if ollama_api_key else ""
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