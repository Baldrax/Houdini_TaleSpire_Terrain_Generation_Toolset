import hou
from tkinter import Tk


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
    current_pane.cd(dest_node.path())


# Clipboard
def copy_to_clipboard(text):
    r = Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(text)
    r.update()
    r.destroy()
