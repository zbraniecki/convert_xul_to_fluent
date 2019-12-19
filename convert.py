import argparse
import os
from migration import Migration
from migrator import Entry, Migrator
from dom import DOMFragment, DOMDiff, ElementDiff, DOMElement
from dtd import DTDFragment, DTDDiff

def file_lines(path):
    return len(open(path).readlines())

def parse_path(mc_path, input, dry_run):
    entry = {
        "path": None,
        "line_start": 0,
        "line_end": None,
        "includes": None
    }
    chunks = input.split(':')
    entry["path"] = os.path.join(mc_path, chunks[0])

    entry["line_end"] = file_lines(os.path.join(mc_path, entry["path"]))

    if len(chunks) > 1:
        if chunks[1].isnumeric():
            entry["line_start"] = int(chunks[1])
        else:
            entry["includes"] = chunks[1]
            return Entry(entry["path"], entry["line_start"], entry["line_end"], entry["includes"])

    if len(chunks) > 2:
        if chunks[2].isnumeric():
            entry["line_end"] = int(chunks[2])
        else:
            entry["includes"] = chunks[2]
            return Entry(entry["path"], entry["line_start"], entry["line_end"], entry["includes"])
    
    if len(chunks) > 3:
        entry["includes"] = chunks[3]
    return Entry(entry["path"], entry["line_start"], entry["line_end"], entry["includes"], dry_run)

def init_migrator(parser):
    args = parser.parse_args()
    bug_id = args.bug_id
    mc = args.mc
    dry_run = args.dry_run

    dom_entries = []
    dtd_entries = []
    ftl_entries = []

    if args.dom:
        for path in args.dom:
            entry = parse_path(mc, path, dry_run)
            dom_entries.append(entry)

    if args.dtd:
        for path in args.dtd:
            entry = parse_path(mc, path, dry_run)
            dtd_entries.append(entry)

    if args.ftl:
        for path in args.ftl:
            entry = parse_path(mc, path, dry_run)
            ftl_entries.append(entry)

    if args.interactive:
        print('\nConvert to Fluent, interactive mode\n')
        result = input(f'Bug ID ({bug_id}): ')
        if result:
            bug_id = result

        result = input(f'Path to mozilla-central ("{mc}"): ')
        if result:
            mc = result

        i = 0
        while True:
            candidate = dom_entries[i] if len(dom_entries) > i else None
            suggestion = f' ("{candidate.path}")' if candidate else ''
            file = input(f'XUL/XHTML/HTML file{suggestion}: ')
            if not file and not candidate:
                break
            line_start = input(f'First line ({candidate.line_start}): ')
            line_end = input(f'Last line ({candidate.line_end}): ')
            follow_includes = input(f'Follow includes? ({"Y" if candidate.includes else "N"}): ')
            i += 1

    migrator = Migrator(bug_id, mc, args.description)
    for entry in dom_entries:
        migrator.add_dom_entry(entry)

    for entry in dtd_entries:
        migrator.add_dtd_entry(entry)

    for entry in ftl_entries:
        migrator.add_ftl_entry(entry)

    return migrator

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert Mozilla UI to Fluent')
    parser.add_argument('-i', '--interactive',
                        required=False,
                        action='store_true',
                        help='Turn on an interactive mode.')
    parser.add_argument('--bug_id',
                        help='Bugzilla ID of the issue.')
    parser.add_argument('--description',
                        help='Migration description.')
    parser.add_argument('--mc',
                        required=False,
                        default="./",
                        help='Path to mozilla-central')
    parser.add_argument('--dom', action='append',
                        required=False,
                        help='Path to XUL/XHTML/HTML fragments to be converted.')
    parser.add_argument('--dtd', action='append',
                        required=False,
                        help='Path to DTD fragments to be converted.')
    parser.add_argument('--ftl', action='append',
                        required=False,
                        help='Path to FTL fragments to be converted.')
    parser.add_argument('--js', action='append',
                        required=False,
                        help='Path to a JS file to be converted.')
    parser.add_argument('--dry-run',
                        required=False,
                        action='store_true',
                        help='Turn on dry run.')

    migrator = init_migrator(parser)

    migration = migrator.migrate()

    for dom in migrator.dom_fragments:
        if dom.diffs:
            new_chunk = dom.serialize()
            dom.entry.override(new_chunk)

    for dtd in migrator.dtd_fragments:
        if dtd.diffs:
            new_chunk = dtd.serialize()
            dtd.entry.override(new_chunk)

    for ftl in migrator.ftl_fragments:
        if ftl.diffs:
            new_chunk = ftl.serialize()
            ftl.entry.override(new_chunk)

    entry = Entry(os.path.join(migrator.mc_path, f"python/l10n/fluent_migrations/bug_{migration.bug_id}_migration.py"))
    new_chunk = migration.serialize()
    entry.override(new_chunk)
