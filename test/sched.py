# -- coding: utf-8 --
import time
import pytz
from apscheduler.schedulers.background import BackgroundScheduler    # apscheduler 라이브러리 선언
import configparser
import json
import logging.config
import os
from configparser import ConfigParser

import psycopg2 as pg2
from flask import Flask, jsonify, request, render_template
from flask_caching import Cache

from logging_conf import LOGGING_CONFIG
from src.cmplan import complain_keyword
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
COMPLAIN_KEYWORD_DIC = config_parser.get('table-info', 'COMPLAIN_KEYWORD_DIC')

# Flask & Flask_cache
app = Flask(__name__)  # Flask에 객체를 만들고
app.config.from_pyfile("conf/flask-caching.conf")
app.config['JSON_AS_ASCII'] = False  # jsonify return 시 한글이 ascii 값으로 전달되어 ascii 설정 off 함
cache = Cache(app)  # cache 객체에 flask 객체를 입혀서 처리하는 방식

# LOG
logging.config.dictConfig(LOGGING_CONFIG)


@app.route("/")
def template_test():
    return render_template(
        'index.html',
        title="template test",
        message="ftp test"
    )


@app.route('/ftp', methods=['GET', 'POST'])
def ftp():
    json_data = json.loads(request.data)
    logging.info("json_data: %s", json_data)

    return {"result": "success"}


@app.route('/ping', methods=['GET', 'POST'])
def ping():
    logging.debug("pong")
    return "pong"


@app.route('/scheduler_test', methods=['GET', 'POST'])
def scheduler_test():
    time_check = time.strftime("%H:%M:%S")
    # logging.info("sched info")
    print("sched start : {}".format(time_check))


# sched = BackgroundScheduler(daemon=True, timezone=pytz.timezone('Asia/Seoul'))
# sched.add_job(scheduler_test, 'interval', seconds=5)
# print("add job")
# sched.start()

sched = BackgroundScheduler(daemon=True, timezone=pytz.timezone('Asia/Seoul'))
# sched.add_job(service, 'cron', week='1-53', day_of_week='0-6', hour='21')
# sched.add_job(scheduler_test, 'interval', seconds=5)
sched.add_job(scheduler_test, 'cron', hour='10', minute='7')
sched.start()

if __name__ == '__main__':
    logging.info("b2b_ta_ftp start version: %s", VERSION)
    app.run('0.0.0.0', port=9999, use_reloader=False)

