from flask import Flask, request, render_template, Blueprint, g, session, redirect, url_for, flash
from werkzeug.utils import secure_filename

from App_chatbot.db import get_db

from markdown import markdown
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
    formatted_prompt = f"Le contexte de la conversation est {context}. \n maintenant l'utilisateur demande {question}"
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


def vector_docs(pdf_path, agent_name):

    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=10)
    documents = text_splitter.split_documents(docs)
    
    try:
        vectorStore = FAISS.load_local(f"App_chatbot/vectorsDB/{agent_name}_faiss.index", embeddings, allow_dangerous_deserialization=True)
        vectorStore.add_documents(documents=documents)
        vectorStore.save_local(f"vectorsDB/{agent_name}_faiss.index")
        print("Création d'une nouvelle base de données vectorielle")
    except Exception as e:
        try : 
            vectorStore = FAISS.from_documents(documents, embeddings)
        except Exception as e:
            vectorStore = FAISS.from_documents(documents, embeddings)
        vectorStore.save_local(f"App_chatbot/vectorsDB/{agent_name}_faiss.index")
        print("Ajout des données à la base de données vectorielle")
    return vectorStore

@bp.route("/")
def home():
    return render_template("accueil/home.html")

@bp.route("/<agent_name>", methods=('GET', 'POST'))
def chat_bot(agent_name):
    print(g.user[0])
    try:
        print(f"{session['agent_name']} ici")
        if session['agent_name'] != agent_name:
            session.pop('conversation_history', None)
    except Exception as e:
        print(e)

    session['agent_name'] = agent_name
    db = get_db()
    try: 
        owner = db.execute(f"SELECT entreprise_id FROM agent WHERE agent_name='{agent_name}'").fetchone()[0]
        print(owner)
    except Exception as e:
        owner = None
        print(e)
    
    if 'conversation_history' not in session:
        session['conversation_history'] = []

    if request.method == "POST":
        user_input = request.form["prompt"]
        
        if user_input.upper() == "FIN":
            session.pop('conversation_history', None)
            message = "Conversation terminée. Merci d'avoir utilisé notre service."
            return render_template("chatbot/chatbot.html", context={'history': [], 'message': message, "agent_name": agent_name})
        
        try: 
            response = markdown(rag_chain(session['conversation_history'], user_input, agent_name))
            session['conversation_history'].append({'user': user_input, 'chatbot': response})
            session.modified = True
        except Exception as e:
            flash("le chatbot n'est pas prêt pour l'utilisation, veuillez contacter l'entreprise directement")
    
    context = {
        'history': session.get('conversation_history', []),
        'agent_name': agent_name,
        'owner': owner
    }
    return render_template("chatbot/chatbot.html", context=context)


# add agent
@bp.route('/admin/add_agent', methods=('GET', 'POST'))
def add_agent():
    if 'entreprise_id' not in session:
        return redirect(url_for('views.login'))

    if request.method == 'POST':
        agent_name = request.form['agent_name']
        db = get_db()
        url_vers_la_BD = f"App_chatbot/vectorsDB/{agent_name}_faiss.index"
        try:
            db.execute(
                'INSERT INTO agent (agent_name, url_vers_la_BD, entreprise_id) VALUES (?, ?, ?)',
                (agent_name, url_vers_la_BD ,session['entreprise_id'])
            )
            db.commit()
        except db.IntegrityError:
            error = f"ce nom {agent_name} existe déjà"
            flash(error)
        return redirect(url_for('views.index'))

    return render_template('chatbot/add_agent.html')


@bp.route("/admin/add_documents/<agent_name>", methods=('GET', 'POST'))
def add_documents(agent_name):
    flash('Les documents doivent être au format pdf')
    if request.method == "POST":
        pdf_file = request.files["pdf_file"]
        try:
            pdf_path = os.path.join(create_app().config['UPLOAD_FOLDER'], pdf_file.filename)
            pdf_file.save(pdf_path)
            vector_docs(pdf_path, agent_name)
            print(pdf_path)
            message = "document ajouté avec succès"
            os.remove(pdf_path)
        except Exception as e:
            message = f"une erreur s'est produite {e}"

        return render_template("upload/upload.html", message=message)
    return render_template("upload/upload.html")

# Route pour la page d'accueil après connexion
@bp.route('/admin')
def index():
    if 'entreprise_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_db()
    entreprise_id = session['entreprise_id']
    entreprise = db.execute(
        'SELECT * FROM entreprise WHERE id = ?', (entreprise_id,)
    ).fetchone()

    try:
        agents = db.execute(
            f'SELECT * FROM agent WHERE entreprise_id = {entreprise_id}'
        ).fetchall()
    except Exception as e:
        agents = None
        print(e)

    context = {
        "entreprise": entreprise,
        "agents": agents
    }
    if entreprise is None:
        return redirect(url_for('auth.login'))

    return render_template('accueil/index.html', context=context)

# @app.route("/api_test/")
# def test_api