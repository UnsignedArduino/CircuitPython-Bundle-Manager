# CircuitPython-Bundle-Manager
A Python program that makes it easy to manage modules on a CircuitPython device!

Run [`main.py`](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/blob/main/main.py) to start the program. Make sure that [`bundle_tools`](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/tree/main/bundle_tools) and [`gui_tools`](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/tree/main/gui_tools) is in the same directory and that all [requirements](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/blob/main/requirements.txt) are met!
Note: This will create a bunch of files and directories, so I recommend placing this in its own directory and adding a shortcut or a symlink to the desktop or something like that.

## Options
You can find these options in `config.json`, which is in the same directory as [`main.py`](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/blob/main/main.py), and should be auto-generated upon first run. In case it does not happen, this is the default JSON file:
```json
{
    "last_auth_method_used": "username and password",
    "last_circuitpython_bundle_version": "6",
    "show_traceback_in_error_messages": "false",
    "unix_drive_mount_point": "/media"
}
```
`last_auth_method_used` should be a string of `username and password`, `access token`, or `enterprise`. This is the last method of authentication you used.

`last_circuitpython_bundle_version` should be a string of a number. This is the last CircuitPython version you used.

`show_traceback_in_error_messages` should be a string of a bool. (Like `1`, `true`, `yes` for `True` and anything else for `False`) This will control whether stack traces will appear in error messages.

`unix_drive_mount_point` should be a string of a path that points to the place where your distro automatically mounts drives. Only applies to Unix-based systems.