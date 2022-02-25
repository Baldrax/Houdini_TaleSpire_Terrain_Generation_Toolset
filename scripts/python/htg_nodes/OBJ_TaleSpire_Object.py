import hou
import json
import talespire.decode as ts_decode


def decode_slab(node=None):
    data = node.parm('ts_slab_str').eval()
    node.parm('ts_slab_str').set(data.strip('`'))
    asset_data_list = ts_decode.decode(data)

    node.setUserData('ts_slab', json.dumps(asset_data_list))
    slab_points_node = hou.node(node.path() + '/TS_Object/slab_points')
    slab_points_node.cook(force=True)
