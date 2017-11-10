import json
# from io import StringIO
# from lxml import etree

from lib.xul import collect_messages
from lib.dtd import get_dtd

f = '../mozilla-unified/browser/components/preferences/in-content/search.xul'
d = '../mozilla-unified/browser/locales/en-US/chrome/browser/preferences/search.dtd'


def read_file(path):
    with open(path) as fptr:
        return fptr.read()


def write_file(path, text):
    with open(path, "w") as text_file:
        text_file.write(text)

if __name__ == '__main__':
    dtd = get_dtd(read_file(d))

    s = read_file(f)

    print('======== INPUT ========')
    print(s)

    print('======== OUTPUT ========')
    (new_xul, messages) = collect_messages(s)
    print(new_xul)
    write_file(f, new_xul)

    print('======== L10N ========')

    print(json.dumps(messages, sort_keys=True, indent=2))

