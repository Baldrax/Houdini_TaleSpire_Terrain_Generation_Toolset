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
    else:
        asset_index_paths = []

    report = f"""Houdini TaleSpire Terrain Generation Toolset Report
=========
VERSIONS
=========
Toolset Version: {version}
Houdini Version: {".".join([str(x) for x in hou.applicationVersion()])}
Platform Info: {hou.applicationPlatformInfo()}

=========
TALESPIRE
=========
TaleSpire Location: {ts_basepath}
TaleSpire Location Valid: {ts_basepath_isdir}
ts_encoding Installed: {ts_encoding_installed}
TaleSpire Asset Paths: {";".join([str(x) for x in asset_index_paths])}


=========
VARIABLES
=========
HTG_BASEDIR: {hou.text.expandString("$HTG_BASEDIR")}
HTTGT_DEV: {hou.text.expandString("$HTTGT_DEV")}
HOUDINI_OTLSCAN_PATH: {hou.text.expandString("$HOUDINI_OTLSCAN_PATH")}
PYTHONPATH: {hou.text.expandString("$PYTHONPATH")}

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

