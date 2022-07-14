from flask import Flask
from flask_limiter import Limiter # limit the number of requests per IP for differ pricing tier
from flask_limiter.util import get_remote_address
from flask_mailman import Mail # sending newsletter
from api.routes import api
from web.admin.admin_routes import admin
from web.user.user_routes import user
import os, stripe # stripe for payment
from dotenv import load_dotenv


load_dotenv()


app = Flask(__name__)
app.config['SESSION_COOKIE_NAME'] = 'session'
app.config['SECRET_KEY'] = '192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config["UPLOAD_FOLDER_IMAGE"] = "static/image"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ("png", "jpg", "jpeg")
app.config["UPLOAD_FOLDER_VIDEO"] = "static/videos"
app.config["ALLOWED_VIDEO_EXTENSIONS"] = (".mp4, .mov, .avi, .mpeg4, .webm, .mpegs, .wmv")

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "tommy-destiny@gmail.com"
app.config["MAIL_PASSWORD"] = os.getenv("EMAIL_PASS")
mail = Mail(app)

limiter = Limiter(app, key_func=get_remote_address, default_limits=["30 per second"])

app.register_blueprint(api)
app.register_blueprint(admin)
app.register_blueprint(user)

if __name__ == '__main__':
    app.run(debug=True)

'''
Project Structure:

Tommy-Destiny
├── README.md
├── requirements.txt
└── Tommy-Destiny
   ├── __init__.py
   ├── api
   │  │  └── routes.cpython-39.pyc
   │  └── routes.py
   ├── mitigations
   │  ├── A2_Broken_authentication.py
   │  ├── A3_Sensitive_data_exposure.py
   │  ├── A5_Broken_access_control.py
   │  ├── A7_Cross_site_scripting.py
   │  ├── API3_Excessive_data_exposure.py
   │  ├── API4_Lack_of_resource_and_rate_limiting.py
   │  ├── API6_Mass_Assignment.py
   │  └── API10_Insufficient_logging_and_monitoring.py
   ├── Procfile
   ├── static
   │  ├── css
   │  │  └── screen.css
   │  ├── js
   │  │  └── firebaseConfiguration.js
   │  └── py
   │     └── firebaseConnection.py
   ├── templates
   │  ├── base.html
   │  └── includes
   │     ├── footer.html
   │     ├── formHelper.html
   │     └── navbar.html
   └── web
      ├── admin
      │  ├── admin_routes.py
      │  ├── static
      │  │  ├── css
      │  │  │  └── admin.css
      │  │  └── py
      │  │     └── Post.py
      │  └── templates
      │     ├── admin_dashboard.html
      │     ├── admin_editor.html
      │     ├── admin_members.html
      │     ├── admin_pages.html
      │     ├── admin_post.html
      │     ├── admin_settings.html
      │     ├── admin_tags.html
      │     └── admin_viewsite.html
      └── user
         ├── static
         │  ├── css
         │  │  └── signup.css
         │  └── py
         │     └── Forms.py
         ├── templates
         │  ├── home.html
         │  ├── login.html
         │  ├── payment.html
         │  ├── pricing.html
         │  ├── signup.html
         │  └── view_post.html
         └── user_routes.py

'''