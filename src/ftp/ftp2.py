import csv
import json
import logging
import os
import shutil
import subprocess
import time
from queue import Queue
from threading import Thread
import requests

from config import (
    FTP_UPLOAD_PATH, FTP_FILE_ENCODING,
    PR_INFO_COUNT, REMAINED_FILE_COUNT, CSV_SEPARATOR,
    DEMO_FLAG, SERVER_URL, SFTP_CONFIG_PATH, SFTP_CONFIG_DEFAULT_FILE_PATH)
from make_prinfo import make_product_info
from utils.time_utils import current_time
from version import VERSION

csv_queue = Queue()


def _parsing_csv(file):
    try:
        filename = os.path.basename(file)
        logging.info('start to parse file : %s', filename)
        task_id = filename
        logging.info('task id : %s', task_id)

        product_list = []
        row_total_count = 0
        row_count = 0
        row_err_count = 0
        error_log = []

        csv_file = file

        temp_row = []
        concat_count = 0

        with open(csv_file, 'r', encoding=FTP_FILE_ENCODING, errors='ignore') as f:
            lines = list(csv.reader(f, delimiter=CSV_SEPARATOR))
            for raw in lines:
                try:
                    if raw:
                        row_total_count += 1
                        if len(raw) != PR_INFO_COUNT:
                            if len(raw) == 16:
                                temp_row = raw
                                continue
                            else:
                                temp_row[15] = temp_row[15] + '\n' + raw[0]
                                if len(temp_row) > 1:
                                    temp_row.extend(raw[1:])

                                if len(temp_row) == PR_INFO_COUNT:
                                    raw = temp_row
                                    logging.debug('concat: %s', temp_row)
                                    concat_count += 1
                                    temp_row = []
                                else:
                                    continue

                        pr_info = [''] + list(map(str.strip, raw)) + [''] * 6

                        product = make_product_info(pr_info)
                        product_list.append(product)
                        row_count += 1
                except Exception as e:
                    logging.exception("handle error : %s\nraw data: %s", e, raw)
                    error_log.append("handle error : %s\nraw data: %s" % (e, raw))
                    row_err_count += 1

        if row_err_count > 0:
            requests.post('http://' + SERVER_URL + '/api/alarm/csv-parse-error',
                          json={'csv': filename, 'total_count': row_total_count, 'error_count': row_err_count})
        logging.info('total: %s, err: %s, update: %s, concat: %s', row_total_count, row_err_count, row_count, concat_count)

        data = {
            'taskId': task_id, 'priorTaskId': task_id, 'storeCode': 'store-1', 'product': product_list,
            'fileInfo': {
                'filename': task_id,
                'total': row_total_count,
                'update': row_count,
                'led': 0,
                'ledOnly': 0,
                'error': row_err_count,
                'errorLog': error_log,
                'warning': 0,
                'warningLog': [],
            }
        }

        if not DEMO_FLAG:
            resp = requests.post('http://' + SERVER_URL + '/api/product', json=data)
            logging.info('response : %s', resp.json())
        logging.info('demo: %s, posting /api/product \n==>%s', DEMO_FLAG, product_list[:3])
    except Exception as e:
        logging.exception("handle error : %s", e)
    finally:
        for f in _sorted_dir(FTP_UPLOAD_PATH)[REMAINED_FILE_COUNT:]:
            os.remove(os.path.join(FTP_UPLOAD_PATH, f))
            logging.info('remove file : %s', f)


def _sorted_dir(folder):
    def getmtime(name):
        path = os.path.join(folder, name)
        return os.path.getmtime(path)
    return list(filter(lambda x: not x.startswith('CHECK'), sorted(os.listdir(folder), key=getmtime, reverse=True)))


def csv_executor():
    while True:
        try:
            filename = csv_queue.get()
            _parsing_csv(filename)
        except Exception as e:
            logging.exception("handle error : %s", e)


def get_file_list(username, password, host, port, path):
    cmd = "sshpass -p '{password}' ssh -oStrictHostKeyChecking=no {username}@{host} -p {port} 'ls -l --full-time {path}'".format(
        username=username, password=password, host=host, port=port, path=path)
    ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    err = ret.stderr.decode('utf-8')
    out = ret.stdout.decode('utf-8')

    if err:
        return err, []

    files = []
    res = out.split('\n')
    for r in res:
        t = r.split()
        if len(t) > 8 and 'd' not in t[0] and 'l' not in t[0]:
            file_name = t[8]
            file_size = t[4]
            file_mtime = " ".join(t[5:7])
            files.append({'name': file_name, 'size': file_size, 'mtime': file_mtime})
    return None, files


def remove_file(username, password, host, port, path, file_name):
    cmd = "sshpass -p '{password}' ssh -oStrictHostKeyChecking=no {username}@{host} -p {port} 'rm -rf {path}/{file_name}'".format(
        username=username, password=password, host=host, port=port, path=path, file_name=file_name)
    subprocess.run(cmd, shell=True)


def csv_checker():
    with open('{}/sftp_config.json'.format(SFTP_CONFIG_PATH)) as config_file:
        sftp_config = json.load(config_file)
        sftp_server = sftp_config['sftp_server']
        sftp_port = int(sftp_config['sftp_port'])
        sftp_username = sftp_config['sftp_username']
        sftp_password = sftp_config['sftp_password']
        sftp_home_dir = sftp_config['sftp_home_dir']

    if not sftp_server or not sftp_port or not sftp_username or not sftp_password or not sftp_home_dir:
        logging.info("Please check the SFTP setting.")
        return False

    check_time = current_time()
    error_time = 0

    while True:
        try:
            err, file_list = get_file_list(sftp_username, sftp_password, sftp_server, sftp_port, sftp_home_dir)
            if err:
                raise Exception(str(err))

            file_dict = {}
            while True:
                file_count = 0
                for file_info in file_list:
                    try:
                        file_count += 1
                        f = file_info['name']
                        file_size = file_info['size']
                        file_mtime = file_info['mtime']

                        if f not in file_dict or (file_dict[f]['size'] != file_size) or (
                                file_dict[f]['mtime'] != file_mtime):
                            file_dict[f] = {
                                'size': file_size,
                                'mtime': file_mtime
                            }
                            logging.info('found filename : %s, size : %s, mtime : %s', f, file_size, file_mtime)
                        elif 'checked' not in file_dict[f]:
                            file_dict[f]['checked'] = True
                            filename, ext = os.path.splitext(f)
                            if ext:
                                ext = '.' + ext
                            target_file = FTP_UPLOAD_PATH + '/{}_{}{}'.format(filename, time.time(), ext)

                            start_time = time.time()
                            logging.info("transfer start : %s", f)
                            subprocess.call(
                                'sshpass -p "{password}" scp -o StrictHostKeyChecking=no {username}@{host}:{home_dir}/{filename} {target_file}'.format(
                                    username=sftp_username, password=sftp_password, host=sftp_server,
                                    home_dir=sftp_home_dir, filename=f, target_file=target_file), shell=True)
                            logging.info("transfer completed : %s, check time: %s", f, time.time() - start_time)

                            remove_file(sftp_username, sftp_password, sftp_server, sftp_port, sftp_home_dir, f)
                            csv_queue.put(target_file)
                    except Exception as e:
                        logging.exception("sftp error : %s, file : %s", e, f)
                if file_count == 0:
                    file_dict.clear()
                    break
                time.sleep(3)

                err, file_list = get_file_list(sftp_username, sftp_password, sftp_server, sftp_port, sftp_home_dir)
                if err:
                    raise Exception(str(err))
                logging.info("dir : %s", file_list)
        except Exception as e:
            logging.exception("handle error : %s", e)
            if check_time > error_time:
                error_time = current_time() + 3600
                requests.post('http://' + SERVER_URL + '/api/alarm/ftp-connection-error', json={'server': sftp_server})
            else:
                check_time = current_time()
        time.sleep(10)


def start():
    if not os.path.exists(FTP_UPLOAD_PATH):
        os.makedirs(FTP_UPLOAD_PATH)
        shutil.chown(FTP_UPLOAD_PATH, 'nginx', 'nginx')
    os.system('chmod 757 {}'.format(FTP_UPLOAD_PATH))

    if not os.path.exists(SFTP_CONFIG_PATH):
        os.makedirs(SFTP_CONFIG_PATH)
        os.system('cp {}/sftp_config.json {}'.format(SFTP_CONFIG_DEFAULT_FILE_PATH, SFTP_CONFIG_PATH))
        os.system('chown -R nginx:nginx {}'.format(SFTP_CONFIG_PATH))

    logging.info('Starting the sftp checker %s', VERSION)

    Thread(target=csv_executor).start()
    csv_checker()