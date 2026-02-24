"""Quick Groq connectivity test"""
from dotenv import load_dotenv
import os
load_dotenv()

key = os.getenv("GROQ_API_KEY", "")
print(f"GROQ_API_KEY loaded: {bool(key)}, prefix: {key[:8] if key else 'MISSING'}")

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatGroq(api_key=key, model_name="llama-3.3-70b-versatile", temperature=0.2)
resp = llm.invoke([SystemMessage(content="You are a DFIR assistant."),
                   HumanMessage(content="Reply with exactly: GROQ IS LIVE")])
print("LLM response:", resp.content)
