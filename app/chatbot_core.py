import os, pickle, hashlib, requests, logging
from groq import Groq
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import concurrent.futures
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama3-70b-8192"

FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), '..', 'cache', 'faiss_index.bin')
FAISS_META_PATH = os.path.join(os.path.dirname(__file__), '..', 'cache', 'faiss_meta.pkl')
EMBED_MODEL = 'all-MiniLM-L6-v2'

# Load FAISS index and metadata at startup
model = SentenceTransformer(EMBED_MODEL)
faiss_index = faiss.read_index(FAISS_INDEX_PATH)
with open(FAISS_META_PATH, 'rb') as f:
    faiss_meta = pickle.load(f)

def embed_query(query):
    return model.encode([query], convert_to_numpy=True)

def find_relevant_chunks_faiss(query, k=6):
    # 1. Direct string match (case-insensitive)
    for meta in faiss_meta:
        if query.lower() in meta['text'].lower():
            return [meta['text']]
    # 2. If not found, use embedding search
    query_vec = embed_query(query)
    D, I = faiss_index.search(query_vec, k)
    return [faiss_meta[i]['text'] for i in I[0]]

def get_ai_response(messages, context):
    system = {
    "role": "system",
        "content": (
            "You are AspireEC's helpful chatbot. Answer only from provided context and message history.\n"
            "Use active voice. Keep answers short (under 20 words).\n"
            "Be clear, informative, professional, and SEO-optimized.\n"
            "Greet if the user greets. Say goodbye politely if user says no, bye, or nothing.\n"
            "Say 'Thank you' if user appreciates. Never add 'Hello, I am happy to assist you.'\n"
            "If question is nonsense or inappropriate, reply: \"I'm sorry, I can't answer that question. Please contact the AspireEC team.\"\n"
            "Avoid filler, repetition, or unnecessary explanation."
            "Strict rule: Do not repeat generic sentences like 'AspireEC can assist with university selection…'. Tailor answers based on query."
            "Avoid reusing same sentence in multiple answers. Each reply must be unique, directly tied to user question."
        )
    }
    all_msgs = [system] + messages[:-1] + [{"role": "user", "content": f"Context: {context}\n\n{messages[-1]['content']}"}]
    try:
        completion = client.chat.completions.create(messages=all_msgs, 
                                                    model=MODEL,
                                                    temperature=0.5,
                                                    max_tokens=100)
        return completion.choices[0].message.content
    except:
        return "I'm sorry, something went wrong. Please try again."

def is_nonsense(query: str):
    bad_words = ["fuck", "shit", "teleport", "mars", "unicorn", "robot", "atlantis"]
    return any(word in query.lower() for word in bad_words)

def is_smalltalk(query: str):
    greetings = ["hi", "hello", "hey"]
    goodbyes = ["bye", "goodbye", "no", "nothing"]
    acknowledgments = ["ok", "okay", "fine"]
    thanks = ["thanks", "thank you"]
    appreciation = ["great", "awesome", "perfect", "nice", "cool"]

    q = query.lower().strip()
    if q in greetings:
        return "Hello! How can I assist you?"
    elif q in goodbyes:
        return "Bye! See you later."
    elif q in acknowledgments:
        return "Great! Let me know if you need any more help."
    elif q in thanks:
        return "You're welcome! Happy to help."
    elif q in appreciation:
        return "Thank you! I appreciate your feedback."
    return None

def answer_query(query, messages, k=6):
    # Handle nonsense
    if is_nonsense(query):
        return "", "I'm sorry, I can't answer that question. Please contact our team."

    # Handle smalltalk
    smalltalk_response = is_smalltalk(query)
    if smalltalk_response:
        return "", smalltalk_response

    # Otherwise proceed with FAISS vector search + LLM
    context = "\n".join(find_relevant_chunks_faiss(query, k=k))
    reply = get_ai_response(messages, context)
    return context, reply



