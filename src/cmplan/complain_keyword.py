import logging
import re


def extract_complain_keyword(sentence, cmplan_kwd_dic):
    try:
        extract_keyword = {}
        for dic in cmplan_kwd_dic:
            count = len(re.findall(dic, sentence))
            if count > 0:
                extract_keyword[dic] = count

        keyword_list = []
        for key, item in extract_keyword.items():
            keyword_dict = {'keyword': key, 'count': item}
            keyword_list.append(keyword_dict)
        result_dict = {"complain_keyword_list": keyword_list}
        logging.debug("extract_complain_keyword Result: %s", result_dict)
    except Exception as e:
        logging.error("Extract Complain Keyword Method Error: {}".format(e))
    return result_dict
