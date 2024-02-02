import os
import platform
import shutil
import sys

if __name__ == '__main__':
    _system = platform.system()
    current_dir = os.getcwd()
    # config_path = '\src\config.txt' if _platform == 'Windows' else '/src/config.txt'

    _split = "\\" if _system == 'Windows' else '/'
    path = ['', 'src', 'config.txt']
    output_path = ['dist', 'config.txt']

    # shutil.copyfile(_split.join(paths), '{0}{1}{2}'.format(_split, _split, paths[1]))
    print(_split.join(path))
    print(_split.join(output_path))
    DISTPATH = "dist"
    # shutil.copyfile(current_dir + _split.join(path), '{0}{1}config.txt'.format(DISTPATH, _split))
    print(current_dir + _split.join(path))
    print('{0}{1}{2}'.format(DISTPATH, _split, path[2]))
