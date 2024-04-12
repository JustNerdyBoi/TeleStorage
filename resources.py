from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired
import math
import pathlib

read_buffer_size = 1024
chunk_size = 2 ** 20 * 25  # 25 megabytes


def _chunk_file(file, extension):
    current_chunk_size = 0
    current_chunk = 1
    done_reading = False
    while not done_reading:
        with open(f'{str(current_chunk).rjust(8, "0")}{extension}.chk', 'ab') as chunk:
            while True:
                bfr = file.read(read_buffer_size)
                if not bfr:
                    done_reading = True
                    break

                chunk.write(bfr)
                current_chunk_size += len(bfr)
                if current_chunk_size + read_buffer_size > chunk_size:
                    current_chunk += 1
                    current_chunk_size = 0
                    break


def split_file(filepath):
    with open(filepath, 'rb') as file:
        print(file)
        _chunk_file(file, pathlib.Path(filepath).suffix)


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


class LoginForm(FlaskForm):
    login = StringField('Login', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField()
    remember_me = BooleanField('Remember me')
