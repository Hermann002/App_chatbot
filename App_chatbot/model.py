from . import db

class Entreprise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), unique=True, nullable=False)
    url_base_donnees = db.Column(db.String(200), unique=True, nullable=False)
    agents = db.relationship('Agent', backref='entreprise', lazy=True)
    documents = db.relationship('Document', backref='entreprise', lazy=True)
    clients = db.relationship('Client', backref='entreprise', lazy=True)
    
class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    chemin = db.Column(db.String(200), nullable=False)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id', nullable=False))
    
class ConversationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    user_input = db.Column(db.Text, nullable=False)
    chatbot_reponse = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
class VectorStore(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    index_path = db.Column(db.String(200), nullable=False)