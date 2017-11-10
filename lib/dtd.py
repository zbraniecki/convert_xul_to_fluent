from io import StringIO
from lxml import etree


def get_dtd(dtd_source):
    entries = {}

    dtd = etree.DTD(StringIO(dtd_source))
    for entity in dtd.entities():
        entries[entity.name] = entity.content
    return entries
