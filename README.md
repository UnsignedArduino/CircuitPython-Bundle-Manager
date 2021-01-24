# CircuitPython-Bundle-Manager
A Python program that makes it easy to manage modules on a CircuitPython device!

Run [`main.py`](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/blob/main/main.py) to start the program. Make sure that [`bundle_tools`](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/tree/main/bundle_tools) and [`gui_tools`](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/tree/main/gui_tools) is in the same directory and that all [requirements](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/blob/main/requirements.txt) are met!
Note: This will create a bunch of files and directories, so I recommend placing this in its own directory and adding a shortcut or a symlink to the desktop or something like that.

## Table of Contents
1. [Installing](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager#installing)
   1. [Installing from a binary](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager#installing-from-a-binary)
   2. [Installing from source](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager#installing-from-source)
2. [Running](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager#running)
3. [How to use](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager#how-to-use)
4. [Options](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager#options)

## Installing

~~Sooner or later, I will get binaries for Windows and Linux. (Sorry macOS users - I don't have a macOS computer!) For now, you are going to have to install everything manually.~~ Binaries are now available! Check it out [here](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/releases).

### Installing from a binary

No installation is required! (Well, there is no installer. You are still going to have to create a shortcut/symlink to it somewhere and extract it if you are using the directory-based executable)

These binaries were built with [PyInstaller](https://www.pyinstaller.org/).

#### Using the one executable:

1. Download the latest binary from [here](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/releases).
2. Put it somewhere. On Windows, I would put it in `C:\Program Files\CircuitPython Bundle Manager`. On Linux, I would put it in `/usr/bin`.
3. Create a shortcut/symlink to it on the desktop!

Note: If you are having trouble with the one-executable, try the one directory method!
#### Pros of the one-executable
* Convenient - you only need to deal with one executable.
* Easy to install - just place the executable somewhere and create a shortcut.
#### Cons of the one-executable
* Takes quite a while to start compared to the one-directory method.
* Needs to execute code out of the temporary directory, which sometimes isn't allowed on Linux.
* If the application crashes, the support code won't be deleted, so it will take up disk space until the OS clears it.
* Needs more space than the one-directory method.

#### Using the one directory:
1. Download the zip/tar.gz file from [here](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/releases).
2. Extract it. 
3. Place the directory somewhere convenient. On Windows, I would put the extracted files and directories in `C:\Program Files\CircuitPython Bundle Manager`.
4. Create a shortcut/symlink to `CircuitPython Bundle Manager.exe`. (`CircuitPython Bundle Manager` on Linux) It is in the top directory.

#### Pros of the one directory:
* Fast - all the support files are ready, no need to extract them like in the one-executable method.
* Less space - needs less disk space then the one-executable method.
#### Cons of the one directory:
* Slightly annoying to install. 

You can find a detailed description of the one-directory method [here](https://pyinstaller.readthedocs.io/en/stable/operating-mode.html#bundling-to-one-folder) and a description of how the one-file method works [here](https://pyinstaller.readthedocs.io/en/stable/operating-mode.html#bundling-to-one-file).

[Back to table of contents](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager#table-of-contents)

### Installing from source

1. [Download](https://git-scm.com/downloads) and install Git. It does not matter what editor you use for Git's default.
    1. Or...download this repo via the `Download ZIP` option under the green `Code` button. 
2. [Download](https://www.python.org/downloads/) and install Python 3. (Here is [Python 3.9](https://www.microsoft.com/en-us/p/python-39/9p7qfqmjrfp7) on the Microsoft Store) Theoretically, you can use a version as early as 3.6, but I only tested this on 3.7 and 3.9.
    1. Make sure to check `Add Python 3.x to PATH`!
    2. Make sure to also install Tk/Tcl support! If you can access the IDLE, then Tk/Tcl is installed!
3. If you are on Windows, I would also install the [Windows Terminal](https://www.microsoft.com/en-us/p/windows-terminal/9n0dx20hk701) while you are at it.
4. If you installed Git, `cd` into a convenient directory (like the home directory or the desktop) and run:
    ```commandline
    git clone https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager
    cd CircuitPython-Bundle-Manager
    ```
    1. If you downloaded the ZIP, move the downloaded ZIP to somewhere convenient (ex. home directory or desktop), extract it, open a terminal and `cd` into the extracted directory.
5. If you run `dir` (or `ls` on Mac and Linux) you should get something like this:
    1. `dir` (Windows):
    ```commandline
    01/18/2021  08:11 PM    <DIR>          .
    01/18/2021  08:11 PM    <DIR>          ..
    01/18/2021  08:11 PM    <DIR>          bundle_tools
    01/18/2021  08:11 PM            39,625 gui.py
    01/18/2021  08:11 PM    <DIR>          gui_tools
    01/18/2021  08:11 PM               329 main.py
    01/18/2021  08:11 PM             1,949 README.md
    01/18/2021  08:11 PM                18 requirements.txt
                   4 File(s)         41,921 bytes
                   4 Dir(s)  x bytes free
    ```
   2. `ls` (macOS and Linux):
    ```commandline
    bundle_tools  gui.py  gui_tools  main.py  README.md  requirements.txt
    ```
6. If you are going to use a [virtual environment](https://docs.python.org/3/library/venv.html), run the following commands:
    1. Windows:
    ```commandline
    python -m venv .venv
    ".venv/Scripts/activate.bat"
    ```
    2. macOS and Linux:
    ```commandline
    python3 -m venv
    source .venv/bin/activate
    ```
7. Install the packages:
    1. Windows:
    ```commandline
    pip install -r requirements.txt
    ```
    2. macOS and Linux:
    ```commandline
    pip3 install -r requirements.txt
    ```
8. You should now be able to run it!
    1. Windows:
    ```commandline
    python main.py
    ```
    2. macOS and Linux:
    ```commandline
    python3 main.py
    ```

[Back to table of contents](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager#table-of-contents)

## Running
**This only applies if you are installing from source!**
If you are not using a virtual environment, then you can just create a `.bat` file containing `python \path\to\the\main.py` (`python3`, forward slashes, and use `.sh` for the extension on macOS and Linux) on the desktop for convenience. Otherwise, you will need to re-activate the virtual environment everytime you want to run it. I highly recommend using these shell scripts:
1. Windows:
```batch
:: Replace this with the path to the directory of the CircuitPython Bundle Manager, should have main.py in it
cd path\to\the\CircuitPython-Bundle-Manager
:: You can use python.exe or pythonw.exe - the w one will just supress output of the program
".venv\Scripts\pythonw.exe" main.py
```
2. macOS and Linux:
```shell
# Replace with the path to the CircuitPython Bundle Manager
cd path/to/the/CircuitPython-Bundle-Manager
.venv/bin/python3 main.py
```
Don't forget to give the `.sh` file execute permission! (`chmod +x shell_file.sh`)

[Back to table of contents](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager#table-of-contents)
## How to use

Nothing here yet...

[Back to table of contents](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager#table-of-contents)
## Options
You can find these options in `config.json`, which is in the same directory as [`main.py`](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager/blob/main/main.py), and should be auto-generated upon first run. In case it does not happen, this is the default JSON file:
```json
{
    "last_auth_method_used": "username and password",
    "last_circuit_python_bundle_version": "6",
    "show_traceback_in_error_messages": "false",
    "unix_drive_mount_point": "/media"
}
```
- `last_auth_method_used` should be a string of `username and password`, `access token`, or `enterprise`. This is the last method of authentication you used.
- `last_circuitpython_bundle_version` should be a string of a number. This is the last CircuitPython version you used.
- `show_traceback_in_error_messages` should be a string of a bool. (Like `1`, `true`, `yes` for `True` and anything else for `False`) This will control whether stack traces will appear in error messages.
- `unix_drive_mount_point` should be a string of a path that points to the place where your distro automatically mounts drives. Only applies to Unix-based systems.

[Back to table of contents](https://github.com/UnsignedArduino/CircuitPython-Bundle-Manager#table-of-contents)