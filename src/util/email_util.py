import requests
import logging
import sys
import os
import json
from src.util.common import get_config


def send_email(config, data: dict, logger=None):
    app_name = 'Automated Redemption'
    email = config.get('account', 'email')
    # content = f'当前账号金币为：{data.get("user_gold")}（若要关闭邮件通知，可在config.txt中将email_notification设为off）'
    content = f'{data.get("content")}（若要关闭邮件通知，可在config.txt中将email_notification设为off）'
    subject = f'{data.get("date")} 签到成功'
    data = {'name': app_name, 'to': email, 'content': content, 'subject': subject}
    headers = {'Content-Type': 'application/json'}
    logger.debug(f'data: {data}')
    logger.debug(f'headers: {headers}')
    # 超时不管【日常大姨妈】
    timeout = config.get('settings', 'connection_timeout')
    try:
        resp = requests.post(url=f'{config.get("api", "email_notification")}',
                             json=data, headers=headers, timeout=int(timeout))

        logger.debug(f'resp_text: {resp.text}')
        if resp.status_code == 200:
            resp_data = resp.json()
            if resp_data.get('code') == 0:
                logger.debug("已成功发送邮件.")
            else:
                logger.debug(f"发送邮件失败->{resp_data.get('message')}")
        else:
            logger.debug(f"发送邮件失败")
    except Exception as e:
        logger.debug(f"发送邮件失败，捕获异常->{e}")


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
