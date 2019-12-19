import os
import re
from dom import DOMFragment, DOMDiff, ElementDiff
from dtd import DTDFragment, DTDDiff
from ftl import FTLFragment, FTLDiff, FTLMessage
from migration import Migration

attribute_map = {
  "tooltiptext": "tooltip",
  "value": "label"
}

def split_attr(id, attr_name):
    if id.endswith(f".{attr_name}"):
        return (id[:(len(attr_name) + 1) * -1], attr_name)

    if attr_name in attribute_map:
        ending = attribute_map[attr_name]
        if id.endswith(f".{ending}"):
            return (id[:(len(ending) + 1) * -1], ending)
    return (id, attr_name)

def camel_to_snake(text):
        str1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', str1).lower()

def convert_id(text, message_ids):
    result = camel_to_snake(text).replace(".", "-")
    if result[-1].isnumeric():
        candidate = result[:-1]
        if candidate not in message_ids:
            result = result[:-1]
    return result

class Entry:
    def __init__(self, path, line_start=0, line_end=None, includes=None, dry_run=False):
        self.path = path
        self.line_start = line_start
        self.line_end = line_end
        self.includes = includes
        self.dry_run = dry_run

    def load_source(self):
        lines = open(self.path).readlines()
        return "".join(lines[self.line_start:self.line_end])

    def override(self, new_chunk):
        if os.path.exists(self.path):
            lines = open(self.path).readlines()
            result = lines[:self.line_start] + [new_chunk] + lines[self.line_end:]
        else:
            result = [new_chunk]
        if not self.dry_run:
            with open(self.path, 'w') as out:
                out.write("".join(result))

class Migrator:
    def __init__(self, bug_id, mc_path, description):
        self.bug_id = bug_id
        self.mc_path = mc_path
        self.description = description

        self.dom_fragments = []
        self.dtd_fragments = []
        self.ftl_fragments = []

    def add_dom_entry(self, entry):
        source = entry.load_source()
        df = DOMFragment(source, entry)
        self.dom_fragments.append(df)

    def add_dtd_entry(self, entry):
        source = entry.load_source()
        df = DTDFragment(source, entry)
        self.dtd_fragments.append(df)

    def add_ftl_entry(self, entry):
        source = entry.load_source()
        df = FTLFragment(source, entry)
        self.ftl_fragments.append(df)

    def migrate(self):
        elements = []
        for fragment in self.dom_fragments:
            elements.extend(fragment.find_dtd_elements())

        messages = []

        # We need to keep track of ids so that we can strip
        # trailing numbers if it won't duplicate ID
        message_ids = []
        for element in elements:
            message = {
                "id": None,
                "value": None,
                "attributes": []
            }
            diff = DOMDiff()
            elem_diff = ElementDiff(element)
            attrs_to_remove = []
            if element.value is not None:
                message["id"] = convert_id(element.value["value"][1:-1], message_ids)
                elem_diff.add_change("remove_value")
                message["value"] = {"entity_id": element.value["value"][1:-1] }
            for attr in element.attrs:
                if attr.is_dtd_attr():
                    migration_attr = {
                        "name": attr.name,
                        "action": None,
                        "entity_id": attr.value[1:-1],
                        "element": element
                    }
                    (new_id, attr_name) = split_attr(attr.value[1:-1], attr.name)
                    new_id = convert_id(new_id, message_ids)
                    if message["id"] is None:
                        message["id"] = new_id
                    elif message["id"] != new_id:
                        raise "We need to resolve id conflict!"
                    message["attributes"].append(migration_attr)
                    attrs_to_remove.append(migration_attr["name"])
            
            replace_attr = None

            if "label" in attrs_to_remove:
                replace_attr = "label"
            elif len(attrs_to_remove)  ==  1:
                replace_attr = attrs_to_remove[0]
            elif len(attrs_to_remove) != 0:
                raise Exception("Don't know how to pick an attribute to replace!")

            for attr_name in attrs_to_remove:
                if attr_name == replace_attr:
                    elem_diff.add_change("replace", attr_name, "data-l10n-id", message["id"])
                else:
                    elem_diff.add_change("remove", attr_name)

            if replace_attr is None:
                    elem_diff.add_change("insert", "data-l10n-id", message["id"])

            message_ids.append(message["id"])
            messages.append(message)
            diff.add_change("modify", elem_diff)
            element.fragment.diffs.append(diff)

        for message in messages:
            if message["value"]:
                candidate = None
                for dtd in self.dtd_fragments:
                    candidate = dtd.find_entity(message["value"]["entity_id"])
                    if candidate:
                        message["value"]["action"] = "copy"
                        message["value"]["dtd"] = dtd
                        message["value"]["entity"] = candidate

                        dtd_diff = DTDDiff(dtd)
                        dtd_diff.add_change("remove", candidate)
                        dtd.diffs.append(dtd_diff)
                        break

                if candidate is None:
                    print(f"Failed to find an entity {attr['entity_id']}")

            for attr in message["attributes"]:
                candidate = None
                for dtd in self.dtd_fragments:
                    candidate = dtd.find_entity(attr["entity_id"])
                    if candidate:
                        attr["action"] = "copy"
                        attr["dtd"] = dtd
                        attr["entity"] = candidate

                        dtd_diff = DTDDiff(dtd)
                        dtd_diff.add_change("remove", candidate)
                        dtd.diffs.append(dtd_diff)
                        break

                if candidate is None:
                    print(f"Failed to find an entity {attr['entity_id']}")

        migration = Migration(self.bug_id, self.mc_path, self.description)

        ftl = self.ftl_fragments[0]
        ftl_diff = FTLDiff()

        for message in messages:
            migration.add_message(message["id"], message["value"], message["attributes"])
            
            msg = FTLMessage(message["id"], message["value"], message["attributes"])

            ftl_diff.add_change("add", msg)

        ftl.diffs.append(ftl_diff)
        return migration
