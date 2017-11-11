from io import StringIO
from lxml import etree
from .utils import read_file


def get_dtds(sources, base_path):
    entries = {}
    for source in sources:
        dtd = get_dtd(source, base_path)
        for entry in dtd:
            entries[entry] = dtd[entry]


def get_dtd(dtd_source, base_path):
    entries = {}

    source = read_file(dtd_source, base_path)

    dtd = etree.DTD(StringIO(source))
    for entity in dtd.entities():
        entries[entity.name] = entity.content
    return entries
