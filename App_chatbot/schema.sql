DROP TABLE IF EXISTS entreprise;
DROP TABLE IF EXISTS agent;
DROP TABLE IF EXISTS client;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS base_donnees;
DROP TABLE IF EXISTS conversation_history;


CREATE TABLE entreprise (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    adresse TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    password_ TEXT NOT NULL
);

CREATE TABLE agent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name VARCHAR(50) NOT NULL,
    url_vers_la_BD VARCHAR(255),
    entreprise_id INTEGER,
    FOREIGN KEY (entreprise_id) REFERENCES entreprise(id)
);

CREATE TABLE client (
    num_ticket INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_entreprise INTEGER,
    nom_fichier VARCHAR(255) NOT NULL,
    chemin_vers_fichier VARCHAR(255) NOT NULL,
    date_d_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_entreprise) REFERENCES entreprise(id)
);

CREATE TABLE base_donnees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom VARCHAR(50) NOT NULL,
    type VARCHAR(50),
    agent_id INTEGER,
    FOREIGN KEY (agent_id) REFERENCES agent(id)
);

CREATE TABLE conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_client INTEGER,
    user_input TEXT,
    response TEXT,
    datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_client) REFERENCES client(num_ticket)
    -- Ajouter ici les clés étrangères vers les documents si nécessaire
);