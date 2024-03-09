
import os
import platform
import shutil
import sys
import datetime

if __name__ == '__main__':
    _system = platform.system()
    current_dir = os.getcwd()
    # config_path = '\src\config.txt' if _platform == 'Windows' else '/src/config.txt'

    _split = "\\" if _system == 'Windows' else '/'
    path = ['', 'src', 'config.txt']
    output_path = ['dist', 'config.txt']

    # shutil.copyfile(_split.join(paths), '{0}{1}{2}'.format(_split, _split, paths[1]))
    print(_split.join(path))
    print(_split.join(output_path))
    DISTPATH = "dist"
    # shutil.copyfile(current_dir + _split.join(path), '{0}{1}config.txt'.format(DISTPATH, _split))
    print(current_dir + _split.join(path))
    print('{0}{1}{2}'.format(DISTPATH, _split, path[2]))
    # now = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    # print(now)
    # tomorrow = datetime.timedelta(hours=8)
    # print(1)
    today = datetime.datetime.today()
    # print(today)
    # current = datetime.datetime.now()
    # print(current)
    # print(current + tomorrow)
    # # print(tomorrow.total_seconds())
    # print(current < (datetime.datetime.now() + tomorrow))
    # print(tomorrow + today)
    today_000 = today.replace(hour=0, minute=0, second=0)

    limit = today_000 + datetime.timedelta(days=1, hours=8)
    t1 = {'a': limit, 'abc': '123'}
    print(t1)
    print(t1.get('a'))
    t1.pop('abc')
    print('abc' not in t1)
    limit_str = "2024-03-08 12:30:33"
    a = datetime.datetime.strptime(limit_str, "%Y-%m-%d %H:%M:%S")
    print(a)
    t1['b'] = a
    print(t1)

