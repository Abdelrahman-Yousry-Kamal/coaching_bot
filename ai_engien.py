import os
import dotenv
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

dotenv.load_dotenv()
API_KEY = os.getenv("Gemini_api_key")
if not API_KEY:
    raise ValueError("API key not found in .env file")

def initialize_llm():
    return ChatGoogleGenerativeAI(
        google_api_key=API_KEY,
        model="gemini-2.5-flash"
    )

def load_food_data(csv_file_path="cleaned_food_data.csv"):
    try:
        df = pd.read_csv(csv_file_path)
        documents = []
        for _, row in df.iterrows():
            doc_text = (f"Food: {row['Food']}, Calories: {row['Calories']} kcal, "
                        f"Protein: {row['Protein']} g, Fat: {row['Fat']} g, "
                        f"Carbohydrates: {row['Carbohydrates']} g, "
                        f"Nutrition Density: {row['Nutrition Density']}")
            documents.append(Document(page_content=doc_text, metadata={"food": row['Food']}))
        return documents
    except FileNotFoundError:
        raise FileNotFoundError(f"File {csv_file_path} not found")
    except Exception as e:
        raise Exception(f"Error loading CSV data: {str(e)}")

def setup_vector_store(documents):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = Chroma.from_documents(documents, embeddings, collection_name="food_data")
    return vector_store

def retrieve_relevant_data(query, vector_store, k=3):
    results = vector_store.similarity_search(query, k=k)
    context = "\n".join([doc.page_content for doc in results])
    return context

def create_prompt_template():
    return ChatPromptTemplate.from_template(
    """You are a coaching and food nutrition expert.

Answer the user's question using the context provided below. Be friendly and personalized.

USER PROFILE:
- Weight: {weight_kg} kg
- Height: {height_cm} cm
- Age: {age}
- Gender: {gender}
- Activity Level: {activity_level}

RETRIEVED NUTRITION DATA:
{nutrition_context}

Conversation so far:
{chat_history}

User: {question}
Assistant:"""
)

def setup_llm_chain(llm, prompt):
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        input_key="question",
        return_messages=True
    )
    return LLMChain(
        llm=llm,
        prompt=prompt,
        memory=memory,
        output_parser=StrOutputParser()
    )

def run_nutrition_bot():
    print("🤖 Nutrition Coach Bot is running! (type 'exit' to quit)\n")
    
    llm = initialize_llm()
    food_data = load_food_data()
    vector_store = setup_vector_store(food_data)
    prompt = create_prompt_template()
    llm_chain = setup_llm_chain(llm, prompt)
    
    user_info = {
        "weight_kg": 70,
        "height_cm": 175,
        "age": 25,
        "gender": "male",
        "activity_level": "moderate"
    }
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Bot: Goodbye! Stay healthy 🌱")
            break
        
        food_context = retrieve_relevant_data(user_input, vector_store)
        
        input_data = {
            **user_info,
            "question": user_input,
            "food_context": food_context
        }
        
        try:
            for chunk in llm_chain.stream(input_data):
                if isinstance(chunk, dict) and "text" in chunk:
                    print(chunk["text"], end="", flush=True)
                else:
                    print(chunk, end="", flush=True)
            print()
        except Exception as e:
            print(f"Error processing request: {str(e)}")

if __name__ == "__main__":
    try:
        run_nutrition_bot()
    except Exception as e:
        print(f"Error running bot: {str(e)}")

