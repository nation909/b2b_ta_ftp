import re
import time

from jamo import h2j, j2hcj

import csv


def get_jongsung_TF(sample_text):
    sample_text_list = list(sample_text)
    last_word = sample_text_list[-1]
    last_word_jamo_list = list(j2hcj(h2j(last_word)))
    last_jamo = last_word_jamo_list[-1]
    print(sample_text_list)
    print(last_word)
    print(last_word_jamo_list)
    print(last_jamo)

    jongsung_TF = "T"
    if last_jamo in ['ㅏ', 'ㅑ', 'ㅓ', 'ㅕ', 'ㅗ', 'ㅛ', 'ㅜ', 'ㅠ', 'ㅡ', 'ㅣ', 'ㅘ', 'ㅚ', 'ㅙ', 'ㅝ', 'ㅞ', 'ㅢ', 'ㅐ,ㅔ', 'ㅟ', 'ㅖ',
                     'ㅒ']:
        print("if: {}".format(last_jamo))
        jongsung_TF = "F"
    return jongsung_TF


def user_dic_convert():
    try:
        with open('../csv/mecab_apply.csv', encoding='utf-8', newline='') as file:
            lines = list(csv.reader(file))
            with open('../csv/user-dic.csv', 'w+', encoding='utf-8', newline='') as user_dic_file:
                writer = csv.writer(user_dic_file, delimiter=' ', escapechar=' ', quoting=csv.QUOTE_NONE)
                for line in lines:
                    keyword = line[0]
                    print(keyword)
                    user_dic = "{},,,,NNP,*,F,{},*,*,*,*,*".format(keyword, keyword)
                    writer.writerow([user_dic])
    except Exception as e:
        print(e)


def read_keyword_list():
    try:
        keyword_list = []
        with open('../csv/kms_test2.csv', encoding='utf-8', newline='') as file:
            lines = list(csv.reader(file, delimiter=','))
            for line in lines[1:]:  # remove header column
                keyword = line[0]
                remove_char = re.compile(r'[0-9a-zA-Z]')
                output_string = remove_char.sub(' ', keyword).strip()
                if output_string is not '' and len(output_string) > 1:
                    keyword_list.append(output_string)
        return keyword_list
    except Exception as e:
        print(e)


def write_keyword_csv(keyword_list):
    try:
        with open('../csv/mecab_apply.csv', 'w+', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            for keyword in keyword_list:
                print(keyword)
                writer.writerow([keyword])
    except Exception as e:
        print(e)


if __name__ == '__main__':
    print(get_jongsung_TF("구글"))  # 종성 유무 판단
    # user_dic_convert()
    # start_time = time.time()
    # keywords = read_keyword_list()
    # print("keywords: {}".format(keywords))
    #
    # write_keyword_csv(keywords)
    # end_time = time.time()
    # print("time check: {}".format(end_time - start_time))
