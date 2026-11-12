from flask import Flask, request, jsonify, make_response
import requests
import json

app = Flask(__name__)

PORT = 3203
HOST = '0.0.0.0'

BOOKING_URL = "http://localhost:3201"

with open('{}/databases/users.json'.format("."), "r") as jsf:
   users = json.load(jsf)["users"]

def write(users):
   with open('{}/databases/users.json'.format("."), 'w') as f:
      json.dump({"users": users}, f)

# renvoie l'utilisateur correspondant a l'id, ou None s'il n'existe pas
def find_user(userid):
   for user in users:
      if str(user["id"]) == str(userid):
         return user
   return None

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the User service!</h1>"

# liste de tous les utilisateurs, reservee aux admins
# l'id de celui qui fait la demande est passe en parametre : /users?userid=...
@app.route("/users", methods=['GET'])
def get_users():
   requester = find_user(request.args.get("userid"))
   if requester is None or not requester.get("admin"):
      # 403 : on sait qui demande, mais il n'a pas le droit
      return make_response(jsonify({"error": "admin only"}), 403)
   return make_response(jsonify(users), 200)

# un utilisateur (utilise aussi par les autres services pour savoir s'il est admin)
@app.route("/users/<userid>", methods=['GET'])
def get_user(userid):
   user = find_user(userid)
   if user is None:
      return make_response(jsonify({"error": "user not found"}), 404)
   return make_response(jsonify(user), 200)

# l'utilisateur et ses reservations detaillees (appel a Booking, qui appelle Movie)
@app.route("/users/<userid>/bookings", methods=['GET'])
def get_user_bookings(userid):
   user = find_user(userid)
   if user is None:
      return make_response(jsonify({"error": "user not found"}), 404)

   res = requests.get(f"{BOOKING_URL}/bookings/{userid}/details")
   # pas de reservation (404 de Booking) : liste vide
   dates = res.json()["dates"] if res.status_code == 200 else []

   return make_response(jsonify({"user": user, "bookings": dates}), 200)

# creation d'un utilisateur, le corps contient name et last_active
@app.route("/users/<userid>", methods=['POST'])
def add_user(userid):
   if find_user(userid) is not None:
      return make_response(jsonify({"error": "user already exists"}), 409)
   req = request.get_json()
   # l'id vient du chemin, un nouvel utilisateur n'est jamais admin
   user = {
      "id": userid,
      "name": req["name"],
      "last_active": req["last_active"],
      "admin": False
   }
   users.append(user)
   write(users)
   return make_response(jsonify(user), 201)

# modification du nom et/ou de last_active
@app.route("/users/<userid>", methods=['PUT'])
def update_user(userid):
   user = find_user(userid)
   if user is None:
      return make_response(jsonify({"error": "user not found"}), 404)
   req = request.get_json()
   if "name" in req:
      user["name"] = req["name"]
   if "last_active" in req:
      user["last_active"] = req["last_active"]
   write(users)
   return make_response(jsonify(user), 200)

# suppression d'un utilisateur, on renvoie l'utilisateur supprime
@app.route("/users/<userid>", methods=['DELETE'])
def del_user(userid):
   user = find_user(userid)
   if user is None:
      return make_response(jsonify({"error": "user not found"}), 404)
   users.remove(user)
   write(users)
   return make_response(jsonify(user), 200)

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
