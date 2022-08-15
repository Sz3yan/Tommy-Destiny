from email import message
import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import  jwt_required, create_access_token
from static.firebaseConnection import FirebaseAdminClass, FirebaseClass
from mitigations.API10_Insufficient_logging_and_monitoring import User_Logger
import jwt
# from app import app

api = Blueprint('api', __name__, url_prefix='/api')

@api.route("/login", methods=["POST", "GET"])
def api_login():
    print(request.method)
    if request.is_json:
        try:
            email = request.json['email']
            password = request.json['password']

            if not FirebaseClass().login_user(email, password):
                userID = FirebaseClass().get_user()
                User_Logger.log_info("User Login Successful")
                return jsonify(message="Login Successfully", access_token=FirebaseClass().get_user_token()), 200
            else:
                User_Logger.log_info("User Login Failed")
                return jsonify(message="Invalid email or password"), 401
        except:
            return jsonify(message="Invalid key")
    else:
        if request.method == "POST":
            email = request.form["email"]
            password = request.form["password"]

            return jsonify(message=f"d")
        else:
            email = request.form["email"]
            password = request.form["password"]

            return jsonify(message=f"{email}, {password}")
            


@api.route("/favourites")
def api_favourite():
    pass


@api.route("/users")
def api_users():
    if request.is_json:
        name = request.json["user"]
        isAdmin = False
    else:
        isAdmin = request.args.get('isAdmin')
        name = request.args.get("name")
    
    if isAdmin == True:
        return jsonify(message=f"Hi {name}, you are an admin"), 200
    elif name != "":
        return jsonify(message=f"Hi {name}, you are not an admin"), 200
    else:
        return jsonify(message="Invalid parameters"), 404