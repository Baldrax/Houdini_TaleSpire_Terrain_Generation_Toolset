# This Code is adapted from https://github.com/LuPro/SlabelFish

import base64
import gzip
import sys

from talespire.exceptions import *


def create_header(unique_asset_count):
    header = b'\xCE\xFA\xCE\xD1\x02\x00'
    header += unique_asset_count.to_bytes(4, byteorder='little')
    return header


def encode_asset(asset_json):
    uuid_parts = asset_json['uuid'].split("-")
    uuid_bytes = b''
    uuid_bytes += int(uuid_parts[0], 16).to_bytes(4, byteorder='little')
    uuid_bytes += int(uuid_parts[1], 16).to_bytes(2, byteorder='little')
    uuid_bytes += int(uuid_parts[2], 16).to_bytes(2, byteorder='little')
    uuid_bytes += int(uuid_parts[3], 16).to_bytes(2, byteorder='big')
    uuid_bytes += int(uuid_parts[4], 16).to_bytes(6, byteorder='big')
    asset_blob = uuid_bytes + asset_json['instance_count'].to_bytes(4, byteorder='little')
    return asset_blob


def encode_asset_position(instance_json, uuid, offset=None):
    if offset is None:
        offset = [0, 0, 0]
    position_blob = 0
    position_blob |= int(instance_json['x'])
    position_blob |= (int(instance_json['y']) << 36)
    position_blob |= (int(instance_json['z']) << 18)
    position_blob |= (int(instance_json['degree'] / 15) << 54)

    return position_blob.to_bytes(8, byteorder='little')


def create_assets_data(assets_json, offset=None):
    if offset is None:
        offset = [0, 0, 0]
    asset_list = b''
    position_list = b''

    for asset in assets_json:  # create an entry in the asset list for each asset
        asset_list_entry = encode_asset(asset)
        asset_list += asset_list_entry
        for instance in asset['instances']:  # create an entry in the position list for each instance of each asset
            position_list_entry = encode_asset_position(instance, asset['uuid'], offset)
            position_list += position_list_entry

    return asset_list, position_list


def encode(data):
    slab_data = b''  # byte string slab blob
    slab_json = data
    slab_json['unique_asset_count'] = len(slab_json['asset_data'])

    slab_data += create_header(len(slab_json['asset_data']))
    asset_data = create_assets_data(slab_json['asset_data'])
    slab_data += asset_data[0] + asset_data[1] + b'\x00\x00'

    # gzip compress
    slab_compressed_data = gzip.compress(slab_data, compresslevel=9)
    if len(slab_compressed_data) > 30720:
        raise SlabExceedsSizeLimit("Slab exceeds TaleSpire size limit of 30kB (30720 bytes) binary data!")

    base64_bytes = base64.b64encode(slab_compressed_data)
    return str(b'```' + base64_bytes + b'```')
