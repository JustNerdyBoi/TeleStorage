from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired
from requests import post
from config import read_buffer_size, chat_id, bot_tokens
import math
import pathlib
import telebot
from data.chunk import Chunk
from shutil import rmtree

bots = []
upload_tasks = []
for token in bot_tokens:
    bots.append({'bot': telebot.TeleBot(token), 'load': 0})


def upload_by_bot(bot, chunk_path, bot_number, file_id, db_sess, parent_dir):
    message = None
    while message is None:
        try:
            chunk = open(chunk_path, 'rb')
            message = bot['bot'].send_document(chat_id, chunk, timeout=10)
            chunk.close()
        except:
            print(f'Retrying bot {bot_number + 1} task')
    global bots
    global upload_tasks

    bots[bot_number]['load'] -= 1
    for i in range(len(upload_tasks)):
        if upload_tasks[i]['task_name'] == file_id:
            upload_tasks[i]['progress'] += 1
            break

    uploaded_chunk = Chunk()
    uploaded_chunk.chat_id = message.chat.id
    uploaded_chunk.message_id = message.id
    uploaded_chunk.file_id = file_id
    uploaded_chunk.token = bot['bot'].token
    db_sess.add(uploaded_chunk)
    db_sess.commit()
    current_task = upload_tasks[i]

    print(f'Uploading {chunk_path}, msgid:{message.id} - done by bot {bot_number + 1}, '
          f'progress {current_task["progress"]}/{current_task["expected_chunks"]}')

    if current_task["progress"] == current_task["expected_chunks"]:
        print(f'Uploading task {current_task["task_name"]} done, deleting local files')
        rmtree(parent_dir)


def join_file(path):
    chunks = list(pathlib.Path(path).rglob('*.chk'))
    chunks.sort()
    for i in chunks:
        print(i)
    extension = chunks[0].suffixes[0]

    with open(f'join{extension}', 'ab') as file:
        for chunk in chunks:
            with open(chunk, 'rb') as piece:
                while True:
                    bfr = piece.read(read_buffer_size)
                    if not bfr:
                        break
                    file.write(bfr)


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
