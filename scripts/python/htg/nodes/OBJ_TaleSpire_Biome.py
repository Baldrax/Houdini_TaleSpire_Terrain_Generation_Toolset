import hou
import htg.utils


def refresh_biome(node=None):
    cook_paths = ['/biome_pts/biome_cat_points']

    for cook_path in cook_paths:
        cook_node = hou.node(node.path()+cook_path)
        cook_node.cook(force=True)


def edit_objects(node=None):
    dest_node = hou.node(node.path() + '/biome_objects')
    htg.utils.set_network(node, dest_node)


def edit_tiles(node=None):
    dest_node = hou.node(node.path() + '/biome_tiles')
    htg.utils.set_network(node, dest_node)


def edit_props(node=None):
    dest_node = hou.node(node.path() + '/biome_props')
    htg.utils.set_network(node, dest_node)


def default_biome_selected(node=None):
    active = node.parm('default_biome').eval()
    if active == 1:
        for sib_node in node.parent().children():
            if sib_node.type().nameComponents()[2] == 'TaleSpire_Biome' and sib_node != node:
                sib_node.parm('default_biome').set(0)
