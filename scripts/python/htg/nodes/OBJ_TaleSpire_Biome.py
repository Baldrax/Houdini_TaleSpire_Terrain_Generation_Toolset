import hou
import htg.utils
import htg.nodes.common as ts_common


def refresh_biome(node=None):
    cook_paths = ['/biome_pts/biome_cat_points']

    for cook_path in cook_paths:
        cook_node = hou.node(node.path()+cook_path)
        cook_node.cook(force=True)


def edit_objects(node=None):
    dest_node = hou.node(node.path() + '/biome_objects')
    htg.utils.set_network(node, dest_node)


def edit_masks(node=None):
    networks = {
        'biome_masks': 'TaleSpire_Biome_biome_masks_contents.net'
    }

    dest_node = hou.node(node.path() + '/biome_masks')
    if len(dest_node.children()) == 0:
        ts_common.load_networks(node, networks)
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


def load_default_networks(node=None):
    networks = {
        'biome_objects': 'TaleSpire_Biome_biome_objects_contents.net',
        'biome_tiles': 'TaleSpire_Biome_biome_tiles_contents.net',
        'biome_props': 'TaleSpire_Biome_biome_props_contents.net'
    }
    ts_common.load_networks(node, networks)


def save_biome_objects_network(node=None):
    file_name = 'TaleSpire_Biome_biome_objects_contents.net'
    net_node = hou.node(node.path() + '/biome_objects')
    ts_common.save_network(net_node, file_name, mode='node')


def save_biome_masks_network(node=None):
    file_name = 'TaleSpire_Biome_biome_masks_contents.net'
    net_node = hou.node(node.path() + '/biome_masks')
    ts_common.save_network(net_node, file_name, mode='node')


def save_biome_tiles_network(node=None):
    file_name = 'TaleSpire_Biome_biome_tiles_contents.net'
    net_node = hou.node(node.path() + '/biome_tiles')
    ts_common.save_network(net_node, file_name, mode='node')


def save_biome_props_network(node=None):
    file_name = 'TaleSpire_Biome_biome_props_contents.net'
    net_node = hou.node(node.path() + '/biome_props')
    ts_common.save_network(net_node, file_name, mode='node')
