import streamlit as st
import requests

st.set_page_config(page_title="AI Assistant")
st.title("AI Assistant")

if "history" not in st.session_state:
    st.session_state.history = []

for role, text in st.session_state.history:
    st.chat_message(role).write(text)

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.history.append(("user", prompt))
    st.chat_message("user").write(prompt)

    with st.spinner("Thinking..."):
        try:
            r = requests.post("http://backend:8000/chat", json={"message": prompt}, timeout=30)
            data = r.json()
            reply_obj = data.get("reply", "Sorry, something went wrong.")
            reply = reply_obj["answer"] if isinstance(reply_obj, dict) else reply_obj
        except Exception as e:
            reply = f"Backend is unreachable right now, please try again."

    st.session_state.history.append(("assistant", reply))
    st.chat_message("assistant").write(reply)