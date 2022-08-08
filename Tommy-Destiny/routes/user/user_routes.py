import json

from flask import Blueprint, render_template, request, session, redirect, url_for
from mitigations.A3_Sensitive_data_exposure import AES_GCM, GoogleCloudKeyManagement
from mitigations.API10_Insufficient_logging_and_monitoring import User_Logger
from static.py.firebaseConnection import FirebaseClass, FirebaseAdminClass
from routes.user.static.py.Forms import CreateUser, LoginUser

user = Blueprint('user', __name__, template_folder="templates", static_folder='static')
User_Logger = User_Logger()
keymanagement = GoogleCloudKeyManagement()
secret_key = str(keymanagement.retrieve_key("tommy-destiny", "global", "my-key-ring", "key-rotation"))


@user.route("/")
def index():
    try:
        firebase = FirebaseClass()
        posts = [post.val() for post in firebase.get_post().each()]
    except:
        posts = []
        User_Logger.log_exception("No Post in Firebase")

    return render_template('home.html', posts=posts)


@user.route("/pricing")
def pricing():
    return render_template("pricing.html")


@user.route("/login", methods=["POST", "GET"])
def login():
    firebase = FirebaseClass()
    loginUser = LoginUser(request.form)
    if "userID" in session:
        return redirect(url_for('user.profile'))
    else:
        if request.method == "POST" and loginUser.validate():
            session.pop('userID', None)  # auto remove session when trying to login
            User_Logger.log_info("Session removed")
            email = loginUser.email.data
            password = loginUser.password.data

            if not firebase.login_user(email, password):
                userID = firebase.get_user()
                session['userID'] = userID
                User_Logger.log_info("User Login Successful")
                return redirect(url_for("user.profile"))
            else:
                User_Logger.log_info("User Login Failed")
                return render_template('login.html', form=loginUser, message=str(firebase.login_user(email, password)))

    return render_template('login.html', form=loginUser, message="")


@user.route('/logout')
def logout():
    # remove the username from the session if it is there
    session.pop('userID', None)
    User_Logger.log_info("User Logout Successful")
    return redirect(url_for('user.index'))


@user.route('/profile')
def profile():
    
    fa = FirebaseAdminClass()
    if 'userID' in session:
        # this will not hve any id
        user_ID = session["userID"]
        print(user_ID)

        userInfo = fa.get_user(user_ID)
        print(userInfo)
        # g.current_user = userInfo
        return render_template('profile.html')
    else:
        return redirect(url_for('user.index'))


@user.route("/payment")
def payment():
    return render_template("payment.html")


@user.route("/signup", methods=["POST", "GET"])
def signup():
    firebase = FirebaseClass()
    createUser = CreateUser(request.form)
    if request.method == 'POST' and createUser.validate():
        username = createUser.name.data
        email = createUser.email.data
        phno = createUser.phno.data
        password = createUser.register_password.data

        if not firebase.create_user(email, password):
            firebase.create_user_info(username, phno, "customer")
            User_Logger.log_info("User Signup Successful")
        else:
            User_Logger.log_info("User Signup Unsuccessful")
            return render_template('signup.html', form=createUser, message=str(firebase.create_user(email, password)))
    return render_template('signup.html', form=createUser)


@user.route("/post/<id>")
def post(id):
    aes_gcm = AES_GCM()

    data = [{
        "type": "header",
        "data": {
            "text": "Post title",
        }
    }]

    try:
        pull_post = FirebaseClass()

        for i in pull_post.get_post().each():
            if i.val()["_Post__id"] == id:
                plaintext = i.val()["_Post__plaintext"]

                decrypted = aes_gcm.decrypt(secret_key, plaintext)
                print("decrypted: ", decrypted)

                to_json = json.loads(decrypted)
                data = to_json["blocks"]
                User_Logger.log_info(f"view: post_id {id}: " + str(data)) # demo. log only encrypted data
            else:
                data = data
    except:
        User_Logger.log_exception("No posts found")
        return redirect(url_for("home"))

    return render_template('post.html', id=id, data=data)
