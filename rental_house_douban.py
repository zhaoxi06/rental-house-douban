# coding:utf-8
import requests,json,time
import smtplib
from email.mime.text import MIMEText
import random
import sys
reload(sys)
sys.setdefaultencoding('utf8')


# nohup stdbuf -oL python group_api_topics.py &
mailto_list = ['aaa@163.com', 'bbb@163.com']
mail_host = "smtp.qq.com"
mail_user = "123456789@qq.com"
mail_pass = "fkjdhgkgahg"
mail_postfix = "qq.com"

sended_dict = {}
px_pool = []

# 发送邮件到指定邮箱，其中mailuser 为发送邮件邮箱账号， mailto_list 为接收邮件账户列表
def send_mail(to_list, sub, content):
    me = "Server Monitor" + "<" + mail_user + "@" + mail_postfix + ">"
    msg = MIMEText(content, _subtype='html', _charset='utf-8')
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = ";".join(to_list)
    msg["Accept-Language"]="zh-CN"
    msg["Accept-Charset"]="utf-8"
    try:
        server = smtplib.SMTP_SSL()
        server.connect(mail_host)
        server.login(mail_user, mail_pass)
        server.sendmail(me, to_list, msg.as_string())
        server.close()
        return True
    except Exception, e:
        print str(e)
        return False

# 由于豆瓣api限制，每小时只能发送100个请求，此函数为程序加载不同Https代理，每次请求随机选择不同的https代理
def load_proxy_pool():
    for l in open('./proxy_pool','r').readlines():
        px = l.split('\n')[0].split('\t')
        px_pool.append('https://{}:{}'.format(px[0],px[1]))
    print px_pool



#此函数发送 get 请求， params为请求参数，指定从何处开始，每次请求要求返回多少条消息
#返回消息为json格式，具体属性名称及格式参考 https://www.douban.com/group/topic/33507002/

def get_topic_list(groupids= ['tianhezufang']):

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/52.0.2743.116 Safari/537.36'}
    params = {'start': 0, 'count': 500}
    print '-------------------'
    topics = []
    for id in groupids:
        flag = True
        r = None
        while flag:
            proxies = {'https': random.choice(px_pool)}
            print 'groupid: {}, proxy:{}'.format(id, proxies)
            try:
                requests.adapters.DEFAULT_RETRIES = 5 # 增加重连次数
                s = requests.session()
                s.keep_alive = False # 关闭多余连接
                r = requests.get('https://api.douban.com/v2/group/{}/topics'.format(id),
                                 headers = headers,
                                #  proxies = proxies,
                                 params = params)
                if r.status_code == 200:
                    flag = False
                else:
                    print ('Bad proxy:', proxies)
            except Exception, e:
                print ('Error proxy:', proxies)
                print str(e)

        data = json.loads(r.text)
        print data['topics'][0]['updated']
        print data['topics'][-1]['updated']
        topics.extend(data['topics'])
    print '-------------------'
    print 'Save json files'
    json_obj = {"data": topics}
    save_json_file(json_obj)
    return topics

# 过滤掉帖子中包含这些关键字的topic
def exclude_words(topic):
    ex_words = ['求租']
    for word in ex_words:
        if word.decode('utf-8') in topic['title']:
            return False
        elif word.decode('utf-8') in topic['content']:
            return False
    return True

# 搜索topic内容中是否包含 指定关键字的topic
def content_search(topic, key_words = []):
    flag = False
    for k in key_words:
        if k.decode('utf-8') in topic['title']:
            flag = exclude_words(topic)
        elif k.decode('utf-8') in topic['content']:
            flag = exclude_words(topic)
    if flag==True:
        return { 'title': topic['title'], 'url': topic['share_url']}
    else:
        return
# 遍历所有在topics 中的topic， 找到含有关键词列表keywords 的所有topic 并返回
def related_houses(topics, keywords = []):
    houses = []
    for topic in topics:
        filter_house = content_search(topic, keywords)
        if filter_house is not None:
            url = filter_house['url']
        # if url is not None:
            houses.append(filter_house)
    return houses

# 此函数为检测相同的topic是否已发送过， 如果发送过则不发送， 没有发送过则发送并在发送过的字典中添加该topic
def house_filter(houses):
    filterd_hs = []
    for h in houses:
        if not sended_dict.has_key(h['url']):
            sended_dict[h['url']] = ''
            c = '''<p><a href="{my_url}">{my_title}</a></p>'''.format(my_url=h['url'][0:-1], my_title=h['title'])
            filterd_hs.append(c)
            sended_urls = open('./sended_urls', 'w')
            sended_urls.write(str(sended_dict.keys()))
            sended_urls.flush()
            sended_urls.close()
    return filterd_hs

# 此函数为加载是否历史发送过的topic 列表，初始时为空， 每次发送都重新写入
def recovery_sendedurls():
    content = open('./sended_urls', 'r').readline()
    print len(content.strip())
    if len(content.strip())>0:
        strs = eval(content)
        if strs is not None :
            for i in strs:
                sended_dict[i] = ''
    # print sended_dict.keys()

# 此函数为监控的主函数，每隔gap秒对小组列表内的小组发送一次请求，
# 如果返回结果中不含有满足要求topic， 即len(f_houses)=0 则不发送邮件
# 如果含有满足要求的topic 则发送邮件
def topic_monitor(gap = 600, keywords = [], groupids = []):
    while True:
        topics = get_topic_list(groupids = groupids)
        houses = related_houses(topics, keywords)
        f_houses = house_filter(houses)
        if len(f_houses)>0:
            save_results(f_houses)
            f_houses = ''.join(f_houses)
            send_mail(mailto_list, 'For your information, House!', str(f_houses))
            print 'send over'
        time.sleep(gap)

def save_json_file(objs):
    f = open('./results.json','w')
    json.dump(objs, f)
    f.close()

# 将爬取的帖子用html文件保存到results文件夹中
def save_results(houses):
    FILETIMEFORMAT = '%Y%m%d_%X'
    file_time = time.strftime(FILETIMEFORMAT, time.localtime()).replace(':', '')
    result_file_name = 'results/result_' + str(file_time)
    new_result = open(result_file_name + '.html', 'w')
    # with file:
    new_result.write('''<html>
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
        <title>广州租房信息 | 豆瓣</title>
        <link rel="stylesheet" type="text/css" href="../lib/resultPage.css">
        </head>
        <body>''')
    new_result.write('<h1>Guangzhou Renting Information</h1>')

    for h in houses:
        new_result.write(h)

    new_result.write('</body></html>')
    new_result.close()


if __name__ == '__main__':
    # 搜索包含以下关键字的帖子
    keywords = ['岗顶']
    # 
    groupids = ['tianhezufang', 'IloveGZ', 'gz020', 'huangpuzufang', '537239', '341554', 'maquezufang', 'zunar_gz', '637323', '588555']
    # groupids = ['fangzi','beijingzufang', 'opking', '279962','sweethome','zhufang','26926']
    recovery_sendedurls()
    load_proxy_pool()
    topic_monitor(keywords=keywords, groupids = groupids)

    # tianhezufang 广州天河租房（个人房源免费推广）
    ## 576562 广州天河租房【无中介费】
    # 537239 广州免费租房大合集
    # maquezufang 【广州租房】无中介服务站- 找朋友
    ## 584892 广州租房-无中介真实房源
    # zunar_gz  广州租房族（爱分享，易租房）
    # IloveGZ 广州租房（好评度★★★★★）
    # gz020 广州租房★（个人房源免费推广）
    # huangpuzufang 广州3号线+5号线+APM地铁沿线租房
    ## 341554 广州租房信息大全（★★★★★
    ## 514593 广州租房-平安好房
    ## 574643 咚咚广州租房
    ## 514594 广州租房-真房实客网
    ## 589105 广州 租房 （豆瓣优选★★★★★）
    ## 510962 广州租房-无中介真实房源
    ## 637323 广州租房@天河租房
    ## 588555 广州地铁3号线租房