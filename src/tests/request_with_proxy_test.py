import requests
from src.util.user_agent_util import get_random_ua

if __name__ == '__main__':
    UA = get_random_ua()
    # proxies = {
    #     'http': 'http://127.0.0.1:78901'
    # }
    proxies = {}

    resp = requests.get(url="https://www.youtube.com/", proxies=proxies)
    print(resp.text)
