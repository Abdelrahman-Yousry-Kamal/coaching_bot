from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts  import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

import pandas as pd 
import os 
import dotenv

dotenv.load_dotenv()
API_KEY = os.getenv("Gemini_api_key")

chat = ChatGoogleGenerativeAI(google_api_key=API_KEY , model="gemini-2.5-flash")
user_input = input("enter your question: ")
prompt  = ChatPromptTemplate.from_template("you are coaching and food nutrition expert. answer the question based on the following context: {question}")

llm = prompt | chat | StrOutputParser()

for chunk in llm.invoke({"question": user_input}, stream=True):
    print(chunk, end="", flush=True)
