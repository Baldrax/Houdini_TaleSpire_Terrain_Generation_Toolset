import hou
import json

from pathlib import Path

# Pane Navigation
def get_current_pane(node=None):
    """Try to Return the currently active Houdini pane."""
    panetabs = hou.ui.currentPaneTabs()

    for panetab in [pt for pt in panetabs if isinstance(pt, hou.ParameterEditor)]:
        if panetab.currentNode() == node:
            return panetab
    for panetab in [pt for pt in panetabs if isinstance(pt, hou.NetworkEditor)]:
        if panetab.isUnderCursor():
            return panetab
    return None


def set_network(current_node, dest_node):
    """Given a Houdini node, change the network to the destination node."""
    current_pane = get_current_pane(current_node)
    # TODO: When network panel is full screen this creates an error
    current_pane.cd(dest_node.path())


# Clipboard
def copy_to_clipboard(text):
    hou.ui.copyTextToClipboard(text)


def check_external_packages(ui_warning=False, force=False):
    """
    Checks to see if external packages need to be updated/installed, this will only run once per session unless forced.

    If the ui_warning is enabled and a package needs to be updated or installed, the dialog will prompt to run the
    installation.

    Args:
        ui_warning: Will pop up a warning dialog if True.
        force: Will force the check to happen even if it has already been done this session.
    """
    # Store if the packages have been checked in hou.session, this ensures the check only happens once.
    if not force:
        cached = getattr(hou.session, "htg_packages_check_result", None)
        if cached is not None:
            return cached

    package_list = []
    external_packages_file = Path(hou.expandString("$HTG_BASEDIR")) / "external_packages.json"
    with external_packages_file.open("r", encoding="utf-8") as f:
        package_data = json.load(f)

    add_package = False
    package_name = "talespire-encoding"
    package_version = package_data[package_name]["version"]
    package_repo = package_data[package_name]["repo"]
    package = package_data[package_name]["package"]
    current_version = None
    try:
        import ts_encoding
        if ts_encoding.__version__ != package_version:
            add_package = True
            current_version = ts_encoding.__version__
    except ModuleNotFoundError:
        add_package = True

    if add_package:
        package_list.append(
            {
                "package_name": package_name,
                "version": package_version,
                "current_version": current_version,
                "repo": package_repo,
                "package": package
            }
        )

    hou.session.htg_packages_check_result = package_list

    if ui_warning and add_package:
        msg = ("Warning! Necessary external packages are missing or are the wrong version.\n"
               "The toolset will not work properly without these.\n"
               "Launch the Installer to fix the issue.")

        details = f"Current Version: {current_version}\nRequired Version: {package_version}"

        result = hou.ui.displayMessage(
            msg,
            buttons=("Launch Installer", "Cancel"),
            severity=hou.severityType.Warning,
            details=details
        )
        if result == 0:
            hou.hscript("python $HTG_BASEDIR/scripts/python/htg/install_update.py update_packages")

    return package_list
