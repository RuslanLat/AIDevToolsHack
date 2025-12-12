import streamlit as st
import requests
import json

st.set_page_config(page_title="🤖 A2A MCP Agent", layout="wide", page_icon="🤖")
st.title("🤖 A2A MCP Agent Interface")
st.markdown("---")

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8080"

# Sidebar
with st.sidebar:
    st.header("🔧 API Settings")
    api_url = st.text_input(
        "AgentOS URL", value=st.session_state.api_url, key="api_input"
    )
    st.session_state.api_url = api_url

    agent_name = st.text_input("Agent Name", value="mcp-agent", key="agent_input")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Test Connection", use_container_width=True):
            try:
                resp = requests.get(f"{api_url}/health", timeout=5)
                if resp.status_code == 200:
                    st.success(f"✅ Connected! Status: {resp.status_code}")
                else:
                    st.warning(f"⚠️ Status: {resp.status_code}")
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")

    with col2:
        if st.button("📋 List Agents", use_container_width=True):
            try:
                resp = requests.get(f"{api_url}/agents", timeout=5)
                agents = resp.json()
                st.json(agents)
            except Exception as e:
                st.error(f"Failed to list agents: {str(e)}")

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main chat area
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask your MCP agent anything...", key="chat_input"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant response placeholder
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # FIXED: Correct Agno AgentOS API payload
        agent_run_url = f"{st.session_state.api_url}/agents/{agent_name}/runs"

        # CRITICAL FIX: Use form data for 'message' field
        payload = {
            "message": prompt  # Single string, not nested
        }

        try:
            with st.spinner("🤖 Agent thinking..."):
                # FIXED: Use data= (form-encoded) instead of json=
                response = requests.post(
                    agent_run_url,
                    data=payload,  # Changed from json=payload
                    timeout=60,
                )
                response.raise_for_status()

                # Handle non-streaming response (most common for Agno)
                result = response.json()

                # Extract content from Agno response structure
                content = (
                    result.get("output", {}).get("content", "")
                    or result.get("result", "")
                    or result.get("content", "")
                    or str(result)
                )

                full_response = content
                message_placeholder.markdown(full_response)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 422:
                st.error(
                    "❌ 422 Error: Invalid payload. Check agent name and server logs."
                )
            elif e.response.status_code == 404:
                st.error(
                    f"❌ 404: Agent '{agent_name}' not found. Check:\n• Server at {st.session_state.api_url}\n• Visit {st.session_state.api_url}/docs"
                )
            else:
                st.error(f"HTTP {e.response.status_code}: {e.response.text[:300]}")
        except Exception as e:
            st.error(f"API Error: {str(e)}")

        # Save response to history
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )

# Footer
st.markdown("---")
st.markdown("*Powered by Agno AgentOS + Streamlit*")
