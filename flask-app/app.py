from flask import Flask
from flask_login import LoginManager
from routes import bp, login_manager

app = Flask(__name__)
app.secret_key = 'C!typ@y!23#'  # Change this!

app.register_blueprint(bp)
login_manager.init_app(app)

if __name__ == '__main__':
    app.run(debug=True)