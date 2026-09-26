"""Central public identity. Unresolved fields are absent, never invented."""
import json
from pathlib import Path

IDENTITY = json.loads(Path(__file__).with_name('identity.json').read_text())
DISPLAY_NAME = IDENTITY['display_name']
APP_ID = IDENTITY['application_id']
DEVELOPER_ID = IDENTITY['developer_id']
PUBLISHER = IDENTITY['publisher']
TAGLINE = IDENTITY['tagline']
EXECUTABLE_NAME = IDENTITY['executable_name']
VERSION = IDENTITY['version']
LICENSE = IDENTITY['license']
COPYRIGHT = IDENTITY['copyright']


def planned_urls(identity=None):
    """Approved targets only; this does not assert remote existence."""
    identity = IDENTITY if identity is None else identity
    repository = identity.get('repository_url')
    return {'repository_url': repository,
            'homepage_url': identity.get('homepage_url') or
                (repository if identity.get('homepage_strategy') == 'repository' else None),
            'support_url': identity.get('support_url') or
                (repository.rstrip('/') + '/issues' if repository and identity.get('support_strategy') == 'github_issues' else None)}


def public_urls(identity=None):
    """Expose verified metadata links; private repositories still require access."""
    identity = IDENTITY if identity is None else identity
    targets = planned_urls(identity)
    created = identity.get('remote_repository_created') is True
    return {key: value if created and (key == 'repository_url' or identity.get(
                {'homepage_url': 'homepage_reachable', 'support_url': 'support_reachable'}.get(key)) is True) else None
            for key, value in targets.items()}


def unresolved_identity():
    fields = ('publisher', 'developer_id', 'security_contact', 'license')
    return [*(['application_id_finalized'] if not IDENTITY['application_id_finalized'] else []),
            *(['name_finalized'] if not IDENTITY['name_finalized'] else []),
            *(field for field in fields if not IDENTITY.get(field)),
            *(field for field, value in public_urls().items() if not value),
            *(['security_reporting_configured'] if not IDENTITY['security_reporting_configured'] else [])]
