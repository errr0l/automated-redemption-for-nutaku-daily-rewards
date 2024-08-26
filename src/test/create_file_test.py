import os

if __name__ == '__main__':
    data_file_path = "./abc.txt"
    if os.path.exists(data_file_path) is False:
        with open(data_file_path, 'w'):
            pass