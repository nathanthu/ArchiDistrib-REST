from flask import Flask, request, jsonify, make_response
import requests
import json

app = Flask(__name__)

PORT = 3201
HOST = '0.0.0.0'

# adresses des autres services appeles par Booking
MOVIE_URL = "http://localhost:3200"
SCHEDULE_URL = "http://localhost:3202"
USER_URL = "http://localhost:3203"

with open('{}/databases/bookings.json'.format("."), "r") as jsf:
   bookings = json.load(jsf)["bookings"]

def write(bookings):
   with open('{}/databases/bookings.json'.format("."), 'w') as f:
      json.dump({"bookings": bookings}, f)

# renvoie les reservations d'un utilisateur, ou None s'il n'en a pas
def find_booking(userid):
   for booking in bookings:
      if str(booking["userid"]) == str(userid):
         return booking
   return None

# demande au service User si l'utilisateur existe
def get_user(userid):
   res = requests.get(f"{USER_URL}/users/{userid}")
   if res.status_code != 200:
      return None
   return res.json()

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the Booking service!</h1>"

# toutes les reservations, reserve aux admins : /bookings?userid=...
@app.route("/bookings", methods=['GET'])
def get_bookings():
   user = get_user(request.args.get("userid"))
   if user is None or not user["admin"]:
      return make_response(jsonify({"error": "admin only"}), 403)
   return make_response(jsonify(bookings), 200)

# les reservations d'un utilisateur
@app.route("/bookings/<userid>", methods=['GET'])
def get_user_bookings(userid):
   booking = find_booking(userid)
   if booking is None:
      return make_response(jsonify({"error": "no booking for this user"}), 404)
   return make_response(jsonify(booking), 200)

# les reservations d'un utilisateur avec le detail de chaque film (appel a Movie)
@app.route("/bookings/<userid>/details", methods=['GET'])
def get_user_bookings_details(userid):
   booking = find_booking(userid)
   if booking is None:
      return make_response(jsonify({"error": "no booking for this user"}), 404)

   dates = []
   for day in booking["dates"]:
      movies = []
      for movieid in day["movies"]:
         res = requests.get(f"{MOVIE_URL}/movies/{movieid}")
         if res.status_code == 200:
            movies.append(res.json())
         else:
            # film supprime de Movie entre temps : on garde au moins l'id
            movies.append({"id": movieid})
      dates.append({"date": day["date"], "movies": movies})

   return make_response(jsonify({"userid": userid, "dates": dates}), 200)

# ajout d'une reservation, corps : {"date": "...", "movieid": "..."}
@app.route("/bookings/<userid>", methods=['POST'])
def add_booking(userid):
   req = request.get_json()
   date = req["date"]
   movieid = req["movieid"]

   # l'utilisateur doit exister (appel a User)
   if get_user(userid) is None:
      return make_response(jsonify({"error": "user not found"}), 404)

   # le film doit etre programme a cette date (appel a Schedule)
   res = requests.get(f"{SCHEDULE_URL}/schedule/{date}")
   if res.status_code != 200 or movieid not in res.json()["movies"]:
      # 400 : la demande est invalide
      return make_response(jsonify({"error": "movie not scheduled at this date"}), 400)

   # on cree l'entree de l'utilisateur si c'est sa premiere reservation
   booking = find_booking(userid)
   if booking is None:
      booking = {"userid": userid, "dates": []}
      bookings.append(booking)

   # on cherche la date dans ses reservations, sinon on la cree
   day = None
   for d in booking["dates"]:
      if d["date"] == date:
         day = d
   if day is None:
      day = {"date": date, "movies": []}
      booking["dates"].append(day)

   if movieid in day["movies"]:
      return make_response(jsonify({"error": "booking already exists"}), 409)

   day["movies"].append(movieid)
   write(bookings)
   return make_response(jsonify(booking), 201)

# suppression d'une reservation precise (un film a une date)
@app.route("/bookings/<userid>/<date>/<movieid>", methods=['DELETE'])
def del_booking(userid, date, movieid):
   booking = find_booking(userid)
   if booking is not None:
      for day in booking["dates"]:
         if day["date"] == date and movieid in day["movies"]:
            day["movies"].remove(movieid)
            # on enleve la date si elle n'a plus de film
            if not day["movies"]:
               booking["dates"].remove(day)
            write(bookings)
            return make_response(jsonify(booking), 200)
   return make_response(jsonify({"error": "booking not found"}), 404)

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
