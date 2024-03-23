from flask import Flask, render_template
from flask_restful import Api
import resources

from data import db_session

app = Flask(__name__, template_folder="static/htmls")
app.secret_key = 'secretkeychangeonrelease'

api = Api(app, catch_all_404s=True)


@app.route('/', methods=['POST', 'GET'])
def landing():
    return render_template('landing.html')


@app.route("/login", methods=['POST', 'GET'])
def login():
    return 'login page'


@app.route("/register", methods=['POST', 'GET'])
def registration():
    return render_template('registration.html')


@app.route("/home", methods=['POST', 'GET'])
def home():
    return render_template('user-data_show.html')


def main():
    db_session.global_init("db/base.db")  # инициация бд
    app.run(port=8000, host='127.0.0.1')


if __name__ == '__main__':
    main()
#sdasdsaddssddas