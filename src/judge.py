#encoding:utf-8
import requests
import re
import json

#http://ccn.mofcom.gov.cn/1048340/p4563880.html
#http://big5.csrc.gov.cn/SuniT/www.xftjr.com/

def index(url):
    r = requests.get('http://www.npc.gov.cn/npc/xinwen/2013-07/05/nagezuqiutuijiewangshenglvgaojinboshiyulecheng.htm')

    if r.encoding == 'ISO-8859-1':   #如果没有辨认出正确编码，则设为gb
        encoding_match = re.compile(r'(gb2312|utf-8)',re.I).findall(r.text.encode('utf-8'))
        print encoding_match
        if encoding_match:
            r.encoding = encoding_match[0]
        else:
            r.encoding = 'gb2312'

    print r.text



def get_google_response(keyword, page,  url='http://brisk.eu.org/api/google.php'):
    data = {"q": keyword, "n": page}


    try:
        response = requests.get(url, params=data, timeout=10)
        temp = json.loads(response.text)
    except Exception, e:
        print "google信息获取失败,失败原因：%s " % e
        return []

    return temp



# 判断是否含有博彩信息
def lottery_judge(text):
    # pattern = re.compile(r'(博彩|赌场|赌博|娱乐城|AV|六合彩)')
    # judge_list = pattern.findall(text.encode('utf-8'))
    # judge_list = list(set(judge_list))    # URL去重
    # count = len(judge_list)
    # if count >= 2:
    #     return [True, count]
    #
    # return [False, count]
    pattern = re.compile(r'src=test.com')
    test_list = pattern.findall('<script src=test.com')
    print test_list
