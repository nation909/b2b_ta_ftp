import re

import psycopg2 as pg2

import csv


def get_date(start_year, end_year):
    year_list = []
    for year in range(start_year, end_year + 1):
        year_list.append(year)
    return year_list


# def get_date(start_year, end_year):
#     date_list = []
#     for year in range(start_year, end_year + 1):
#         for month in range(1, 12 + 1):
#             mon = month
#             if mon < 10:
#                 mon = '0' + str(mon)
#             date = '{}-{}'.format(year, mon)
#             date_list.append(date)
#     return date_list


def db_connect(dates):
    conn = pg2.connect(host='localhost', user='postgres', password='1234', database='aiccdev', port=5432)
    curs = conn.cursor()
    item_dic_list = []
    for year in dates:
        year = str(year) + '%'
        sql = "select slitm_nm, reg_dtm from kms.bak_im_slitm_mst_if where reg_dtm::text like '{}'".format(year)
        curs.execute(sql)
        for i in curs.fetchall():
            item_dic_list.append({i[1].strftime("%Y-%m-%d"): i[0]})
    conn.close()
    return item_dic_list


# 키워드, 상품기술서명, 날짜 추출
def preprocess(items):
    datas = []
    for item in items:
        for k, v in item.items():
            # print(k, v)
            # 특수문자 제거
            special_char = re.compile(r'[^0-9a-zA-Z가-힣\s]')
            output_string = special_char.sub(' ', v).strip().split(' ')
            print("output_string: {}".format(output_string))
            for keyword in output_string:
                if keyword is "" or keyword is " ":
                    continue
                print("keyword: {}".format(keyword.strip()))
                datas.append([keyword.strip(), v, k])
    return datas


# 키워드만 추출
def preprocess2(items):
    datas = []
    datas_dic = {}
    for item in items:
        for k, v in item.items():
            # print(k, v)
            # 특수문자 제거
            special_char = re.compile(r'[^0-9a-zA-Z가-힣\s]')
            output_string = special_char.sub(' ', v).strip()
            print("output_string1: {}".format(output_string))
            remove_char = re.compile(r'[0-9a-zA-Z]')
            output_string = remove_char.sub(' ', output_string).strip().split(' ')
            print("output_string2: {}".format(output_string))
            for keyword in output_string:
                keyword = keyword.strip()
                if keyword is "" or keyword is " " or len(keyword) <= 1:
                    continue
                print("keyword: {}".format(keyword.strip()))
                if keyword not in datas_dic:
                    datas_dic[keyword.strip()] = 1
    print("dic: {}".format(datas_dic))
    for keyword in datas_dic:
        print(keyword)
        datas.append([keyword])
    return datas


def file_write(datas):
    # csv 파일 만들기
    try:
        with open("/csv/test.csv", 'w+', encoding='utf-8', newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            for data in datas:
                writer.writerow(data)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    # 날짜 리스트
    dates = get_date(2017, 2022)
    print(dates)

    # db 연결
    items_dic = db_connect(dates)
    print("item_dic: {}".format(items_dic))

    # 월별 데이터 가져와서 전처리(특수문자 제거, split 등)
    datas = preprocess2(items_dic)
    print("datas: {}".format(datas))
    print("datas len: {}".format(len(datas)))

    # list csv, excel로 확인
    file_write(datas)
