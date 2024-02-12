import struct
import base64
import hou
import json
import talespire.decode as ts_decode


def lock_collider(parm=None, cook=False):
    node = parm.node()
    stash_node = hou.node(node.path()+'/TS_Object/stash/stash_collider')

    if parm.eval() == 1:
        try:
            if cook:
                stash_node.cook(force=True)
            stash_node.parm('stashinput').pressButton()
        except AttributeError:
            pass


def set_output_obj(node=None):
    out_obj_parm = node.parm('outputobj')

    if out_obj_parm.eval() != 'OUT_TRANSFORM':
        try:
            out_obj_parm.lock(False)
            out_obj_parm.set('OUT_TRANSFORM')
            out_obj_parm.lock(True)
        except hou.PermissionError:
            pass


def check_locks(node=None):
    """This is meant to lock all the footings when Houdini loads, but it isn't working, disabled for now."""
    parm = node.parm('footing_lock')
    if parm.eval() == 0:
        # parm.set(1)
        # lock_collider(parm, cook=True)
        pass


def recook_material(node=None):
    """When changing UUID the material doesn't always cook properly, this forces that"""
    mat_node = hou.node(node.path() + '/TS_Object/material1')
    try:
        mat_node.cook(force=True)
    except hou.OperationFailed:
        pass


def decode_slab(node=None):
    data = node.parm('ts_slab_str').eval()
    node.parm('ts_slab_str').set(data.strip('`'))
    try:
        asset_data_list = ts_decode.decode(data)
    except (struct.error, base64.binascii.Error):
        hou.ui.displayMessage('Not a valid TaleSpire Slab')
        asset_data_list = None

    if asset_data_list:
        node.setUserData('ts_slab', json.dumps(asset_data_list))
    else:
        node.clearUserDataDict()

    slab_points_node = hou.node(node.path() + '/TS_Object/slab_points')
    slab_points_node.cook(force=True)


def copy_slab(node=None):
    export_node = hou.node(node.path()+'/TS_Object/Export')
    export_node.parm('copy_slab').pressButton()


def uuid_replace(uuid, replace_dict):
    if uuid in replace_dict.keys():
        return replace_dict[uuid]
    else:
        return uuid


def generate_slab_points(node=None):
    top_node = node.parent().parent()

    geo = node.geometry()
    geo.addAttrib(hou.attribType.Point, 'uuid', '')
    geo.addAttrib(hou.attribType.Point, 'degree', 0)
    geo.addAttrib(hou.attribType.Point, 'ts_x', 0)
    geo.addAttrib(hou.attribType.Point, 'ts_y', 0)
    geo.addAttrib(hou.attribType.Point, 'ts_z', 0)

    num_replaces = top_node.parm('asset_replace').eval()
    replace_dict = {}
    for i in range(1, num_replaces + 1):
        # hou.ui.displayMessage(i)
        from_uuid = top_node.parm('from_uuid_{}'.format(i)).eval()
        to_uuid = top_node.parm('to_uuid_{}'.format(i)).eval()
        replace_dict[from_uuid] = to_uuid

    if top_node.parm('obj_type').eval() == 'slab':
        try:
            data = json.loads(top_node.userData('ts_slab'))['asset_data']
        except TypeError:
            data = {}

        for asset_data in data:
            uuid = asset_data['uuid'].lower()
            for instance in asset_data['instances']:
                point = geo.createPoint()
                tx = instance['x']
                ty = instance['y']
                tz = instance['z']
                degree = instance['degree']

                point.setPosition((float(tx) * .01, float(tz) * .01, -float(ty) * .01))
                point.setAttribValue('degree', degree)
                point.setAttribValue('uuid', uuid_replace(uuid, replace_dict))
                point.setAttribValue('ts_x', tx)
                point.setAttribValue('ts_y', ty)
                point.setAttribValue('ts_z', tz)
    else:
        point = geo.createPoint()
        point.setAttribValue('degree', 0)
        point.setAttribValue('uuid', top_node.parm('ts_asset_uuid').eval())
