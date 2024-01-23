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
