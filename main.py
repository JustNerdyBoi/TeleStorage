from config import chunk_size, uploading_limit_by_bot
from data import db_session
from data.chunk import Chunk
from data.file import File
from data.user import User
from flask import Flask, render_template, request, redirect, send_file, make_response
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_restful import Api
from hashlib import sha3_256
from math import ceil
from os import listdir
from pathlib import Path
from shutil import rmtree
import resources
import services
import threading

app = Flask(__name__, template_folder="static/htmls")
app.secret_key = 'secretkeychangeonrelease'

api = Api(app, catch_all_404s=True)
api.add_resource(services.SplitAndUpload, '/splitandupload')
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
    downloaded_file_id = str(request.cookies.get("downloading_file_id", 0))
    if downloaded_file_id:
        path_of_file = f"temp/{current_user.id}/{downloaded_file_id}"
        if not resources.is_file_operating(downloaded_file_id) and Path(path_of_file).exists():
            rmtree(path_of_file)
            downloaded_file_id = 0
            print(f'Deleting local file {downloaded_file_id}')

    db_sess = db_session.create_session()

    if request.method == "POST":

        if request.files:
            received_file = request.files['file1']

            filename = received_file.filename

            uploaded_file = File()
            uploaded_file.name = filename
            uploaded_file.user_id = current_user.id
            db_sess.add(uploaded_file)
            db_sess.commit()

            path_of_file = f"temp/{current_user.id}/{uploaded_file.id}/file"
            Path(path_of_file).mkdir(parents=True, exist_ok=True)
            received_file.save(f'{path_of_file}/{filename}')

            bytesize = Path(f'{path_of_file}/{filename}').stat().st_size

            uploaded_file.displaysize = resources.convert_size(bytesize)
            uploaded_file.size = bytesize
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            user.used_storage += bytesize
            db_sess.commit()

            print(f'Got file from {current_user.login} (id:{current_user.id}) - {filename}')

            threading.Thread(target=resources.request_task,
                             args=('http://localhost:8000/splitandupload', {'user_id': current_user.id,
                                                                            'file_id': uploaded_file.id,
                                                                            'file_path': f'{path_of_file}/{filename}',
                                                                            'file_size': bytesize})).start()

            resources.bot_tasks.append({'task_name': uploaded_file.id,
                                        'mode': 'Uploading',  # type of task
                                        'expected_chunks': ceil(bytesize / chunk_size),
                                        'progress': 0})

    tasks = {int(i["task_name"]): i["mode"] for i in resources.bot_tasks}
    files = db_sess.query(File).filter(File.user_id == current_user.id)[::-1]
    response = make_response(render_template('home.html', title='Home',
                                             current_user=current_user, files=files,
                                             used_storage=resources.convert_size(current_user.used_storage),
                                             delet_mode_selected=1, tasks=tasks))
    response.set_cookie('downloading_file_id', str(downloaded_file_id), expires=0)
    return response


@app.route("/delete/<file_id>", methods=['POST', 'GET'])
@login_required
def delete(file_id):
    if resources.is_file_operating(file_id):
        print('del abort')
        return redirect("/home")
    db_sess = db_session.create_session()
    file = db_sess.query(File).filter(File.user_id == current_user.id).filter(File.id == file_id).first()
    chunks = db_sess.query(Chunk).filter(Chunk.file_id == file.id).all()

    if file:
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        user.used_storage -= int(file.size)
        if user.used_storage < 0:
            user.used_storage = 0

        for chunk in chunks:
            db_sess.delete(chunk)
        db_sess.delete(file)

        db_sess.commit()
        print(f'Removed from database file {file_id}')

    path_to_temp_file = (Path.cwd() / 'temp' / str(current_user.id) / file_id)
    if path_to_temp_file.exists():
        rmtree(path_to_temp_file)
        print(f'Removed directory {path_to_temp_file}')

    return redirect('/home')


@app.route("/download/<file_id>", methods=['POST', 'GET'])  # changes
@login_required
def download(file_id):
    db_sess = db_session.create_session()
    file = db_sess.query(File).filter(File.user_id == current_user.id).filter(File.id == file_id).first()
    if not file:
        return redirect('/home')

    if resources.is_file_operating(file_id):
        return render_template('download_page.html')

    path_of_file = f"temp/{current_user.id}/{file_id}"
    if Path(path_of_file).exists():
        dirlist = listdir(path_of_file + '/file')
        if dirlist:
            full_path = path_of_file + '/file/' + dirlist[0]
            if int(Path(full_path).stat().st_size) == int(file.size):
                print('Sending file to client')
                return send_file(full_path, as_attachment=True)
    print('Starting downloading')
    Path(path_of_file + '/file').mkdir(parents=True, exist_ok=True)
    Path(path_of_file + '/chunks').mkdir(parents=True, exist_ok=True)

    chunks = list(db_sess.query(Chunk).filter(Chunk.file_id == file_id))

    resources.bot_tasks.append({'task_name': file_id,
                                'mode': 'download',
                                'expected_chunks': len(chunks),
                                'progress': 0})
    while chunks:
        wait_for_bot = True
        while wait_for_bot:
            for chunk in chunks:
                for bot_number in range(len(resources.bots)):
                    bot = resources.bots[bot_number]
                    if bot['bot'].token == chunk.token and bot['load'] < uploading_limit_by_bot:
                        wait_for_bot = False
                        break
        threading.Thread(
            target=resources.download_by_bot,
            args=(bot, bot_number, file_id, path_of_file, chunk)
        ).start()
        chunks.remove(chunk)

    response = make_response(render_template('download_page.html', title=str(file.name)))
    response.set_cookie("downloading_file_id", str(file_id),
                        max_age=60 * 60 * 24 * 365 * 2)
    return response


def main():
    from waitress import serve
    db_session.global_init("db/base.db")  # инициация бд
    serve(app, host="192.168.1.54", port=4040, threads=6)



if __name__ == '__main__':
    main()

