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

def get_attr_ending(attr_name, id):
    if id.endswith(f".{attr_name}"):
        return attr_name

    if attr_name in attribute_map:
        ending = attribute_map[attr_name]
        if id.endswith(f".{ending}"):
            return ending
    return None

def camel_to_snake(text):
        str1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', str1).lower()

class Entry:
    def __init__(self, path, line_start=0, line_end=None, includes=None):
        self.path = path
        self.line_start = line_start
        self.line_end = line_end
        self.includes = includes

    def load_source(self):
        lines = open(self.path).readlines()
        return "".join(lines[self.line_start:self.line_end])

    def override(self, new_chunk):
        if os.path.exists(self.path):
            lines = open(self.path).readlines()
            result = lines[:self.line_start] + [new_chunk] + lines[self.line_end:]
        else:
            result = [new_chunk]
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

    def calculate_attr_name(self, message, element, attr):
        result = {
            "name": None,
            "action": None,
            "entity_id": attr.value[1:-1],
            "element": element
        }
        result["name"] = result["entity_id"]

        ending = get_attr_ending(attr.name, result["name"])
        if ending is not None:
            message_id_candidate = result["name"][:(len(ending) + 1) * -1]
            result["name"] = result["name"][len(message_id_candidate) + 1:]

            message_id_candidate = camel_to_snake(message_id_candidate)
            if message["id"] is None:
                message["id"] = message_id_candidate
            elif message["id"] != message_id_candidate:
                raise "We need to resolve id conflict!"
        return result

    def migrate(self):
        elements = []
        for fragment in self.dom_fragments:
            elements.extend(fragment.find_dtd_elements())

        messages = []
        for element in elements:
            message = {
                "id": None,
                "value": None,
                "attributes": []
            }
            diff = DOMDiff()
            elem_diff = ElementDiff(element)
            attrs_to_remove = []
            for attr in element.attrs:
                if attr.is_dtd_attr():
                    migration_attr = self.calculate_attr_name(message, element, attr)
                    message["attributes"].append(migration_attr)
                    attrs_to_remove.append(migration_attr["name"])
            
            for attr_name in attrs_to_remove:
                if attr_name == "label":
                    elem_diff.add_change("replace", attr_name, "data-l10n-id", message["id"])
                else:
                    elem_diff.add_change("remove", attr_name)
            messages.append(message)
            diff.add_change("modify", elem_diff)
            element.fragment.diffs.append(diff)

        for message in messages:
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
