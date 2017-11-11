import os


def read_file(path, base_path=None):
    if base_path is not None:
        path = os.path.join(base_path, path)
    with open(path) as fptr:
        return fptr.read()


def write_file(path, text, base_path=None):
    if base_path is not None:
        path = os.path.join(base_path, path)
    with open(path, "w") as text_file:
        text_file.write(text)
