from flask import Flask, request, render_template, Blueprint, g
import os
from decouple import config

try:
    os.environ.pop('MISTRAL_API_KEY')
except Exception:
     pass
api_key = config('MISTRAL_API_KEY')

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings

from mistralai import Mistral
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings

from . import create_app

bp = Blueprint("views", __name__, url_prefix="/")

client = Mistral(api_key=api_key)
model = "mistral-large-latest"
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
try: 
    vectorStore = FAISS.load_local("faiss.index", embeddings, allow_dangerous_deserialization=True)
    retriever = vectorStore.as_retriever()
except Exception:
    pass


def _llm(question, context):
    formatted_prompt = f"question: {question}\n\n context: {context}"
    response = client.chat.complete(
        model=model,
        messages=[{
            "role": "user",
            "content" : formatted_prompt
        }])
    return response.choices[0].message.content


def combine_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
        
def rag_chain(question):
    retrieved_docs = retriever.invoke(question)
    formatted_context = combine_docs(retrieved_docs)
    return _llm(question, formatted_context)

def vector_docs(pdf_path):

    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=10)
    documents = text_splitter.split_documents(docs)
    
    try:
        vectorStore = FAISS.load_local("faiss.index", embeddings, allow_dangerous_deserialization=True)
        vectorStore.add_documents(documents=documents)
        vectorStore.save_local("faiss.index")
        print("Création d'une nouvelle base de données vectorielle")
    except Exception as e:
        try : 
            vectorStore = FAISS.from_documents(documents, embeddings)
        except Exception as e:
            vectorStore = FAISS.from_documents(documents, embeddings)
        vectorStore.save_local("faiss.index")
        print("Ajout des données à la base de données vectorielle")
    return vectorStore

@bp.route("/", methods=('GET', 'POST'))
def chat_bot():
    if request.method == "POST":
        result = rag_chain(request.form["prompt"])
        return render_template("chatbot/chatbot.html", result=result)
    return render_template("chatbot/chatbot.html")

@bp.route("/admin/add_documents", methods=('GET', 'POST'))
def add_documents():
    if request.method == "POST":
        pdf_file = request.files["pdf_file"]
        try:
            pdf_path = os.path.join(create_app().config['UPLOAD_FOLDER'], pdf_file.filename)
            pdf_file.save(pdf_path)
            vector_docs(pdf_path)
            print(pdf_path)
            message = "document ajouté avec succès"
            os.remove(pdf_path)
        except Exception as e:
            message = f"une erreur s'est produite {e}"
        return render_template("upload/upload.html", message=message)
    return render_template("upload/upload.html")
#@app.route("/api_test/")
# def test_api 