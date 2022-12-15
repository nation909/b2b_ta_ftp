import os
import shutil
import datetime

from flask import Flask
app = Flask(__name__)  # Flask에 객체를 만들고

if __name__ == '__main__':
    # Mecab 기존 CSV파일 오늘날짜로 백업 및 DB 사전데이터 CSV로 컨버팅
    try:
        csv_dir = '../csv/'
        today = datetime.datetime.today().strftime('%Y%m%d')
        bak_dir = '../csv/bak/'

        # 백업 폴더 만들기(해당날짜)
        if not os.path.exists(bak_dir + today):
            os.makedirs(bak_dir + today)
            print("created backup directory: {}".format(bak_dir + today))

        csv_list = [file for file in os.listdir(csv_dir) if file.endswith('.csv')]
        print("csv_list: {}".format(csv_list))
        for csv in csv_list:
            shutil.copy(csv_dir + csv, bak_dir + today)
            print("copy backup user csv file: {}".format(csv))
            print()

        # 사용자 사전 (custom_dic.csv)
        custom_dic_file = csv_dir + 'custom_dic.csv'
        if os.path.exists(custom_dic_file):
            os.remove(custom_dic_file)

        with open(custom_dic_file, 'w', encoding='utf-8') as f:
            f.write('모카브라운,,,,NNP,*,T,모카브라운,*,*,*,*,*\n')
            f.write('테스트,,,,NNP,*,F,테스트,*,*,*,*,*')

        # 일주일전 백업파일 삭제
        before_week_day = (datetime.datetime.today() - datetime.timedelta(weeks=1)).strftime('%Y%m%d')
        if os.path.exists(bak_dir + before_week_day):
            shutil.rmtree(bak_dir + before_week_day)
            print("remove backup directory: {}".format(bak_dir + before_week_day))

    except Exception as e:
        print("Mecab CSV Convert Error: {}".format(e))
