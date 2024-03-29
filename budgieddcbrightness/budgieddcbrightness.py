#!/usr/bin/env python3
# TODO does not work with arrow keys
import re
import subprocess
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Budgie', '1.0')
from gi.repository import Budgie, Gdk, Gio, GLib, GObject, Gtk


class BudgieDdcBrightness(GObject.Object, Budgie.Plugin):
    __gtype_name__ = "budgie-ddc-brightness-applet"

    def __init__(self):
        GObject.Object.__init__(self)

    def do_get_panel_widget(self, uuid):
        return BudgieDdcBrightnessApplet(uuid)


class BudgieDdcBrightnessApplet(Budgie.Applet):
    def __init__(self, uuid):
        Budgie.Applet.__init__(self)
        self.uuid = uuid
        self.manager = None
        self.displays = self.detect_displays()

        # Panel Button
        self.box = Gtk.EventBox()
        self.icon = Gtk.Image.new_from_icon_name(
            "display-brightness-symbolic",
            Gtk.IconSize.MENU)
        self.icon.use_fallback = True
        self.box.add(self.icon)
        self.box.set_tooltip_text("Screen Brightness")
        self.add(self.box)

        # Popover
        self.popover = Budgie.Popover.new(self.box)
        self.popover.get_style_context().add_class("ddc-brightness-popover")
        self.popover.set_default_size (200, 80)
        layout = Gtk.Grid()
        layout.set_border_width(6)

        self.set_events(Gdk.EventMask.BUTTON_RELEASE_MASK)

        adjustment = Gtk.Adjustment(50, 5, 100, 5, 0, 0)

        self.scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=adjustment)

        self.scale.set_draw_value(False)

        self.scale.set_vexpand(True)
        self.scale.set_hexpand(True)

        for mark in (0, 25, 50, 75, 100):
            self.scale.add_mark(mark, Gtk.PositionType.LEFT, str(mark))

        # Connect signals
        self.scale.connect("button-release-event", self.button_released)

        self.brightness = self.get_brightness()
        self.scale.set_value(self.brightness)

        layout.attach(self.scale, 0, 0, 1, 1)

        self.popover.add(layout)

        self.popover.get_child().show_all()
        self.box.show_all()
        self.show_all()

        self.box.connect("button-press-event", self._on_press)

    def button_released(self, scale, event):
        brightness = int(self.scale.get_value())
        self.set_brightness(brightness)
        return True

    def detect_displays(self):
        out = subprocess.check_output(['ddcutil', 'detect'], encoding='utf8')
        displays = [d for d in re.findall('Display ([1-9])', out)]
        return displays

    def do_supports_settings(self):
        return False

    def do_update_popovers(self, manager):
        manager.register_popover(self.box, self.popover)
        self.manager = manager

    def get_brightness(self):
        # Example:
        # "VCP 10 C 50 100"
        values = []
        for d in self.displays:
            _, _, _, value, maximum = subprocess.check_output(
                ['ddcutil', '-d', d, '-t', 'getvcp', '10'],
                encoding='utf8').split()
            values.append(int(value))
        value = max(values)
        self.update_icon(value)
        return value

    def set_brightness(self, value):
        self.popover.hide()
        for d in self.displays:
            self.brightness = value
            self.update_icon(value)
            args = ['ddcutil', '-d', d, 'setvcp', '10', str(value)]
            subprocess.call(args)

    def update_icon(self, value):
        if value <= 25:
            icon = "display-brightness-low-symbolic"
        elif value <= 75:
            icon = "display-brightness-medium-symbolic"
        else:
            icon = "display-brightness-high-symbolic"

        self.icon.set_from_icon_name(icon, Gtk.IconSize.BUTTON)

    def _on_press(self, box, e):
        # Ignore anything other than left or middle click
        if e.button not in [1, 2]:
            return Gdk.EVENT_PROPAGATE

        # If middle button clicked, set max brightness
        elif e.button == 2:
            self.set_brightness(100)
            self.scale.set_value(100)
            return Gdk.EVENT_STOP

        # Show / hide popover
        if self.popover.get_visible():
            self.popover.hide()
        else:
            self.manager.show_popover(self.box)
        return Gdk.EVENT_STOP


if __name__ == '__main__':
    import uuid

    win = Gtk.Window()

    ba = BudgieDdcBrightnessApplet(uuid.uuid4())
    ba.do_update_popovers(Budgie.PopoverManager())
    # setup an instance with config
    win.add(ba)
    win.show_all()
    Gtk.main()
