from flask import Flask, render_template, request, redirect
from flask_restful import Api
from flask_login import LoginManager
from data.user import User
import resources

from data import db_session

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
        print(request.form['email'])
        return redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


@app.route("/register", methods=['POST', 'GET'])
def registration():
    if request.method == 'GET':
        return render_template('registration.html')
    elif request.method == 'POST':
        user = User()
        user.email = request.form['email']
        user.hashed_password = request.form['password']
        db_sess = db_session.create_session()
        db_sess.add(user)
        db_sess.commit()
        return redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


@app.route("/home", methods=['POST', 'GET'])
def home():
    return render_template('user-data_show.html')


def main():
    db_session.global_init("db/base.db")  # инициация бд
    app.run(port=8000, host='127.0.0.1')


if __name__ == '__main__':
    main()
# sdasdsaddssddas
