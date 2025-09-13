from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from dataclasses import dataclass
import json
from datetime import datetime
from enum import Enum
import os
import glob

# Import existing modules
from searchengine import (
    get_user_profile, get_user_nutrition, get_user_chats, 
    get_user_field, build_chatbot_context
)
from db import load_index, USERS_DIR

# ===============================
# 1. Data Models & Enums
# ===============================
class SourceType(Enum):
    NUTRITION_CSV = "nutrition"
    USER_PROFILE = "profile" 
    CHAT_HISTORY = "chat"

@dataclass
class SearchResult:
    documents: List[str]
    metadata: List[Dict[str, Any]]
    scores: Optional[List[float]] = None

# ===============================
# 2. Data Loaders for the System
# ===============================
class NutritionDataLoader:
    @staticmethod
    def load_all_user_profiles() -> List[Dict[str, Any]]:
        """Load all user profiles from your existing user files"""
        try:
            index = load_index()
            all_profiles = []
            
            for user_id, file_path in index.items():
                if os.path.exists(file_path):
                    profile = get_user_profile(user_id)
                    if profile:
                        all_profiles.append(profile)
            
            print(f"Loaded {len(all_profiles)} user profiles from database")
            return all_profiles
            
        except Exception as e:
            print(f"Error loading user profiles: {e}")
            return []
    
    @staticmethod
    def load_all_chat_history() -> List[Dict[str, Any]]:
        """Load all chat history from your existing user files"""
        try:
            index = load_index()
            all_chats = []
            
            for user_id, file_path in index.items():
                chats = get_user_chats(user_id)
                for i, chat in enumerate(chats):
                    # Convert chat format to our format
                    all_chats.extend([
                        {
                            "message_id": f"{user_id}_chat_{i}_user",
                            "user_id": user_id,
                            "timestamp": chat.get("timestamp", ""),
                            "speaker": "user",
                            "message": chat.get("user", ""),
                            "intent": None
                        },
                        {
                            "message_id": f"{user_id}_chat_{i}_bot", 
                            "user_id": user_id,
                            "timestamp": chat.get("timestamp", ""),
                            "speaker": "bot",
                            "message": chat.get("bot", ""),
                            "intent": None
                        }
                    ])
            
            print(f"Loaded {len(all_chats)} chat messages from database")
            return all_chats
            
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return []
    
    @staticmethod
    def load_user_specific_data(user_id: str) -> Dict[str, Any]:
        """Load specific user's profile, nutrition, and chat data"""
        return {
            "profile": get_user_profile(user_id),
            "nutrition": get_user_nutrition(user_id),
            "chats": get_user_chats(user_id),
            "context": build_chatbot_context(user_id)
        }

# ===============================
# 3. Document Processing Module
# ===============================
class DocumentProcessor(ABC):
    @abstractmethod
    def process_data(self, data: Any) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Returns (documents, metadata_list)"""
        pass

class NutritionCSVProcessor(DocumentProcessor):
    def __init__(self, template: str = None):
        self.template = template or (
            "Food: {Food}. Calories: {Calories}. Protein: {Protein}g. "
            "Fat: {Fat}g. Carbohydrates: {Carbohydrates}g. "
            "Nutrition Density Score: {Nutrition Density}."
        )

    def process_data(self, data: pd.DataFrame) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Convert DataFrame rows to formatted document strings"""
        documents = [self.template.format(**row.to_dict()) for _, row in data.iterrows()]
        metadata = [
            {**row.to_dict(), "source_type": SourceType.NUTRITION_CSV.value, "source_id": f"food_{i}"}
            for i, (_, row) in enumerate(data.iterrows())
        ]
        return documents, metadata

class UserProfileProcessor(DocumentProcessor):
    def process_data(self, profiles: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Convert user profiles from your system to searchable documents"""
        documents = []
        metadata = []
        
        for profile in profiles:
            if not profile:
                continue
                
            # Build searchable text from profile
            parts = [f"User profile for {profile.get('name', profile.get('user_id', 'unknown'))}"]
            
            if profile.get('age'): 
                parts.append(f"Age: {profile['age']} years")
            if profile.get('weight'): 
                parts.append(f"Weight: {profile['weight']}kg")
            if profile.get('height'): 
                parts.append(f"Height: {profile['height']}cm")
            if profile.get('goal'): 
                parts.append(f"Goal: {profile['goal']}")
            if profile.get('activity_level'): 
                parts.append(f"Activity level: {profile['activity_level']}")
            
            document = ". ".join(parts)
            documents.append(document)
            
            # Add metadata
            profile_meta = {
                **profile,
                "source_type": SourceType.USER_PROFILE.value,
                "source_id": f"profile_{profile.get('user_id', 'unknown')}"
            }
            metadata.append(profile_meta)
        
        return documents, metadata

class ChatHistoryProcessor(DocumentProcessor):
    def process_data(self, messages: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Convert chat messages from your system to searchable documents"""
        documents = []
        metadata = []
        
        for msg in messages:
            if not msg or not msg.get("message"):
                continue
                
            # Build searchable text
            timestamp = msg.get("timestamp", "")
            speaker = msg.get("speaker", "unknown")
            message = msg.get("message", "")
            
            document = f"{speaker} ({timestamp}): {message}"
            documents.append(document)
            
            # Add metadata
            chat_meta = {
                **msg,
                "source_type": SourceType.CHAT_HISTORY.value,
                "source_id": msg.get("message_id", f"msg_{len(documents)}")
            }
            metadata.append(chat_meta)
        
        return documents, metadata

# ===============================
# 4. Embedding Module
# ===============================
class EmbeddingModel(ABC):
    @abstractmethod
    def encode(self, texts: List[str]) -> List[List[float]]:
        pass

class SentenceTransformerEmbedding(EmbeddingModel):
    def __init__(self, model_name: str = "minilm-l6-v2"):
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

    def encode(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for input texts"""
        return self.model.encode(texts).tolist()

    def encode_query(self, query: str) -> List[float]:
        """Generate embedding for a single query"""
        return self.model.encode([query]).tolist()[0]

# ===============================
# 5. Vector Store Module
# ===============================
class ChromaVectorStore:
    def __init__(self, collection_name: str = "nutrition_assistant", persist_path: str = "./chroma_nutrition"):
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection_name = collection_name
        self._initialize_collection()

    def _initialize_collection(self):
        """Initialize or recreate the collection"""
        try:
            self.client.delete_collection(self.collection_name)
        except:
            pass
        self.collection = self.client.create_collection(self.collection_name)

    def add_documents(self, documents: List[str], embeddings: List[List[float]],
                     metadata: List[Dict[str, Any]], ids: List[str]):
        """Add documents to the vector store"""
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadata
        )

    def search(self, query_embedding: List[float], top_k: int = 5,
               filters: Optional[Dict[str, Any]] = None) -> SearchResult:
        """Search for similar documents"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters
        )

        return SearchResult(
            documents=results.get("documents", [None])[0] or [],
            metadata=results.get("metadatas", [None])[0] or [],
            scores=results.get("distances", [None])[0] if results.get("distances") else None
        )

