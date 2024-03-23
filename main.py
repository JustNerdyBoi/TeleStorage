from flask import Flask
from flask_restful import Api
import resources

from data import db_session

app = Flask(__name__)
app.secret_key = 'secretkeychangeonrelease'

api = Api(app, catch_all_404s=True)


def main():
    db_session.global_init("db/base.db")  # инициация бд

    api.add_resource(resources.Landing, '/')
    api.add_resource(resources.Login, '/login')
    api.add_resource(resources.Register, '/register')
    api.add_resource(resources.Home, '/home')

    app.run()


if __name__ == '__main__':
    main()
#sdasdsaddssddas