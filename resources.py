from flask import jsonify
from flask_restful import abort, Resource


class Landing(Resource):
    def get(self):
        return 'landing page'


class Login(Resource):
    def get(self):
        return 'login page'


class Register(Resource):
    def get(self):
        return 'register page'


class Home(Resource):
    def get(self):
        return 'home page'
