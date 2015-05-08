#encoding:utf-8
import threading
import requests
import json
import re
from urlparse import urlparse

lock = threading.Lock()
lock2 = threading.Lock()
url_list = []           # 待检索的URL
key_word_list = []      # 二次检索key_word
result_list = []        # 博彩网站list
bad_url_list = []       # 无法连接的URL列表
ErrorInfoPost = True    # 误报信息反馈
# 设定查询URL的页数（省级城市查询前十页，市级查询前5页，县级查询前两页）
UnitPageCount = {"1": 15, "2": 10, "3": 5}

# google搜索发包高级封装
# @input : keyword - 搜索关键字, page - 页码
# @output: google返回的包，list格式
# @错误处理 : 十秒没有数据返回时，返回空list
def get_google_response(location, page, thread_name='null', parse=True, url='http://brisk.eu.org/api/google.php'):
    data = {"q": location, "n": page}
    try:
        response = requests.get(url, params=data, timeout=10)
        temp = json.loads(response.text)
    except Exception, e:
        print "%s 获取页面信息出错" % thread_name
        print e
        return

    for x in temp:
        lock.acquire()
        try:
            if parse:
                url_list.append(urlparse(x["url"]).hostname)
            else:
                url_list.append(x["url"])
        finally:
            lock.release()

def get_google_response_not_thread(location, page, url='http://brisk.eu.org/api/google.php'):
    lists = []
    data = {"q": location, "n": page}
    try:
        response = requests.get(url, params=data, timeout=10)
        temp = json.loads(response.text)
    except Exception, e:
        print "获取google页面信息出错"
        return []

    for x in temp:
        lists.append(x["url"])

    return lists


def get_url_controller(location, page_num, parse=True):
    thread_arr = {}
    for page in range(1, page_num+1):
        thread_arr[page] = threading.Thread(target=get_google_response, args=(location, page, 'thread-%d' % page, parse))
        print "正在读取第 %d 页的内容" % page
        thread_arr[page].start()

    for x in thread_arr:
        thread_arr[x].join()

# 获取第二次检索keyword
# @input : keyword - 检索关键字，如博彩
# @output: keyword_list - 二次检索的直接关键词，若有多个返回list
def get_search_words(keyword):
    if len(url_list) % 28 == 0:         # 第二次检索每次检索28个URL
        time_count = int(len(url_list)/28)
    else:
        time_count = int(len(url_list)/28)+1

    for count in range(time_count):
        keyword_str = keyword           # 重置初始字符串
        if time_count - 1 > count or len(url_list) % 28 == 0:      # 如果不是最后一组或者总数为28的倍数
            temp_time = 28
        else:
            temp_time = len(url_list) % 28

        for each in range(temp_time):
            keyword_str = '%s site:%s OR' % (keyword_str, url_list[count*28 + each].encode('utf-8'))
        key_word_list.append(keyword_str[:-3])


# 判断是否含有博彩信息
def lottery_judge(text):
    pattern = re.compile(r'(博彩|赌场|赌博|娱乐城|AV|六合彩)')
    judge_list = pattern.findall(text.encode('utf-8'))
    judge_list = list(set(judge_list))    # URL去重
    count = len(judge_list)
    if count > 3:
        return [True, count]

    return [False, count]

def get_all_result(keyword):
    page_before = get_google_response_not_thread(keyword, 1)
    lists = page_before
    count = 2
    page_now = get_google_response_not_thread(keyword, count)
    while page_now != page_before and len(page_now) == 10:
        print "...",
        count += 1
        lists += page_now
        page_before = page_now
        page_now = get_google_response_not_thread(keyword, count)

    return lists

def judge_controller(lists, thread_name):
    global bad_url_list
    global result_list
    for page in lists:
        # 产生错误的网址不再访问
        if urlparse(page).hostname in bad_url_list:
            if ErrorInfoPost:
                print "该网站曾有超时现象，跳过"
            continue

        # 页面出错处理
        try:
            page_content = requests.get(page, timeout=10)
            page_content.raise_for_status()
        except Exception, e:
            lock.acquire()
            try:
                bad_url_list.append(urlparse(page).hostname)
            finally:
                lock.release()

            if ErrorInfoPost:
                print "页面超时或连接错误，跳过"
            continue

        # 编码问题
        if page_content.encoding == None:
            if ErrorInfoPost:
                print "无法解码，跳过"
            continue
        if page_content.encoding == 'ISO-8859-1':   # 如果没有辨认出正确编码，则设为gb
            encoding_match = re.compile(r'(gb2312|utf-8)').findall(page_content.text.encode('utf-8'))
            if encoding_match:
                page_content.encoding = encoding_match[0]
            else:
                page_content.encoding = 'gb2312'

        # 判断是否确实为博彩信息
        res = lottery_judge(page_content.text)
        if res[0]:
            lock2.acquire()
            try:
                result_list.append(page)
            finally:
                lock.release()
            print '确定有博彩信息: %d (%s)' % (res[1], page.encode('utf-8'))
        else:
            if ErrorInfoPost:
                if page_content.text == '':
                    print '误报信息: 空页面'
                else:
                    print '误报信息: %d (%s)' % (res[1], page.encode('utf-8'))



# 入口1
# @input : city - 省或市或县的名字 city_grade - 省市县分别对应1/2/3
def index(city, city_grade):
    global url_list

    get_url_controller(city, UnitPageCount[str(city_grade)])     # 第一次获取url_list
    url_list = list(set(url_list))                          # URL去重
    get_search_words('博彩')                                 # 获得二次检索关键词
    print "由第一次检索的 %d 个有效URL，得到 %d 条二次检索key_word" % (len(url_list),len(key_word_list))

    thread_arr = {}
    for key_word in key_word_list:
        lists = get_all_result(key_word)
        print "当前关键词共检索到目标网站 %d 个" % len(lists)
        print lists

        if len(lists)%10 == 0:
            time_count = len(lists)/10
        else:
            time_count = int(len(lists)/10) + 1

        for count in range(time_count):
            thread_arr[count] = threading.Thread(target=judge_controller, args=(lists[count*10:(count+1)*10], 'thread-%d' % count))
            thread_arr[count].start()

            for x in thread_arr:
                thread_arr[x].join()



index('镇江', 3)



