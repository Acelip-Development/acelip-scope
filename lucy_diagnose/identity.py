"""Central public identity. Unresolved fields are absent, never invented."""
import json
from pathlib import Path

IDENTITY = json.loads(Path(__file__).with_name('identity.json').read_text())
DISPLAY_NAME = IDENTITY['display_name']
APP_ID = IDENTITY['app_id']


def unresolved_identity():
    fields = ('publisher', 'website', 'repository_url', 'support_url', 'security_contact', 'license')
    return [*(['name_finalized'] if not IDENTITY['name_finalized'] else []),
            *(field for field in fields if not IDENTITY[field])]
