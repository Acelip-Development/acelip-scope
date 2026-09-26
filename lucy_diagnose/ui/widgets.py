"""Native widgets shared by the unified dashboard."""
from gi.repository import Gtk, Pango
from ..telemetry import METRICS
from ..themes.catalog import GRAPH_LIMITS, graph_color, graph_state, rgb


def set_expander_content(expander, child):
    # Collapsed content can be unrooted by GTK. Keep it out of keyboard focus
    # traversal until expanded, rather than sending focus into a detached tree.
    child.set_visible(expander.get_expanded())
    expander.set_child(child)
    expander.connect('notify::expanded', lambda widget, _: child.set_visible(widget.get_expanded()))


def accessible_name(widget, name):
    widget.update_property([Gtk.AccessibleProperty.LABEL], [name])
    return widget


def label(text='', css=None, wrap=False):
    widget = Gtk.Label(label=text, xalign=0, wrap=wrap)
    widget.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
    if css:
        widget.add_css_class(css)
    return widget


def box(orientation=Gtk.Orientation.VERTICAL, spacing=10):
    return Gtk.Box(orientation=orientation, spacing=spacing)


def padded(widget, amount=20):
    for side in ('top', 'bottom', 'start', 'end'):
        getattr(widget, f'set_margin_{side}')(amount)
    return widget


def clear(container):
    while container.get_first_child():
        container.remove(container.get_first_child())


def text_view(text='', height=220):
    view = Gtk.TextView(editable=False, cursor_visible=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR)
    for side in ('left', 'right', 'top', 'bottom'):
        getattr(view, f'set_{side}_margin')(12)
    view.get_buffer().set_text(text)
    scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True, min_content_height=height)
    scroll.set_child(view)
    scroll.add_css_class('report-view')
    return scroll, view


class MetricCard(Gtk.Box):
    def __init__(self, key, history, themes):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.key, self.history = key, history
        self.themes, self.paused, self.latest_value = themes, False, None
        self.add_css_class('metric-card')
        self.set_size_request(175, -1)
        self.append(label(METRICS[key][0], 'dim-label'))
        self.value = label('—', 'metric-value')
        self.append(self.value)
        self.state_label = label('○ NO MEASUREMENT', 'graph-state')
        self.append(self.state_label)
        self.graph = Gtk.DrawingArea(content_height=46, hexpand=True)
        accessible_name(self.graph, METRICS[key][0] + ' history; current value is shown as text')
        self.graph.set_draw_func(self.draw)
        self.graph.set_tooltip_text(f'{METRICS[key][0]} · last two minutes; gaps mean no measurement')
        self.append(self.graph)
        self.note = label('Waiting for a sample', 'caption', True)
        self.note.set_max_width_chars(27)
        self.note.set_lines(2)
        self.note.set_ellipsize(Pango.EllipsizeMode.END)
        self.append(self.note)
        themes.listeners.append(self.theme_changed)

    def theme_changed(self):
        self.graph.queue_draw()

    def set_paused(self, paused):
        self.paused = paused
        (self.add_css_class if paused else self.remove_css_class)('paused')
        self.refresh_state()

    def refresh_state(self):
        status, text = graph_state(self.key, self.latest_value, self.paused)
        for name in ('ok', 'info', 'warning', 'error', 'unavailable'):
            self.state_label.remove_css_class('indicator-' + name)
        self.state_label.add_css_class('indicator-' + status)
        self.state_label.set_text(text)

    def refresh(self, sample):
        value, unit = sample.values[self.key], METRICS[self.key][1]
        self.latest_value = value
        self.refresh_state()
        self.value.set_text(f'{value:.1f} {unit}' if value is not None else 'Unavailable')
        note = sample.notes.get(self.key, 'No measurement')
        self.note.set_text(note)
        self.note.set_tooltip_text(note)
        self.graph.queue_draw()

    def draw(self, _, cr, width, height):
        samples = list(self.history.samples)
        colors = self.themes.colors
        cr.set_source_rgba(*rgb(colors['grid']), .6)
        cr.set_line_width(1)
        for frac in (.25, .75):
            cr.move_to(0, height * frac)
            cr.line_to(width, height * frac)
        cr.stroke()
        ceiling = 110 if self.key.endswith('_temp') else 100
        valid = [s.values[self.key] for s in samples if s.values[self.key] is not None]
        ceiling = max(ceiling, max(valid, default=0))
        # Dashed guide lines are labeled in the tooltip, not diagnostic assertions.
        warning, error, _ = GRAPH_LIMITS[self.key]
        self.graph.set_tooltip_text(f'{METRICS[self.key][0]} · 2 min · guide {warning}' +
                                   (f' / {error}' if error else '') + f' {METRICS[self.key][1]} · gaps: unavailable')
        cr.set_dash([3, 4])
        for value, color in ((warning, 'warning'), (error, 'error')):
            if value is not None:
                cr.set_source_rgba(*rgb(colors[color]), .6)
                y = height - 3 - value / ceiling * (height - 6)
                cr.move_to(0, y)
                cr.line_to(width, y)
                cr.stroke()
        cr.set_dash([])
        if not samples:
            return
        end = samples[-1].observed_at.timestamp()
        active, last_time = False, None
        cr.set_source_rgb(*rgb(graph_color(colors, self.key)))
        cr.set_line_width(2)
        for sample in samples:
            value, at = sample.values[self.key], sample.observed_at.timestamp()
            if value is None or end - at > 120:
                active = False
                continue
            x = width * (1 - (end - at) / 120)
            y = height - 3 - max(0, min(1, value / ceiling)) * (height - 6)
            if active and last_time is not None and at - last_time <= 5:
                cr.line_to(x, y)
            else:
                cr.move_to(x, y)
            active, last_time = True, at
        cr.stroke()
