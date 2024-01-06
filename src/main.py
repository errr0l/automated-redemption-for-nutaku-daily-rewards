import json
import os
import datetime
import sys
from json import JSONDecodeError

import requests
import configparser
import urllib.parse

from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup

err_message = '请检查网络（代理、梯子等）是否正确.'
success_message = '---> 成功.'
success_message2 = '---> 成功，'
fail_message = '---> 失败.'
fail_message2 = '---> 失败，'


# 读取配置文件【账号&密码】
def get_config(config_dir):
    config = configparser.ConfigParser()
    config.read(config_dir + "/../config.txt", encoding="utf-8")
    return config


def get_calendar_id(html):
    soup = BeautifulSoup(html, 'html.parser')
    rewards_calendar_ele = soup.find('section', {'class': 'js-rewards-calendar'})
    if rewards_calendar_ele is None:
        return None
    else:
        return rewards_calendar_ele.attrs['data-calendar-id']


def get_nutaku_home(cookies, proxies):
    url = "https://www.nutaku.net/home/"
    cookies['isIpad'] = 'false'
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        "Cookie": urllib.parse.urlencode(cookies).replace("&", ";") if cookies is not None else "",
        'Host': 'www.nutaku.net',
        'Origin': 'https://www.nutaku.net',
        'Referer': 'https://www.nutaku.net/home/'
    }

    # print('---> headers: ' + str(headers))

    resp = requests.get(url, headers=headers, proxies=proxies)
    if resp.status_code == 200:
        return resp
    raise RuntimeError(fail_message2 + err_message)


# 签到获取金币
def get_rewards(cookies, calendar_id, proxies):
    url = 'https://www.nutaku.net/rewards-calendar/redeem/'
    cookies['isIpad'] = 'false'
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "x-csrf-token": cookies.get("XSRF-TOKEN"),
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        "Cookie": urllib.parse.urlencode(cookies).replace("&", ";")
    }
    data = "calendar_id={}".format(calendar_id)
    # print('---> headers: ' + str(headers))
    # print('---> data：' + data)
    resp = requests.post(url, headers=headers, data=data, proxies=proxies)
    # 请求成功时，将会返回{"userGold": "1"}
    if resp.status_code == 200:
        try:
            return resp.json()
        except JSONDecodeError:
            raise RuntimeError(fail_message2 + err_message)
    raise RuntimeError(fail_message2 + err_message)


def getting_rewards_handler(cookies, calendar_id, proxies):
    print('---> 开始签到.')
    reward_resp_data = get_rewards(cookies=cookies, calendar_id=calendar_id, proxies=proxies)
    print(success_message)
    print("---> 当前金币为：" + reward_resp_data['userGold'] + "\n")


# 登陆nutaku账号；
# 请求成功后，将返回的cookie存储与本地文件中，以便后续使用；
def login(config, cookies, proxies):
    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        "X-CSRF-TOKEN": cookies['XSRF-TOKEN'],
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": "NUTAKUID={}; isIpad=false;".format(cookies['NUTAKUID']),
        'Host': 'www.nutaku.net',
        'Origin': 'https://www.nutaku.net',
        'Referer': 'https://www.nutaku.net/home/'
    }

    data = "email={}&password={}&rememberMe=1&pre_register_title_id=".format(config.get('account', 'email'),
                                                                             config.get('account', 'password'))

    # print('---> headers: ' + str(headers))
    # print('---> data：' + data)

    url = 'https://www.nutaku.net/execute-login/'
    resp = requests.post(url, headers=headers, data=data, proxies=proxies)
    # 返回的是一个重定向链接，token是在cookie中
    # {"redirectURL":"https:\/\/www.nutaku.net\/home"}
    if resp.status_code == 200:
        return resp
    return RuntimeError(fail_message2 + err_message)


def logging_in_handler(config, cookies, cookie_file_path, proxies):
    print("---> 开始登陆.")
    loginResp = login(config=config, cookies=cookies)
    try:
        respData = loginResp.json()
        if respData['redirectURL'] is not None:
            login_cookies = loginResp.cookies.get_dict()
            with open(cookie_file_path, 'w') as file:
                json.dump(login_cookies, file)
            print(success_message)
            print('<--- 重新获取nutaku主页，并获取calendar_id.')
            home_resp = get_nutaku_home(cookies=cookies, proxies=proxies)
            cookies = cookies | login_cookies | home_resp.cookies.get_dict()
            calendar_id = get_calendar_id(home_resp.text)
            if calendar_id is not None:
                print(success_message)
                getting_rewards_handler(cookies=cookies, calendar_id=calendar_id, proxies=proxies)
            else:
                raise RuntimeError(fail_message2 + err_message)
        elif respData['status'] == 'error':
            print('---> 账号或密码错误，请重新输入后再启动程序.')
            sys.exit()

    except JSONDecodeError:
        raise RuntimeError(fail_message2 + err_message)


def redeem():
    currentDir = os.getcwd()
    cookie_file_path = currentDir + '/../cookies.json'
    # 尝试读取本地cookie文件
    local_cookies = {}
    print('---> 读取配置文件.')
    config = get_config(currentDir)
    proxies = {
        'http': config['proxy']
    }
    print(success_message)
    print('---> 读取本地cookies.')
    if os.path.exists(cookie_file_path):
        with open(cookie_file_path, 'r') as file:
            jsonStr = file.read()
            if len(jsonStr) > 0:
                local_cookies = json.loads(jsonStr)
                print(success_message)
            else:
                print('---> 文件内容为空.')
    else:
        print('---> 本地cookies不存在.')
    print('---> 请求nutaku主页.')
    home_resp = get_nutaku_home(cookies=local_cookies, proxies=proxies)
    # 合并cookie，以使用新的XSRF-TOKEN、NUTAKUID
    merged = local_cookies | home_resp.cookies.get_dict()
    print(success_message)
    print('---> 获取calendar_id.')
    calendar_id = get_calendar_id(home_resp.text)
    # 未登陆或登陆已失效
    if calendar_id is None:
        # 需要用到XSRF-TOKEN、NUTAKUID
        print(fail_message)
        print('---> 尝试重新登陆账号.')
        # 登陆返回的cookie包含Nutaku_TOKEN
        logging_in_handler(config=config, cookies=merged, cookie_file_path=cookie_file_path, proxies=proxies)
    else:
        print(success_message)
        getting_rewards_handler(cookies=merged, calendar_id=calendar_id, proxies=proxies)


def listener(event, sd):
    print(f'Job {event.job_id} raised {event.exception.__class__.__name__}')
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    # 获取当前时间，加上1小时后的时间
    next_time = datetime.datetime.now() + datetime.timedelta(hours=1)
    # 如果已经到第二天时，不再执行
    if next_time < tomorrow:
        sd.add_job(id='002', func=redeem, trigger='date', next_run_time=next_time)
    else:
        dateFormat = '{}/{}/{}'.format(today.year, today.month, today.day)
        print('---> {}签到失败，已经逾期.'.format(dateFormat))

def wrapper(fn, sd):
    def inner(event):
        return fn(event, sd)
    return inner


if __name__ == '__main__':
    # todo：程序开始前，应该先检查今天是否已经执行了；可以根据定时任务的时间，如果时间没到时，可以不执行，如果已经过了，就需要检查；
    scheduler = BlockingScheduler()
    # 每天9：30执行
    scheduler.add_job(id='001', func=redeem, trigger='cron', hour=9, minute=30)
    scheduler.add_listener(wrapper(listener, scheduler), EVENT_JOB_ERROR)
    print('按 Ctrl+{0} 退出程序'.format('Break' if os.name == 'nt' else 'C'))
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
