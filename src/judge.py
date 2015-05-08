#encoding:utf-8
import requests
import re

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

def lottery_judge(text):
    pattern = re.compile(r'(博彩|赌场|赌博|娱乐城|AV|六合彩)')
    judge_list = pattern.findall(text.encode('utf-8'))
    judge_list = list(set(judge_list))    # URL去重
    count = len(judge_list)
    if count > 3:
        return [True, count]

    return [False, count]



print lottery_judge(r.text)