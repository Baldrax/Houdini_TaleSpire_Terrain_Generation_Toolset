import hou
import talespire.assets
import os
import htg.configs as ts_configs


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
    geo.addAttrib(hou.attribType.Point, 'proxy_path', '')

    cfg = ts_configs.Configs()
    ts_basepath = cfg.get_config('talespire_directory')
    if not os.path.isdir(ts_basepath):
        hou.ui.displayMessage('ERROR: TaleSpire directory not found, check the settings on the TaleSpire Terrain Node!',
                              details=ts_basepath, severity=hou.severityType.Error)
        return None
    index_dict_list = talespire.assets.get_assets(ts_basepath)

    proxy_names = []
    htg_basedir = hou.text.expandString('$HTG_BASEDIR')
    for proxy_file in os.listdir(os.path.join(htg_basedir, 'geo', 'ts_proxies')):
        proxy_names.append(proxy_file.split('.')[0])

    seen_ids = []
    for index_dict in index_dict_list:
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

                        m_Center = asset_dict['ColliderBoundsBound']['m_Center']
                        m_Extent = asset_dict['ColliderBoundsBound']['m_Extent']

                        point.setAttribValue('m_Center', hou.Vector3([m_Center['x'], m_Center['y'], m_Center['z']]))
                        point.setAttribValue('m_Extent', hou.Vector3([m_Extent['x'], m_Extent['y'], m_Extent['z']]))

                        extent = (m_Extent['x'], m_Extent['y'], m_Extent['z'])
                        if extent in ((1.0, 0.25, 1.0), (0.5, 0.25, 0.5)):
                            isfloor = True
                        else:
                            isfloor = False

                        proxy_name = asset_name.replace(' ', '_').replace('/', '_').replace('(', '_').replace(')', '_')
                        if proxy_name in proxy_names:
                            point.setAttribValue('proxy_path',
                                                 '{}/geo/ts_proxies/{}.bgeo.sc'.format(htg_basedir, proxy_name))
                        elif isfloor and tag_name.strip() in ('1x1', '2x2'):
                            point.setAttribValue('proxy_path',
                                                 '{}/geo/ts_proxies/Standin_floor_{}.bgeo.sc'.format(htg_basedir,
                                                                                                     tag_name.strip()))
