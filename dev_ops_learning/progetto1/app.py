from flask import Flask, request, jsonify, render_template, Response
from pymongo import MongoClient
from bson import ObjectId, json_util

app = Flask(__name__)

# Connessione a MongoDB
#client = MongoClient("mongodb://localhost:27017/")  vecchia 
#inserita su suggerimento di gelsomino
client = MongoClient("mongodb://mongo:27017/")
db = client["mio_db_mongolo1"]
collection = db["utenti"]

#definizione del file index.html

@app.route("/")
def home():
    return render_template("index.html")

# Endpoint 1: Inserire un nuovo utente (POST)
@app.route("/aggiungi", methods=["POST"])
def aggiungi_utente():
    data = request.json
    result = collection.insert_one(data)
    return jsonify({"message": "Utente inserito!", "id": str(result.inserted_id)}), 201

# Endpoint 2: Recuperare tutti gli utenti (GET)
@app.route("/utenti", methods=["GET"])
def ottieni_utenti():
    utenti = list(collection.find({}, {"_id": 0}))
    return jsonify(utenti), 200

# Endpoint 3: aggiunta multiutente (POST)
@app.route("/aggiungi-molti", methods=["POST"])
def aggiungi_molti():
    nuovi_utenti = request.json # Aspettati una lista di dizionari
    result = collection.insert_many(nuovi_utenti)
    return jsonify({"message": f"Inseriti {len(result.inserted_ids)} utenti"}), 201

# Endpoint 4: Ricerca utenti per nome (GET)
@app.route("/utenti/cerca-nome/", methods=["POST"])
def trova_utente_per_nome():
    data = request.json
    nome_da_cercare = data.get("nome")
    # CORREZIONE: Applichiamo la collation alla query
    # find_one accetta un argomento 'collation'
    utente = collection.find_one(
        {"nome": nome_da_cercare}, 
        {"_id": 0},
        collation={"locale": "it", "strength": 2} # La passiamo qui come opzione
    )
    if utente:
        return jsonify(utente), 200
    return jsonify({"error": f"Utente '{nome_da_cercare}' non trovato"}), 404

# Endpoint 4b: Ricerca utenti per ObjectId
@app.route("/utenti/id/<id>", methods=["GET"])
def trova_utente_per_id(id):
    utente = collection.find_one({"_id": ObjectId(id)}, {"_id": 0})
    if utente:
        return jsonify(utente), 200
    return jsonify({"error": "Utente non trovato"}), 404

# Endpoint 5: Modifica mail utente
@app.route("/aggiorna", methods=["PUT"])
def aggiorna_email():
    data = request.json
    # Cerca per nome, aggiorna il campo email
    collection.update_one({"nome": data["nome"]}, {"$set": {"email": data["email"]}})
    return jsonify({"message": "Email aggiornata!"}), 200

# Endpoint 6: Ricerca Avanzata da json
@app.route("/utenti/cerca", methods=["POST"])
def cerca_utenti():
    query = request.json
    filtri = []
    # Esempio: se nel JSON passi "id", lo aggiungiamo ai filtri
    if "id" in query:
        filtri.append({"_id": ObjectId(query["id"])})
    # Esempio: AND tra nome e cognome
    if "nome" in query and "cognome" in query:
        filtri.append({"nome": query["nome"], "cognome": query["cognome"]})
    # Esempio: OR tra nome e email
    if "nome" in query and "email" in query:
        filtri.append({"$or": [{"nome": query["nome"]}, {"email": query["email"]}]})
    # Esegui la query finale (se abbiamo filtri)
    if filtri:
        risultati = list(collection.find({"$and": filtri}, {"_id": 0}))
        return jsonify(risultati), 200
    return jsonify({"error": "Nessun criterio di ricerca valido"}), 400

# Endpoint 7 inserimento utente avanzato
@app.route("/aggiungi-avanzato", methods=["POST"])
def aggiungi_avanzato():
    data = request.json
    
    # Costruiamo il documento in modo flessibile
    nuovo_documento = {
        "nome": data.get("nome"),
        "cognome": data.get("cognome"),
        "email": data.get("email"),
        # Aggiungiamo il file/txt come sottodocumento
        "extra": {
            "chiave_txt": data.get("txt_content"),
            "data_creazione": "2026-06-10"
        }
    }
    result = collection.insert_one(nuovo_documento)
    return jsonify({"message": "Utente avanzato inserito!", "id": str(result.inserted_id)}), 201

# Endpoint 8 modifica da object id
@app.route("/aggiorna-id/<id>", methods=["PUT"])
def aggiorna_per_id(id):
    data = {k: v for k, v in request.json.items() if v} # Filtra solo i campi non vuoti
    collection.update_one({"_id": ObjectId(id)}, {"$set": data})
    return jsonify({"message": "Aggiornato solo i campi forniti!"})

if __name__ == "__main__":
    # Avvia il server Flask ascoltando su tutte le interfacce
    app.run(host="0.0.0.0", port=5000, debug=True)