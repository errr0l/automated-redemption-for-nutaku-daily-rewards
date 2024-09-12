from bs4 import BeautifulSoup

if __name__ == '__main__':
    with open('../home.html') as _f:
        html = _f.read()
        soup = BeautifulSoup(html, 'html.parser')
        _rewards_list = soup.find('div', {'class': 'reward-list'})
        _text_rewards = _rewards_list.find_all('span', {'class': 'text-reward'})
        total = 0
        for item in _text_rewards:
            print(item)
            if 'Gold' in item.text:
                total += int(item.text.replace("Gold", "").strip())
        print(total)
