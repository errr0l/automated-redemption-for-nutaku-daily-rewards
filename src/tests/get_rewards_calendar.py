import requests

if __name__ == '__main__':
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0',
        'Accept': '*/*',
        'Referer': 'https://www.nutaku.net/zh/home/'
    }
    resp = requests.get('https://www.nutaku.net/zh/rewards-calendar-details/')

    print(resp.status_code)
    print(resp.text)
    if "/login" in resp.text:
        print("未登录")
