from config import read_buffer_size, chat_id, bot_tokens
from data.chunk import Chunk
from data.db_session import create_session
from data.file import File
from flask_wtf import FlaskForm
from requests import post
from shutil import rmtree
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired
import math
import pathlib
import telebot

bots = []
bot_tasks = []
for token in bot_tokens:
    bots.append({'bot': telebot.TeleBot(token), 'load': 0})


def is_file_operating(file_id):
    tasks = [i["task_name"] for i in bot_tasks]
    if file_id in tasks:
        return True
    return False


def download_by_bot(bot, bot_number, file_id, path_of_file, chunk):
    downloaded_file = None
    file_id_info = bot['bot'].get_file(chunk.chat_file_id)
    while downloaded_file is None:
        try:
            downloaded_file = bot['bot'].download_file(file_id_info.file_path)
        except:
            print(f'Retrying bot {bot_number + 1} task')
    print(f'Downloading {chunk.file_name} of {file_id} done')
    with open(f"{path_of_file}/chunks/{chunk.file_name}", 'wb') as new_file:
        new_file.write(downloaded_file)

    global bots
    global bot_tasks
    if bots[bot_number]['load'] > 0:
        bots[bot_number]['load'] -= 1
    for i in range(len(bot_tasks)):
        current_task = bot_tasks[i]
        if current_task['task_name'] == file_id and current_task['mode'] == 'download':
            current_task['progress'] += 1
            break

    if current_task["progress"] == current_task["expected_chunks"]:
        print(f'Downloading {file_id} done')
        assemble_file(path_of_file, file_id)
        del bot_tasks[i]


def upload_by_bot(bot, chunk_path, bot_number, file_id, db_sess, parent_dir):
    message = None
    while message is None:
        try:
            chunk = open(chunk_path, 'rb')
            message = bot['bot'].send_document(chat_id, chunk, timeout=10)
            chunk.close()
        except:
            chunk.close()
            print(f'Retrying bot {bot_number + 1} task')
    global bots
    global bot_tasks

    for i in range(len(bot_tasks)):
        current_task = bot_tasks[i]
        if current_task['task_name'] == file_id and current_task['mode'] == 'Uploading':
            current_task['progress'] += 1
            break

    uploaded_chunk = Chunk()
    uploaded_chunk.chat_file_id = message.document.file_id
    uploaded_chunk.file_name = chunk_path.split('/')[-1]
    uploaded_chunk.file_id = file_id
    uploaded_chunk.token = bot['bot'].token
    db_sess.add(uploaded_chunk)

    print(f'Uploading {chunk_path}, msgid:{message.id} - done by bot {bot_number + 1}, '
          f'progress {current_task["progress"]}/{current_task["expected_chunks"]}')
    if bots[bot_number]['load'] > 0:
        bots[bot_number]['load'] -= 1

    if current_task["progress"] == current_task["expected_chunks"]:
        del bot_tasks[i]
        print(f'Uploading {file_id} done, deleting local files, remaining bot tasks: {bot_tasks}')
        db_sess.commit()
        db_sess.close()
        rmtree(parent_dir)


def assemble_file(path_of_file, file_id):
    print(f'Starting assembling {file_id}')
    db_sess = create_session()
    name = db_sess.query(File.name).filter(File.id == file_id)[0][0]
    db_sess.close()
    chunks = list(pathlib.Path(f"{path_of_file}/chunks").rglob('*.chk'))
    chunks.sort()

    with open(f"{path_of_file}/file/{name}", 'ab') as file:
        for chunk in chunks:
            with open(chunk, 'rb') as piece:
                while True:
                    bfr = piece.read(read_buffer_size)
                    if not bfr:
                        break
                    file.write(bfr)
            piece.close()
    print(f'File {file_id} assembled')
    rmtree(f"{path_of_file}/chunks")


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def request_task(url, json):
    post(url, json=json, timeout=(10, 1200))


class LoginForm(FlaskForm):
    login = StringField('Login', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField()
    remember_me = BooleanField('Remember me')
