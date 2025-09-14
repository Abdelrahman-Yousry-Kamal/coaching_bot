import os
import base64
import pandas as pd
import speech_recognition as sr
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import logging
from datetime import datetime
import db

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize Google Gemini API
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "AIzaSyBqmRouG7ExZh-IFRgdxt4OFn3cBJll8nM")
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_food_image(image_bytes: bytes) -> str:
    """
    Analyzes a food image using Google Gemini API and provides calorie estimation and nutrition advice.
    """
    try:
        logger.debug("Analyzing food image")
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        contents = [
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": encoded_image
                }
            },
            {
                "text": (
                    "You are a certified nutritionist. Carefully analyze this food image. "
                    "List each food item you see, estimate the calories for each item and the total calories. "
                    "Include portion size estimates and any basic nutrition advice for a healthy diet. "
                    "Respond in clear, concise language suitable for a user who wants to track their daily intake."
                    "Use emojis like 🍎🥦🍗🍰 to make it engaging."
                    """ou are an Omani nutrition specialist. Analyze the following image and identify its food content, then provide an approximate estimate of carbohydrates, fats, and proteins (in grams), as well as calories accurately. If you are not certain, give a logical estimate based on the dish components. Respond in Omani Arabic dialect in a formal and concise manner.
Respond only in the following format:
Carbohydrates: [grams] g
Fats: [grams] g
Protein: [grams] g
Calories: [calories] kcalou are an Omani nutrition specialist. Analyze the following image and identify its food content, then provide an approximate estimate of carbohydrates, fats, and proteins (in grams), as well as calories accurately. If you are not certain, give a logical estimate based on the dish components. Respond in Omani Arabic dialect in a formal and concise manner.
Respond only in the following format:
Carbohydrates: [grams] g
Fats: [grams] g
Protein: [grams] g
Calories: [calories] kcal"""
                   
                )
            }
        ]
        response = model.generate_content(contents)
        result = response.text.strip() if hasattr(response, 'text') else "❌ Error analyzing image. Please try again."
        logger.info("Image analysis completed")
        return result
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        return f"Error: {str(e)}"

def analyze_voice(audio_data: bytes) -> str:
    """
    Analyzes voice input using speech recognition and converts it to text.
    """
    try:
        logger.debug("Analyzing voice input")
        recognizer = sr.Recognizer()
        audio = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)
        text = recognizer.recognize_google(audio)
        logger.info("Voice analysis completed")
        return text
    except sr.UnknownValueError:
        logger.error("Could not understand audio")
        return "Error: Could not understand audio"
    except sr.RequestError as e:
        logger.error(f"Speech recognition error: {str(e)}")
        return f"Error: Speech recognition failed - {str(e)}"
    except Exception as e:
        logger.error(f"Error analyzing voice: {str(e)}")
        return f"Error: {str(e)}"

def initialize_llm():
    """
    Initializes the Google Gemini LLM with the specified API key and model.
    """
    try:
        return ChatGoogleGenerativeAI(
            google_api_key=os.environ["GEMINI_API_KEY"],
            model="gemini-1.5-flash",
            temperature=0.7
        )
    except Exception as e:
        raise Exception(f"Failed to initialize LLM: {str(e)}")

def load_food_data(csv_file_path="cleaned_food_data.csv"):
    """
    Loads food data from a CSV file and converts it into LangChain Document objects.
    """
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
    """
    Sets up a Chroma vector store with HuggingFace embeddings for the food data.
    """
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_store = Chroma.from_documents(documents, embeddings, collection_name="food_data")
        return vector_store
    except Exception as e:
        raise Exception(f"Error setting up vector store: {str(e)}")

def retrieve_relevant_data(query, vector_store, k=3):
    """
    Retrieves relevant food data from the vector store based on the query.
    """
    try:
        results = vector_store.similarity_search(query, k=k)
        context = "\n".join([doc.page_content for doc in results])
        return context
    except Exception as e:
        return f"Error retrieving data: {str(e)}"

def create_prompt_template():
    """
    Creates a prompt template for the nutrition and fitness coach.
    """
    return ChatPromptTemplate.from_template(
        """You are a nutrition and fitness coach. Answer the question based on the following information:
    take with  emojjis 🍎🥦 🍗🍰 all emojis"
                    "Format the response as a numbered list if  multiple items are present."
                    "memorize all infomation and use it in future conversations
        - Weight: {weight_kg} kg
        - Height: {height_cm} cm
        - Age: {age} years
        - Gender: {gender}
        - Activity Level: {activity_level}
        - Food Data:
        {food_context}

        Conversation so far:
        {chat_history}

        User Question: {question}
        Answer in a concise and helpful manner:"""
    )

def setup_llm_chain(llm, prompt):
    """
    Sets up the LLM chain with conversation memory.
    """
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

def get_bot_response(user_id: str, user_input: str = None, image_data: bytes = None, 
                    voice_data: bytes = None) -> str:
    """
    Processes user input (text, image, or voice) and returns the bot's response.
    """
    try:
        llm = initialize_llm()
        documents = load_food_data()
        vector_store = setup_vector_store(documents)
        prompt = create_prompt_template()
        llm_chain = setup_llm_chain(llm, prompt)

        user_data = db.load_user_data(user_id)
        if not user_data:
            return "Error: User not found. Please create a user profile."
        user_info = {
            "weight_kg": user_data.get("weight", 0),
            "height_cm": user_data.get("height", 0),
            "age": user_data.get("age", 0),
            "gender": user_data.get("gender", ""),
            "activity_level": user_data.get("activity_level", "")
        }

        if voice_data:
            user_input = analyze_voice(voice_data)
            if user_input.startswith("Error"):
                return user_input

        food_context = retrieve_relevant_data(user_input or "", vector_store)
        if image_data:
            image_analysis = analyze_food_image(image_data)
            food_context += f"\nImage Analysis: {image_analysis}"
            user_data.setdefault("image_analyses", []).append({
                "analysis": image_analysis,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            db.save_user_data(user_id, user_data)

        chats = db.get_chats(user_id)
        chat_history = "\n".join([f"User: {chat['user']}\nBot: {chat['bot']}" 
                                 for chat in chats[-5:]])

        input_data = {
            **user_info,
            "question": user_input or "",
            "food_context": food_context,
            "chat_history": chat_history
        }

        response = ""
        for chunk in llm_chain.stream(input_data):
            response += chunk if isinstance(chunk, str) else chunk.get("text", "")

        if user_input:
            db.add_chat(user_id, user_input, response)

        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return f"Error processing request: {str(e)}"

if __name__ == "__main__":
    print("=== Nutrition Coach Bot ===")
    print("Running in standalone mode. Enter user ID to start.")
    user_id = input("Enter user ID: ").strip()
    print("Type 'exit' to quit")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Bot: Goodbye! Stay healthy 🌱")
            break
        
        response = get_bot_response(user_id, user_input)
        print(f"Bot: {response}")