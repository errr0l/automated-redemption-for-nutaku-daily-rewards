import requests
# import logging
# import sys
# import os
# import json
# from common import get_config


def send_email(config, data: dict, logger=None):
    app_name = 'Automated Redemption'
    email = config.get('account', 'email')
    content = f'当前账号金币为：{data.get("user_gold")}（若要关闭邮件通知，可在config.txt中将email_notification设为off）'
    subject = f'{data.get("date")} 签到成功'
    data = {'name': app_name, 'to': email, 'content': content, 'subject': subject}
    headers = {'Content-Type': 'application/json'}
    logger.debug(f'data: {data}')
    logger.debug(f'headers: {headers}')
    base_url = 'http://errol.shenzhuo.vip:26107/easyshop/portal/'
    # base_url = 'http://127.0.0.1:8082/'
    resp = requests.post(url=f'{base_url}api/email/notification',
                         json=data, headers=headers)
    logger.debug(f'resp_text: {resp.text}')
    resp_data = resp.json()
    if resp_data.get('code') == 0:
        logger.debug("已成功发送邮件.")
    else:
        logger.debug(f"发送邮件失败->{resp_data.get('message')}")


# if __name__ == '__main__':
#     current_dir = os.path.dirname(sys.argv[0])
#     print('---> 当前目录为：' + current_dir)
#     print('---> 读取配置文件.')
#     config = get_config(current_dir + '/../')
#     logging.basicConfig()
#     logger = logging.getLogger(__name__)
#     logger.setLevel(logging.DEBUG)
#     with open('./data.json', 'r') as file:
#         data = json.load(file)
#         send_email(config, data=data, logger=logger)