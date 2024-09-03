from flask import Flask, request, render_template, Blueprint, g

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings

import ollama
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings

from . import create_app

bp = Blueprint("views", __name__, url_prefix="/")

embeddings = OllamaEmbeddings(model="llama3")
vectorStore = Chroma(persist_directory="./vector_store_db", embedding_function=embeddings)
retriever = vectorStore.as_retriever()

def ollama_llm(question, context):
    formatted_prompt = f"question: {question}\n\n context: {context}"
    response = ollama.chat(model="llama3", messages=[{'role': 'user', "content": formatted_prompt}])
    return response['message']['content']


def combine_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
        
def rag_chain(question):
    retrieved_docs = retriever.invoke(question)
    formatted_context = combine_docs(retrieved_docs)
    return ollama_llm(question, formatted_context)

@bp.route("/", methods=('GET', 'POST'))
def chat_bot():
    if request.method == "POST":
        result = rag_chain(request.form["prompt"])
        return render_template("chatbot/chatbot.html", result=result)
    return render_template("chatbot/chatbot.html")


#@app.route("/api_test/")
# def test_api 