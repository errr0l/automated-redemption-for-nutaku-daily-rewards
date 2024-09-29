import datetime
import re
# import json
# import os
# import threading
# import time
# # from ..main import redeem
#
#
# def p(event):
#     while not event.is_set():
#         print(1)
#         time.sleep(5)
#     print('over')
#
#
# def reward_resp_data_handler(resp_data: dict, data: dict):
#     item = resp_data.get('userGold')
#     _content = "当前签到物件为未知物件"
#     if item is not None:
#         # 获取本月金币
#         month = data.get('month')
#         monthly_amount = data.get(month)
#         print("monthly_amount")
#         print(monthly_amount)
#         data[month] = (data.get('current_gold') + int(monthly_amount)) if monthly_amount is not None else data.get('current_gold')
#         print(f"---> 当前金币为：{item}，本月累计金币为：{data[month]}\n")
#         _content = f'当前账号金币为：{item}，本月累计金币为：{data[month]}'
#         data['user_gold'] = item
#     data['content'] = _content
#
#
# def getting_rewards_handler():
#     print('---> 开始签到.')
#     # reward_resp_data = get_rewards(cookies=cookies, html_data=html_data, proxies=proxies, config=config)
#     # logger.debug("resp_data->{}".format(reward_resp_data))
#     # status_code = reward_resp_data.get('code')
#
#     # data_file_path = config.get('sys', 'dir') + separator + 'data.json.backup'
#     _date = datetime.datetime.today().strftime("%Y-%m")
#     data = {'date': '2024-09-08', 'email': 'err0l@qq.com', 'month': '2024-09', 'current_gold': 10, _date: '111'}
#     reward_resp_data = {
#         "userGold": "5",
#     }
#     reward_resp_data_handler(reward_resp_data, data)
#
#     # 创建文件
#     data_file_path = "./data.json.backup"
#
#     if os.path.exists(data_file_path) is False:
#         with open(data_file_path, 'w'):
#             pass
#
#     with open(data_file_path, 'r+') as _file:
#         json_str = _file.read()
#         is_not_empty = len(json_str) > 0
#         # merged = (json.loads(json_str) if is_not_empty else {}) | data
#         merged = {**(json.loads(json_str) if is_not_empty else {}), **data}
#         print(merged)
#         # 清空文件内容，再重新写入
#         if is_not_empty:
#             _file.seek(0)
#             _file.truncate()
#         json.dump(merged, _file)
#
#
# def redeem_test():
#     pass
#
#
import threading

if __name__ == '__main__':
    now = datetime.datetime.now()
    print(now.day)
    print(now.weekday())
    print(now.strftime("%Y-%m-%d"))
    print(now.strftime("%Y-%m"))
    d1 = "2024-9-12"
    r = re.findall("-(\\d+)$", d1)
    print(r)
    event = threading.Event()
    print(event.is_set())
    event.set()
    print(event.is_set())
#     getting_rewards_handler()
#     # stop_event = threading.Event()
#     # jobs_checker_thread = None
#     # try:
#     #     jobs_checker_thread = threading.Thread(target=p, args=(stop_event,))
#     #     jobs_checker_thread.start()
#     #     time.sleep(60)
#     # except (Exception, KeyboardInterrupt) as e:
#     #     print(e)
#     #     stop_event.set()
#     #     if jobs_checker_thread is not None:
#     #         jobs_checker_thread.join()
#     #     print('---> 退出程序.')
#
