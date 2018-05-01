# Budgie DDC Brightness Applet

Budgie desktop applet to set screen brightness on external monitors
Requires `ddcutil` to be installed and user to be a member of the `i2c` group.

    # On Debian/Ubuntu based distros
    sudo apt install ddcutil
    sudo usermod -G i2c -a $USER

Install `BudgieDdcBrightness.plugin` and `budgieddcbrightness.py` to `~/.local/share/budgie-desktop/plugins/budgieddcbrightness`