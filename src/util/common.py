import configparser
import json
import os
import signal
import time
import platform


def get_separator():
    _system = platform.system()
    return "\\" if _system == 'Windows' else '/'


separator = get_separator()


# 读取配置文件【账号&密码】
def get_config(config_dir, logger):
    config = configparser.ConfigParser()
    config_file_path = config_dir + separator + "config.txt"
    logger.debug("配置文件路径为：" + config_file_path)
    if os.path.exists(config_file_path) is False:
        print("---> 配置文件不存在或路径不正确，将退出程序.")
        time.sleep(3)
        kill_process()
    else:
        config.read(config_file_path, encoding="utf-8")
    return config


def parse_execution_time(execution_time: str):
    hours, minutes = execution_time.split(":")
    return {'hours': hours, 'minutes': minutes}


def kill_process():
    pid = os.getpid()
    os.kill(pid, signal.SIGTERM)


# 如果为模式2时，签到完后，退出程序
def exit_if_necessary(config, logger):
    is_mode_2 = config.get('settings', 'execution_mode') == '2'
    if is_mode_2:
        print("---> 即将退出程序.")
        time.sleep(3)
        kill_process()


def load_data(config: dict, logger):
    data_file_path = config.get('sys', 'dir') + separator + 'data.json'
    logger.debug("->加载本地数据.")
    logger.debug("路径为：" + data_file_path)
    data = {}
    if os.path.exists(data_file_path):
        with open(data_file_path, 'r') as file:
            json_str = file.read()
            if len(json_str) > 0:
                data = json.loads(json_str)
    logger.debug("->{}".format(data))
    return data


def clear(tips: bool):
    os.system('cls' if os.name == 'nt' else 'clear')
    if tips:
        print('>> 按 Ctrl+{0} 退出程序...'.format('Break' if os.name == 'nt' else 'C'))
        print()
