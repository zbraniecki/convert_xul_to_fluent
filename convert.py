import json

from lib.xul import collect_messages
from lib.dtd import get_dtds
from lib.utils import read_file, write_file
from lib.migration import build_migration
from lib.fluent import build_ftl

pane = 'search'

data = {
    'bug_id': '1411012',
    'description': 'Migrate several strings from Preferences:Search',
    'mozilla-central': '../mozilla-unified',
    'xul': 'browser/components/preferences/in-content/{0}.xul'.format(pane),
    'dtd': [
        'browser/locales/en-US/chrome/browser/preferences/{0}.dtd'.format(pane),
        'browser/locales/en-US/chrome/browser/preferences/preferences.dtd'
    ],
    'migration': './migration.py',
    'ftl': 'browser/locales/en-US/browser/preferences/{0}.ftl'.format(pane),
}


if __name__ == '__main__':
    dtds = get_dtds(data['dtd'], data['mozilla-central'])

    s = read_file(data['xul'], data['mozilla-central'])

    print('======== INPUT ========')
    print(s)

    print('======== OUTPUT ========')
    (new_xul, messages) = collect_messages(s)
    print(new_xul)
    # write_file(data['xul'], new_xul, data['mozilla-central'])

    print('======== L10N ========')

    print(json.dumps(messages, sort_keys=True, indent=2))

    migration = build_migration(messages, dtds, data)

    print('======== MIGRATION ========')
    print(migration)

    ftl = build_ftl(messages, dtds, data)

    print('======== Fluent ========')
    print(ftl)
