class Entreprise:
    def __init__(self, id, nom):
        self.id = id
        self.nom = nom
        self.agents = []
        self.documents = []

    def ajouter_agent(self, agent):
        self.agents.append(agent)

    def televerser_document(self, document):
        self.documents.append(document)

    def trouver_document(self, question):
        # Logique pour trouver le document pertinent en fonction de la question
        pass

class Agent:
    def __init__(self, id, nom):
        self.id = id
        self.nom = nom
        self.historique = []

    def poser_question(self, question):
        # Logique pour poser une question au chatbot
        pass

class Document:
    def __init__(self, id, chemin, contenu):
        self.id = id
        self.chemin = chemin
        self.contenu = contenu

    def extraire_contenu(self):
        # Logique pour extraire le contenu du document PDF
        pass

class Historique:
    def __init__(self, id, question, reponse):
        self.id = id
        self.question = question
        self.reponse = reponse
