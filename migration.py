class Migration:
    def __init__(self, bug_id=None, mc_path=None, description=None):
        self.bug_id = bug_id
        self.mc_path = mc_path
        self.description = description
        self.helpers = []
        self.migrate_ops = []

        self.messages = []

    def add_message(self, id, value, attributes):
        self.messages.append({
            "id": id,
            "value": value,
            "attributes": attributes,
        })

    def relative_path(self, path):
        result = path
        if result.startswith(self.mc_path):
            result = path[len(self.mc_path):]
        if result.startswith("./"):
            result = result[2:]
        return result

    def get_path_alias(self, path, shared_paths):
        path = path.replace("locales/en-US/", "")
        for name in shared_paths:
            if shared_paths[name] == path:
                return name

        new_name = f"path{len(shared_paths) + 1}"
        shared_paths[new_name] = path
        return new_name

    def serialize(self):
        body = ""

        shared_paths = {}

        for message in self.messages:
            body += f'{message["id"]} ='
            if message["value"] is not None:
                value = message["value"]
                if value["action"] == "copy":
                    if "COPY" not in self.helpers:
                        self.helpers.append("COPY")
                    path = self.relative_path(value["dtd"].entry.path)
                    name = self.get_path_alias(path, shared_paths)

                    body += f' {{ COPY({name}, "{value["entity_id"]}") }}\n'
                else:
                    raise NotImplementedError
            body += '\n'
            for attr in message["attributes"]:
                if attr["action"] == "copy":
                    if "COPY" not in self.helpers:
                        self.helpers.append("COPY")
                    path = self.relative_path(attr["dtd"].entry.path)
                    name = self.get_path_alias(path, shared_paths)
                    
                    body += f'    .{attr["name"]} = {{ COPY({name}, "{attr["entity_id"]}") }}\n'
                else:
                    raise NotImplementedError

        res = (f"# coding=utf8\n\n"
            f"# Any copyright is dedicated to the Public Domain.\n"
            f"# http://creativecommons.org/publicdomain/zero/1.0/\n\n"
            f"from __future__ import absolute_import\n"
            f"import fluent.syntax.ast as FTL\n"
            f"from fluent.migrate.helpers import transforms_from\n")
        if self.helpers:
            res += f"from fluent.migrate.helpers import {', '.join(self.helpers)}\n"
        if self.migrate_ops:
            res += f"from fluent.migrate import {', '.join(self.migrate_ops)}\n"

        desc_postfix = ", part {index}"

        from_paths = []
        for name in shared_paths:
            from_paths.append(f'{name}="{shared_paths[name]}"')

        res += (f'\ndef migrate(ctx):\n'
                f'    """Bug {self.bug_id} - {self.description}{desc_postfix}"""\n\n'
                f'    ctx.add_transforms(\n'
                f'        "browser/browser/browser.ftl",\n'
                f'        "browser/browser/browser.ftl",\n'
                f'        transforms_from(\n'
                f'            """\n\n'
                f'{body}'
                f'""", {", ".join(from_paths)}))\n')

        return res

