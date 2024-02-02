if __name__ == '__main__':
    d1 = {'name': 'errol'}
    d2 = {'name': 'errrrro000000l'}
    d3 = {'a': ''}
    print(d1 | d2 | d3)
    print(d3.get('a') is None)