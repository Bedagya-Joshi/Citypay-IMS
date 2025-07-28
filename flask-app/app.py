from flask import Flask
from flask_login import LoginManager
from routes import bp, login_manager
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.register_blueprint(bp)
login_manager.init_app(app)

if __name__ == '__main__':
    app.run(host="localhost", port=1451, debug=True)