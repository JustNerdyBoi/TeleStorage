import pathlib
read_buffer_size = 1024
chunk_size = 2 ** 20 * 25


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


if __name__ == '__main__':
    command = input('command: ')

    if command.lower() == 'split':
        split_file(input('path: '))
    elif command.lower() == 'join':
        join_file(input('path: '))
    else:
        print('use either split or join')
