"""Fallback for imported/manual observations; backend probes provide exact sources."""

def source_for(section, title):
    if title.startswith('Disk ·') or title == 'Filesystem usage':
        return 'Filesystem usage'
    return f'{section} collector'
