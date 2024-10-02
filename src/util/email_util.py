import datetime

import requests
import logging
import sys
import os
import json
from src.util.common import get_config, get_month_days


def send_email(config, data: dict, logger=None):
    app_name = 'Automated Redemption'
    email = config.get('account', 'email')
    # content = f'当前账号金币为：{data.get("user_gold")}（若要关闭邮件通知，可在config.txt中将email_notification设为off）'
    content = f'{data.get("content")}（若要关闭邮件通知，可在config.txt中将email_notification设为off）'
    subject = f'{data.get("date")} 签到成功'
    _data = {'name': app_name, 'to': email, 'content': content, 'subject': subject}
    headers = {'Content-Type': 'application/json'}
    logger.debug(f'data: {_data}')
    logger.debug(f'headers: {headers}')
    # 超时不管【日常大姨妈】
    timeout = config.get('settings', 'connection_timeout')
    try:
        resp = requests.post(url=f'{config.get("api", "email_notification")}',
                             json=_data, headers=headers, timeout=int(timeout))

        logger.debug(f'resp_text: {resp.text}')
        if resp.status_code == 200:
            resp_data = resp.json()
            if resp_data.get('code') == 0:
                logger.debug("已成功发送邮件.")
                return 1
            else:
                logger.debug(f"发送邮件失败->{resp_data.get('message')}")
                return 2
        else:
            logger.debug(f"发送邮件失败")
            return 2
    except Exception as e:
        logger.debug(f"发送邮件失败，捕获异常->{e}")
        return 2


# def set_email_by_strategy(config, local_data, logger, destination):
#     if config.get('settings', 'email_notification') == 'on':
#         strategy = config.get('settings', 'email_notification_strategy')
#         now = datetime.datetime.now()
#         _date = local_data.get("emailed", '')
#         _map = {'day': 1, 'week': 7}
#         interval = _map.get(strategy)
#         if destination:
#             local_data['content'] = '本月签到已全部完成，' + local_data.get('content').replace('本月', '')
#         r = False
#         if _date == '':
#             # r = send_email(config, local_data, logger)
#             print(1)
#         else:
#             _date = [int(item) for item in _date.split("-")]
#             # 年份不同暂不考虑；
#             # 如果月份不同，则间隔算法为：上月总天数-上月最后的签到日期+当月天数；如果月份相同，则为：当天-_date[2]
#             if _date[1] != now.month:
#                 last_month_days = get_month_days(_date[1], _date[0])
#                 if interval >= (last_month_days - _date[2] + now.day):
#                     # r = send_email(config, local_data, logger)
#                     print(2)
#             elif now.day - interval >= _date[2]:
#                 # r = send_email(config, local_data, logger)
#                 print(3)
#         if r:
#             local_data['emailed'] = now.strftime('%Y-%m-%d')


if __name__ == '__main__':
    current_dir = os.path.dirname(sys.argv[0])
    print('---> 当前目录为：' + current_dir)
    print('---> 读取配置文件.')

    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    config = get_config(current_dir + '/../', logger=logger)
    with open('../data.json', 'r') as file:
        data = json.load(file)
        send_email(config, data=data, logger=logger)
        # set_email_by_strategy(config, data, logger, True)
    # last_month_days = get_month_days(9, 2024)
    # print(last_month_days)
    # _date = [2024, 9, 28]
    # interval = 1
    # print(last_month_days - _date[2] + datetime.datetime.now().day)
    # if (last_month_days - _date[2] + datetime.datetime.now().day) >= interval:
    #     print(1)
    # else:
    #     print(2)
