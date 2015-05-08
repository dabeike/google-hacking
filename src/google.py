#encoding:utf-8

import requests
import json
import re
from urlparse import urlparse

'''
参考资料：http://blog.163.com/lixiangqiu_9202/blog/static/5357503720142841142897/
调用接口：http://brisk.eu.org/api/google.php
接口Get参数：q 必选 查询的关键字,n 可选 页数
返回值：Json数组
'''
# 设定查询URL的页数（省级城市查询前十页，市级查询前5页，县级查询前两页）
UnitPageCount = {"1": 15, "2": 10, "3": 5}
# 默认不显示错误信息
ErrorInfoPost = False

# google搜索发包高级封装
# @input : keyword - 搜索关键字, page - 页码
# @output: google返回的包，list格式
# @错误处理 : 十秒没有数据返回时，返回空list
def get_google_response(keyword, page,  url='http://brisk.eu.org/api/google.php'):
    data = {"q": keyword, "n": page}
    try:
        response = requests.get(url, params=data, timeout=10)
        temp = json.loads(response.text)
    except Exception, e:
        print "google信息获取失败"
        print data
        return []

    return temp


# 处理google返回的数据包，返回URL或URL-host
# @input : list_arr - google数据list parse - 是否解析URL
# @output: parse=True 返回host，否则返回url
def url_parse(list_arr, parse=True):
    url_list = []
    for x in list_arr:
        if parse:
            url_list.append(urlparse(x["url"]).hostname)
        else:
            url_list.append(x["url"])

    return url_list


# 获取后缀为 gov.cn的域名
# @input :  keyword 检索关键词,grade  当前检索的等级（省=1 市=2 县=3）
# @output:  url_list 得到的URL list
def get_url(keyword, grade):
    url_list = []

    print "正在查询 %s 的政府网站：" % keyword,
    for x in range(1, UnitPageCount[grade]+1):  # 按页发起查询
        print '.',
        url_list += url_parse(get_google_response("%s site:gov.cn" % keyword, x))

    url_list = list(set(url_list))    # URL去重
    print "\n查询了前 %d 页，共得到 %d 个有效URL" % (UnitPageCount[grade], len(url_list))

    return url_list


# 获取第二次检索keyword
# @input : keyword - 检索关键字，如博彩，url_list - 需要二次检索的url列表
# @output: keyword_list - 二次检索的直接关键词，若有多个返回list
def get_search_words(keyword, url_list):
    keyword_list = []
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
        keyword_list.append(keyword_str[:-3])

    return keyword_list


# 判断是否含有博彩信息
def lottery_judge(text):
    pattern = re.compile(r'(博彩|赌场|赌博|娱乐城|AV|六合彩)')
    judge_list = pattern.findall(text.encode('utf-8'))
    judge_list = list(set(judge_list))    # URL去重
    count = len(judge_list)
    if count > 3:
        return [True, count]

    return [False, count]


# 入口1
# @input : city - 省或市或县的名字 city_grade - 省市县分别对应1/2/3
def index(city, city_grade):
    bad_url = []    # 超时的页面信息记录
    page_count = 1
    search_words = get_search_words('博彩', get_url(city, str(city_grade)))       # 获得二次搜索的索引内容组

    for search_word in search_words:
        print "检索关键词 %s" % search_word
        page_count = 1

        final_res = url_parse(get_google_response(search_word, str(page_count)), False)     # 获得当前搜索组的第一页
        while len(final_res):
            print "在检索结果第 %d 页找到 %d 个结果，解析中..." % (page_count, len(final_res))
            for page in final_res:
                if urlparse(page).hostname in bad_url:      # 产生错误的网址不再访问
                    if ErrorInfoPost:
                        print "该网站曾有超时现象，跳过"
                    continue

                try:                                         # 页面出错处理
                    page_content = requests.get(page, timeout=10)
                    page_content.raise_for_status()
                except Exception, e:
                    if ErrorInfoPost:
                        bad_url.append(urlparse(page).hostname)
                        print "页面超时或连接错误，跳过 %s" % page.encode('utf-8')
                    continue

                if page_content.encoding == None:
                    if ErrorInfoPost:
                        print "无法解码，跳过"
                    continue

                if page_content.encoding == 'ISO-8859-1':   # 如果没有辨认出正确编码，则设为gb
                    encoding_match = re.compile(r'(gb2312|utf-8)',re.I).findall(page_content.text.encode('utf-8'))
                    if encoding_match:
                        page_content.encoding = encoding_match[0]
                    else:
                        page_content.encoding = 'gb2312'

                res = lottery_judge(page_content.text)
                if res[0]:
                    print '确定有博彩信息: %d (%s)' % (res[1], page.encode('utf-8'))
                else:
                    if page_content.text == '':
                        if ErrorInfoPost:
                            print '误报信息: 空页面 %s' % page.encode('utf-8')
                    else:
                        print '误报信息: %d (%s)' % (res[1], page.encode('utf-8'))

            # 在page页码数大于总页数，会返回最后一页。所以要检测当前页面是否为最后一页。
            page_count += 1
            temp_res = url_parse(get_google_response(search_word, str(page_count)), False)
            if temp_res == final_res or len(final_res) != 10:
                break

            final_res = temp_res


# 入口函数二,输入省全自动化扫描
# @input : city 省的名字 （比如山东省、北京市）
def index_2(city):
    china = json.load(file('china.json'))
    for x in china:
        if x['region']['name'].encode('utf-8') == city:    # 找到省
            index(x['region']['name'].encode('utf-8'), 1)
            for y in x['region']['state']:
                # print y['name']     # 找到市
                index(y['name'].encode('utf-8'), 2)
                for z in y['city']:
                    # print z['name']     # 找到区县
                    index(z['name'].encode('utf-8'), 3)


# index_2('辽宁省')
index('辽宁',1)