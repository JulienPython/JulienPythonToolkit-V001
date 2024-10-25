# This file is part of the "your-package-name" project.
# It is licensed under the "Custom Non-Commercial License".
# You may not use this file for commercial purposes without
# explicit permission from the author.


import os

def path_to_this_file(file):
    return os.path.dirname(os.path.realpath(file))

def join(*args):
    return os.path.join(*args)