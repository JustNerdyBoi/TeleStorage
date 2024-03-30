from flask import Flask, render_template, request, redirect
from flask_restful import Api
import resources
from hashlib import sha3_256
from flask_login import LoginManager
from data import db_session
from data.user import User

app = Flask(__name__, template_folder="static/htmls")
app.secret_key = 'secretkeychangeonrelease'

api = Api(app, catch_all_404s=True)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(id)


@app.route('/', methods=['POST', 'GET'])
def landing():
    return render_template('landing.html')


@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        db_sess = db_session.create_session()
        current_user = db_sess.query(User).filter(User.email == request.form['email']).first()
        if current_user:
            if current_user.hashed_password == sha3_256(request.form['password'].encode()).hexdigest():
                return 'successful login'
        return 'incorrect email or password'


@app.route("/register", methods=['POST', 'GET'])
def registration():
    if request.method == 'GET':
        return render_template('registration.html')

    elif request.method == 'POST':

        db_sess = db_session.create_session()

        if db_sess.query(User).filter(User.email == request.form['email']).all():
            return 'email exists'

        if not request.form['password']:
            return 'no password'

        user = User()
        user.email = request.form['email']
        user.hashed_password = sha3_256(request.form['password'].encode()).hexdigest()
        db_sess.add(user)
        db_sess.commit()

        return 'successful registration'


@app.route("/home", methods=['POST', 'GET'])
def home():
    return render_template('user-data_show.html')


def main():
    db_session.global_init("db/base.db")  # инициация бдl
    app.run(port=8000, host='127.0.0.1')


if __name__ == '__main__':
    main()
