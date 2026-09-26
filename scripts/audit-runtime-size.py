#!/usr/bin/env python3
"""Read-only size inventory; output paths are relative, never personal build paths."""
import argparse
from collections import defaultdict
import json
from pathlib import Path


def inventory(root):
    groups = defaultdict(int)
    files = []
    for path in root.rglob('*'):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        size = path.stat().st_size
        groups['/'.join(relative.parts[:2])] += size
        files.append({'path': relative.as_posix(), 'bytes': size})
    return {'uncompressed_regular_file_bytes': sum(groups.values()),
            'groups': sorted(({'path': k, 'bytes': v} for k,v in groups.items()), key=lambda x:-x['bytes']),
            'largest_files': sorted(files, key=lambda x:-x['bytes'])[:25]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runtime', type=Path)
    args = parser.parse_args()
    print(json.dumps(inventory(args.runtime), indent=2))
