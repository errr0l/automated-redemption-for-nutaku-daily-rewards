import datetime
import json
import logging
import os
import sys
import threading
import time
import urllib.parse
from json import JSONDecodeError

import requests
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup

from util.common import get_config, parse_execution_time, exit_if_necessary, load_data, clear, \
    kill_process, get_separator, get_month_days
from util.email_util import send_email
from util.user_agent_util import get_random_ua

err_message = '请检查网络（代理、梯子等）是否正确.'
success_message = '---> 成功.'
success_message2 = '---> 成功，'
fail_message = '---> 失败.'
fail_message2 = '---> 失败，'
UA = None
logger = logging.getLogger("Automated Redemption")
logger.setLevel(logging.INFO)
separator = get_separator()
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_html_for_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    _rewards_calendar = soup.find('section', {'class': 'js-rewards-calendar'})

    _meta = soup.find('meta', {'name': 'csrf-token'})
    # 表示是否已经全部签到完成（无可再签）
    calendar_id = _rewards_calendar.attrs['data-calendar-id'] if _rewards_calendar is not None else None
    future_reward = soup.find('div', {'class': 'reward-status-future'})
    _d = {
        'csrf_token': _meta.attrs['content'],
        'calendar_id': calendar_id,
        'destination': False,
        'gold': 0, 'url': ''
    }
    if calendar_id is not None:
        # 有可能是金币或优惠卷
        reward = _rewards_calendar.find('div', class_='reward-status-current-not-claimed')
        if future_reward is None:
            _d['destination'] = reward is None
        if _d['destination'] is False:
            if reward is None:
                reward = future_reward.find_previous_sibling('div')
            _d['url'] = reward.attrs['data-link']
            reward_text = reward.div.span.text
            if 'Gold' in reward_text:
                _d['gold'] = reward_text.replace("Gold", "").strip()
        _rewards_list = soup.find('div', {'class': 'reward-list'})
        _text_rewards = _rewards_list.find_all('span', {'class': 'text-reward'})
        total = 0
        for item in _text_rewards:
            if 'Gold' in item.text:
                total += int(item.text.replace("Gold", "").strip())
        _d['total_gold'] = total
    return _d


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
    resp = requests.get(url, headers=headers, proxies=proxies, timeout=int(timeout), verify=False)
    if resp.status_code == 200:
        return resp
    raise RuntimeError(fail_message2 + err_message)


# 签到获取金币
def get_rewards(cookies, html_data, proxies, config):
    _cookie = "NUTAKUID={}; Nutaku_TOKEN={}; isIpad=false"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-CSRF-TOKEN": html_data.get("csrf_token"),
        "User-Agent": UA,
        "Cookie": _cookie,
        'Origin': 'https://www.nutaku.net',
        'Referer': 'https://www.nutaku.net/home/',
        "X-Requested-With": "XMLHttpRequest",
        'Host': 'www.nutaku.net'
    }

    data = "calendarId={}".format(html_data.get('calendar_id'))

    logger.debug("data->{}".format(data))
    logger.debug("headers->{}".format(headers))
    timeout = config.get('settings', 'connection_timeout')
    headers['Cookie'] = _cookie.format(cookies.get("NUTAKUID"), cookies.get("Nutaku_TOKEN"))
    resp = requests.post(html_data.get('url'), headers=headers, data=data, proxies=proxies, timeout=int(timeout),
                         verify=False)
    logger.info("status_code->{}".format(resp.status_code))
    logger.info("resp_text->{}".format(resp.text))
    status_code = resp.status_code
    if status_code == 200:
        try:
            return resp.json()
        except JSONDecodeError:
            raise RuntimeError(fail_message2 + err_message)
    raise RuntimeError(fail_message2 + err_message)


# 签到获取的物件，除了金币以外，还有优惠卷
def reward_resp_data_handler(resp_data: dict, data: dict):
    item = resp_data.get('userGold')
    _content = "当前签到物件为未知物件"
    if item is not None:
        # 获取本月金币
        month = data.get('month')
        monthly_amount = data.get(month)
        data[month] = (data.get('current_gold') + int(monthly_amount)) if monthly_amount is not None else data.get(
            'current_gold')
        print(f"---> 当前金币：{item}，本月累计领取：{data[month]}/{data.get(f'{month}_total')}\n")
        _content = f"当前账号金币：{item}，本月累计领取：{data[month]}/{data.get(f'{month}_total')}"
        data['user_gold'] = item
    elif resp_data.get('coupon') is not None:
        item = resp_data.get('coupon')
        _content = "获取到优惠卷：{}/{}".format(item.get('title'), item.get('code'))
        print("---> " + _content + "\n")
    else:
        print("---> " + _content + "\n")
    data['content'] = _content


def record(config, data):
    data_file_path = config.get('sys', 'dir') + separator + 'data.json'
    # 创建文件
    if os.path.exists(data_file_path) is False:
        with open(data_file_path, 'w'):
            pass

    with open(data_file_path, 'r+') as _file:
        json_str = _file.read()
        is_not_empty = len(json_str) > 0
        # merged = (json.loads(json_str) if is_not_empty else {}) | data
        merged = {**(json.loads(json_str) if is_not_empty else {}), **data}
        # 清空文件内容，再重新写入
        if is_not_empty:
            _file.seek(0)
            _file.truncate()
        json.dump(merged, _file)


def getting_rewards_handler(cookies, proxies, config, html_data, local_data):
    print('---> 开始签到.')
    reward_resp_data = get_rewards(cookies=cookies, html_data=html_data, proxies=proxies, config=config)
    logger.info("resp_data->{}".format(reward_resp_data))
    status_code = reward_resp_data.get('code')

    now = datetime.datetime.now()
    _date = now.strftime("%Y-%m")
    data = {
        'date': now.strftime('%Y-%m-%d'),
        'email': config.get('account', 'email'),
        'utc_date': datetime.datetime.utcnow().strftime('%Y-%m-%d'),
        'month': _date,
        'limit_str': local_data.get('limit').strftime(DATE_FORMAT),
        'current_gold': int(html_data.get('gold')),
        _date: local_data.get(_date), f'{_date}_total': html_data.get("total_gold")
    }
    if status_code is not None and status_code == 422:
        logger.info("结果->重复签到或其他（多为前者）.")
        print('---> {} 已经签到.'.format(data.get('date')))
        return
    else:
        print(success_message)
        reward_resp_data_handler(reward_resp_data, data)
    emailed = set_email_by_strategy(config, local_data, logger, False)
    if emailed is not None:
        data['emailed'] = emailed
    record(config, data)


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

    data = "email={}&password={}&rememberMe=1&pre_register_title_id="
    logger.debug('headers->{}'.format(headers))
    logger.debug('data->{}'.format(data))
    url = 'https://www.nutaku.net/execute-login/'
    timeout = config.get('settings', 'connection_timeout')
    resp = requests.post(url, headers=headers,
                         data=data.format(config.get('account', 'email'), config.get('account', 'password')),
                         proxies=proxies, timeout=int(timeout), verify=False)
    # 返回的是一个重定向链接，token是在cookie中
    # {"redirectURL":"https:\/\/www.nutaku.net\/home"}
    if resp.status_code == 200:
        return resp
    return RuntimeError(fail_message2 + err_message)


def logging_in_handler(config, cookies, cookie_file_path, proxies, html_data, local_data):
    login_resp = login(config=config, cookies=cookies, proxies=proxies, csrf_token=html_data.get("csrf_token"))
    try:
        resp_data = login_resp.json()
        logger.info("resp_data->{}".format(resp_data))
        if resp_data['redirectURL'] is not None:
            login_cookies = login_resp.cookies.get_dict()
            with open(cookie_file_path, 'w') as _file:
                json.dump(login_cookies, _file)
            print(success_message)
            print('---> 重新请求nutaku主页，并获取calendar_id.')
            cookies = {**cookies, **login_cookies}
            home_resp = get_nutaku_home(cookies=cookies, proxies=proxies, config=config)
            cookies = {**cookies, **home_resp.cookies.get_dict()}
            html_data = parse_html_for_data(home_resp.text)
            logger.info("html_data->{}".format(html_data))
            if html_data.get("destination"):
                destination_handler(local_data)
                return
            if html_data.get("calendar_id") is not None:
                print(success_message)
                getting_rewards_handler(cookies=cookies, html_data=html_data, proxies=proxies, config=config,
                                        local_data=local_data)
            else:
                raise RuntimeError(fail_message2 + err_message)
        elif resp_data['status'] == 'error':
            logger.info("签到出现异常.")
            print('---> 账号或密码错误，请重新输入后再启动程序.')
            kill_process()
    except JSONDecodeError:
        logger.info("登陆失败，未知原因.")
        raise RuntimeError(fail_message2 + err_message)


# 默认情况下，全部签到完成后，会发一次邮件（如果近期内未通知时）；
def set_email_by_strategy(config, local_data, logger, destination):
    if config.get('settings', 'email_notification') == 'on':
        strategy = config.get('settings', 'email_notification_strategy')
        now = datetime.datetime.now()
        _date = local_data.get("emailed", '')
        _map = {'day': 1, 'week': 7}
        interval = _map.get(strategy)
        if destination:
            local_data['content'] = '本月签到已全部完成，' + local_data.get('content').replace('本月', '')
        r = False
        if _date == '':
            r = send_email(config, local_data, logger)
        else:
            _date = [int(item) for item in _date.split("-")]
            # 年份不同暂不考虑；
            # 如果月份不同，则间隔算法为：上月总天数-上月最后的签到日期+当月天数；如果月份相同，则为：当天-_date[2]
            if _date[1] != now.month:
                last_month_days = get_month_days(_date[1], _date[0])
                if (last_month_days - _date[2] + now.day) >= interval:
                    r = send_email(config, local_data, logger)
            elif now.day - _date[2] >= interval:
                r = send_email(config, local_data, logger)
        if r:
            return now.strftime('%Y-%m-%d')


def destination_handler(local_data):
    print("恭喜，已经全部签到完成.")
    emailed = set_email_by_strategy(config, local_data, logger, True)
    if emailed is not None:
        record(config, {'emailed': emailed})
    kill_process()


def redeem(config, clearing=False, local_data: dict = None, reloading=False):
    # 重新加载数据
    if reloading:
        local_data = load_data(config, logger)
    set_limit_time(local_data)
    if clearing:
        clear(True)
    if not check(True, local_data):
        global UA
        UA = get_random_ua()
        cookie_file_path = config.get('sys', 'dir') + separator + 'cookies.json'
        local_cookies = {}
        print('---> 读取本地cookie.')
        if os.path.exists(cookie_file_path):
            with open(cookie_file_path, 'r') as file:
                json_str = file.read()
                if len(json_str) > 0:
                    _local_cookies = json.loads(json_str)
                    _email = local_data.get('email')
                    logger.info("记录的账号->{}".format(_email))
                    if _email is not None:
                        if _email == config.get('account', 'email'):
                            local_cookies = _local_cookies
                            print(success_message)
                        else:
                            print('---> 检测到账号发生变化，停止使用当前加载的cookie.')
                    else:
                        print('---> 记录的账号为空，停止使用当前加载的cookie.')
                else:
                    print('---> 文件内容为空.')
        else:
            print('---> 本地cookie不存在.')

        proxies = {}
        if config.get('network', 'proxy') == 'off':
            # 可以这样设置是因为，当前所有的接口都是该域名下的
            proxies['no_proxy'] = 'nutaku.net'
            logger.info("绕过代理->{}".format(proxies))
        # 默认情况下，请求时会自动应用代理
        else:
            logger.info("启用代理（系统代理）")
        print('---> 请求nutaku主页.')
        home_resp = get_nutaku_home(cookies=local_cookies, proxies=proxies, config=config)
        # 合并cookie，以使用新的XSRF-TOKEN、NUTAKUID
        # merged = local_cookies | home_resp.cookies.get_dict()
        merged = {**local_cookies, **home_resp.cookies.get_dict()}
        print(success_message)
        print('---> 获取calendar_id与csrf_token.')
        html_data = parse_html_for_data(home_resp.text)
        logger.debug("html_data->{}".format(html_data))
        if html_data.get("destination"):
            destination_handler(local_data)
            return
        # 未登陆或登陆已失效
        if html_data.get('calendar_id') is None:
            print(fail_message2 + '未登陆或登陆过期')
            if local_cookies.get('Nutaku_TOKEN') is not None:
                print('---> 尝试重新登陆账号.')
            else:
                print('---> 登陆账号.')
            # 登陆返回的cookie包含Nutaku_TOKEN
            logging_in_handler(config=config, cookies=merged, cookie_file_path=cookie_file_path,
                               proxies=proxies, html_data=html_data, local_data=local_data)
        else:
            print(success_message)
            getting_rewards_handler(cookies=merged, html_data=html_data, proxies=proxies, config=config,
                                    local_data=local_data)


def listener(event, sd, conf):
    if event.code == EVENT_JOB_EXECUTED:
        logger.info("任务执行完成.")
        if event.job_id == '001' or event.job_id == '002':
            exit_if_necessary(conf, logger)
    elif event.code == EVENT_JOB_ERROR:
        today = datetime.datetime.today()
        local_data = load_data(conf, logger)
        limit_str = local_data.get('limit_str')
        # 限制时间是第二天的早上8点，因此，一般情况下limit和today不在同一天；而如果处于同一天时，说明limit还没更新（比如没有请求n站成功就进入了重试逻辑）
        limit = datetime.datetime.strptime(limit_str, DATE_FORMAT) if limit_str is not None else today
        # 获取当前时间，加上时间间隔
        next_time = get_next_time(int(conf.get('settings', 'retrying_interval')))
        logger.info("当前时间：{}".format(today))
        logger.info("截止日期：{}".format(limit))
        matched = today.day == limit.day if limit is not None else False
        is_job_001 = event.job_id == '001'
        if is_job_001:
            set_retrying_copying(conf, conf.get('settings', 'retrying'))
        if matched:
            logger.info("截止日期未更新")
        _retrying = int(conf.get('settings', '_retrying'))
        if _retrying > 1:
            _retrying -= 1
            set_retrying_copying(conf, str(_retrying))
            if limit is None or next_time < limit or matched:
                print(f'---> 请求失败，将会在{next_time}进行重试.')
                # 如果是001时，删除002任务，以免出现冲突，即如果id=001的任务出现错误时，还在等待中的id=002的任务将会被清除
                if is_job_001:
                    job = sd.get_job('002')
                    if job is not None:
                        sd.remove_job('002')
                sd.add_job(id='002', func=redeem, trigger='date', next_run_time=next_time,
                           args=[conf, False, local_data],
                           misfire_grace_time=conf.getint('settings', 'misfire_grace_time') * 60)
            else:
                date_format = '{}-{}-{}'.format(today.year, today.month, today.day)
                print('---> {} 签到失败.'.format(date_format))
                exit_if_necessary(conf, logger)
        else:
            print('---> 已到达最大重试次数，将停止签到；如本日签到还未完成时，请手动签到.')
            exit_if_necessary(conf, logger)


def get_next_time(minutes):
    next_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    return next_time


# 设置签到截止日期
def set_limit_time(local_data: dict):
    today = datetime.datetime.today()
    # 获取第二天早上8点0分0秒的时间，即utc+0的00:00:00，若当前时间已经超过该时间点，将不再执行
    # limit是相对于today_000的时间
    today_000 = today.replace(hour=0, minute=0, second=0)
    limit = today_000 + datetime.timedelta(days=1, hours=8)
    _limit = local_data.get("limit")
    if _limit != limit:
        local_data['limit'] = limit


def wrapper(fn, sd, conf):
    def inner(event):
        return fn(event, sd, conf)

    return inner


# 检查任务是否已经执行；True表示已经签到，False表示未签到
def check(printing: bool = True, local_data: dict = None):
    now = datetime.datetime.utcnow()
    current_utc = now.strftime('%Y-%m-%d')
    print('---> 检查中...')
    utc_date = local_data.get('utc_date')
    if utc_date is None or utc_date != current_utc:
        if printing:
            print('---> 即将执行签到.')
        return False
    if printing:
        print('---> {} 签到已完成.'.format(local_data.get('date')))
    return True


def get_dict_params(mode, execution_time):
    params = {}
    if mode == '1':
        params['hour'] = execution_time['hours']
        params['minute'] = execution_time['minutes']
        params['trigger'] = 'cron'
    else:
        params['trigger'] = 'date'
        params['next_run_time'] = get_next_time(1)
    return params


# 使用额外线程，每隔段时间唤醒scheduler
def jobs_checker(sc):
    while True:
        logger.info('->{} 任务检查线程休眠...'.format(datetime.datetime.now().strftime(DATE_FORMAT)))
        time.sleep(60 * 60)
        logger.info('->{} 任务检查线程休眠；唤醒定时任务调度器...'.format(datetime.datetime.now().strftime(DATE_FORMAT)))
        sc.wakeup()


def set_retrying_copying(conf, value):
    conf.set('settings', '_retrying', value)


if __name__ == '__main__':
    clear(True)
    current_dir = os.path.dirname(sys.argv[0])
    print('---> 当前目录为：' + current_dir)
    print('---> 读取配置文件.')
    config = get_config(current_dir, logger)
    config.add_section('sys')
    config.set('sys', 'dir', current_dir)
    set_retrying_copying(config, config.get('settings', 'retrying'))
    print(success_message)
    mode = config.get('settings', 'execution_mode')
    logging.basicConfig(filename='app.log', format='%(asctime)s - %(levelname)s - %(message)s')
    if config.get('settings', 'debug') == 'on':
        logging.getLogger('apscheduler').setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    scheduler = BlockingScheduler(option={'logger': logger})
    execution_time = parse_execution_time(config.get('settings', 'execution_time'))

    scheduler.add_listener(wrapper(listener, scheduler, config), (EVENT_JOB_EXECUTED | EVENT_JOB_ERROR))
    scheduler.add_job(id='001', func=redeem, **get_dict_params(mode, execution_time),
                      args=[config, True, None, True],
                      misfire_grace_time=config.getint('settings', 'misfire_grace_time') * 60)
    try:
        if mode == '1':
            jobs_checker_thread = threading.Thread(target=jobs_checker, args=(scheduler,))
            jobs_checker_thread.setDaemon(True)
            jobs_checker_thread.start()
        scheduler.start()
    except:
        print('---> 退出程序.')
        scheduler.shutdown()
