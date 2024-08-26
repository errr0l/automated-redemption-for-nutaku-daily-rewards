
import os
import platform
import shutil
import sys
import datetime

from bs4 import BeautifulSoup


# def parse_html_for_data(html):
#     soup = BeautifulSoup(html, 'html.parser')
#     rewards_calendar_ele = soup.find('section', {'class': 'js-rewards-calendar'})
#
#     meta_ele = soup.find('meta', {'name': 'csrf-token'})
#     # 表示是否已经全部签到完成（无可再签）
#     calendar_id = rewards_calendar_ele.attrs['data-calendar-id'] if rewards_calendar_ele is not None else None
#     # current_reward = soup.find('div', {'class': 'reward-status-current-not-claimed'})
#     # reward-status-current-claimed
#     future_reward = soup.find('div', {'class': 'reward-status-future'})
#     # 有可能是金币或优惠卷
#     reward = soup.find('div', class_='reward-status-current-not-claimed')
#     print('1')
#     print(reward)
#     if reward is None:
#         reward = future_reward.find_previous_sibling('div')
#         print('2')
#         print(reward)
#     reward = reward.div.span.text
#
#     return {
#         'csrf_token': meta_ele.attrs['content'],
#         'calendar_id': calendar_id,
#         'destination': calendar_id is not None and future_reward is None and soup.find('div', {'class': 'reward-status-current-not-claimed'}) is None,
#         'gold': reward.replace("Gold", "").strip() if 'Gold' in reward else 0,
#     }


if __name__ == '__main__':
    # with open('../home.html') as _f:
    #     _home = _f.read()
    #     r = parse_html_for_data(_home)
    #     print(r)
    # _system = platform.system()
    # current_dir = os.getcwd()
    # config_path = '\src\config.txt' if _platform == 'Windows' else '/src/config.txt'

    # _split = "\\" if _system == 'Windows' else '/'
    # path = ['', 'src', 'config.txt']
    # output_path = ['dist', 'config.txt']

    # shutil.copyfile(_split.join(paths), '{0}{1}{2}'.format(_split, _split, paths[1]))
    # print(_split.join(path))
    # print(_split.join(output_path))
    # DISTPATH = "dist"
    # shutil.copyfile(current_dir + _split.join(path), '{0}{1}config.txt'.format(DISTPATH, _split))
    # print(current_dir + _split.join(path))
    # print('{0}{1}{2}'.format(DISTPATH, _split, path[2]))
    # now = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    # print(now)
    # tomorrow = datetime.timedelta(hours=8)
    # print(1)
    # today = datetime.datetime.today()
    # print(today)
    # current = datetime.datetime.now()
    # print(current)
    # print(current + tomorrow)
    # # print(tomorrow.total_seconds())
    # print(current < (datetime.datetime.now() + tomorrow))
    # print(tomorrow + today)
    # today_000 = today.replace(hour=0, minute=0, second=0)
    #
    # limit = today_000 + datetime.timedelta(days=1, hours=8)
    # t1 = {'a': limit, 'abc': '123'}
    # print(t1)
    # print(t1.get('a'))
    # t1.pop('abc')
    # print('abc' not in t1)
    # limit_str = "2024-03-08 12:30:33"
    # a = datetime.datetime.strptime(limit_str, "%Y-%m-%d %H:%M:%S")
    # print(a)
    # t1['b'] = a
    # print(t1)
    # print(today)
    # print(today.strftime("%Y-%m"))
    d1 = {'x': 1, 'y': 2}
    print(d1.get('abc'))
    # d2 = {'a': 1}
    # print({**d1, **d2, 'a': 333})
    # s1 = "10 Gold"
    # print('Gold' in s1)
    # print(s1.replace("Gold", "").strip())

