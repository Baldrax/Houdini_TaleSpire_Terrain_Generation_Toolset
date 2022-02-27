import hou
import htg.utils


def edit_objects(node=None):
    dest_node = hou.node(node.path() + '/biome_objects')
    htg.utils.set_network(node, dest_node)


def edit_tiles(node=None):
    dest_node = hou.node(node.path() + '/biome_tiles')
    htg.utils.set_network(node, dest_node)


def edit_props(node=None):
    dest_node = hou.node(node.path() + '/biome_props')
    htg.utils.set_network(node, dest_node)
