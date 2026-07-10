"""
Build a double-clickable ToonTrack.app with py2app.

    pip3 install -r requirements.txt py2app
    python3 setup.py py2app
"""

from setuptools import setup

APP = ["toonhq_invasion_tracker.py"]
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "ToonTrack.icns",
    "packages": ["rumps", "requests"],
    "plist": {
        "CFBundleName": "ToonTrack",
        "CFBundleDisplayName": "ToonTrack",
        "CFBundleIdentifier": "com.toontrack.invasion-tracker",
        "CFBundleVersion": "1.2.1",
        "CFBundleShortVersionString": "1.2.1",
        "LSUIElement": True,
        "NSHumanReadableCopyright": "Unofficial fan tool — not affiliated with Toontown Rewritten or ToonHQ.",
    },
}

setup(
    name="ToonTrack",
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
