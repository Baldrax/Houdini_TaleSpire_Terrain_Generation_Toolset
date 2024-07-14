import hou
import htg.utils
import htg.nodes.common as ts_common


def edit_objects(node=None):
    dest_node = hou.node(node.path() + '/terrain_tiler/Floor_Tiles/object_sets')
    htg.utils.set_network(node, dest_node)


def load_default_networks(node=None):
    networks = {
        'terrain_tiler/Floor_Tiles/object_sets': 'TaleSpire_Cavern_Helper_objects_contents.net'
    }
    ts_common.load_networks(node, networks)


def save_objects_network(node=None):
    file_name = 'TaleSpire_Cavern_Helper_objects_contents.net'
    net_node = hou.node(node.path() + '/terrain_tiler/Floor_Tiles/object_sets')
    ts_common.save_network(net_node, file_name, mode='node')
