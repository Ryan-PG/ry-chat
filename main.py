import streamlit as st
from openai import OpenAI
import base64

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
            value=openai_api_key if openai_api_key else ""
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
        default_model = "qwen2.5:latest"

    model = st.text_input(
        "Model",
        value=default_model
    )

    # File uploader added here
    uploaded_file = st.file_uploader(
        "Upload a document or image", 
        type=["png", "jpg", "jpeg", "pdf", "txt"]
    )

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # If the content is stored as a list (multimodal), find and display the text part
        if isinstance(msg["content"], list):
            for part in msg["content"]:
                if part.get("type") == "text":
                    st.markdown(part["text"])
        else:
            st.markdown(msg["content"])

# User input
prompt = st.chat_input("Type your message...")

if prompt:
    # Build content based on whether a file was uploaded
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        mime_type = uploaded_file.type
        base64_file = base64.b64encode(file_bytes).decode("utf-8")
        
        # Structure payload for vision/multimodal compatible endpoints
        message_content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_file}"
                }
            }
        ]
    else:
        message_content = prompt

    st.session_state.messages.append(
        {
            "role": "user",
            "content": message_content,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file is not None:
            st.caption(f"📎 Attached file: {uploaded_file.name}")

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
                # Some API providers expect data as flat text blocks if it's a non-image text file.
                # The Base64 URI structure passes natively for multimodal target architectures.
            )

            full_response = ""

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
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