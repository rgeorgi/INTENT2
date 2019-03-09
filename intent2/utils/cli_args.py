import os
from argparse import ArgumentTypeError
import glob

def existstype(arg, filefunc, err_str):
    if os.path.exists(arg):
        if filefunc(arg):
            return arg
        else:
            raise ArgumentTypeError('"{}" {}.'.format(arg, err_str))
    else:
        raise ArgumentTypeError('"{}" does not exist.'.format(arg))

def proportion(arg) -> float:
    """
    An argument type that is a float between 0 and 1.
    """
    try:
        arg = float(arg)
        assert 0 <= arg <=1
    except:
        raise ArgumentTypeError('"{}" must be a float between 0 and 1')
    else:
        return arg

def existsfile(arg):
    return existstype(arg, os.path.isfile, "must be a file, not directory.")


def globfiles(arg):
    return glob.glob(arg)


def existsdir(arg):
    return existstype(arg, os.path.isdir, "must be a directory, not file.")


def get_dir_files(dir_paths, ext_filter=None, recursive=False):
    """
    Given a list of directory paths
    """
    for dir_path in dir_paths:
        for root, dir, files in os.walk(dir_path):
            if (os.path.abspath(root) != os.path.abspath(dir_path)) and (not recursive):
                break
            for path in files:
                if not ext_filter or path.endswith(ext_filter):
                    yield os.path.join(root, path)
    else:
        return []
