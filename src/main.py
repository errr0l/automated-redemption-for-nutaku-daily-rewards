import datetime
import json
import logging
import math
import os
import sys
import threading
import time
import signal
import urllib.parse
import urllib3
from json import JSONDecodeError

import requests
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup

from util.common import get_config, parse_execution_time, exit_if_necessary, load_data, clear, \
    kill_process, get_separator, get_month_days
from util.email_util import send_email
from util.user_agent_util import get_random_ua

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

messages = ["成功.", "失败.", "请检查网络（代理、梯子等）是否正确", "成功, ", "失败, "]
logger = logging.getLogger("Automated Redemption")
separator = get_separator()
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def build_headers(type, cookies):
    headers = {
        'User-Agent': get_random_ua(),
        'Accept': 'application/json, */*',
        'Referer': 'https://www.nutaku.net/games/project-qt/',
        'Host': 'www.nutaku.net',
        'Origin': 'https://www.nutaku.net',
        "Cookie": urllib.parse.urlencode(cookies).replace("&", ";") if cookies is not None else ""
    }

    # ajax请求
    if type == 1:
        headers['Content-Type'] = "application/x-www-form-urlencoded; charset=UTF-8"
    return headers


# 获取签到数据
def get_rewards_calendar(cookies, html_data):
    logger.info("获取签到数据.")
    url = "https://www.nutaku.net/rewards-calendar-details/"
    headers = build_headers(0, cookies)
    resp = requests.get(url, headers=headers)
    logger.debug("headers: {}".format(headers))
    if resp.text.startswith("<!DOCTYPE"):
        logger.info(messages[1])
        return None
    else:
        try:
            resp_data = resp.json()
            # 如果当前签到奖励不是金币的话，current_gold为0
            logger.debug("resp_data: {}".format(resp_data))
            current_gold = 0
            total_gold = 0
            if resp_data.get('id') is None:
                logger.info(messages[1])
                return None
            for item in resp_data["rewards"]:
                if item['benefitType'] == 'gold':
                    gold = int(item['slotTitle'].replace("Gold", "").strip())
                    total_gold += gold
                    # 当日没签到时为current-not-claimed，签到后为current-claimed
                    if item['status'] == 'current-not-claimed' and current_gold == 0:
                        current_gold = gold
            html_data['destination'] = resp_data['areAllRewardClaimed']
            html_data['gold'] = current_gold
            html_data['total_gold'] = total_gold
            html_data['calendar_id'] = resp_data.get('id')
            html_data['is_reward_claimed'] = resp_data['isRewardClaimed']
            return 1
        except JSONDecodeError:
            logger.error(messages[1])


# [2025-8-20]网站改版
def parse_html_for_data(html):
    logger.info("解析html页面.")
    soup = BeautifulSoup(html, 'html.parser')
    _meta = soup.find('meta', {'name': 'csrf-token'})
    _d = {
        'csrf_token': _meta.attrs['content'],
        'url': 'https://www.nutaku.net/rewards-calendar/rewards-calendar/redeem/'
    }
    logger.info("{}".format(_d))
    return _d


# 获取网站主页
def get_nutaku_home(cookies, proxies, config):
    logger.info("获取n站主页.")
    url = "https://www.nutaku.net/home/"
    cookies['isIpad'] = 'false'
    headers = build_headers(0, cookies)
    logger.debug("headers->{}".format(headers))
    timeout = config.get('settings', 'connection_timeout')
    resp = requests.get(url, headers=headers, proxies=proxies, timeout=int(timeout), verify=False)
    if resp.status_code == 200:
        return resp
    logger.info(messages[1])


# 签到获取金币
def get_rewards(cookies, html_data, proxies, config):
    logger.info("请求签到接口.")
    _cookie = "NUTAKUID={}; Nutaku_TOKEN={}; isIpad=false"
    headers = build_headers(1, cookies)
    headers['X-CSRF-TOKEN'] = html_data.get("csrf_token")
    data = "calendarId={}".format(html_data.get('calendar_id'))
    logger.debug("data->{}".format(data))
    logger.debug("headers->{}".format(headers))
    timeout = config.get('settings', 'connection_timeout')
    resp = requests.post(html_data.get('url'), headers=headers, data=data, proxies=proxies, timeout=int(timeout),
                         verify=False)
    logger.debug("status_code->{}".format(resp.status_code))
    logger.debug("resp_text->{}".format(resp.text))
    status_code = resp.status_code
    if status_code == 200:
        try:
            return resp.json()
        except JSONDecodeError:
            logger.info(messages[1])


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
        print(f"当前金币：{item}，本月累计领取：{data[month]}/{data.get(f'{month}_total')}\n")
        _content = f"当前账号金币：{item}，本月累计领取：{data[month]}/{data.get(f'{month}_total')}"
        data['user_gold'] = item
    elif resp_data.get('coupon') is not None:
        item = resp_data.get('coupon')
        _content = "获取到优惠卷：{}/{}".format(item.get('title'), item.get('code'))
        print(_content)
    else:
        print(_content)
    data['content'] = _content


def record(config, data):
    logger.info("保存数据至data.json")
    data_file_path = config.get('sys', 'dir') + separator + 'data.json'
    logger.info("路径: {}".format(data_file_path))
    # 创建文件
    if os.path.exists(data_file_path) is False:
        with open(data_file_path, 'w'):
            pass
    with open(data_file_path, 'r+') as _file:
        json_str = _file.read()
        is_not_empty = len(json_str) > 0
        merged = {**(json.loads(json_str) if is_not_empty else {}), **data}
        logger.debug("data: {}".format(merged))
        # 清空文件内容，再重新写入
        if is_not_empty:
            _file.seek(0)
            _file.truncate()
        json.dump(merged, _file)


def getting_rewards_handler(cookies, proxies, config, html_data, local_data):
    print("开始签到...")
    reward_resp_data = get_rewards(cookies=cookies, html_data=html_data, proxies=proxies, config=config)
    logger.debug("resp_data->{}".format(reward_resp_data))

    now = datetime.datetime.now()
    _date = now.strftime("%Y-%m")
    data = {
        'date': now.strftime('%Y-%m-%d'),
        'email': config.get('account', 'email'),
        'utc_date': datetime.datetime.utcnow().strftime('%Y-%m-%d'),
        'month': _date,
        'limit_str': local_data.get('limit').strftime(DATE_FORMAT),
        'current_gold': html_data.get('gold'),
        _date: local_data.get(_date), f'{_date}_total': html_data.get("total_gold")
    }
    if reward_resp_data is None:
        logger.info("重复签到或签到失败(多为前者).")
        return
    reward_resp_data_handler(reward_resp_data, data)
    emailed = set_email_by_strategy(config, {**local_data, **data}, logger, False)
    if emailed is not None:
        data['emailed'] = emailed
    record(config, data)


# 登陆nutaku账号；
# 请求成功后，将返回的cookie存储与本地文件中，以便后续使用；
def login(config, cookies, proxies, csrf_token):
    logger.info("请求登录接口.")
    headers = build_headers(1, None)
    headers['X-Csrf-Token'] = csrf_token
    headers["Cookie"] = "NUTAKUID={}; isIpad=false;".format(cookies['NUTAKUID'])

    data = "email={}&password={}&rememberMe=1&pre_register_title_id="
    logger.debug('headers->{}'.format(headers))
    logger.debug('data->{}'.format(data))
    url = 'https://www.nutaku.net/execute-login/'
    timeout = config.get('settings', 'connection_timeout')
    resp = requests.post(url, headers=headers,
                         data=data.format(config.get('account', 'email'), config.get('account', 'password')),
                         proxies=proxies, timeout=int(timeout), verify=False)
    # 返回的是一个重定向链接，token是在cookie中
    logger.debug("resp_text->{}".format(resp.text))
    if resp.status_code == 200:
        try:
            resp_data = resp.json()
            success = resp_data.get("success")
            if success is not None and success == "success":
                return resp.cookies.get_dict()
            logger.info(messages[1])
        except JSONDecodeError:
            logger.info(messages[1])


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
        r = 0
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
        if r == 1:
            _time = now.strftime('%Y-%m-%d')
            print('邮件通知已发送.')
            return _time
        elif r == 2:
            print('邮件通知发送失败，详细信息请查看日志.')


def destination_handler(local_data, config):
    print("恭喜，本月已经全部签到完成.")
    emailed = set_email_by_strategy(config, local_data, logger, True)
    month = local_data.get('month')
    _map = {f'{month}_destination': 1}
    if emailed is not None:
        _map['emailed'] = emailed
    # kill_process()
    record(config, _map)


def redeem(config, clearing=False, local_data: dict = None, reloading=False):
    # 重新加载数据
    if reloading:
        local_data = load_data(config, logger)
    set_limit_time(local_data)
    if clearing:
        clear(True)
    local_email = local_data.get('email')
    config_email = config.get('account', 'email')
    email_matched = True
    if local_email is not None and local_email != config_email:
        logger.info('检测到账号发生变化: {}/{}，停止使用本地数据(cookie和用户数据).'.format(config_email, local_email))
        local_data.clear()
        email_matched = False
    if not check(True, local_data, email_matched):
        local_cookies = {}
        cookie_file_path = config.get('sys', 'dir') + separator + 'cookies.json'
        # 邮箱相同时, 使用本地cookie
        if email_matched:
            logger.info("读取本地cookie.")
            if os.path.exists(cookie_file_path):
                with open(cookie_file_path, 'r') as file:
                    json_str = file.read()
                    if len(json_str) > 0:
                        local_cookies = json.loads(json_str)
                    else:
                        logger.info('cookie文件内容为空.')
            else:
                logger.info('本地cookie不存在.')
        proxies = {}
        if config.get('network', 'proxy') == 'off':
            # 可以这样设置是因为，当前所有的接口都是该域名下的
            proxies['no_proxy'] = 'nutaku.net'
            logger.info("绕过代理->{}".format(proxies))
        # 默认情况下，请求时会自动应用代理
        else:
            logger.info("启用代理(系统代理).")
        home_resp = get_nutaku_home(cookies=local_cookies, proxies=proxies, config=config)
        # 合并cookie，以使用新的XSRF-TOKEN、NUTAKUID
        merged = {**local_cookies, **home_resp.cookies.get_dict()}
        html_data = parse_html_for_data(home_resp.text)
        print("拉取签到数据...")
        result = get_rewards_calendar(cookies=merged, html_data=html_data)
        # 未登陆或登陆已失效
        if result is None:
            print('失败, 未登陆或登陆过期.')
            if local_cookies.get('Nutaku_TOKEN') is not None:
                print('尝试重新登陆...')
            else:
                print('登陆...')
            # 登陆返回的cookie包含Nutaku_TOKEN
            login_cookies = login(config=config, cookies=merged, proxies=proxies, csrf_token=html_data.get("csrf_token"))
            if login_cookies is not None:
                logger.debug("login_resp_data->{}".format(login_cookies))
                with open(cookie_file_path, 'w') as _file:
                    json.dump(login_cookies, _file)
            else:
                print("失败，账号&密码错误或" + messages[2] + ", 之后重新运行程序.")
                kill_process()
                return
            merged = {**merged, **login_cookies}
            result = get_rewards_calendar(cookies=merged, html_data=html_data)
            if result is None:
                print("拉取签到数据...")
                raise RuntimeError(messages[2])
        logger.debug("html_data->{}".format(html_data))
        if html_data.get("destination"):
            destination_handler(local_data, config)
            return
        if html_data['is_reward_claimed']:
            print("今日已签到.")
            return
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
            logger.info("截止日期未更新.")
        _retrying = int(conf.get('settings', '_retrying'))
        if _retrying > 0:
            _retrying -= 1
            set_retrying_copying(conf, str(_retrying))
            if limit is None or next_time < limit or not matched:
                print(f'请求失败，将会在{next_time}进行重试.')
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
                print('{} 签到失败.'.format(date_format))
                exit_if_necessary(conf, logger)
        else:
            print('已到达最大重试次数，如本日签到还未完成时，还请手动签到.')
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


def wrapper(fn, p1, p2):
    def inner(event):
        return fn(event, p1, p2)
    return inner


# 检查任务是否需要执行；1）账号，2）日期
# True表示已经签到，False表示未签到
def check(printing: bool = True, local_data: dict = None, email_matched: bool = False):
    if not email_matched:
        if printing:
            logger.info('即将执行签到.')
        return False
    now = datetime.datetime.utcnow()
    current_utc = now.strftime('%Y-%m-%d')
    month = current_utc[:7]
    if local_data.get(f'{month}_destination') is not None:
        msg = '{} 已全部签到完成.'.format(month)
        print(msg)
        logger.info(msg)
        return True
    logger.info('检查中...')
    utc_date = local_data.get('utc_date')
    if utc_date is None or utc_date != current_utc:
        if printing:
            logger.info('即将执行签到.')
        return False
    if printing:
        msg = '{} 已签到完成.'.format(local_data.get('date'))
        logger.info(msg)
        print(msg)
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
def jobs_checker(sc, check_interval):
    while True:
        print_next_run_time(sc.get_job(job_id="001"))
        logger.info('[{}] 任务检查线程休眠...'.format(datetime.datetime.now().strftime(DATE_FORMAT)))
        time.sleep(60 * check_interval)
        logger.info('[{}] 任务检查线程休眠；唤醒定时任务调度器...'.format(datetime.datetime.now().strftime(DATE_FORMAT)))
        sc.wakeup()


def print_next_run_time(job):
    now = datetime.datetime.now()
    if hasattr(job, 'next_run_time'):
        print(f"预计执行时间：{job.next_run_time} (in {math.ceil(job.next_run_time.timestamp() - now.timestamp())}s)")
    elif hasattr(job, 'trigger'):
        fields = job.trigger.fields
        hours = str(fields[5])
        minutes = str(fields[6])
        _minutes = minutes.split(',')
        for i, item in enumerate(hours.split(',')):
            _hour = int(item)
            if _hour < now.hour:
                continue
            # 计算执行时间
            _timedelta = datetime.timedelta(
                hours=_hour - now.hour,
                minutes=(int(_minutes[0]) if len(_minutes) == 1 else int(_minutes[i])) - now.minute)

            print(f"预计执行时间：{now + _timedelta} (in {_timedelta.seconds}s)")
            break


def set_retrying_copying(conf, value):
    conf.set('settings', '_retrying', value)


def shutdown_handler(signum, frame):
    sys.exit(0)


def main():
    clear(True)
    current_dir = os.path.dirname(sys.argv[0])
    print('当前目录为：' + current_dir)
    print('读取配置文件...')
    config = get_config(current_dir, logger)
    config.add_section('sys')
    config.set('sys', 'dir', current_dir)
    set_retrying_copying(config, config.get('settings', 'retrying'))
    print(messages[0])
    mode = config.get('settings', 'execution_mode')
    log_output = config.get("log", 'output')
    log_level = int(config.get("log", 'level'))
    if log_output == "file":
        logging.basicConfig(filename=f'{current_dir}/app.log', format='%(asctime)s - %(levelname)s - %(message)s')
    elif log_output == 'console':
        logging.basicConfig( format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.setLevel(level=log_level)
    scheduler = BlockingScheduler(option={'logger': logger})
    execution_time = parse_execution_time(config.get('settings', 'execution_time'))

    scheduler.add_listener(wrapper(listener, scheduler, config), (EVENT_JOB_EXECUTED | EVENT_JOB_ERROR))
    scheduler.add_job(id='001', func=redeem, **get_dict_params(mode, execution_time),
                      args=[config, True, None, True],
                      misfire_grace_time=config.getint('settings', 'misfire_grace_time') * 60)
    if mode == '1':
        jobs_checker_thread = threading.Thread(target=jobs_checker,
                                               args=(scheduler, int(config.get("settings", "check_interval"))))
        jobs_checker_thread.setDaemon(True)
        jobs_checker_thread.start()
    else:
        print_next_run_time(scheduler.get_job(job_id="001"))
    signal.signal(signal.SIGINT, shutdown_handler)
    scheduler.start()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error("An unexpected error occurred", exc_info=True)
        sys.exit(1)
