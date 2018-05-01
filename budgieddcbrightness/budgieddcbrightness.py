#!/usr/bin/env python3
import subprocess
import dbus
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

        # Panel Button
        self.box = Gtk.EventBox()
        self.icon = Gtk.Image.new_from_icon_name(
            "display-brightness-symbolic",
            Gtk.IconSize.MENU)
        self.box.add(self.icon)
        self.box.set_tooltip_text("Screen Brightness")
        self.add(self.box)

        # Popover
        self.popover = Budgie.Popover.new(self.box)
        self.popover.get_style_context().add_class("ddc-brightness-popover")
        self.popover.set_default_size (200, 80)
        layout = Gtk.Grid()
        layout.set_border_width(6)

        adjustment = Gtk.Adjustment(50, 0, 100, 5, 0, 0)

        self.scale = DiscreteScale(list(range(5,105,5)), 
            orientation=Gtk.Orientation.HORIZONTAL, 
            adjustment=adjustment)
        self.set_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.scale.set_draw_value(False)

        self.scale.set_vexpand(True)
        self.scale.set_hexpand(True)

        self.scale.add_mark(5, Gtk.PositionType.LEFT, '5')
        for i in range(25, 125, 25):
            self.scale.add_mark(i, Gtk.PositionType.LEFT, str(i))

        layout.add(self.scale)

        self.popover.add(layout)

        self.popover.get_child().show_all()
        self.box.show_all()
        self.show_all()

        # Connect signals
        self.scale.connect("button-release-event", self.button_released)
        self.box.connect("button-press-event", self._on_press)

        self.scale.set_value(self.get_brightness())

    def button_released(self, *args, **kwargs):
        self.set_brightness(self.scale.get_value())
        return True 

    def do_supports_settings(self):
        return False

    def do_update_popovers(self, manager):
        manager.register_popover(self.box, self.popover)
        self.manager = manager

    def get_brightness(self):
        # Example:
        # "VCP 10 C 50 100"
        _, _, _, value, maximum = subprocess.check_output(
            ['ddcutil', '-t', 'getvcp', '10'], 
            encoding='utf8').split()
        value = int(value)
        self.update_icon(value)
        return value

    def set_brightness(self, value):
        subprocess.call(['ddcutil' ,'setvcp', '10', str(value)])
        self.update_icon(value)

    def update_icon(self, value):
        if value <= 10:
            icon = "display-brightness-off-symbolic"
        elif value <= 25:
            icon = "display-brightness-low-symbolic"
        elif value <= 75:
            icon = "display-brightness-medium-symbolic"
        else:
            icon = "display-brightness-high-symbolic"

        self.icon.set_from_icon_name(icon, Gtk.IconSize.BUTTON)

    def	_on_press(self, box, e):
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


class DiscreteScale(Gtk.Scale):
    """ CC-By-SA https://stackoverflow.com/a/39036673 """
    def __init__(self, values, *args, **kwargs):
        super().__init__(*args, **kwargs)

        values.sort()
        self.previous_value = None
        self.values= values

        adjustment= self.get_adjustment()
        adjustment.set_lower(values[0])
        adjustment.set_upper(values[-1])

        self.__changed_value_id= self.connect('change-value', self.__change_value)

    def get_value(self, *args, **kwargs):
        return self.__closest_value(super().get_value())

    def set_value(self, value, scroll_type=None):
        self.handler_block(self.__changed_value_id)
        if scroll_type is None:
            super().set_value(value)
        else:
            self.emit('change-value', scroll_type, value)
        self.handler_unblock(self.__changed_value_id)

    def __change_value(self, scale, scroll_type, value):
        # find the closest valid value
        value = self.__closest_value(value)
        self.set_value(value, scroll_type)
        return True #prevent the signal from escalating


    def __closest_value(self, value):
        return min(self.values, key=lambda v:abs(value-v))


if __name__ == '__main__':
    import uuid

    win = Gtk.Window()

    ba = BudgieDdcBrightnessApplet(uuid.uuid4())
    ba.do_update_popovers(Budgie.PopoverManager())
    # setup an instance with config
    win.add(ba)
    win.show_all()
    Gtk.main()
