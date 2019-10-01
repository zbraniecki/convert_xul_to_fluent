import re

class DTDDiff:
    def __init__(self, fragment):
        self.changes = []
        self.fragment = fragment

    def add_change(self, action, entity):
        self.changes.append((action, entity))

    def recalculate_spans(self, start, change):
        for entity in self.fragment.entities:
            if entity.span[1] <= start:
                continue

            entity.span = (entity.span[0] + change, entity.span[1] + change)
        pass

    def apply(self, source):
        for change in self.changes:
            if change[0] == "remove":
                start = change[1].span[0]
                end = change[1].span[1]
                if start > 0 and source[start - 1] == "\n":
                    start -= 1
                source = source[:start] + source[end:]
                self.fragment.entities.remove(change[1])
                self.recalculate_spans(end, (end - start) * -1)
            else:
                raise NotImplementedError
        return source

class DTDEntity:
    def __init__(self, id, value, span):
        self.id = id
        self.value = value
        self.span = span

    def __repr__(self):
        return f"<!ENTITY {self.id} \"{self.value}\">"

class DTDFragment:
    def __init__(self, source, entry):
        self.source = source
        self.entry = entry
        self.diffs = []
        self.entities = None
        self.get_entities()

    def get_entities(self):
        if self.entities is None:
            self.entities = self.find_all_entities()
        return self.entities

    def find_all_entities(self):
        entities = []

        matches = re.finditer("<!ENTITY (?P<id>[\w\.]+)\s+\"(?P<value>[^\"]*)\">", self.source)
        for match in matches:
            entities.append(DTDEntity(match.group("id"), match.group("value"), match.span(0)))
        return entities

    def find_entity(self, id):
        for e in self.entities:
            if e.id == id:
                return e
        return None

    def serialize(self):
        source = self.source

        for diff in self.diffs:
            source = diff.apply(source)
        return source
