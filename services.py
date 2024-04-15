from flask_restful import Resource
from flask import request
import pathlib
import resources
from config import read_buffer_size, chunk_size, bot_tokens, uploading_limit_by_bot
import telebot
from shutil import rmtree
import threading


class SplitAndUpload(Resource):
    def post(self):
        bots = []
        for token in bot_tokens:
            bots.append(telebot.TeleBot(token))

        file_data = request.json
        filepath = file_data['file_path']

        with open(filepath, 'rb') as file:
            path = pathlib.Path(filepath)
            current_chunk_size = 0
            current_chunk = 1
            done_reading = False

            parent_dir = path.parents[1]
            pathlib.Path(f'{parent_dir}/chunks').mkdir()

            while not done_reading:
                chunk_path = f'{parent_dir}/chunks/{str(current_chunk).rjust(8, "0")}{path.suffix}.chk'
                with open(chunk_path, 'ab') as chunk:
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
                wait_for_bot = True
                while wait_for_bot:
                    for bot_number in range(len(resources.current_uploading)):
                        if resources.current_uploading[bot_number] < uploading_limit_by_bot:
                            wait_for_bot = False
                            break
                current_bot = bots[bot_number]
                resources.current_uploading[bot_number] += 1
                print(
                    f'Starting upload task ({chunk_path}) for bot {bot_number + 1},'
                    f' load of bots - {resources.current_uploading}')
                threading.Thread(target=resources.upload_by_bot, args=(current_bot, chunk_path, bot_number)).start()