import json
import os
import datetime
import sys
import threading
import time
import logging
import requests
import urllib.parse
from apscheduler.events import EVENT_JOB_ERROR, EVENT_ALL, EVENT_JOB_EXECUTED
from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup
from json import JSONDecodeError
from util.email_util import send_email
from util.common import get_config, parse_execution_time, exit_if_necessary, load_data, clear

err_message = '请检查网络（代理、梯子等）是否正确.'
success_message = '---> 成功.'
success_message2 = '---> 成功，'
fail_message = '---> 失败.'
fail_message2 = '---> 失败，'
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
# UA = ('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36')
logger = logging.getLogger("Automated Redemption")
logger.setLevel(logging.INFO)


def parse_html_for_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    rewards_calendar_ele = soup.find('section', {'class': 'js-rewards-calendar'})

    meta_ele = soup.find('meta', {'name': 'csrf-token'})
    return {
        'csrf_token': meta_ele.attrs['content'],
        'calendar_id': rewards_calendar_ele.attrs['data-calendar-id'] if rewards_calendar_ele is not None else None
    }


# 获取网站主页
def get_nutaku_home(cookies, proxies, config):
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
    timeout = config.get('settings', 'connection_timeout')
    resp = requests.get(url, headers=headers, proxies=proxies, timeout=int(timeout))
    if resp.status_code == 200:
        return resp
    raise RuntimeError(fail_message2 + err_message)


# 签到获取金币
def get_rewards(cookies, html_data, proxies, config):
    url = 'https://www.nutaku.net/rewards-calendar/redeem/'
    headers = {
        "Accept": "application/json, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "x-csrf-token": html_data.get("csrf_token"),
        "User-Agent": UA,
        "Cookie": "NUTAKUID={}; Nutaku_TOKEN={}".format(cookies.get("NUTAKUID"), cookies.get("Nutaku_TOKEN")),
        'Origin': 'https://www.nutaku.net',
        'Referer': 'https://www.nutaku.net/home/'
    }
    data = "calendarId={}".format(html_data.get('calendar_id'))

    logger.debug("headers->{}".format(headers))
    logger.debug("data->{}".format(data))
    timeout = config.get('settings', 'connection_timeout')
    resp = requests.post(url, headers=headers, data=data, proxies=proxies, timeout=int(timeout))
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


def getting_rewards_handler(cookies, proxies, config, html_data):
    print('---> 开始签到.')
    reward_resp_data = get_rewards(cookies=cookies, html_data=html_data, proxies=proxies, config=config)
    logger.debug("resp_data->{}".format(reward_resp_data))
    status_code = reward_resp_data.get('code')

    data_file_path = config.get('sys', 'dir') + '/data.json'
    data = {'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'email': config.get('account', 'email')}
    if status_code is not None and status_code == 422:
        logger.debug("result->重复签到.")
        print('---> {} 已经签到.'.format(data.get('date')))
    else:
        print(success_message)
        user_gold = reward_resp_data['userGold']
        print("---> 当前金币为：" + user_gold + "\n")
        data['user_gold'] = user_gold
        # 邮箱通知
        if config.get('settings', 'email_notification') == 'on':
            send_email(config=config, data=data, logger=logger)

    if os.path.exists(data_file_path):
        with open(data_file_path, 'r+') as _file:
            json_str = _file.read()
            merged = (json.loads(json_str) if len(json_str) > 0 else {}) | data
            _file.seek(0)
            json.dump(merged, _file)
    else:
        with open(data_file_path, 'w') as _file:
            json.dump(data, _file)


# 登陆nutaku账号；
# 请求成功后，将返回的cookie存储与本地文件中，以便后续使用；
def login(config, cookies, proxies, csrf_token):
    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": UA,
        "X-Csrf-Token": csrf_token,
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
    timeout = config.get('settings', 'connection_timeout')
    resp = requests.post(url, headers=headers, data=data, proxies=proxies, timeout=int(timeout))
    # 返回的是一个重定向链接，token是在cookie中
    # {"redirectURL":"https:\/\/www.nutaku.net\/home"}
    if resp.status_code == 200:
        return resp
    return RuntimeError(fail_message2 + err_message)


def logging_in_handler(config, cookies, cookie_file_path, proxies, html_data):
    loginResp = login(config=config, cookies=cookies, proxies=proxies, csrf_token=html_data.get("csrf_token"))
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
            home_resp = get_nutaku_home(cookies=cookies, proxies=proxies, config=config)
            cookies = cookies | home_resp.cookies.get_dict()
            html_data = parse_html_for_data(home_resp.text)
            logger.debug("html_data->{}".format(html_data))
            if html_data.get("calendar_id") is not None:
                print(success_message)
                getting_rewards_handler(cookies=cookies, html_data=html_data, proxies=proxies, config=config)
            else:
                raise RuntimeError(fail_message2 + err_message)
        elif resp_data['status'] == 'error':
            print('---> 账号或密码错误，请重新输入后再启动程序.')
            sys.exit()
    except JSONDecodeError:
        logger.debug("登陆失败，未知原因.")
        raise RuntimeError(fail_message2 + err_message)


def redeem(config, clearing=False, local_data=None):
    if clearing:
        clear(True)
    if not check(config, True, local_data):
        cookie_file_path = config.get('sys', 'dir') + '/cookies.json'
        # 尝试读取本地cookie文件
        local_cookies = {}
        print('---> 读取本地cookie.')
        if os.path.exists(cookie_file_path):
            with open(cookie_file_path, 'r') as file:
                json_str = file.read()
                if len(json_str) > 0:
                    _local_cookies = json.loads(json_str)
                    _email = local_data.get('email')
                    if _email is not None:
                        if _email == config.get('account', 'email'):
                            local_cookies = _local_cookies
                            print(success_message)
                        else:
                            logger.debug("检测到账号发生变化，停止使用当前加载的cookie.")
                    else:
                        logger.debug("data文件邮件为空，停止使用当前加载的cookie.")
                else:
                    print('---> 文件内容为空.')
        else:
            print('---> 本地cookie不存在.')
        proxies = {
            'http': config.get('network', 'proxy')
        }
        print('---> 请求nutaku主页.')
        home_resp = get_nutaku_home(cookies=local_cookies, proxies=proxies, config=config)
        # 合并cookie，以使用新的XSRF-TOKEN、NUTAKUID
        merged = local_cookies | home_resp.cookies.get_dict()
        print(success_message)
        print('---> 获取calendar_id与csrf_token.')
        html_data = parse_html_for_data(home_resp.text)
        # 未登陆或登陆已失效
        if html_data.get('calendar_id') is None:
            print(fail_message2 + '未登陆或登陆过期')
            if local_cookies.get('Nutaku_TOKEN') is not None:
                print('---> 尝试重新登陆账号.')
            else:
                print('---> 登陆账号.')
            # 登陆返回的cookie包含Nutaku_TOKEN
            logging_in_handler(config=config, cookies=merged, cookie_file_path=cookie_file_path,
                               proxies=proxies, html_data=html_data)
        else:
            print(success_message)
            getting_rewards_handler(cookies=merged, html_data=html_data, proxies=proxies, config=config)


def listener(event, sd, conf, local_data):
    if event.code == EVENT_JOB_EXECUTED:
        logger.debug("任务执行完成.")
        if event.job_id == '001' or event.job_id == '002':
            exit_if_necessary(conf, logger)
    elif event.code == EVENT_JOB_ERROR:
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        # 获取当前时间，加上时间间隔
        next_time = get_next_time(int(conf.get('settings', 'retrying_interval')))
        retrying = int(conf.get('settings', 'retrying'))
        if retrying > 1:
            retrying -= 1
            conf.set('settings', 'retrying', str(retrying))
            print(f'---> 将会在{next_time}进行重试.')
            # 如果已经到第二天时，不再执行
            if next_time.date() < tomorrow:
                sd.add_job(id='002', func=redeem, trigger='date', next_run_time=next_time,
                           args=[conf, False, local_data],
                           misfire_grace_time=config.getint('settings', 'misfire_grace_time') * 60)
            else:
                dateFormat = '{}-{}-{}'.format(today.year, today.month, today.day)
                print('---> {}签到失败，已经逾期.'.format(dateFormat))
        else:
            print('---> 已到达最大重试次数，将退出程序.')
            sys.exit()


def get_next_time(minutes):
    next_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    return next_time


def wrapper(fn, sd, conf, local_data):
    def inner(event):
        return fn(event, sd, conf, local_data)

    return inner


# 检查任务是否已经执行；True表示已经签到，False表示未签到
def check(config: dict, printing: bool = True, local_data: dict = None):
    now = datetime.datetime.now()
    date = now.strftime('%Y-%m-%d')
    print('---> 检查中...')
    _date = local_data.get('date')
    if _date is None or _date != date:
        if printing:
            print('---> 即将执行签到.')
        return False
    if printing:
        print('---> {} 签到已完成.'.format(date))
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
        time.sleep(60 * 39)
        logger.debug(
            '->{} 任务检查线程休眠；唤醒定时任务调度器...'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
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

    logger.debug("->加载本地数据.")
    local_data = load_data(config)
    logger.debug("->{}".format(local_data))

    scheduler = BlockingScheduler()
    execution_time = parse_execution_time(config.get('settings', 'execution_time'))

    scheduler.add_listener(wrapper(listener, scheduler, config, local_data), EVENT_ALL)
    scheduler.add_job(id='001', func=redeem, **get_dict_params(mode),
                      args=[config, True, local_data],
                      misfire_grace_time=config.getint('settings', 'misfire_grace_time') * 60)

    try:
        if mode == '1':
            jobs_checker_thread = threading.Thread(target=jobs_checker, args=(scheduler,))
            jobs_checker_thread.start()
        scheduler.start()
    except BaseException as e:
        logger.debug(f"捕获异常->{e}")
        print('---> 退出程序.')
