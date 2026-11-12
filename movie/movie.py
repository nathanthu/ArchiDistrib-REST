from flask import Flask, request, jsonify, make_response
import json

app = Flask(__name__)

PORT = 3200
HOST = '0.0.0.0'

# chargement de la "base de donnees" json en memoire au demarrage
with open('{}/databases/movies.json'.format("."), 'r') as jsf:
    movies = json.load(jsf)["movies"]

# reecrit tout le fichier json a partir de la liste en memoire
def write(movies):
    with open('{}/databases/movies.json'.format("."), 'w') as f:
        full = {}
        full['movies'] = movies
        json.dump(full, f)

# root message
@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Movie service!</h1>", 200)

# tous les films
@app.route("/json", methods=['GET'])
def get_json():
    return make_response(jsonify(movies), 200)

# un film a partir de son id (id dans le chemin)
@app.route("/movies/<movieid>", methods=['GET'])
def get_movie_byid(movieid):
    for movie in movies:
        if str(movie["id"]) == str(movieid):
            return make_response(jsonify(movie), 200)
    # 404 : la ressource demandee n'existe pas
    return make_response(jsonify({"error": "movie ID not found"}), 404)

# un film a partir de son titre (titre en parametre de requete : ?title=...)
@app.route("/moviesbytitle", methods=['GET'])
def get_movie_bytitle():
    title = request.args.get("title")
    for movie in movies:
        if str(movie["title"]) == str(title):
            return make_response(jsonify(movie), 200)
    return make_response(jsonify({"error": "movie title not found"}), 404)

# ajout d'un film, le film est donne en json dans le corps de la requete
@app.route("/movies/<movieid>", methods=['POST'])
def add_movie(movieid):
    req = request.get_json()

    for movie in movies:
        if str(movie["id"]) == str(movieid):
            # 409 : conflit avec une ressource existante
            return make_response(jsonify({"error": "movie ID already exists"}), 409)

    movies.append(req)
    write(movies)
    # 201 : ressource creee
    return make_response(jsonify({"message": "movie added"}), 201)

# modification de la note d'un film
@app.route("/movies/<movieid>/<rate>", methods=['PUT'])
def update_movie_rating(movieid, rate):
    for movie in movies:
        if str(movie["id"]) == str(movieid):
            movie["rating"] = float(rate)
            write(movies)
            return make_response(jsonify(movie), 200)

    return make_response(jsonify({"error": "movie ID not found"}), 404)

# suppression d'un film, on renvoie le film supprime
@app.route("/movies/<movieid>", methods=['DELETE'])
def del_movie(movieid):
    for movie in movies:
        if str(movie["id"]) == str(movieid):
            movies.remove(movie)
            write(movies)
            return make_response(jsonify(movie), 200)

    return make_response(jsonify({"error": "movie ID not found"}), 404)

if __name__ == "__main__":
    print("Server running in port %s" % (PORT))
    app.run(host=HOST, port=PORT)
