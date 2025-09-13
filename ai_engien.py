from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts  import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
import os 
import dotenv

dotenv.load_dotenv()
API_KEY = os.getenv("Gemini_api_key")

chat = ChatGoogleGenerativeAI(
    google_api_key=API_KEY,
    model="gemini-2.5-flash"
)

memory = ConversationBufferMemory(
    memory_key="chat_history", 
    input_key="question", 
    return_messages=True
)

prompt  = ChatPromptTemplate.from_template(
    """You are a coaching and food nutrition expert. 
Answer the question based on the following context:

- Weight: {weight_kg} kg
- Height: {height_cm} cm
- Age: {age}
- Gender: {gender}
- Activity Level: {activity_level}

Conversation so far:
{chat_history}

User: {question}
Assistant:"""
)

llm = LLMChain(
    llm=chat,
    prompt=prompt,
    memory=memory,
    output_parser=StrOutputParser()
)

print("🤖 Nutrition Coach Bot is running! (type 'exit' to quit)\n")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Bot: Goodbye! Stay healthy 🌱")
        break

    for chunk in llm.stream({
        "question": user_input,
        "weight_kg": 70,
        "height_cm": 175,
        "age": 25,
        "gender": "male",
        "activity_level": "moderate"
    }):
        if isinstance(chunk, dict) and "text" in chunk:
            print(chunk["text"], end="", flush=True)
        else:
            print(chunk, end="", flush=True)
    print()
