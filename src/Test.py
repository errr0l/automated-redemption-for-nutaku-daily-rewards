import datetime
import sys


def fn1():
    print("Hello")
    sys.exit()


if __name__ == '__main__':
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    next_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
    print(next_time.date() < tomorrow)

    try:
        fn1()
    except SystemExit as e:
        print("Caught SystemExit")
