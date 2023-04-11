# Most of the code in here is a duplicate of what is in OBJ_TaleSpire_Terrain as the features are being moved.
#  Once this node is complete the redundant functions will be removed.
import json
import htg.utils
import talespire.encode as ts_encode
import hou


def set_slab_range(node=None):
    force_update(node)
    si1_parm = node.parm('slabindex1')
    si2_parm = node.parm('slabindex2')
    slabs_node = hou.node(node.path()+'/NUM_SLABS')
    num_points = len(slabs_node.geometry().points())
    si1_parm.set(1)
    si2_parm.deleteAllKeyframes()
    si2_parm.set(num_points)


def copy_slab_from_node(node=None):
    force_update(node)
    json_data = get_js(node)
    slab = ts_encode.encode(json_data)
    htg.utils.copy_to_clipboard(slab.strip("b'`"))


def force_update(node=None):
    current_frame = hou.frame()
    grid_node = hou.node(node.path() + '/grid_neg_Z')
    grid_node.cook(force=True, frame_range=(current_frame, current_frame+1))


def get_js(geonode=None):
    geo = geonode.geometry()
    uuid_data = {}
    for point in geo.points():
        uuid = point.attribValue('ts_uuid')
        x = point.attribValue('ts_x')
        y = point.attribValue('ts_y')
        z = point.attribValue('ts_z')
        degree = point.attribValue('ts_degree')
        if uuid not in uuid_data:
            uuid_data[uuid] = []
        uuid_data[uuid].append({'x': x, 'y': y, 'z': z, 'degree': degree})

    data = {'unique_asset_count': len(uuid_data.keys()), 'asset_data': []}
    for auuid in uuid_data.keys():
        asset_data = {
            'uuid': auuid,
            'instance_count': len(uuid_data[auuid]),
            'instances': uuid_data[auuid]
        }
        data['asset_data'].append(asset_data)

    json_dump = json.dumps(data)
    return data


def get_slab_with_pos(node=None):
    offset_node = hou.node(node.path() + '/First_Tile')
    geo = offset_node.geometry()
    point = geo.point(0)
    try:
        pos = tuple(point.position())
        json_data = get_js(node)
        slab = ts_encode.encode(json_data)
        out = {
            "position": {"x": pos[0], "y": pos[1], "z": -pos[2]},
            "code": slab.strip("b'`")
        }
    except AttributeError:
        out = None

    return out


def encode_slabs(node=None):
    force_update(node)
    num_assets = asset_count(node)
    do_export = True
    if num_assets >= 1000000:
        button_result = hou.ui.displayMessage('Warning: This export contains more that 1 Million assets.\n'
                                              'TaleSpire will likely crash.\n'
                                              'Are you sure you want to do this?',
                                              buttons=('OK', 'Cancel'))
        if button_result != 0:
            do_export = False

    if do_export:
        grid_node = hou.node(node.path() + '/SLAB_GRID')
        num_slabs = len(grid_node.geometry().prims())
        slab_index_parm = node.parm('slabindex1')
        og_index = slab_index_parm.eval()

        slab_json = []
        for i in range(1, num_slabs + 1):
            slab_index_parm.set(i)
            slab_pos = get_slab_with_pos(node)
            if slab_pos is not None:
                slab_json.append(slab_pos)
        htg.utils.copy_to_clipboard(json.dumps(slab_json))
        slab_index_parm.set(og_index)


def asset_count(node=None):
    try:
        asset_node = hou.node(node.path() + '/INFO')
        geo = asset_node.geometry()
        points = geo.points()
        num_assets = len(points)
    except AttributeError:
        num_assets = 0

    return num_assets
