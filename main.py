import streamlit as st
import urllib.request
import json
import base64
import time
import os

# Optional fallback if python-dotenv isn't loaded in stlite browser context
try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

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
        default_model = "gpt-4o-mini"
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
            value=ollama_api_key if ollama_api_key else "ollama"
        )
        default_model = "qwen2.5:latest"

    model = st.text_input(
        "Model",
        value=default_model
    )

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
        if isinstance(msg["content"], list):
            for part in msg["content"]:
                if part.get("type") == "text":
                    st.markdown(part["text"])
                elif part.get("type") == "image_url":
                    st.image(part["image_url"]["url"])
        else:
            st.markdown(msg["content"])
        
        # Display performance metadata from history
        if "latency" in msg and "tokens_per_sec" in msg:
            st.caption(f"⏱️ Latency: {msg['latency']:.2f}s | ⚡ Speed: {msg['tokens_per_sec']:.1f} tk/s")

# User input
prompt = st.chat_input("Type your message...")

if prompt:
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        mime_type = uploaded_file.type
        base64_file = base64.b64encode(file_bytes).decode("utf-8")
        
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
            if uploaded_file.type.startswith("image/"):
                st.image(uploaded_file)
            else:
                st.caption(f"📎 Attached file: {uploaded_file.name}")

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        try:
            # Clean trailing slash variations
            clean_url = base_url.rstrip("/") + "/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": st.session_state.messages,
                "stream": True
            }
            
            req = urllib.request.Request(
                url=clean_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )

            start_time = time.time()
            full_response = ""
            
            with urllib.request.urlopen(req) as response:
                buffer = ""
                while True:
                    chunk = response.read(1024)
                    if not chunk:
                        break
                    
                    buffer += chunk.decode("utf-8")
                    
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        
                        if not line or line == "data: [DONE]":
                            continue
                        
                        if line.startswith("data: "):
                            try:
                                json_str = line[6:]
                                data_chunk = json.loads(json_str)
                                
                                choices = data_chunk.get("choices", [])
                                if choices and "delta" in choices[0]:
                                    # Fallback safely to empty string if 'content' is missing or explicitly None
                                    delta = choices[0]["delta"].get("content") or ""
                                    
                                    if delta:
                                        full_response += delta
                                        placeholder.markdown(full_response + "▌")
                            except json.JSONDecodeError:
                                continue

            # Calculate total generation duration
            latency = time.time() - start_time
            
            # Estimate token count (Total Characters / 4)
            estimated_tokens = len(full_response) / 4
            tokens_per_sec = estimated_tokens / latency if latency > 0 else 0

            # Render final output with stats
            placeholder.markdown(full_response)
            st.caption(f"⏱️ Latency: {latency:.2f}s | ⚡ Speed: {tokens_per_sec:.1f} tk/s")

            # Append Assistant message along with metric variables into history
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": full_response,
                    "latency": latency,
                    "tokens_per_sec": tokens_per_sec
                }
            )
            
            st.rerun()

        except Exception as e:
            st.error(f"Request Error: {str(e)}")