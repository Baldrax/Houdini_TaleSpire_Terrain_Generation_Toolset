import hou
import talespire.assets
import os
import htg.configs as ts_configs
from PIL import Image
from PIL import ImageChops


def build_ts_database(node):
    base_node = node.parent().parent()
    geo = node.geometry()

    geo.addAttrib(hou.attribType.Point, 'Id', '')
    geo.addAttrib(hou.attribType.Point, 'Name', '')
    geo.addAttrib(hou.attribType.Point, 'Type', '')
    geo.addAttrib(hou.attribType.Point, 'IsDeprecated', 0)
    geo.addAttrib(hou.attribType.Point, 'GroupTag', '')
    geo.addAttrib(hou.attribType.Point, 'm_Center', hou.Vector3([0, 0, 0]))
    geo.addAttrib(hou.attribType.Point, 'm_Extent', hou.Vector3([0, 0, 0]))
    geo.addArrayAttrib(hou.attribType.Point, 'Tags', hou.attribData.String)
    geo.addAttrib(hou.attribType.Point, 'Folder', '')
    geo.addAttrib(hou.attribType.Point, 'proxy_path', '')
    geo.addAttrib(hou.attribType.Point, 'texture_path', '')
    geo.addAttrib(hou.attribType.Point, 'IconAtlas', '')
    geo.addAttrib(hou.attribType.Point, 'IconRegion', hou.Vector4([0, 0, 0, 0]))

    cfg = ts_configs.Configs()
    ts_basepath = cfg.get_config('talespire_directory')
    if not os.path.isdir(ts_basepath):
        hou.ui.displayMessage('ERROR: TaleSpire directory not found, check the settings on the TaleSpire Terrain Node!',
                              details=ts_basepath, severity=hou.severityType.Error)
        return None
    asset_dicts = talespire.assets.get_asset_dicts(ts_basepath)

    proxy_names = []
    htg_basedir = hou.text.expandString('$HTG_BASEDIR')
    for proxy_file in os.listdir(os.path.join(htg_basedir, 'geo', 'ts_proxies')):
        proxy_names.append(proxy_file.split('.')[0])

    seen_ids = []
    for index_name in asset_dicts:
        index_path = asset_dicts[index_name]['path']
        index_dict = asset_dicts[index_name]['index']

        icon_atlases = list()
        for atlas_entry in index_dict['IconsAtlases']:
            icon_atlases.append(atlas_entry['Path'])

        for type in index_dict:
            if type in ['Tiles', 'Props']:
                for asset_dict in index_dict[type]:
                    uuid = asset_dict['Id'].lower()
                    if uuid not in seen_ids:
                        seen_ids.append(uuid)
                        point = geo.createPoint()
                        point.setAttribValue('Id', uuid)
                        asset_name = asset_dict['Name']
                        asset_tags = asset_dict['Tags']

                        tag_name = ''
                        if '2x2' in asset_tags:
                            tag_name = ' 2x2'
                        elif '1x1' in asset_tags:
                            tag_name = ' 1x1'
                        elif '1x2' in asset_tags:
                            tag_name = ' 1x2'
                        elif '2x1' in asset_tags:
                            tag_name = ' 2x1'

                        if ('2x2' not in asset_name and '1x1' not in asset_name and type == 'Tiles'):
                            asset_name += tag_name

                        point.setAttribValue('Name', asset_name)
                        point.setAttribValue('Type', type)
                        point.setAttribValue('IsDeprecated', asset_dict['IsDeprecated'])
                        point.setAttribValue('GroupTag', asset_dict['GroupTag'])
                        point.setAttribValue('Tags', asset_tags)
                        point.setAttribValue('Folder', asset_dict['Folder'])

                        m_Center = asset_dict['ColliderBoundsBound']['m_Center']
                        m_Extent = asset_dict['ColliderBoundsBound']['m_Extent']

                        point.setAttribValue('m_Center', hou.Vector3([m_Center['x'], m_Center['y'], m_Center['z']]))
                        point.setAttribValue('m_Extent', hou.Vector3([m_Extent['x'], m_Extent['y'], m_Extent['z']]))

                        extent = (m_Extent['x'], m_Extent['y'], m_Extent['z'])
                        if extent in ((1.0, 0.25, 1.0), (0.5, 0.25, 0.5)):
                            is_floor = True
                        else:
                            is_floor = False

                        proxy_name = asset_name.replace(' ', '_').replace('/', '_').replace('(', '_').replace(')', '_')
                        if proxy_name in proxy_names:
                            point.setAttribValue('proxy_path',
                                                 '{}/geo/ts_proxies/{}.bgeo.sc'.format(htg_basedir, proxy_name))
                        elif is_floor and tag_name.strip() in ('1x1', '2x2'):
                            point.setAttribValue('proxy_path',
                                                 '{}/geo/ts_proxies/Standin_floor_{}.bgeo.sc'.format(htg_basedir,
                                                                                                     tag_name.strip()))
                        atlas_index = asset_dict['Icon']['AtlasIndex']
                        point.setAttribValue('IconAtlas', os.path.join(os.path.dirname(index_path), icon_atlases[atlas_index]))
                        atlas_region = asset_dict['Icon']['Region']
                        point.setAttribValue('IconRegion', hou.Vector4(
                            [atlas_region['x'],
                             atlas_region['y'],
                             atlas_region['width'],
                             atlas_region['height']
                             ]))


def process_images(node, process_type='textures'):
    geo = node.geometry()
    img_dict = dict()

    for point in geo.points():
        icon_atlas = point.attribValue('IconAtlas')
        icon_region = point.attribValue('IconRegion')
        uuid = point.attribValue('Id')

        if uuid == 'b83392b1-8833-43c9-a97f-2ac3df659e66' or True:
            if icon_atlas not in img_dict:
                img_dict[icon_atlas] = []

            img_dict[icon_atlas].append({'uuid': uuid, 'region': icon_region})

    for icon_atlas in img_dict:
        task_list = img_dict[icon_atlas]
        im = Image.open(icon_atlas)
        x_size, y_size = im.size
        print(icon_atlas)

        for task_dict in task_list:
            uuid = task_dict['uuid']
            region = task_dict['region']
            output_path = '{}/images/cache/{}/{}.png'.format(hou.text.expandString('$HTG_BASEDIR'), process_type, uuid)
            left = (region[0])*x_size
            right = left+region[2]*x_size
            lower = (1-region[1])*y_size
            upper = lower-region[3]*y_size
            crop_area = (left, upper, right, lower)
            print(output_path)
            print(crop_area)
            img = im.crop(crop_area)

            if process_type == 'textures':
                img = simple_texture(img)

            img.save(output_path)


def simple_texture(image):
    fg = image.convert('RGB')

    ys = Image.new('RGBA', image.size, (0, 0, 0, 255))
    xs01 = Image.new('RGBA', image.size, (0, 0, 0, 255))
    xs02 = Image.new('RGBA', image.size, (0, 0, 0, 255))

    ys.paste(fg, (0, 8), image)
    ys.paste(fg, (0, -8), image)

    xs01.paste(fg, (-8, 0), image)
    xs02.paste(fg, (8, 0), image)

    xs = ImageChops.lighter(xs01, xs02)

    combo = ImageChops.lighter(ys, xs)

    combo.paste(fg, (0, 0), image)

    return combo
