from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired
from requests import post
from config import read_buffer_size, chat_id, bot_tokens
import math
import pathlib

current_uploading = [0] * len(bot_tokens)


def upload_by_bot(bot, chunk_path, bot_number):
    message_id = None
    while message_id is None:
        try:
            chunk = open(chunk_path, 'rb')
            message_id = bot.send_document(chat_id, chunk, timeout=10)
            chunk.close()
        except:
            print(f'Retrying bot {bot_number + 1} task')
    global current_uploading
    current_uploading[bot_number] -= 1

    print(f'Uploading {chunk_path}, msgid:{message_id.id} - done by bot {bot_number + 1},'
          f' load of bots - {current_uploading}')


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
