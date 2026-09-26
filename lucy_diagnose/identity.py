"""Central public identity. Unresolved fields are absent, never invented."""
import json
from pathlib import Path

IDENTITY = json.loads(Path(__file__).with_name('identity.json').read_text())
DISPLAY_NAME = IDENTITY['display_name']
APP_ID = IDENTITY['application_id']
PUBLISHER = IDENTITY['publisher']
TAGLINE = IDENTITY['tagline']
EXECUTABLE_NAME = IDENTITY['executable_name']
VERSION = IDENTITY['version']


def unresolved_identity():
    fields = ('publisher', 'homepage_url', 'repository_url', 'support_url', 'security_contact', 'license')
    return [*(['application_id_finalized'] if not IDENTITY['application_id_finalized'] else []),
            *(['name_finalized'] if not IDENTITY['name_finalized'] else []),
            *(field for field in fields if not IDENTITY[field])]
