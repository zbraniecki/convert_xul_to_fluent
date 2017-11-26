import json

from lib.xul import collect_messages
from lib.dtd import get_dtds
from lib.utils import read_file, write_file
from lib.migration import build_migration
from lib.fluent import build_ftl

dry_run = False

pane = 'containers'

data = {
    'bug_id': '1419547',
    'description': 'Migrate several strings from Preferences:Containers',
    'mozilla-central': '../mozilla-unified',
    'xul': 'browser/base/content/browser-menubar.inc',
    'dtd': [
    	'browser/locales/en-US/chrome/browser/browser.dtd',
        'toolkit/locales/en-US/chrome/global/charsetMenu.dtd',
        'browser/locales/en-US/chrome/browser/baseMenuOverlay.dtd',
        'browser/locales/en-US/chrome/browser/safebrowsing/phishing-afterload-warning-message.dtd',
        'browser/locales/en-US/chrome/browser/safebrowsing/report-phishing.dtd',
    ],
    'migration': './migration.py',
    'ftl': 'browser/locales/en-US/browser/menubar.ftl'
}


if __name__ == '__main__':
    dtds = get_dtds(data['dtd'], data['mozilla-central'])

    s = read_file(data['xul'], data['mozilla-central'])

    print('======== INPUT ========')
    print(s)

    print('======== OUTPUT ========')
    (new_xul, messages) = collect_messages(s)
    print(new_xul)
    if not dry_run:
        write_file(data['xul'], new_xul, data['mozilla-central'])

    print('======== L10N ========')

    print(json.dumps(messages, sort_keys=True, indent=2))

    migration = build_migration(messages, dtds, data)

    print('======== MIGRATION ========')
    print(migration)

    ftl = build_ftl(messages, dtds, data)

    print('======== Fluent ========')
    print(ftl)
    if not dry_run:
        write_file(data['ftl'], ftl, data['mozilla-central'])
