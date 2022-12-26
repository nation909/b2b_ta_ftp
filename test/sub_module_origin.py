# -- coding: utf-8 --
import configparser
import datetime
import logging.config
import os
import shutil
import subprocess
import time
from configparser import ConfigParser

import psycopg2 as pg2
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from jamo import h2j, j2hcj

from logging_conf import LOGGING_CONFIG
from version import VERSION

# Config
CURR_DIR = os.getcwd()
config = ConfigParser()
config.read(CURR_DIR + '/config.ini')
target = config.get('server', 'target', fallback='dev')

config_file_path = CURR_DIR + '/conf/ta_sub_module_{}.conf'.format(target)
config_parser = configparser.RawConfigParser()
config_parser.read(config_file_path)
HOST = config_parser.get('postgres-info', 'POSTGRES_HOST')
PORT = config_parser.get('postgres-info', 'POSTGRES_PORT')
ID = config_parser.get('postgres-info', 'POSTGRES_ID')
PW = config_parser.get('postgres-info', 'POSTGRES_PW')
DB = config_parser.get('postgres-info', 'POSTGRES_DB')
CUSTOM_DIC = config_parser.get('table-info', 'CUSTOM_DIC')
NER_DIC = config_parser.get('table-info', 'NER_DIC')
MECAB_PATH = config_parser.get('mecab-info', 'MECAB_PATH')

# Flask & Flask_cache
app = Flask(__name__)  # Flask에 객체를 만들고
app.config.from_pyfile("conf/flask-caching.conf")
app.config['JSON_AS_ASCII'] = False  # jsonify return 시 한글이 ascii 값으로 전달되어 ascii 설정 off 함

# LOG
logging.config.dictConfig(LOGGING_CONFIG)


def custom_dic_load():
    conn = pg2.connect(host=HOST, user=ID, password=PW, database=DB, port=PORT)
    curs = conn.cursor()
    sql = "select morphem, pos, synonym, costs from {} where use_yn = 'Y'".format(CUSTOM_DIC)
    curs.execute(sql)
    custom_dic = {i[0]: [i[1], i[2], i[3]] for i in curs.fetchall()}
    conn.close()
    return custom_dic


def ner_dic_load():
    conn = pg2.connect(host=HOST, user=ID, password=PW, database=DB, port=PORT)
    curs = conn.cursor()
    sql = "select keyword, ne, pos from {} where ne = '인명' and use_yn = 'Y'".format(NER_DIC)
    curs.execute(sql)
    person_dic = {i[0]: [i[1], i[2]] for i in curs.fetchall()}

    sql = "select keyword, ne, pos from {} where ne = '지명' and use_yn = 'Y'".format(NER_DIC)
    curs.execute(sql)
    place_dic = {i[0]: [i[1], i[2]] for i in curs.fetchall()}
    conn.close()
    return person_dic, place_dic


def get_jongsung_TF(text):
    text_list = list(text)
    last_word = text_list[-1]
    last_word_jamo_list = list(j2hcj(h2j(last_word)))
    last_jamo = last_word_jamo_list[-1]

    jongsung_TF = "T"
    if last_jamo in ['ㅏ', 'ㅑ', 'ㅓ', 'ㅕ', 'ㅗ', 'ㅛ', 'ㅜ', 'ㅠ', 'ㅡ', 'ㅣ', 'ㅘ', 'ㅚ', 'ㅙ', 'ㅝ', 'ㅞ', 'ㅢ', 'ㅐ,ㅔ', 'ㅟ', 'ㅖ',
                     'ㅒ']:
        jongsung_TF = "F"
    return jongsung_TF


@app.route('/mecab_rebuild', methods=['POST'])
def mecab_rebuild_post():
    check = mecab_rebuild()
    # global tagger
    # tagger = Mecab.Tagger('-d {}'.format(MECAB_PATH))
    if check == 0:
        return "rebuild failed, check the error log"
    else:
        return "success"


def run_command(command):
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = p.communicate()
    try:
        err = error.decode('utf-8').splitlines()
    except UnicodeDecodeError:
        err = str(error)

    if len(err) != 0 and p.poll() != 0:
        return [0, err]
    else:
        return [1, output]


def mecab_rebuild():
    result = run_command("sh " + CURR_DIR + "/script/mecab_custom_dic.sh " + MECAB_PATH)
    if result[0] != 1:
        logging.error(result[1] if len(result) >= 2 else "Fail to Mecab_Custom_Vocab_Rebuild, Command was Wrong")
        return 0
    else:
        return 1


@app.route('/mecab_convert', methods=['GET', 'POST'])
def mecab_convert():
    start_time = time.time()
    logging.info("Mecab Convert Start: {}".format(time.strftime('%H:%M:%S')))

    # Mecab 기존 CSV파일 오늘날짜로 백업 및 DB 사전데이터 CSV로 컨버팅
    try:
        # local
        # csv_dir = './csv/'
        # today = datetime.datetime.today().strftime('%Y%m%d')
        # bak_dir = './csv/bak/

        # dev
        csv_dir = '/home/aiccta/project/mecab/dic/user-dic/'
        today = datetime.datetime.today().strftime('%Y%m%d')
        bak_dir = '/home/aiccta/project/mecab/dic/user-dic/bak/'

        # 1. user-dic CSV 백업 (해당날짜)
        if not os.path.exists(bak_dir + today):
            os.makedirs(bak_dir + today)
            logging.info("Create Backup Directory: {}".format(bak_dir + today))

        csv_list = [file for file in os.listdir(csv_dir) if file.endswith('.csv')]
        logging.info("Backup CSV List: {}".format(csv_list))
        for csv in csv_list:
            shutil.copy(csv_dir + csv, bak_dir + today)

        # 2-1. 사용자사전 DB Data Load
        custom_dic = custom_dic_load()
        logging.info("Custom Dic Data Load Length: {}".format(len(custom_dic)))

        # 2-2. 사용자사전 CSV Write (custom_dic.csv)
        custom_dic_file = csv_dir + 'custom_dic.csv'
        if os.path.exists(custom_dic_file):
            os.remove(custom_dic_file)

        with open(custom_dic_file, 'w', encoding='utf-8') as f:
            for keyword, value_list in custom_dic.items():
                synonym = value_list[1].split(',')
                check = False
                for i in synonym:
                    if keyword == i:
                        check = True
                    f.write("{},,,{},{},*,{},{},*,*,*,*,*\n".format(i, value_list[2], value_list[0],
                                                                    get_jongsung_TF(keyword), keyword))

                if check is False:  # 유의어와 키워드(대표어)가 다른 케이스만 있는 경우
                    f.write("{},,,{},{},*,{},{},*,*,*,*,*\n".format(keyword, value_list[2], value_list[0],
                                                                    get_jongsung_TF(keyword), keyword))

        logging.info("Custom Dic CSV Write Success: {}".format(time.strftime('%H:%M:%S')))

        # 3-1. 개체명사전 DB Data Load
        person_dic, place_dic = ner_dic_load()
        logging.info("NER Dic Data Load Person Length: {}, Place Length: {}".format(len(person_dic, len(place_dic))))

        # 3-2-1. 개체명사전 인명 CSV Write (person.csv)
        person_dic_file = csv_dir + 'person.csv'
        if os.path.exists(person_dic_file):
            os.remove(person_dic_file)

        with open(person_dic_file, 'w', encoding='utf-8') as f:
            for keyword, value_list in person_dic.items():
                f.write("{},,,,{},{},{},{},*,*,*,*,*\n".format(keyword, value_list[1], value_list[0],
                                                               get_jongsung_TF(keyword), keyword))
        logging.info("Person Dic CSV Write Success: {}".format(time.strftime('%H:%M:%S')))

        # 3-2-2. 개체명사전 지명 CSV Write (place.csv)
        place_dic_file = csv_dir + 'place.csv'
        if os.path.exists(place_dic_file):
            os.remove(place_dic_file)

        with open(place_dic_file, 'w', encoding='utf-8') as f:
            for keyword, value_list in place_dic.items():
                f.write("{},,,,{},{},{},{},*,*,*,*,*\n".format(keyword, value_list[1], value_list[0],
                                                               get_jongsung_TF(keyword), keyword))
        logging.info("Place Dic CSV Write Success: {}".format(time.strftime('%H:%M:%S')))

        # 일주일전 백업파일 삭제
        before_week_day = (datetime.datetime.today() - datetime.timedelta(weeks=1)).strftime('%Y%m%d')
        if os.path.exists(bak_dir + before_week_day):
            shutil.rmtree(bak_dir + before_week_day)
            logging.info("Remove Backup Directory: {}".format(bak_dir + before_week_day))

        _ = mecab_rebuild_post()

    except Exception as e:
        logging.error("Mecab CSV Convert Error: {}".format(e))

    end_time = time.time()
    logging.info("Mecab Convert Process Time: {}".format(end_time - start_time))


@app.route('/ping', methods=['GET', 'POST'])
def ping():
    logging.debug("sub module pong")
    return "sub module pong"


sched = BackgroundScheduler(daemon=True, timezone=pytz.timezone('Asia/Seoul'))
sched.add_job(mecab_convert, 'cron', hour='3')  # 새벽 3시 Mecab Convert
sched.add_job(mecab_convert, 'interval', seconds=30)  # 30초마다 반복 Mecab Convert
sched.start()

if __name__ == '__main__':
    logging.info("TA Sub Module Start Version: %s", VERSION)
    app.run('0.0.0.0', port=9999, use_reloader=False)
