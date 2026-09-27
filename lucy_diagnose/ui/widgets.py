"""Native widgets shared by the unified dashboard."""
import math

from gi.repository import Gtk, Pango

from ..telemetry import METRICS
from ..themes.catalog import GRAPH_LIMITS, graph_color, graph_state, rgb


def set_expander_content(expander, child):
    title = expander.get_label()
    if title:
        expander.set_label_widget(label(title, wrap=True))
        accessible_name(expander, title)
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


def wrap_check_button(button):
    text = button.get_label()
    button.set_label(None)
    button.set_child(label(text, wrap=True))
    accessible_name(button, text)


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


def overview_note(text):
    """Keep the dashboard concise while preserving the complete note as a tooltip."""
    if not text:
        return 'No measurement'
    for marker in (' · Partial sandbox-visible', '. This diagnostic is restricted'):
        if marker in text:
            text = text.split(marker, 1)[0]
    return text.strip() or 'No measurement'


class GaugeCard(Gtk.Box):
    """Compact live metric with a semicircular gauge and text-first fallback."""

    def __init__(self, key, history, themes, embedded=False):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.key, self.history = key, history
        self.themes, self.paused, self.latest_value = themes, False, None
        self.embedded = embedded
        self.add_css_class('gauge-card')
        self.add_css_class('gauge-embedded' if embedded else 'metric-card')
        self.set_size_request(205 if not embedded else 230, -1)

        title = label(METRICS[key][0], 'gauge-title')
        self.append(title)

        overlay = Gtk.Overlay(hexpand=True)
        self.gauge = Gtk.DrawingArea(content_height=128, hexpand=True)
        accessible_name(self.gauge, METRICS[key][0] + ' gauge; current value is also shown as text')
        self.gauge.set_draw_func(self.draw_gauge)
        overlay.set_child(self.gauge)

        readout = box(spacing=2)
        readout.set_halign(Gtk.Align.CENTER)
        readout.set_valign(Gtk.Align.CENTER)
        readout.set_margin_top(32)
        self.value = label('—', 'gauge-value')
        self.value.set_xalign(.5)
        readout.append(self.value)
        self.state_label = label('○ NO MEASUREMENT', 'graph-state')
        self.state_label.set_xalign(.5)
        readout.append(self.state_label)
        overlay.add_overlay(readout)
        self.append(overlay)

        self.note = label('Waiting for a sample', 'caption', True)
        self.note.set_max_width_chars(34)
        self.note.set_lines(2)
        self.note.set_ellipsize(Pango.EllipsizeMode.END)
        self.append(self.note)
        themes.listeners.append(self.theme_changed)

    @property
    def ceiling(self):
        return 110 if self.key.endswith('_temp') else 100

    def theme_changed(self):
        self.gauge.queue_draw()

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
        self.value.set_text(f'{value:.1f} {unit}' if value is not None else 'N/A')
        note = sample.notes.get(self.key, 'No measurement')
        self.note.set_text(overview_note(note))
        self.note.set_tooltip_text(note)
        self.gauge.set_tooltip_text(
            f'{METRICS[self.key][0]} · guide {GRAPH_LIMITS[self.key][0]}' +
            (f' / {GRAPH_LIMITS[self.key][1]}' if GRAPH_LIMITS[self.key][1] else '') +
            f' {unit} · unavailable values are shown as gaps')
        self.gauge.queue_draw()

    def draw_gauge(self, _, cr, width, height):
        colors = self.themes.colors
        center_x, center_y = width / 2, height * .88
        radius = max(28, min(width * .40, height * .68))
        start, end = math.pi, 2 * math.pi

        cr.set_line_width(12)
        cr.set_source_rgba(*rgb(colors['grid']), .42)
        cr.arc(center_x, center_y, radius, start, end)
        cr.stroke()

        # Small ticks improve quick scanning without turning the gauge into a dial.
        cr.set_line_width(1)
        cr.set_source_rgba(*rgb(colors['muted']), .50)
        for index in range(11):
            angle = start + (end - start) * index / 10
            inner = radius - 18
            outer = radius - 10
            cr.move_to(center_x + math.cos(angle) * inner, center_y + math.sin(angle) * inner)
            cr.line_to(center_x + math.cos(angle) * outer, center_y + math.sin(angle) * outer)
        cr.stroke()

        value = self.latest_value
        if value is None:
            return
        fraction = max(0., min(1., value / self.ceiling))
        warning, error, _ = GRAPH_LIMITS[self.key]
        color = graph_color(colors, self.key)
        if error is not None and value >= error:
            color = colors['error']
        elif error is not None and value >= warning:
            color = colors['warning']

        cr.set_line_width(12)
        cr.set_source_rgb(*rgb(color))
        cr.arc(center_x, center_y, radius, start, start + math.pi * fraction)
        cr.stroke()


class GpuMetricCard(Gtk.Box):
    """One wide GPU surface instead of three repetitive unavailable cards."""

    def __init__(self, history, themes):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.history, self.themes, self.paused = history, themes, False
        self.add_css_class('metric-card')
        self.add_css_class('gpu-card')

        heading = box(Gtk.Orientation.HORIZONTAL, 8)
        title = label('NVIDIA GPU', 'gauge-title')
        title.set_hexpand(True)
        heading.append(title)
        self.status = label('○ NO MEASUREMENT', 'graph-state')
        heading.append(self.status)
        self.append(heading)

        body = box(Gtk.Orientation.HORIZONTAL, 14)
        self.utilization = GaugeCard('gpu', history, themes, embedded=True)
        self.utilization.set_hexpand(True)
        body.append(self.utilization)

        stats = Gtk.Grid(column_spacing=8, row_spacing=8, column_homogeneous=True, hexpand=True)
        self.temp_value, self.temp_note = self._stat(stats, 0, 'GPU temperature')
        self.vram_value, self.vram_note = self._stat(stats, 1, 'VRAM')
        body.append(stats)
        self.append(body)

        self.note = label('Waiting for a GPU sample', 'caption', True)
        self.append(self.note)

    def _stat(self, grid, column, title_text):
        panel = box(spacing=3)
        panel.add_css_class('gpu-stat')
        panel.append(label(title_text, 'dim-label'))
        value = label('N/A', 'gpu-stat-value')
        panel.append(value)
        note = label('No measurement', 'caption', True)
        note.set_max_width_chars(28)
        note.set_lines(2)
        note.set_ellipsize(Pango.EllipsizeMode.END)
        panel.append(note)
        grid.attach(panel, column, 0, 1, 1)
        return value, note

    def set_paused(self, paused):
        self.paused = paused
        self.utilization.set_paused(paused)
        (self.add_css_class if paused else self.remove_css_class)('paused')
        self._update_status()

    def _update_status(self):
        for name in ('ok', 'info', 'warning', 'error', 'unavailable'):
            self.status.remove_css_class('indicator-' + name)
        if self.paused:
            status, text = 'info', 'Ⅱ PAUSED'
        elif self.utilization.latest_value is None:
            status, text = 'unavailable', '○ TELEMETRY UNAVAILABLE'
        else:
            status, text = 'info', '● LIVE'
        self.status.add_css_class('indicator-' + status)
        self.status.set_text(text)

    def refresh(self, sample):
        self.utilization.refresh(sample)
        self._update_status()

        temp = sample.values['gpu_temp']
        self.temp_value.set_text(f'{temp:.1f} °C' if temp is not None else 'N/A')
        temp_note = sample.notes.get('gpu_temp', 'No measurement')
        self.temp_note.set_text(overview_note(temp_note))
        self.temp_note.set_tooltip_text(temp_note)

        vram = sample.values['vram']
        self.vram_value.set_text(f'{vram:.1f} %' if vram is not None else 'N/A')
        vram_note = sample.notes.get('vram', 'No measurement')
        self.vram_note.set_text(overview_note(vram_note))
        self.vram_note.set_tooltip_text(vram_note)

        gpu_note = sample.notes.get('gpu', 'GPU telemetry unavailable')
        self.note.set_text(overview_note(gpu_note))
        self.note.set_tooltip_text(gpu_note)


# Compatibility alias for extensions that imported the original class name.
MetricCard = GaugeCard
