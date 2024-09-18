from flask import Flask, request, render_template, Blueprint, g, session, redirect, url_for
from werkzeug.utils import secure_filename

from App_chatbot.db import get_db

import os
from decouple import config
from markupsafe import escape

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

def retriever_func(agent_name):
    vectorStore = FAISS.load_local(f"App_chatbot/vectorsDB/{agent_name}_faiss.index", embeddings, allow_dangerous_deserialization=True)
    retriever = vectorStore.as_retriever()
    return retriever

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
        
# def rag_chain(question):
#     retrieved_docs = retriever.invoke(question)
#     formatted_context = combine_docs(retrieved_docs)
#     return _llm(question, formatted_context)

def rag_chain(history, question, agent_name):
    history_text = "\n".join(f"User: {h['user']}\nChatbot: {h['chatbot']}" for h in history)
    full_context = history_text + "\nUser: " + question
    retriever = retriever_func(agent_name)
    retrieved_docs = retriever.invoke(full_context)
    formatted_context = combine_docs(retrieved_docs)
    return _llm(full_context, formatted_context)


def vector_docs(pdf_path):

    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=10)
    documents = text_splitter.split_documents(docs)
    
    try:
        vectorStore = FAISS.load_local("App_chatbot/vectorsDB/faiss.index", embeddings, allow_dangerous_deserialization=True)
        vectorStore.add_documents(documents=documents)
        vectorStore.save_local("vectorsDB/faiss.index")
        print("Création d'une nouvelle base de données vectorielle")
    except Exception as e:
        try : 
            vectorStore = FAISS.from_documents(documents, embeddings)
        except Exception as e:
            vectorStore = FAISS.from_documents(documents, embeddings)
        vectorStore.save_local("App_chatbot/vectorsDB/faiss.index")
        print("Ajout des données à la base de données vectorielle")
    return vectorStore

@bp.route("/")
def home():
    return """<h3> Hello, welcome to kosi AI, please ask the link of agent to you provider !</h3>
            test link: <a href="http://156.67.29.207:5000/Hermann">Hermann agent</a>
        """

@bp.route("/<agent_name>", methods=('GET', 'POST'))
def chat_bot(agent_name):
    agent_name = escape(agent_name)
    
    if 'conversation_history' not in session:
        session['conversation_history'] = []

    if request.method == "POST":
        user_input = request.form["prompt"]
        
        if user_input.upper() == "FIN":
            session.pop('conversation_history', None)
            message = "Conversation terminée. Merci d'avoir utilisé notre service."
            return render_template("chatbot/chatbot.html", context={'history': [], 'message': message})
        
        response = rag_chain(session['conversation_history'], user_input, agent_name)
        session['conversation_history'].append({'user': user_input, 'chatbot': response})
        session.modified = True
    
    context = {
        'prompt': "",
        'result': "",
        'history': session.get('conversation_history', []),
        'agent_name': agent_name
    }
    return render_template("chatbot/chatbot.html", context=context)


# Route pour ajouter un agent
@bp.route('/add_agent', methods=('GET', 'POST'))
def add_agent():
    if 'entreprise_id' not in session:
        return redirect(url_for('views.login'))

    if request.method == 'POST':
        agent_name = request.form['agent_name']
        db = get_db()
        db.execute(
            'INSERT INTO agent (agent_name, entreprise_id) VALUES (?, ?)',
            (agent_name, session['entreprise_id'])
        )
        db.commit()
        return redirect(url_for('views.index'))

    return render_template('chatbot/add_agent.html')


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

# Route pour la page d'accueil après connexion
@bp.route('/index')
def index():
    if 'entreprise_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_db()
    entreprise_id = session['entreprise_id']
    entreprise = db.execute(
        'SELECT * FROM entreprise WHERE id = ?', (entreprise_id,)
    ).fetchone()

    if entreprise is None:
        return redirect(url_for('auth.login'))

    return render_template('accueil/index.html', entreprise=entreprise)

# @app.route("/api_test/")
# def test_api