# import json
# import os
# import sys
# import logging
# from src.util.common import get_config, load_json
#
# if __name__ == '__main__':
#     logger = logging.getLogger("Test")
#     current_dir = "/Users/errol/MyApp.localized/automated-redemption-for-nutaku-daily-rewards"
#     # logger.info('当前目录为：' + current_dir)
#     # logger.info('读取配置文件...')
#     print(current_dir)
#     config = get_config(current_dir, logger)
#     config.add_section('sys')
#     logger.info("添加sys配置项")
#     config.set('sys', 'dir', current_dir)
#     logger.info(f"设置config.sys.dir: {current_dir}")
#     config.add_section("local_store")
#     logger.info("添加local_store配置项")
#     # set_retrying_copying(config, config.get('settings', 'retrying'))
#     # logger.info(messages[0])
#     mode = config.get('settings', 'execution_mode')
#     # config_logger(config, current_dir)
#     print(config)
#     # print(config.get("local_store", 'json'))
#     local_store = load_json(config, "data.json", logger)
#     config.set("local_store", "json", json.dumps(local_store))
#     print(local_store)