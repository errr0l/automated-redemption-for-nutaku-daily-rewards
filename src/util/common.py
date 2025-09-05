import configparser
import json
import os
import signal
import time
import platform


def get_platform():
    return platform.system()


def get_separator():
    _system = get_platform()
    return "\\" if _system == 'Windows' else '/'


separator = get_separator()


# 读取配置文件【账号&密码】
def get_config(config_dir, logger):
    config = configparser.ConfigParser()
    config_file_path = config_dir + separator + "config.txt"
    logger.debug("配置文件路径为：" + config_file_path)
    _system = get_platform()
    if os.path.exists(config_file_path) is False:
        msg = "配置文件不存在或路径不正确，将退出程序."
        print(msg)
        logger.debug(msg)
        time.sleep(3)
        kill_process()
    else:
        config.read(config_file_path, encoding='utf-8-sig' if _system == 'Windows' else "utf-8")
    return config


def parse_execution_time(execution_time: str):
    hours, minutes = execution_time.split(":")
    return {'hours': hours, 'minutes': minutes}


# 关闭窗口
def kill_process():
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    pid = os.getpid()
    os.kill(pid, signal.SIGTERM)


# 如果为模式2时，签到完后，退出程序
def exit_if_necessary(config, logger, mode: str = None):
    is_mode_2 = (mode if mode is not None else config.get('settings', 'execution_mode')) == '2'
    if is_mode_2:
        print("即将退出程序...")
        time.sleep(3)
        kill_process()


def load_json(config: dict, filename: str, logger):
    logger.debug("加载json数据.")
    file_path = config.get('sys', 'dir') + separator + filename
    logger.debug("路径为：" + file_path)
    result = {}
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            json_str = file.read()
            if len(json_str) > 0:
                result = json.loads(json_str)
    logger.debug("{}.".format(result))
    return result


def save_json(config: dict, filename: str, data, logger):
    logger.debug("保存json数据.")
    file_path = config.get('sys', 'dir') + separator + filename
    logger.debug("路径为：" + file_path)
    # 创建文件
    if os.path.exists(file_path) is False:
        with open(file_path, 'w'):
            pass
    with open(file_path, 'r+') as _file:
        json_str = _file.read()
        is_not_empty = len(json_str) > 0
        result = json.loads(json_str) if is_not_empty else {}
        key = config.get("account", "email")
        user_data = result.get(key)
        if user_data is None:
            result[key] = data
        else:
            result[key] = {**user_data, **data}
        logger.debug("user_data: {}".format(user_data))
        # 记录邮箱
        emails = result.get("emails", "")
        if key not in emails:
            result['emails'] = key if len(emails) == 0 else f"{emails},{key}"
        # 清空文件内容，再重新写入
        if is_not_empty:
            _file.seek(0)
            _file.truncate()
        json.dump(result, _file)


def clear(tips: bool):
    os.system('cls' if os.name == 'nt' else 'clear')
    if tips:
        print('>> 按 Ctrl+{0} 退出程序...'.format('Break' if os.name == 'nt' else 'C'))
        print()


def get_month_days(month, year):
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if month == 2 and year % 4 == 0 and year % 100 != 0 or year % 400 == 0:
        return 28
    else:
        return days[month - 1]
