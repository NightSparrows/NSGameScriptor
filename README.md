# NSGameScriptor
 
Require python 3.11.2

## Windows

```bat
"../toolkit/python/python.exe" -m pip install -r requirements.txt
run.bat        REM CLI
run_gui.bat    REM GUI
```

## Linux

```sh
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.txt
./run.sh        # CLI
./run_gui.sh    # GUI
```

adb is resolved from `../toolkit/adb/adb(.exe)` if present, otherwise from `adb`/`adb.exe` on `PATH` (e.g. Android SDK platform-tools). MuMu Player emulator lifecycle management (`emulator: 1` in config) is Windows-only; on Linux use `emulator: 0` and point `device` at whatever adb target your emulator/device exposes, with `screencap: 2` (ADB, via `adbutils` - no native deps).
