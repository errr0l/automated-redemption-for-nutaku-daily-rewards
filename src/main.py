import json
import os
import datetime
import sys
import threading
import time
import logging
import requests
import configparser
import urllib.parse
from apscheduler.events import EVENT_JOB_ERROR, EVENT_ALL, EVENT_JOB_EXECUTED
from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup
from json import JSONDecodeError

err_message = '请检查网络（代理、梯子等）是否正确.'
success_message = '---> 成功.'
success_message2 = '---> 成功，'
fail_message = '---> 失败.'
fail_message2 = '---> 失败，'
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 '
      'Safari/605.1.15')
logger = logging.getLogger("Automated Redemption")
logger.setLevel(logging.INFO)


# 读取配置文件【账号&密码】
def get_config(config_dir):
    config = configparser.ConfigParser()
    config.read(config_dir + "/config.txt", encoding="utf-8")
    return config


def get_calendar_id(html):
    soup = BeautifulSoup(html, 'html.parser')
    rewards_calendar_ele = soup.find('section', {'class': 'js-rewards-calendar'})
    if rewards_calendar_ele is None:
        return None
    else:
        return rewards_calendar_ele.attrs['data-calendar-id']


# 获取网站主页
def get_nutaku_home(cookies, proxies):
    url = "https://www.nutaku.net/home/"
    cookies['isIpad'] = 'false'
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "User-Agent": UA,
        "Cookie": urllib.parse.urlencode(cookies).replace("&", ";") if cookies is not None else "",
        'Host': 'www.nutaku.net',
        'Origin': 'https://www.nutaku.net',
        'Referer': 'https://www.nutaku.net/home/'
    }
    logger.debug("headers->{}".format(headers))
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
        "User-Agent": UA,
        "Cookie": urllib.parse.urlencode(cookies).replace("&", ";")
    }
    data = "calendar_id={}".format(calendar_id)

    logger.debug("headers->{}".format(headers))
    logger.debug("data->{}".format(data))
    resp = requests.post(url, headers=headers, data=data, proxies=proxies)
    # 请求成功时，将会返回{"userGold": "1"}
    logger.debug("status_code->{}".format(resp.status_code))
    logger.debug("resp_text->{}".format(resp.text))
    status_code = resp.status_code
    if status_code == 422:
        resp_data = resp.json()
        resp_data['code'] = status_code
        return resp_data
    if status_code == 200:
        try:
            return resp.json()
        except JSONDecodeError:
            raise RuntimeError(fail_message2 + err_message)
    raise RuntimeError(fail_message2 + err_message)


def getting_rewards_handler(cookies, calendar_id, proxies, config):
    print('---> 开始签到.')
    reward_resp_data = get_rewards(cookies=cookies, calendar_id=calendar_id, proxies=proxies)
    logger.debug("resp_data->{}".format(reward_resp_data))
    if reward_resp_data['code'] == 422:
        logger.debug("->重复签到.")
        pass
    else:
        print(success_message)
        user_gold = reward_resp_data['userGold']
        print("---> 当前金币为：" + user_gold + "\n")
        data_file_path = config.get('sys', 'dir') + '/data.json'
        data = {'user_gold': user_gold, 'date': datetime.datetime.now().strftime('%Y-%m-%d'),
                'email': config.get('account', 'email')}
        with open(data_file_path, 'w') as _file:
            json.dump(data, _file)


# 如果为模式2时，签到完后，退出程序
def exit_if_necessary(config):
    is_mode_2 = config.get('settings', 'execution_mode') == '2'
    if is_mode_2:
        try:
            sys.exit()
        except SystemExit:
            logger.debug("捕获SystemExit异常.")
            print('---> 退出程序.')


# 登陆nutaku账号；
# 请求成功后，将返回的cookie存储与本地文件中，以便后续使用；
def login(config, cookies, proxies):
    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": UA,
        "X-CSRF-TOKEN": cookies['XSRF-TOKEN'],
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": "NUTAKUID={}; isIpad=false;".format(cookies['NUTAKUID']),
        'Host': 'www.nutaku.net',
        'Origin': 'https://www.nutaku.net',
        'Referer': 'https://www.nutaku.net/home/'
    }

    data = "email={}&password={}&rememberMe=1&pre_register_title_id=".format(config.get('account', 'email'),
                                                                             config.get('account', 'password'))
    logger.debug('headers->{}'.format(headers))
    logger.debug('data->{}'.format(data))
    url = 'https://www.nutaku.net/execute-login/'
    resp = requests.post(url, headers=headers, data=data, proxies=proxies)
    # 返回的是一个重定向链接，token是在cookie中
    # {"redirectURL":"https:\/\/www.nutaku.net\/home"}
    if resp.status_code == 200:
        return resp
    return RuntimeError(fail_message2 + err_message)


def logging_in_handler(config, cookies, cookie_file_path, proxies):
    print("---> 开始登陆.")
    loginResp = login(config=config, cookies=cookies, proxies=proxies)
    try:
        resp_data = loginResp.json()
        logger.debug("resp_data->{}".format(resp_data))
        if resp_data['redirectURL'] is not None:
            login_cookies = loginResp.cookies.get_dict()
            with open(cookie_file_path, 'w') as _file:
                json.dump(login_cookies, _file)
            print(success_message)
            print('---> 重新请求nutaku主页，并获取calendar_id.')
            cookies = cookies | login_cookies
            home_resp = get_nutaku_home(cookies=cookies, proxies=proxies)
            cookies = cookies | home_resp.cookies.get_dict()
            calendar_id = get_calendar_id(home_resp.text)
            if calendar_id is not None:
                print(success_message)
                getting_rewards_handler(cookies=cookies, calendar_id=calendar_id, proxies=proxies, config=config)
            else:
                raise RuntimeError(fail_message2 + err_message)
        elif resp_data['status'] == 'error':
            print('---> 账号或密码错误，请重新输入后再启动程序.')
            sys.exit()
    except JSONDecodeError:
        raise RuntimeError(fail_message2 + err_message)


def parse_execution_time(execution_time: str):
    hours, minutes = execution_time.split(":")
    return {'hours': hours, 'minutes': minutes}


def redeem(config, clearing=False):
    if clearing:
        clear(True)
    if not check(config):
        cookie_file_path = config.get('sys', 'dir') + '/cookies.json'
        # 尝试读取本地cookie文件
        local_cookies = {}
        print('---> 读取本地cookies.')
        if os.path.exists(cookie_file_path):
            with open(cookie_file_path, 'r') as file:
                jsonStr = file.read()
                if len(jsonStr) > 0:
                    _local_cookies = json.loads(jsonStr)
                    if _local_cookies['email'] != config.get('account', 'email'):
                        logger.debug("检测到账号发生变化，停止使用当前加载的cookies.")
                    else:
                        local_cookies = _local_cookies
                        print(success_message)
                else:
                    print('---> 文件内容为空.')
        else:
            print('---> 本地cookies不存在.')
        proxies = {
            'http': config.get('network', 'proxy')
        }
        print('---> 请求nutaku主页.')
        home_resp = get_nutaku_home(cookies=local_cookies, proxies=proxies)
        # 合并cookie，以使用新的XSRF-TOKEN、NUTAKUID
        merged = local_cookies | home_resp.cookies.get_dict()
        print(success_message)
        print('---> 获取calendar_id.')
        calendar_id = get_calendar_id(home_resp.text)
        # 未登陆或登陆已失效
        if calendar_id is None:
            print(fail_message)
            print('---> 尝试重新登陆账号.')
            # 登陆返回的cookie包含Nutaku_TOKEN
            logging_in_handler(config=config, cookies=merged, cookie_file_path=cookie_file_path, proxies=proxies)
        else:
            print(success_message)
            getting_rewards_handler(cookies=merged, calendar_id=calendar_id, proxies=proxies, config=config)


def listener(event, sd, conf):
    if event.code == EVENT_JOB_EXECUTED:
        if event.job_id == '001' or event.job_id == '002':
            exit_if_necessary(conf)
    elif event.code == EVENT_JOB_ERROR:
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        # 获取当前时间，加上时间间隔
        next_time = get_next_time(int(conf.get('settings', 'retrying_interval')))
        print(f'---> 将会在{next_time}进行重试.')
        # 如果已经到第二天时，不再执行
        if next_time.date() < tomorrow:
            sd.add_job(id='002', func=redeem, trigger='date', next_run_time=next_time, args=[conf],
                       misfire_grace_time=config.getint('settings', 'misfire_grace_time') * 60)
        else:
            dateFormat = '{}-{}-{}'.format(today.year, today.month, today.day)
            print('---> {}签到失败，已经逾期.'.format(dateFormat))


def get_next_time(minutes):
    next_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    return next_time


def wrapper(fn, sd, conf):
    def inner(event):
        return fn(event, sd, conf)
    return inner


def clear(tips: bool):
    os.system('cls' if os.name == 'nt' else 'clear')
    if tips:
        print('>> 按 Ctrl+{0} 退出程序...'.format('Break' if os.name == 'nt' else 'C'))
        print()


# 检查任务是否已经执行；True表示已经签到，False表示未签到
def check(config: dict, printing: bool = True):
    now = datetime.datetime.now()
    date = now.strftime('%Y-%m-%d')
    print('---> 检查中...')
    data_file_path = config.get('sys', 'dir') + '/data.json'
    if os.path.exists(data_file_path):
        with open(data_file_path, 'r') as file:
            jsonStr = file.read()
            data = json.loads(jsonStr)
    else:
        data = {'date': '-'}
    if data['date'] is None:
        raise RuntimeError('---> 数据格式错误：' + data)
    if data['date'] != date:
        if printing:
            print('---> 即将执行签到.')
        return False
    if printing:
        print('---> {}签到已完成.'.format(date))
    return True


def get_dict_params(mode):
    params = {}
    if mode == '1':
        params['hour'] = execution_time['hours']
        params['minute'] = execution_time['minutes']
        params['trigger'] = 'cron'
    else:
        params['trigger'] = 'date'
        params['next_run_time'] = get_next_time(1)
    return params


# 使用额外线程，每30分钟唤醒一次scheduler
def jobs_checker(sc):
    while True:
        logger.debug('->{} 任务检查线程休眠...'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        time.sleep(60 * 30)
        logger.debug('->{} 任务检查线程休眠；唤醒定时任务调度器...'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        sc.wakeup()


"""
todo：1、Nutaku_ageGateCheck是秒数，如果到期了，那估计还需要调用对应的接口（are you over 18 years old？）；
"""
if __name__ == '__main__':
    clear(True)
    current_dir = os.path.dirname(sys.argv[0])
    print('---> 当前目录为：' + current_dir)
    print('---> 读取配置文件.')
    config = get_config(current_dir)
    config.add_section('sys')
    config.set('sys', 'dir', current_dir)

    print(success_message)

    mode = config.get('settings', 'execution_mode')
    _debug = config.get('settings', 'debug')
    if _debug == 'on':
        logging.basicConfig()
        logging.getLogger('apscheduler').setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    scheduler = BlockingScheduler()
    execution_time = parse_execution_time(config.get('settings', 'execution_time'))
    scheduler.add_listener(wrapper(listener, scheduler, config), EVENT_ALL)

    scheduler.add_job(id='001', func=redeem, **get_dict_params(mode),
                      args=[config, True], misfire_grace_time=config.getint('settings', 'misfire_grace_time') * 60)

    try:
        if mode == '1':
            jobs_checker_thread = threading.Thread(target=jobs_checker, args=(scheduler,))
            jobs_checker_thread.start()

        scheduler.start()
    except (KeyboardInterrupt, SystemExit) as e:
        logger.debug("捕获异常->{}".format(str(e)))
        print('---> 退出程序.')
