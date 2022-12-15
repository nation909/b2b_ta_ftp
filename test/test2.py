

if __name__ == '__main__':
    pos_list = ['NNP', 'NNG']
    stopword = ['확인', '싶어']
    wordfilter = lambda w: w[0] not in stopword and len(w[0]) >= 2 and w[1] in pos_list
    # print(wordfilter)
    print(wordfilter('NNP'))
    # temp = []
    # for w in pos_list:
    #     if w[0] not in stopword and len(w[0]) >= 2 and w[1]:
    #         temp.append(w)
    # print(temp)
