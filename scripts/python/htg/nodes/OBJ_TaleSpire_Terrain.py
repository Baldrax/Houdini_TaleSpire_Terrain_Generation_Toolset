import hou
import json
import os
import htg.utils
import talespire.encode as ts_encode
import htg.configs as ts_configs
import htg.nodes.common as ts_common


def read_configs(node=None):
    cfg = ts_configs.Configs()
    parm_list = node.parms()
    for cfg_name in cfg.default_config_keys:
        parm = node.parm('cfg_{}'.format(cfg_name))
        if parm in parm_list:
            parm.set(cfg.get_config(cfg_name))


def write_config(parm=None):
    parm_name = parm.name()
    cfg_name = parm_name.split('cfg_')[-1]

    cfg = ts_configs.Configs()
    cfg.set_config(cfg_name, parm.eval())

    if cfg_name == 'talespire_directory':
        if os.path.isdir(parm.eval()):
            ts_data = ts_common.SharedData()
            ts_data.cook_database_node()
        else:
            hou.ui.displayMessage('The Directory is not Valid. You must select a valid TaleSpire install directory.')


def cook_the_things(node=None):
    ts_data = ts_common.SharedData()
    ts_data.cook_database_node()
    set_lod_size(node)
    for snode in node.allSubChildren():
        if snode.type().nameComponents()[2] == 'python':
            # print('cooking: {}'.format(snode.path()))
            try:
                snode.cook(force=True)
            except hou.OperationFailed:
                pass


def edit_terrain(node=None):
    dest_node = hou.node(node.path() + '/terrain_edit')
    htg.utils.set_network(node, dest_node)


def edit_biomes(node=None):
    dest_node = hou.node(node.path() + '/biomes')
    htg.utils.set_network(node, dest_node)


def set_lod_size(node=None):
    value = node.parm('bbox_lod_vis_size').eval()
    hou.hscript('set TS_LOD_SIZE = {}'.format(value))
    hou.hscript('varchange')


def get_database_node(node):
    database_node = hou.node(node.path() + '/DATA/TS_Database')
    return database_node


def get_out_node(node):
    out_node = hou.node(node.path() + '/Export_Slab/OUT')
    return out_node


def set_terrain_path(node=None):
    force_cook_nodes = ['DATA/Biome_info']
    obj_node = hou.node("/obj")
    obj_node.setUserData('terrain_path', node.path())
    hou.hscript('setenv TS_Terrain_Path = {}'.format(node.path()))
    hou.hscript('varchange')
    for cook_node_name in force_cook_nodes:
        cook_node = hou.node(node.path() + '/' + cook_node_name)
        cook_node.cook(force=True)


def write_terrain_tiles(node=None):
    write_node = hou.node(node.path() + '/terrain_tiler/write_terrain_tiles')
    read_node = hou.node(node.path() + '/terrain_tiler/read_terrain_tiles')
    write_node.parm('execute').pressButton()
    read_node.parm('reload').pressButton()


def cache_uuids(node):
    database_node = get_database_node(node)
    uuid_dict = {}
    db_geo = database_node.geometry()
    for point in db_geo.points():
        uuid = point.getAttribValue('Id')
        type = point.getAttribValue('Type')
        uuid_dict[uuid] = {
            'ptnum': point.number(),
            'type': type
        }
    node.setUserData('uuid_dict', json.dumps(uuid_dict))


def copy_slab(node=None):
    json_data = get_js(node)
    slab = ts_encode.encode(json_data)
    htg.utils.copy_to_clipboard(slab.strip("b'`"))


def copy_slab_and_advance(node=None):
    slab_index_parm = node.parm('slabindex1')
    copy_slab(node=node)
    slab_index_parm.set(slab_index_parm.eval() + 1)


def encode_slabs(node=None):
    grid_node = hou.node(node.path() + '/Export_Slab/SLAB_GRID')
    num_slabs = len(grid_node.geometry().prims())
    slab_index_parm = node.parm('slabindex1')
    og_index = slab_index_parm.eval()

    slab_json = []
    for i in range(1, num_slabs + 1):
        slab_index_parm.set(i)
        slab_pos = get_slab_with_pos(node)
        slab_json.append(slab_pos)
    htg.utils.copy_to_clipboard(json.dumps(slab_json))
    slab_index_parm.set(og_index)


def get_slab_with_pos(node=None):
    offset_node = hou.node(node.path() + '/Export_Slab/First_Tile')
    geo = offset_node.geometry()
    point = geo.point(0)
    pos = tuple(point.position())
    json_data = get_js(node)
    slab = ts_encode.encode(json_data)
    out = {
        "position": {"x": pos[0], "y": pos[1], "z": -pos[2]},
        "code": slab.strip("b'`")
    }
    return out


def get_js(node=None):
    geonode = get_out_node(node)
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


# TODO: Not sure what this was for, might not be needed.
def get_asset(uuid):
    """Deprecated"""
    node = hou.pwd()
    uuid_dict = json.loads(node.userData('uuid_dict'))
    uuid_data = uuid_dict[uuid]
    return {"Id": uuid, "type": uuid_data['type']}
