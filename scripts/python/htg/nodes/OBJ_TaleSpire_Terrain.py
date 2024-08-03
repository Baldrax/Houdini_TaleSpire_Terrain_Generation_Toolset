import hou
import json
import os
import htg.utils
import htg.configs as ts_configs
import htg.nodes.common as ts_common
import htg.nodes.SOP_TaleSpire_Export as ts_export


def read_configs(node=None):
    cfg = ts_configs.Configs()
    parm_list = node.parms()
    for cfg_name in cfg.default_config_keys:
        parm = node.parm('cfg_{}'.format(cfg_name))
        if parm in parm_list:
            parm.set(cfg.get_config(cfg_name))


def set_slab_range(node=None):
    si1_parm = node.parm('slabindex1')
    si2_parm = node.parm('slabindex2')
    slabs_node = hou.node(node.path() + '/Export_Slab/NUM_SLABS')
    num_points = len(slabs_node.geometry().points())
    si1_parm.set(1)
    si2_parm.deleteAllKeyframes()
    si2_parm.set(num_points)


def write_config(parm=None):
    parm_name = parm.name()
    cfg_name = parm_name.split('cfg_')[-1]

    cfg = ts_configs.Configs()
    cfg.set_config(cfg_name, parm.eval())

    if cfg_name == 'talespire_directory':
        ts_data = ts_common.SharedData()
        ts_data.cook_database_node()


def load_default_networks(node=None):
    networks = {
        'terrain_edit': 'TaleSpire_Terrain_terrain_edit_contents.net',
        'biomes': 'TaleSpire_Terrain_biomes_contents.net'
    }
    ts_common.load_networks(node, networks)


def set_default_parms(node=None):
    cfg_textured_tiles = node.parm('cfg_textured_tiles').eval()
    node.parm('textured_tiles').set(cfg_textured_tiles)


def save_terrain_edit_network(node=None):
    file_name = 'TaleSpire_Terrain_terrain_edit_contents.net'
    net_node = hou.node(node.path() + '/terrain_edit')
    ts_common.save_network(net_node, file_name, mode='node')


def save_biome_edit_network(node=None):
    file_name = 'TaleSpire_Terrain_biomes_contents.net'
    net_node = hou.node(node.path() + '/biomes')
    ts_common.save_network(net_node, file_name, mode='node')


def set_attributions(node=None):
    pts_node = hou.node(node.path() + '/terrain_props/DISPLAY')

    authors = set([])
    data = {}

    for pt in pts_node.geometry().points():
        obj_type = pt.attribValue('obj_type')
        if obj_type == 'slab':
            author_name = pt.attribValue('author_name').strip()
            author_url = pt.attribValue('author_url').strip()
            if author_name and author_name != '':
                authors.add(author_name)
                if author_name not in data:
                    data[author_name] = set([])
                data[author_name].add(author_url)

    author_list = list(authors)
    author_list.sort()

    m = ''
    if len(author_list) > 0:
        m += 'This map contains assets created by other community members.\n'
        for name in author_list:
            m += '\n{}\n'.format(name)
            for url in data[name]:
                m += '- {}\n'.format(url)
    else:
        dm = 'No Attributions Found.\n'
        dm += 'If you are using slab assets from other creators, please add the attributions to the ' \
              'TaleSpire_Object nodes for those assets.'
        hou.ui.displayMessage(dm)

    if m != '':
        m += '\n'
    m += 'This map was generated with the aid of Baldrax\'s Houdini TaleSpire Terrain Generation Toolset\n'
    m += 'https://github.com/Baldrax/Houdini_TaleSpire_Terrain_Generation_Toolset\n'

    atr_parm = node.parm('attribution_string')
    atr_parm.set(m)


def clip_attributions(node=None):
    text = node.parm('attribution_string').eval()
    htg.utils.copy_to_clipboard(text)


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
    # Check to see if the scene has been saved first
    filename = hou.hipFile.path()
    if not os.path.isfile(filename):
        hou.ui.displayMessage('Error: You must save the scene before caching the terrain tiles',
                              severity=hou.severityType.Error)
    else:
        write_node = hou.node(node.path() + '/terrain_tiler/write_terrain_tiles')
        read_node = hou.node(node.path() + '/terrain_tiler/read_terrain_tiles')
        write_node.parm('execute').pressButton()
        read_node.parm('reload').pressButton()
        biome_data_node = hou.node(node.path() + '/DATA/Biome_info')
        try:
            biome_data_node.cook(force=True)
        except hou.OperationFailed:
            pass


def cache_uuids(node):
    database_node = get_database_node(node)
    uuid_dict = {}
    db_geo = database_node.geometry()
    for point in db_geo.points():
        uuid = point.getAttribValue('Id')
        ts_type = point.getAttribValue('Type')
        uuid_dict[uuid] = {
            'ptnum': point.number(),
            'type': ts_type
        }
    node.setUserData('uuid_dict', json.dumps(uuid_dict))


def copy_slab(node=None):
    json_data = get_js(node)
    slab = ts_export.encode_slab(json_data)
    htg.utils.copy_to_clipboard(slab.strip("b'`"))


def copy_slab_and_advance(node=None):
    slab_index_parm = node.parm('slabindex1')
    copy_slab(node=node)
    slab_index_parm.set(slab_index_parm.eval() + 1)


def encode_slabs(node=None):
    num_assets = asset_count(node)['num_assets']
    do_export = True
    if num_assets >= 1000000:
        button_result = hou.ui.displayMessage('Warning: This map contains more that 1 Million assets.\n'
                                              'TaleSpire will likely crash.\n'
                                              'Are you sure you want to do this?',
                                              buttons=('OK', 'Cancel'))
        if button_result != 0:
            do_export = False

    if do_export:
        grid_node = hou.node(node.path() + '/Export_Slab/SLAB_GRID')
        num_slabs = len(grid_node.geometry().prims())
        slab_index_parm = node.parm('slabindex1')
        og_index = slab_index_parm.eval()

        slab_json = []
        multi_use_list = node.parm('multi_use_list').eval() == 1
        if multi_use_list:
            range_list_string = node.parm('multi_range_list').eval()
            range_list = multi_range(range_list_string, num_slabs)
        else:
            range_list = range(1, num_slabs + 1)

        for i in range_list:
            slab_index_parm.set(i)
            slab_pos = get_slab_with_pos(node)
            if slab_pos is not None:
                slab_json.append(slab_pos)
        htg.utils.copy_to_clipboard(json.dumps(slab_json))
        slab_index_parm.set(og_index)


def multi_range(range_string, num_slabs=None):
    range_list = [x.strip() for x in range_string.split(",")]
    output_list = []
    for range_item in range_list:
        inc_split = range_item.split(":")
        if len(inc_split) == 2:
            inc = int(inc_split[-1])
        else:
            inc = None

        range_pair = inc_split[0].split("-")
        if len(range_pair) == 1:
            r_start = int(range_pair[0])
            if inc:
                output_list += range(r_start, num_slabs+1, inc)
            else:
                output_list += [r_start]
        elif len(range_pair) == 2:
            r_start, r_end = range_pair
            r_start = int(r_start)
            if r_end == "NSLABS":
                r_end = num_slabs
            else:
                r_end = int(r_end)

            if inc:
                output_list += range(r_start, r_end+1, inc)
            else:
                output_list += range(r_start, r_end+1)

    return output_list


def get_slab_with_pos(node=None):
    offset_node = hou.node(node.path() + '/Export_Slab/First_Tile')
    offset_node.cook(force=True)
    geo = offset_node.geometry()
    point = geo.point(0)
    try:
        pos = tuple(point.position())
        json_data = get_js(node)

        slab = ts_export.encode_slab(json_data)

        out = {
            "position": {"x": pos[0], "y": pos[1], "z": -pos[2]},
            "code": slab.strip("b'`")
        }
    except AttributeError:
        out = None

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


def asset_count(node=None, unique=False):
    results = {}
    try:
        asset_node = hou.node(node.path() + '/Export_Slab/FOR_EXPORT')
        geo = asset_node.geometry()
        num_assets = len(geo.points())
        num_tiles = len(geo.findPointGroup('tiles').points())
        num_props = len(geo.findPointGroup('props').points())
        results = {
            'num_assets': num_assets,
            'num_tiles': num_tiles,
            'num_props': num_props
        }
        if unique:
            unique_assets = set()
            for point in geo.points():
                unique_assets.add(point.attribValue('uuid'))
            num_unique_assets = len(unique_assets)
            results['num_unique_assets'] = num_unique_assets

    except AttributeError:
        pass

    return results


def show_asset_count(node=None):
    asset_data = asset_count(node, unique=True)
    message = f"Tiles: {asset_data['num_tiles']}\n"\
              f"Props: {asset_data['num_props']}\n"\
              f"Total Asset Count: {asset_data['num_assets']}\n\n"\
              f"Unique Assets: {asset_data['num_unique_assets']}"
    hou.ui.displayMessage('', details=message, details_expanded=True)
