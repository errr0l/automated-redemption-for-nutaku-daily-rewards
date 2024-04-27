import datetime
import json
import os

if __name__ == '__main__':
    today = datetime.datetime.today()
    today_000 = today.replace(hour=0, minute=0, second=0)
    limit = today_000 + datetime.timedelta(days=1, hours=8)
    t1 = {'a': limit}
    print(t1)
    print(t1.get('a'))
    data_file_path = "../abc.txt"
    data = {"data": "2024-12-12", "afsdf": "123123", 'a': limit.strftime('%Y-%m-%d %H:%M:%S')}
    # 创建文件
    if os.path.exists(data_file_path) is False:
        with open(data_file_path, 'w'):
            pass
    with open(data_file_path, 'r+') as _file:
        json_str = _file.read()
        is_not_empty = len(json_str) > 0
        merged = (json.loads(json_str) if is_not_empty else {}) | data
        # 清空文件内容，再重新写入
        print(merged)
        print(is_not_empty)
        if is_not_empty:
            _file.seek(0)
            _file.truncate()
        json.dump(merged, _file)
