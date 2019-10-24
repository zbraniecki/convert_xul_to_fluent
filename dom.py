import re

class DOMDiff:
    def __init__(self):
        self.changes = []

    def add_change(self, action, elem_diff):
        self.changes.append((action, elem_diff))

    def apply(self, source):
        for change in self.changes:
            if change[0] == "modify":
                source = change[1].apply(source)
            else:
                raise NotImplementedError
        return source

class ElementDiff:
    def __init__(self, element):
        self.changes = []
        self.element = element

    def add_change(self, action, attr_name, new_value=None, new_value2=None):
        self.changes.append((action, attr_name, new_value, new_value2))

    def recalculate_spans(self, start, change):
        for element in self.element.fragment.elements:
            for attr in element.attrs:
                if attr.span[0] >= start:
                    attr.span = (attr.span[0] + change, attr.span[1] + change)
            if element.span[0] >= start:
                element.span = (element.span[0] + change, element.span[1] + change)

    def select_cut(self, source, start, end):
        ws_end = start
        ws_start = end
        ptr = end
        while ptr < len(source):
            if source[ptr] == "\n":
                ws_end = ptr
                break
            if not source[ptr].isspace():
                ws_end = ptr - 1
                break
            ptr += 1

        ptr = start - 1
        while ptr > 0:
            if source[ptr] == "\n":
                ws_start = ptr
                break
            if not source[ptr].isspace():
                ws_start = ptr + 1
                break
            ptr -= 1

        return (ws_start, ws_end)

    def apply(self, source):
        for change in self.changes:
            if change[0] == "remove":
                for attr in self.element.attrs:
                    if attr.name == change[1]:
                        (start, end) = self.select_cut(source, attr.span[0], attr.span[1])
                        source = source[:start] + source[end:]
                        self.recalculate_spans(end, (end - start) * -1)
            elif change[0] == "insert":
                end = self.element.span[0] + 1 + len(self.element.id)

                if self.element.attrs:
                    last_attr = self.element.attrs[-1]
                    end = last_attr.span[1]

                new_attr = DOMAttribute(change[1], change[2], (end + 1, end + len(change[1]) + len(change[2]) + 4))
                source = source[:end] + " " + str(new_attr) + source[end:]
                self.element.attrs.append(new_attr)
                self.recalculate_spans(end, len(str(new_attr)) + 1)
            elif change[0] == "replace":
                for attr in self.element.attrs:
                    if attr.name == change[1]:
                        new_attr = DOMAttribute(change[2], change[3], (attr.span[0], attr.span[0] + len(change[2]) + len(change[3]) + 3))
                        source = source[:attr.span[0]] + str(new_attr) + source[attr.span[1]:]

                        idx = self.element.attrs.index(attr)
                        self.element.attrs.insert(idx, new_attr)
                        self.element.attrs.remove(attr)
                        self.recalculate_spans(attr.span[1], (new_attr.span[1] - new_attr.span[0]) - (attr.span[1] - attr.span[0]))
            else:
                raise NotImplementedError
        return source

class DOMAttribute:
    def __init__(self, name, value, span):
        self.name = name
        self.value = value
        self.span = span

    def is_dtd_attr(self):
        if self.value and self.value.startswith("&") and self.value.endswith(";"):
            return True
        return False

    def __repr__(self):
        return f"{self.name}=\"{self.value}\""

class DOMElement:
    def __init__(self, fragment, id, attrs, value, span):
        self.fragment = fragment
        self.id = id
        self.attrs = attrs
        self.value = value
        self.span = span

    def is_dtd_element(self):
        if self.value and self.value.startswith("&") and self.value.endswith(";"):
            return True

        for attr in self.attrs:
            if attr.is_dtd_attr():
                return True

        return False

    def __repr__(self):
        attrs = ""
        for attr in self.attrs:
            attrs += f" {attr.name}=\"{attr.value}\""
        if self.value:
            return f"<{self.id}{attrs}>{self.value}</{self.id}>"
        return f"<{self.id}{attrs}/>"

class DOMFragment:
    def __init__(self, source, entry):
        self.source = source
        self.entry = entry
        self.diffs = []
        self.elements = None
        self.get_elements()

    def get_elements(self):
        if self.elements is None:
            self.elements = self.find_all_elements()
        return self.elements

    def find_dtd_elements(self):
        result = []
        for element in self.elements:
            if element.is_dtd_element():
                result.append(element)

        return result

    def find_all_elements(self):
        elements = []
        matches = re.finditer("<(?P<id>\w+)\s*(?P<attrs>(?:[\w-]+\s*=\s*\"[^\"]*\"\s*)*)/>", self.source)
        elements.extend(matches)

        matches = re.finditer("<(?P<id>\w+)\s*(?P<attrs>(?:[\w-]+\s*=\s*\"[^\"]*\"\s*)*)>(?P<value>[^<]*)</\w+>", self.source)
        elements.extend(matches)

        result = []
        for match in elements:
            attrs = self.parse_attributes(match.group("attrs"), match.span("attrs"), match.span(0))
            value = match.group("value") if "value" in match.groupdict() else None
            elem = DOMElement(
                    self,
                    match.group("id"),
                    attrs,
                    value,
                    match.span(0))
            result.append(elem)
        return result

    def parse_attributes(self, input, attrs_span, elem_span):
        attrs = []
        matches = re.finditer("(?P<name>\w+)\s*=\s*\"(?P<value>[^\"]*)\"", input)
        for match in matches:
            span = (attrs_span[0] + match.span(0)[0], attrs_span[0] + match.span(0)[1])
            attrs.append(DOMAttribute(
              match.group("name"),
              match.group("value"),
              span
            ))
        return attrs

    def serialize(self):
        source = self.source

        for diff in self.diffs:
            source = diff.apply(source)
        return source
