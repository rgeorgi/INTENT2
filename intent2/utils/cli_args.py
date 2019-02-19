import os
from argparse import ArgumentTypeError

def existsfile(arg):
    if os.path.exists(arg):
        if os.path.isfile(arg):
            return arg
        else:
            return ArgumentTypeError('"{}" must be a file, not directory.'.format(arg))
    else:
        raise ArgumentTypeError('"{}" does not exist.'.format(arg))
