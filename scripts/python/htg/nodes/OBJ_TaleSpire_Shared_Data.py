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
    geo.addAttrib(hou.attribType.Point, 'uv_proxy_path', '')
    geo.addAttrib(hou.attribType.Point, 'texture_path', '')
    geo.addAttrib(hou.attribType.Point, 'IconAtlas', '')
    geo.addAttrib(hou.attribType.Point, 'IconRegion', hou.Vector4([0, 0, 0, 0]))
    geo.addAttrib(hou.attribType.Point, 'is_floor', 0)

    cfg = ts_configs.Configs()
    ts_basepath = cfg.get_config('talespire_directory')
    asset_dicts = talespire.assets.get_asset_dicts(ts_basepath)

    if asset_dicts is None or len(asset_dicts) == 0:
        hou.ui.displayMessage('ERROR: Unable to find TaleSpire asset definitions, check the talespire_directory in '
                              'the settings tab of the TaleSpire Terrain Node. TaleSpire must be installed on this '
                              'machine in order to use the toolset.',
                              details=ts_basepath, severity=hou.severityType.Error)
        return None

    proxy_names = []
    htg_basedir = hou.text.expandString('$HTG_BASEDIR')
    for proxy_file in os.listdir(os.path.join(htg_basedir, 'geo', 'ts_proxies')):
        proxy_names.append(proxy_file.split('.')[0])

    seen_ids = []
    is_missing_textures = False
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
                            tag_name = '2x2'
                        elif '1x1' in asset_tags:
                            tag_name = '1x1'
                        elif '1x2' in asset_tags:
                            tag_name = '1x2'
                        elif '2x1' in asset_tags:
                            tag_name = '2x1'

                        if '2x2' not in asset_name and '1x1' not in asset_name and type == 'Tiles':
                            asset_name += f' {tag_name}'

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
                        proxy_base_path = f'{htg_basedir}/geo/ts_proxies'

                        if is_floor and tag_name in ('1x1', '2x2') and not asset_dict['IsDeprecated'] == 1:
                            point.setAttribValue('is_floor', 1)
                            point.setAttribValue('proxy_path',
                                                 f'{proxy_base_path}/Standin_floor_{tag_name}.bgeo.sc')
                            point.setAttribValue('uv_proxy_path',
                                                 f'{proxy_base_path}/Textured_floor_{tag_name}.bgeo.sc')

                        if proxy_name in proxy_names:
                            # This will override the Standin_floor proxy_path above for floors that have a proxy.
                            point.setAttribValue('proxy_path', f'{proxy_base_path}/{proxy_name}.bgeo.sc')

                        atlas_index = asset_dict['Icon']['AtlasIndex']
                        point.setAttribValue('IconAtlas',
                                             os.path.join(os.path.dirname(index_path), icon_atlases[atlas_index]))
                        atlas_region = asset_dict['Icon']['Region']
                        point.setAttribValue('IconRegion', hou.Vector4(
                            [atlas_region['x'],
                             atlas_region['y'],
                             atlas_region['width'],
                             atlas_region['height']
                             ]))
                        texture_path = f'{htg_basedir}/images/cache/textures/{uuid}.png'
                        point.setAttribValue('texture_path', texture_path)
                        if not os.path.isfile(texture_path):
                            is_missing_textures = True

    if is_missing_textures:
        process_images(geo=geo)


def process_images(node=None, geo=None, process_type='textures', force_all=False):
    if geo is None:
        geo = node.geometry()
    img_dict = dict()

    num_tasks = 0

    for point in geo.points():
        icon_atlas = point.attribValue('IconAtlas')
        icon_region = point.attribValue('IconRegion')
        output_path = point.attribValue('texture_path').replace('textures', process_type)
        is_floor = point.attribValue('is_floor')
        uuid = point.attribValue('Id')

        if icon_atlas not in img_dict:
            img_dict[icon_atlas] = []

        if (not os.path.isfile(output_path) or force_all) and is_floor == 1:
            num_tasks += 1
            img_dict[icon_atlas].append({'uuid': uuid, 'region': icon_region, 'path': output_path})

    with hou.InterruptableOperation(
        f'Processing {num_tasks} asset textures',
        open_interrupt_dialog=True
    ) as operation:
        progress_index = 0
        for icon_atlas in img_dict:
            task_list = img_dict[icon_atlas]
            im = Image.open(icon_atlas)
            x_size, y_size = im.size

            for task_dict in task_list:
                uuid = task_dict['uuid']
                region = task_dict['region']
                output_path = task_dict['path']
                left = (region[0])*x_size
                right = left+region[2]*x_size
                lower = (1-region[1])*y_size
                upper = lower-region[3]*y_size
                crop_area = (left, upper, right, lower)
                texture_name = process_type[0:-1]
                # print(f'Making {texture_name} for asset {uuid}')
                img = im.crop(crop_area)

                if process_type == 'textures':
                    img = simple_texture(img)

                img.save(output_path)
                progress_index += 1
                operation.updateProgress( float(progress_index)/float(num_tasks))


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
