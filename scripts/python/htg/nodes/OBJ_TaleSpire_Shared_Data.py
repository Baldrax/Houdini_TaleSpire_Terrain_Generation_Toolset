import hou
import os
import htg.configs as ts_configs

from pathlib import Path
from PIL import Image
from PIL import ImageChops


def get_asset_library():
    from ts_encoding.assets import TSAssetLib
    from ts_encoding import InvalidTaleSpireDirectory

    cfg = ts_configs.Configs()
    ts_basepath = cfg.get_config('talespire_directory')

    if hasattr(hou.session, "ts_asset_lib") and isinstance(hou.session.ts_asset_lib, TSAssetLib):
        return hou.session.ts_asset_lib
    else:
        try:
            ts_asset_lib = TSAssetLib(ts_basepath, asset_filter=["Tiles", "Props"])
            hou.session.ts_asset_lib = ts_asset_lib
            return ts_asset_lib
        except InvalidTaleSpireDirectory:
            hou.ui.displayMessage('ERROR: Unable to find TaleSpire asset definitions, check the talespire_directory in '
                                  'the settings tab of the TaleSpire Terrain Node. TaleSpire must be installed on this '
                                  'machine in order to use the toolset.',
                                  details=ts_basepath, severity=hou.severityType.Error)
            return None


def build_ts_database(node):
    base_node = node.parent().parent()
    geo = node.geometry()

    geo.addAttrib(hou.attribType.Point, 'Id', '')
    geo.addAttrib(hou.attribType.Point, 'Name', '')
    geo.addAttrib(hou.attribType.Point, "OgName", "")
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

    ts_asset_lib = get_asset_library()

    proxy_names = []
    htg_basedir = hou.text.expandString('$HTG_BASEDIR')
    for proxy_file in os.listdir(os.path.join(htg_basedir, 'geo', 'ts_proxies')):
        proxy_names.append(proxy_file.split('.')[0])

    is_missing_textures = False
    for ts_asset in ts_asset_lib.assets():
        asset_uuid = ts_asset.id
        point = geo.createPoint()
        point.setAttribValue("Id", asset_uuid)
        asset_name = ts_asset.name
        point.setAttribValue("OgName", asset_name)
        point.setAttribValue("Type", ts_asset.asset_type)
        point.setAttribValue("IsDeprecated", ts_asset.asset_dict["IsDeprecated"])
        point.setAttribValue("GroupTag", ts_asset.asset_dict["GroupTag"])
        asset_tags = ts_asset.asset_dict["Tags"]
        point.setAttribValue("Tags", asset_tags)
        point.setAttribValue("Folder", ts_asset.asset_dict["Folder"])

        m_center = ts_asset.asset_dict["ColliderBoundsBound"]["m_Center"]
        m_extent = ts_asset.asset_dict["ColliderBoundsBound"]["m_Extent"]
        point.setAttribValue('m_Center', hou.Vector3([m_center['x'], m_center['y'], m_center['z']]))
        point.setAttribValue('m_Extent', hou.Vector3([m_extent['x'], m_extent['y'], m_extent['z']]))

        tag_name = ""
        is_floor = False
        if ts_asset.asset_type == "Tiles":
            tile_tags = ["2x2", "1x1", "1x2", "2x1"]
            for tile_tag in tile_tags:
                if tile_tag in asset_tags:
                    tag_name = tile_tag
                    break

            if tag_name not in asset_name:
                asset_name += f" {tag_name}"

            extent = (m_extent['x'], m_extent['y'], m_extent['z'])
            if extent in ((1.0, 0.25, 1.0), (0.5, 0.25, 0.5)):
                is_floor = True

        point.setAttribValue("Name", asset_name)

        proxy_name = asset_uuid
        proxy_base_path = f"{htg_basedir}/geo/ts_proxies"

        if (
            is_floor and tag_name in ("1x1", "2x2")
            and not ts_asset.deprecated
            and not "tempwater" in asset_name.lower()
        ):
            point.setAttribValue("is_floor", 1)
            point.setAttribValue("proxy_path",
                                 f"{proxy_base_path}/Standin_floor_{tag_name}.bgeo.sc")
            point.setAttribValue("uv_proxy_path",
                                 f"{proxy_base_path}/Textured_floor_{tag_name}.bgeo.sc")

        if proxy_name in proxy_names:
            # This will override the Standin_floor proxy_path above for floors that have a proxy.
            point.setAttribValue("proxy_path", f"{proxy_base_path}/{proxy_name}.bgeo.sc")

        point.setAttribValue("IconAtlas", ts_asset.icon_atlas)
        point.setAttribValue("IconRegion", hou.Vector4(ts_asset.atlas_region))
        texture_path = f"{htg_basedir}/images/cache/textures/{asset_uuid}.png"
        point.setAttribValue("texture_path", texture_path)
        if not Path(texture_path).is_file():
            is_missing_textures = True

    if is_missing_textures:
        process_images(geo=geo)


def process_images(node=None, geo=None, process_type="textures", force_all=False):
    if geo is None:
        geo = node.geometry()
    img_dict = {}

    num_tasks = 0

    for point in geo.points():
        icon_atlas = point.attribValue("IconAtlas")
        icon_region = point.attribValue("IconRegion")
        output_path = Path(point.attribValue("texture_path").replace("cache/textures/", f"cache/{process_type}/"))
        is_floor = point.attribValue("is_floor")
        uuid = point.attribValue("Id")

        if icon_atlas not in img_dict:
            img_dict[icon_atlas] = []

        if (not output_path.is_file() or force_all) and (is_floor == 1 or process_type != "textures"):
            num_tasks += 1
            img_dict[icon_atlas].append({"uuid": uuid, "region": icon_region, "path": output_path})

    if num_tasks > 0:
        htg_basedir = hou.text.expandString("$HTG_BASEDIR")
        image_dir = Path(f"{htg_basedir}/images/cache/{process_type}")
        if not image_dir.is_dir():
            os.makedirs(image_dir)

    with hou.InterruptableOperation(
            f"Processing {num_tasks} asset textures",
            open_interrupt_dialog=True
    ) as operation:
        progress_index = 0
        for icon_atlas in img_dict:
            task_list = img_dict[icon_atlas]
            im = Image.open(icon_atlas)
            x_size, y_size = im.size

            for task_dict in task_list:
                uuid = task_dict["uuid"]
                region = task_dict["region"]
                output_path = task_dict["path"]
                left = region[0]
                right = left + region[2]
                lower = y_size - region[1]
                upper = lower - region[3]
                crop_area = (left, upper, right, lower)
                texture_name = process_type[0:-1]
                # print(f'Making {texture_name} for asset {uuid}')
                img = im.crop(crop_area)

                if process_type == "textures":
                    img = simple_texture(img)

                img.save(output_path)
                progress_index += 1
                operation.updateProgress(float(progress_index) / float(num_tasks))


def simple_texture(image):
    fg = image.convert("RGB")

    ys = Image.new("RGBA", image.size, (0, 0, 0, 255))
    xs01 = Image.new("RGBA", image.size, (0, 0, 0, 255))
    xs02 = Image.new("RGBA", image.size, (0, 0, 0, 255))

    ys.paste(fg, (0, 8), image)
    ys.paste(fg, (0, -8), image)

    xs01.paste(fg, (-8, 0), image)
    xs02.paste(fg, (8, 0), image)

    xs = ImageChops.lighter(xs01, xs02)

    combo = ImageChops.lighter(ys, xs)

    combo.paste(fg, (0, 0), image)

    return combo
