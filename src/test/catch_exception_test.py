import sys


def fn1():
    print("Hello")
    sys.exit()


if __name__ == '__main__':
    try:
        fn1()
    except SystemExit as e:
        print("Caught SystemExit")