"""Single source of color tokens for GTK CSS and all six graph renderers."""

from dataclasses import dataclass

DEFAULT_THEME = 'system'


@dataclass(frozen=True)
class Theme:
    id: str
    name: str
    category: str
    mode: str
    colors: dict


DARK = dict(background='#18191c', panel='#25262b', elevated='#2e3036', text='#f2f3f5', muted='#bec2cb',
            primary='#80d2c2', secondary='#c3b3ed', accent_bg='#246659', ok='#8be0af', info='#94d4ff',
            warning='#ffd18b', error='#ff9fa6', grid='#555966')
LIGHT = dict(background='#f6f6f8', panel='#ffffff', elevated='#ebecf1', text='#202126', muted='#555865',
             primary='#64429b', secondary='#3d6289', accent_bg='#64429b', ok='#176342', info='#185782',
             warning='#784800', error='#ad2434', grid='#b5b8c4')


def variant(**colors):
    return {**DARK, **colors}


THEMES = {
    t.id: t for t in (
        Theme('system', 'System', 'System', 'system', {}),
        Theme('dark', 'Dark', 'System', 'dark', DARK),
        Theme('light', 'Light', 'System', 'light', LIGHT),
        Theme('arcanum', 'Arcanum', 'Signature', 'dark', variant(
            background='#121014', panel='#211c28', elevated='#302438', primary='#ef79dc', secondary='#bb9bff',
            accent_bg='#972b88', text='#f7f0fa', muted='#c5b8cd', grid='#55445f')),
        Theme('slate', 'Slate', 'Workstation', 'dark', variant(background='#171b20', panel='#242b33', primary='#becbdb', secondary='#9ab6c3', accent_bg='#4a6075')),
        Theme('ion', 'Ion', 'Workstation', 'dark', variant(background='#111a1d', panel='#1b2b30', primary='#75e0dc', secondary='#b0c7ff', accent_bg='#206968')),
        Theme('verdant', 'Verdant', 'Workstation', 'dark', variant(background='#141b17', panel='#222e26', primary='#a0dfaa', secondary='#d6d595', accent_bg='#3a6744')),
        Theme('frostline', 'Frostline', 'Workstation', 'light', {**LIGHT, 'background': '#edf3f5', 'panel': '#fafcfd', 'primary': '#346174', 'secondary': '#596b86', 'accent_bg': '#346174'}),
        Theme('ember', 'Ember', 'Creative', 'dark', variant(background='#1d1513', panel='#30241f', primary='#ffb184', secondary='#e8bd98', accent_bg='#95502e')),
        Theme('nocturne', 'Nocturne', 'Creative', 'dark', variant(background='#15141e', panel='#242133', primary='#c2afff', secondary='#e1a6d0', accent_bg='#67538b')),
        Theme('cinder', 'Cinder', 'Creative', 'dark', variant(background='#191818', panel='#292626', primary='#dfb3a5', secondary='#d8c0a4', accent_bg='#795048')),
        Theme('mauveglass', 'Mauveglass', 'Creative', 'light', {**LIGHT, 'background': '#f4eff4', 'panel': '#fffaff', 'primary': '#825073', 'secondary': '#655684', 'accent_bg': '#825073'}),
        Theme('midnight-circuit', 'Midnight Circuit', 'Creative', 'dark', variant(background='#111717', panel='#1c2827', primary='#91e3bc', secondary='#b9abf4', accent_bg='#376657')),
    )
}
CATEGORIES = ('System', 'Signature', 'Workstation', 'Creative')
SEVERITY_ICONS = {'ok': '✓ OK', 'info': 'ⓘ INFO', 'warning': '⚠ WARN', 'error': '✕ ERROR', 'unavailable': '○ UNAVAILABLE'}


def normalize_theme(value):
    key = value.strip().lower().replace(' ', '-') if isinstance(value, str) else ''
    return key if key in THEMES else DEFAULT_THEME


def palette(theme_id, system_dark=False, system_accent=None):
    theme = THEMES[normalize_theme(theme_id)]
    result = dict((DARK if system_dark else LIGHT) if theme.mode == 'system' else theme.colors)
    if theme.mode == 'system':
        result['primary'] = system_accent or ('#99c1f1' if system_dark else '#1c71d8')
        result['secondary'] = result['primary']
    return result


def rgb(color):
    return tuple(int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))


def graph_color(colors, metric):
    return colors[{'cpu': 'primary', 'cpu_temp': 'secondary', 'ram': 'ok', 'gpu': 'secondary',
                   'gpu_temp': 'warning', 'vram': 'primary'}[metric]]


GRAPH_LIMITS = {'cpu': (85, None, 'Busy'), 'gpu': (85, None, 'Busy'), 'cpu_temp': (90, 100, 'Hot'),
                'gpu_temp': (85, 95, 'Hot'), 'ram': (90, 98, 'High'), 'vram': (90, 98, 'High')}


def graph_state(metric, value, paused=False):
    if paused:
        return 'info', 'Ⅱ PAUSED · last sample'
    if value is None:
        return 'unavailable', '○ NO MEASUREMENT'
    warning, error, text = GRAPH_LIMITS[metric]
    if error is not None and value >= error:
        return 'error', f'✕ {text.upper()} · review reading'
    if value >= warning:
        return ('info' if error is None else 'warning'), f'⚠ {text.upper()} · guide threshold'
    return 'info', '● LIVE'
