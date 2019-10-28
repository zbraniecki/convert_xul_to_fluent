from fluent.syntax.ast import Message, Identifier, Attribute, Pattern, TextElement
from fluent.syntax.serializer import serialize_message

class FTLDiff:
    def __init__(self):
        self.changes = []

    def add_change(self, action, msg):
        self.changes.append((action, msg))

    def apply(self, source):
        for change in self.changes:
            if change[0] == "add":
                msg = change[1]

                source += serialize_message(msg)

            else:
                raise NotImplementedError
        return source

class FTLMessage(Message):
    def __init__(self, id, value=None, attributes=None):
        v = None
        if value is not None:
            v = Pattern([TextElement(value["entity"].value)])

        attrs = []

        if attributes:
            for attr in attributes:
                attrs.append(Attribute(Identifier(attr["name"]), Pattern([TextElement(attr["entity"].value)])))
        super().__init__(Identifier(id), v, attrs)


class FTLFragment:
    def __init__(self, source, entry):
        self.source = source
        self.entry = entry
        self.diffs = []

    def serialize(self):
        source = self.source

        for diff in self.diffs:
            source = diff.apply(source)
        return source
