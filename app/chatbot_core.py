import os, pickle, hashlib, requests, logging
from groq import Groq
import PyPDF2
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import concurrent.futures

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama3-70b-8192"

# def scrape_website(url):
#     try:
#         res = requests.get(url)
#         return BeautifulSoup(res.text, "html.parser").get_text()
#     except Exception as e:
#         return ""

def extract_text(page):
    try: return page.extract_text()
    except: return ""

def process_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(extract_text, p) for p in reader.pages]
            for fut in concurrent.futures.as_completed(futures):
                try: text += fut.result() + "\n"
                except: continue
    return text

def split_into_chunks(text, chunk_size=1000, overlap=100):
    chunks, start = [], 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start += chunk_size - overlap
    return chunks

def get_or_create_chunks(pdf_paths):
    combined_text = ""
    for path in pdf_paths:
        with open(path, "rb") as f:
            content = f.read()
            file_hash = hashlib.md5(content).hexdigest()
        cache_path = f"cache/{file_hash}_chunks.pkl"
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                combined_text += " ".join(pickle.load(f))
        else:
            text = process_pdf(path)
            combined_text += text
    # combined_text += web_text
    chunks = split_into_chunks(combined_text)
    os.makedirs("cache", exist_ok=True)
    with open(f"cache/{hashlib.md5(combined_text.encode()).hexdigest()}_chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)
    return chunks

def initialize_resources():
    pdfs = ["./Aspire Data/UK.pdf", "./Aspire Data/FAQ;s.pdf","./Aspire Data/AspireEC-Data.pdf"]
    chunks = get_or_create_chunks(pdfs)
    return chunks, TfidfVectorizer().fit(chunks)

def find_relevant_chunks(query, chunks, vectorizer, k=6):
    query_vec = vectorizer.transform([query])
    chunk_vecs = vectorizer.transform(chunks)
    sims = cosine_similarity(query_vec, chunk_vecs)[0]
    indices = sims.argsort()[-k:][::-1]
    return [chunks[i] for i in indices]

def get_ai_response(messages, context):

    # system = {
    # "role": "system",
    # "content": (
    #     "You are a helpful chatbot for Aspire Educational Consulting.\n"
    #     "Answer based only on provided context and history.\n"
    #     "Use active voice. Keep responses under 20 words.\n"
    #     "Greet when user come and when thry greet.\n"
    #     "Say goodbye with nice conversation if user says no/bye/nothing.\n"
    #     "Appreciate compliments politely and also deal with appriciation for your good response.\n"
    #     "For nonsense questions or profanity: 'I'm sorry, I can't answer that question. contact to the AspireEC team \n"
    #     "Answer will be short ,infomative, professional\n"
    #     "Do not use hello i am happy to assist you in start of every response"
    #     )
    # }
   
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

def answer_query(query, messages, chunks, vectorizer):
    # Handle nonsense
    if is_nonsense(query):
        return "", "I'm sorry, I can't answer that question. Please contact our team."

    # Handle smalltalk
    smalltalk_response = is_smalltalk(query)
    if smalltalk_response:
        return "", smalltalk_response

    # Otherwise proceed with vector search + LLM
    context = "\n".join(find_relevant_chunks(query, chunks, vectorizer))
    reply = get_ai_response(messages, context)
    return context, reply



# #hadling the bad words
# def is_nonsense(query: str):
#     bad_words = ["fuck", "shit", "teleport", "mars", "unicorn", "robot", "atlantis"]
#     return any(word in query.lower() for word in bad_words)

# def answer_query(query, messages, chunks, vectorizer):
#     if is_nonsense(query):
#         return "", "I'm sorry, I can't answer that question. Please contact our team."
#     context = "\n".join(find_relevant_chunks(query, chunks, vectorizer))
#     reply = get_ai_response(messages, context)
#     return context, reply


