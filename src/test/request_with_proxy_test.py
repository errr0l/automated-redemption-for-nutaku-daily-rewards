import requests
from fake_useragent import UserAgent

if __name__ == '__main__':
    print("开始")
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 " \
         "Safari/537.36 Edge/13.10586 "
    proxies = {
        'http': 'http://127.0.0.1:78901'
    }

    ua = UserAgent()
    print(ua.random)
    resp = requests.get(url="https://www.youtube.com/", proxies=proxies)
    print(resp.text)
