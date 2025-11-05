import streamlit as st
from langgraph_database_backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid

# =========================== UTILITY FUNC. =======================
def generate_thread_id():
    return str(uuid.uuid4())

def generate_default_title():
    return "New Conversation"

def add_thread(thread_id, title=None):
    """Add a new chat thread with an optional title"""
    if 'chat_threads' not in st.session_state:
        st.session_state['chat_threads'] = []

    # Avoid duplicates
    if not any(t['id'] == thread_id for t in st.session_state['chat_threads']):
        st.session_state['chat_threads'].append({
            'id': thread_id,
            'title': title or generate_default_title()
        })

def reset_chat():
    """Start a new conversation"""
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []

def load_conversation(thread_id):
    """Fetch stored conversation for a given thread ID"""
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])


# =========================== MAIN APP ===========================

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    thread_ids = retrieve_all_threads()
    st.session_state['chat_threads'] = [
        {'id': tid, 'title': f"Conversation {i+1}"} 
        for i, tid in enumerate(thread_ids)
    ]


# Ensure at least one thread exists
add_thread(st.session_state['thread_id'])

#===================SIDEBAR UI =======================

st.sidebar.title("LANGGRAPH Chatbot")

if st.sidebar.button('New Chat'):
    reset_chat()  

st.sidebar.header("My Conversations")

# Show conversation titles instead of raw UUIDs
for thread in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(thread['title']):
        messages = load_conversation(thread['id'])

        temp_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages
        st.session_state['thread_id'] = thread['id']

# loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:
    # first add the message to message_history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)
    
    #CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
    CONFIG ={
        'configurable': {'thread_id': st.session_state['thread_id']},
        'metadata':{'thread_id': st.session_state['thread_id']},
        'run_name': 'chatbot_run'
    }
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})

    # 🧠 Auto-generate a title if it's a new thread
    for t in st.session_state['chat_threads']:
        if t['id'] == st.session_state['thread_id'] and t['title'] == "New Conversation":
            preview = user_input[:25] + "..." if len(user_input) > 25 else user_input
            t['title'] = preview
            break
