import datetime
import json
import sys
from json import JSONDecodeError

def fn1():
    print("Hello")
    sys.exit()


if __name__ == '__main__':
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    next_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
    print(next_time.date() < tomorrow)
    d1 = {'name': 'errol'}
    d2 = {'name': 'errrrrol'}
    d3 = {'a': ''}
    print(d1 | d2 | d3)
    print(d3.get('a') is None)

    # try:
    #     fn1()
    # except SystemExit as e:
    #     print("Caught SystemExit")
    # data_file_path = '../dist/abc.json'
    #data = {'email12312312313123123123213': '123@46.com'}

    # data = {'date': datetime.datetime.now().strftime('%Y-%m-%d'),
    #         'email': 'email'}
    # with open(data_file_path, 'r+') as _file:
    #     json_str = _file.read()
    #     merged = data | (json.loads(json_str) if len(json_str) > 0 else {})
    #     print(merged)
    #     _file.seek(0)
    #     json.dump(merged, _file)
