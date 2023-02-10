import hou
import htg.utils
import htg.nodes.common as ts_common


def refresh_objects(node=None):
    cook_paths = ['/object_set_points']

    for cook_path in cook_paths:
        cook_node = hou.node(node.path()+cook_path)
        cook_node.cook(force=True)


def edit_objects(node=None):
    dest_node = hou.node(node.path() + '/object_sets')
    htg.utils.set_network(node, dest_node)


def load_default_networks(node=None):
    networks = {
        'object_sets': 'TaleSpire_Object_Set_object_sets_contents.net'
    }
    ts_common.load_networks(node, networks)


def save_object_sets_network(node=None):
    file_name = 'TaleSpire_Object_Set_object_sets_contents.net'
    net_node = hou.node(node.path() + '/object_sets')
    ts_common.save_network(net_node, file_name, mode='node')
