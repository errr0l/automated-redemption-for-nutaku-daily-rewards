import random

ua_list = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 '
    'Safari/537.36 Edge/13.10586 '
    ,
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 '
    'Safari/537.36 '
    , 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36']


def get_random_ua():
    index = random.randint(0, len(ua_list) - 1)
    return ua_list[index]


# if __name__ == '__main__':
#     get_random_ua()

