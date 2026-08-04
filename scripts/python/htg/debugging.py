import sys

import hou

from pathlib import Path

from htg.version import version
import htg.configs as ts_configs
import htg.nodes.common as ts_common
from htg.utils import copy_to_clipboard

try:
    import ts_encoding
    from ts_encoding.assets import get_asset_index_paths
    ts_encoding_installed = True
except ImportError:
    ts_encoding_installed = False


TAB_LINE: str = "\n\t"

def scrub_path(path) -> str:
    """Removes user info from paths."""

    username = hou.text.expandString("$USER")
    return str(path).replace(username, "<username>")


def debug_report():
    """
    Displays a simple report that a user can submit with a bug report to give some context on their installation and
    environment.
    """

    cfg = ts_configs.Configs()
    ts_basepath = Path(cfg.get_config('talespire_directory'))
    ts_basepath_isdir = ts_basepath.is_dir()

    if ts_basepath_isdir and ts_encoding_installed:
        asset_index_paths = get_asset_index_paths(ts_basedir=ts_basepath)
        asset_path_str = TAB_LINE + TAB_LINE.join([str(scrub_path(x)) for x in asset_index_paths])
    else:
        asset_index_paths = []
        asset_path_str = ""

    report = f"""Houdini TaleSpire Terrain Generation Toolset Report
=========
VERSIONS
=========
Toolset Version: {version}
Houdini Version: {".".join([str(x) for x in hou.applicationVersion()])}
Python Version: {sys.version}
Platform Info: {hou.applicationPlatformInfo()}

=========
TALESPIRE
=========
TaleSpire Location: {scrub_path(ts_basepath)}
TaleSpire Location Valid: {ts_basepath_isdir}
ts_encoding Installed: {ts_encoding_installed}
TaleSpire Asset Paths: {asset_path_str}

=========
VARIABLES
=========
HTG_BASEDIR: {scrub_path(hou.text.expandString("$HTG_BASEDIR"))}
HTTGT_DEV: {hou.text.expandString("$HTTGT_DEV")}
HOUDINI_OTLSCAN_PATH: {scrub_path(hou.text.expandString("$HOUDINI_OTLSCAN_PATH"))}
PYTHONPATH: {scrub_path(hou.text.expandString("$PYTHONPATH"))}
HOUDINI_PATH: {TAB_LINE}{TAB_LINE.join([scrub_path(x) for x in hou.houdiniPath()])}

=========
STATES
=========
Network Loading: {ts_common.network_loading()}

"""

    result = hou.ui.displayMessage(
        "Debugging Information:",
        buttons=("Copy to Clipboard", "OK"),
        default_choice=1,
        details=report,
        details_expanded=True)

    if result == 0:
        copy_to_clipboard(report)

