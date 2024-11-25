import argparse
import tarfile
import json
import datetime
import os
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(description='Эмулятор оболочки ОС')
    parser.add_argument('-u', '--username', required=True, help='Имя пользователя для приглашения')
    parser.add_argument('-c', '--computername', required=True, help='Имя компьютера для приглашения')
    parser.add_argument('-f', '--fs', required=True, help='Путь к архиву виртуальной файловой системы')
    parser.add_argument('-l', '--logfile', required=True, help='Путь к лог-файлу')
    return parser.parse_args()

def load_filesystem(fs_path):
    try:
        tar = tarfile.open(fs_path, 'r')
        return tar
    except FileNotFoundError:
        print(f'Ошибка: Файловая система {fs_path} не найдена.')
        sys.exit(1)
    except tarfile.ReadError:
        print(f'Ошибка: Не удалось прочитать архив {fs_path}.')
        sys.exit(1)

def log_action(logfile, user, action):
    log_entry = {
        'timestamp': datetime.datetime.now().isoformat(),
        'user': user,
        'action': action
    }
    with open(logfile, 'a', encoding='utf-8') as f:
        json.dump(log_entry, f, ensure_ascii=False)
        f.write('\n')

def handle_ls(tar_fs, current_dir, options):
    path = current_dir.strip('/')
    if options:
        path = os.path.normpath(os.path.join(path, options[0])).strip('/')
    entries = set()
    for member in tar_fs.getmembers():
        if member.name.startswith(path):
            relative_path = member.name[len(path):].lstrip('/')
            if relative_path == '':
                continue
            parts = relative_path.split('/', 1)
            entry = parts[0]
            entries.add(entry)
    for entry in sorted(entries):
        print(entry, end='  ')
    print()

def handle_cd(tar_fs, current_dir, path):
    if path == '/':
        return '/'
    new_path = os.path.normpath(os.path.join(current_dir, path))
    if not new_path.endswith('/'):
        new_path += '/'
    normalized_path = new_path.strip('/')
    for member in tar_fs.getmembers():
        if member.name.strip('/') == normalized_path and member.isdir():
            return new_path
    print(f'cd: {path}: Нет такого файла или каталога')
    return current_dir

def handle_wc(tar_fs, current_dir, filename):
    file_path = os.path.normpath(os.path.join(current_dir, filename)).lstrip('/')
    try:
        file_member = tar_fs.getmember(file_path)
        if file_member.isfile():
            f = tar_fs.extractfile(file_member)
            content = f.read()
            lines = content.count(b'\n')
            words = len(content.split())
            bytes_count = len(content)
            print(f' {lines} {words} {bytes_count} {filename}')
        else:
            print(f'wc: {filename}: Это не файл')
    except KeyError:
        print(f'wc: {filename}: Нет такого файла')

def handle_tac(tar_fs, current_dir, filename):
    file_path = os.path.normpath(os.path.join(current_dir, filename)).lstrip('/')
    try:
        file_member = tar_fs.getmember(file_path)
        if file_member.isfile():
            f = tar_fs.extractfile(file_member)
            content = f.read().decode('utf-8')
            lines = content.rstrip('\n').split('\n')
            for line in reversed(lines):
                print(line)
        else:
            print(f'tac: {filename}: Это не файл')
    except KeyError:
        print(f'tac: {filename}: Нет такого файла')

def main():
    args = parse_arguments()
    tar_fs = load_filesystem(args.fs)
    current_dir = '/'
    while True:
        try:
            prompt = f'{args.username}@{args.computername}:{current_dir}$ '
            command_input = input(prompt).strip()
            if not command_input:
                continue
            log_action(args.logfile, args.username, command_input)
            command_parts = command_input.split()
            command = command_parts[0]
            parameters = command_parts[1:]

            if command == 'exit':
                break
            elif command == 'ls':
                handle_ls(tar_fs, current_dir, parameters)
            elif command == 'cd':
                if parameters:
                    current_dir = handle_cd(tar_fs, current_dir, parameters[0])
                else:
                    current_dir = '/'
            elif command == 'wc':
                if parameters:
                    handle_wc(tar_fs, current_dir, parameters[0])
                else:
                    print('wc: отсутствует операнд')
            elif command == 'tac':
                if parameters:
                    handle_tac(tar_fs, current_dir, parameters[0])
                else:
                    print('tac: отсутствует операнд')
            else:
                print(f'{command}: команда не найдена')
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            print('exit')
            break

if __name__ == '__main__':
    main()