from flask import Flask, render_template, request, redirect
from flask_restful import Api
import resources
from hashlib import sha3_256
from flask_login import LoginManager, login_user, logout_user, current_user
from werkzeug.utils import secure_filename
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
    return db_sess.query(User).get(user_id)


@app.route('/', methods=['POST', 'GET'])
def landing():
    if current_user.is_authenticated:
        return redirect('/home')

    return render_template('landing.html', title='Home')


@app.route("/login", methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect('/home')

    form = resources.LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.login == request.form['login']).first()
        if user:
            if user.hashed_password == sha3_256(request.form['password'].encode()).hexdigest():
                login_user(user, remember=form.remember_me.data)
                return redirect('/home')
        form.password.errors.append('Incorrect login or password')
    return render_template('login_form.html', form=form, title='Login')


@app.route("/register", methods=['POST', 'GET'])
def registration():
    if current_user.is_authenticated:
        return redirect('/home')

    form = resources.LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.login == request.form['login']).all():
            form.login.errors.append('This login already used')

        elif request.form['password']:
            user = User()
            user.login = request.form['login']
            user.hashed_password = sha3_256(request.form['password'].encode()).hexdigest()
            db_sess.add(user)
            db_sess.commit()

            login_user(user, remember=form.remember_me.data)
            return redirect('/home')

    return render_template('login_form.html', form=form, title='Registration')


@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect("/")


@app.route("/home", methods=['POST', 'GET'])
def home():
    if not current_user.is_authenticated:
        return redirect('/')
    form = resources.UploadForm()
    if form.validate_on_submit():
        if form.file.data:
            filename = secure_filename(form.file.data.filename)
            form.file.data.save('temp/uploads/' + filename)
        else:
            form.file.errors.append('Choose file to upload')
    return render_template('home.html', title='Home', current_user=current_user, form=form)



def main():
    db_session.global_init("db/base.db")  # инициация бдl
    app.run(port=8000, host='127.0.0.1')


if __name__ == '__main__':
    main()
