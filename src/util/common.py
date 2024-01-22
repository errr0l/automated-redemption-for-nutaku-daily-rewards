import configparser
import sys, os, json

# 读取配置文件【账号&密码】
def get_config(config_dir):
    config = configparser.ConfigParser()
    config.read(config_dir + "/config.txt", encoding="utf-8")
    return config


def parse_execution_time(execution_time: str):
    hours, minutes = execution_time.split(":")
    return {'hours': hours, 'minutes': minutes}


# 如果为模式2时，签到完后，退出程序
def exit_if_necessary(config, logger):
    is_mode_2 = config.get('settings', 'execution_mode') == '2'
    if is_mode_2:
        try:
            sys.exit()
        except SystemExit:
            logger.debug("捕获SystemExit异常.")
            print('---> 退出程序.')


def load_data(config: dict):
    data_file_path = config.get('sys', 'dir') + '/data.json'
    data = {}
    if os.path.exists(data_file_path):
        with open(data_file_path, 'r') as file:
            json_str = file.read()
            if len(json_str) > 0:
                data = json.loads(json_str)
    return data


def clear(tips: bool):
    os.system('cls' if os.name == 'nt' else 'clear')
    if tips:
        print('>> 按 Ctrl+{0} 退出程序...'.format('Break' if os.name == 'nt' else 'C'))
        print()