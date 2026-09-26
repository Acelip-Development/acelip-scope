"""Native widgets shared by the unified dashboard."""
from gi.repository import Gtk, Pango
from ..telemetry import METRICS


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
    def __init__(self, key, history):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.key, self.history = key, history
        self.add_css_class('metric-card')
        self.set_size_request(175, -1)
        self.append(label(METRICS[key][0], 'dim-label'))
        self.value = label('—', 'metric-value')
        self.append(self.value)
        self.graph = Gtk.DrawingArea(content_height=46, hexpand=True)
        self.graph.set_draw_func(self.draw)
        self.graph.set_tooltip_text(f'{METRICS[key][0]} · last two minutes; gaps mean no measurement')
        self.append(self.graph)
        self.note = label('Waiting for a sample', 'caption', True)
        self.note.set_max_width_chars(27)
        self.note.set_lines(2)
        self.note.set_ellipsize(Pango.EllipsizeMode.END)
        self.append(self.note)

    def refresh(self, sample):
        value, unit = sample.values[self.key], METRICS[self.key][1]
        self.value.set_text(f'{value:.1f} {unit}' if value is not None else 'Unavailable')
        note = sample.notes.get(self.key, 'No measurement')
        self.note.set_text(note)
        self.note.set_tooltip_text(note)
        self.graph.queue_draw()

    def draw(self, _, cr, width, height):
        samples = list(self.history.samples)
        cr.set_source_rgba(.65, .70, .82, .12)
        cr.set_line_width(1)
        for frac in (.25, .75):
            cr.move_to(0, height * frac)
            cr.line_to(width, height * frac)
        cr.stroke()
        if not samples:
            return
        ceiling = 110 if self.key.endswith('_temp') else 100
        valid = [s.values[self.key] for s in samples if s.values[self.key] is not None]
        ceiling = max(ceiling, max(valid, default=0))
        end = samples[-1].observed_at.timestamp()
        active, last_time = False, None
        cr.set_source_rgb(*((.97, .72, .43) if self.key.endswith('_temp') else (.57, .78, .95)))
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
