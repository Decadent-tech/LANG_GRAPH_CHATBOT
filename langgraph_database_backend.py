from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
import sqlite3


load_dotenv()
# Initialize the language model
api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(api_key=api_key, model_name="gpt-3.5-turbo")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

# Checkpointer
#sqlite3.connect(database = 'chatbot_database.db',check_same_thread=False)  # Ensure the database file is created
checkpointer = SqliteSaver(conn = sqlite3.connect(database = 'chatbot_database.db',check_same_thread=False))

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

# test invocation

'''
CONFIG = {'configurable': {'thread_id':'thread-1'}}
response = chatbot.invoke(
    {'messages': [HumanMessage(content="Where is delhi ?")]},
    config=CONFIG
)
print(response)  # For debugging purposes
'''
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)