# This Code is adapted from https://github.com/LuPro/SlabelFish

import base64
import gzip
import struct


def format_binary(data):
    return ":".join("{:02X}".format(b) for b in data)


def print_info(level, msg, verbose, quiet):
    pass


#    if (level == "info_quiet" and verbose == True and quiet == False):
#        print(msg)
#    if (level == "data_warning_quiet" and quiet == False):
#        print(msg)
#    elif (level == "info" and verbose == True and quiet == False):
#        print(level + ": " + msg)
#    elif ((level == "data_warning" or level == "warning") and quiet == False):
#        print(level + ": " + msg)
#    elif (level == "error" and quiet == False):
#        print(level + ": " + msg, file=sys.stderr)


# replace with .from_bytes?
def assemble_bytes(byte_data):
    total = 0
    for byte in byte_data:
        # take old total, shift it to the left by 8 (make space for another byte), add next byte in list
        total = (total << 8) + byte
    return total


def decode_asset(asset_data, verbose=False, quiet=False):
    print_info("info_quiet", "      asset: " + format_binary(asset_data), verbose, quiet)
    dec_data = struct.unpack('IHH8BI', asset_data)
    uuid = (dec_data[0], dec_data[1], dec_data[2], assemble_bytes(dec_data[3:5]), assemble_bytes(dec_data[5:11]))
    uuid_strings = (format(uuid[0], "08X"), format(uuid[1], "04X"), format(uuid[2], "04X"), format(uuid[3], "04X"),
                    format(uuid[4], "012X"))
    instance_count = dec_data[11]
    # print("\ndecoded tile data:", '-'.join(format(x, 'X') for x in decData))
    # print("ordered decoded tile data:", '-'.join(format(x, 'X') for x in uuid))
    uuid_string = '-'.join(x for x in uuid_strings)
    print_info("info_quiet", "      UUID: " + uuid_string + ", # instances: " + str(instance_count), verbose, quiet)

    return {
        "uuid": uuid_string,
        "instance_count": instance_count,
        "instances": []  # rename to instance_position? or just positions?
    }


# decodes an asset position, returns a tuple of which asset this position belongs to (index from asset list)
# as well as the position
def decode_asset_position(asset_position_data, asset_data_list, dec_asset_count, verbose=False, quiet=False):
    # decode position from blob passed on
    print_info(
        "info_quiet", "\n\tDecoding asset position from list: " + format_binary(asset_position_data),
        verbose, quiet)

    # unpack as little endian. data is stored as:
    #   2 bit pad, 8 bit rot, 2 bit pad, 16 bit y, 2 bit pad, 16 bit z, 2 bit pad, 16 bit x
    position_blob = struct.unpack("<Q", asset_position_data)[0]
    print_info("info_quiet",
               "\tRead position blob as little endian (64 bit binary):\n\t" + format(position_blob, '064b'),
               verbose, quiet)
    # x, y and z are 16bit, rot is 8 bit. all have 2 bit padding between each other.
    x = position_blob & 0xFFFF  # isolate lowest 16 bits (x position)
    y = (position_blob >> 36) & 0xFFFF  # shift away the x and z coord + 2*2 bit padding
    z = (position_blob >> 18) & 0xFFFF  # shift away the x coord + 2 bit padding
    rot = position_blob >> 54  # shift away x, y and z coord + 3*2 padding (54 places) to get rotation to LSB
    print_info("info_quiet",
               "\tExtracted coordinates and rotation from blob:\n\tx: " +
               str(x) + ", y: " + str(y) + ", z: " + str(z) + " | rot: " + str(rot) + "(=" + str(rot * 15) + "°)",
               verbose, quiet)

    # figure out which asset this position actually belongs to and store it
    print_info("info_quiet", "\tKeeping track of which asset's position is being read (count asset list)",
               verbose, quiet)
    # print_info("info_quiet", "      Keep track of which asset position is being read. Done by iterating through asset list and summing up instance counts until the current number of parsed asset positions is lower or equal to the number of asset instances from the list. This is the asset this position belongs to.", verbose, quiet)
    sub_total = 0
    for i, asset in enumerate(asset_data_list):
        sub_total += asset['instance_count']
        if (
                # check if the currently iterated through asset in the asset list is the one we are
                # currently decoding the pos of
                dec_asset_count < sub_total):
            return (i, {
                "x": x,
                "y": y,
                "z": z,
                "degree": rot * 15
            })


def decode(data):
    verbose = False
    quiet = False

    asset_list_entry_length = 20
    asset_position_entry_length = 8

    print_info("info", "Decoding slab:\n" + data + "\n", verbose, quiet)

    # decode base64
    base64_bytes = data.encode('ascii')
    slab_compressed_data = base64.b64decode(base64_bytes)

    # decompress gzip
    slab_data = gzip.decompress(slab_compressed_data)
    print_info("info_quiet",
               "Binary slab data after first base64 decoding, then gzip unpacking:\n" + format_binary(slab_data) + "\n",
               verbose, quiet)
    print_info("info_quiet", "--- Starting to parse slab", verbose, quiet)
    print_info("info_quiet", "  - Decoding slab header and splitting data into parts", verbose, quiet)

    header = slab_data[:10]
    unique_asset_count = struct.unpack('I', header[6:])[0]
    asset_list = slab_data[len(header):len(header) + unique_asset_count * asset_list_entry_length]
    asset_position_list = slab_data[len(header) + len(asset_list):]

    print_info("info_quiet", "    Extracted header from binary slab data from indexes 0 to " + str(
        len(header)) + ", header is:\n      " + format_binary(header), verbose, quiet)
    print_info("info_quiet", "    Read unique asset count of " + str(
        unique_asset_count) + " from header. List length = unique_asset_count * 20 bytes per asset in list", verbose,
               quiet)
    print_info("info_quiet",
               "    Extracted asset list from binary slab data from indexes " + str(len(header)) + " to " + str(
                   (len(header) + len(asset_list))) + ", asset list is:\n" + format_binary(asset_list) + "\n", verbose,
               quiet)
    print_info("info_quiet", "    Extracted position list from binary data from index " + str(
        (len(header) + len(asset_list))) + " to the end:\n" + format_binary(asset_position_list) + "\n", verbose, quiet)

    # decode asset list
    print_info("info_quiet", "  - Decoding asset list", verbose, quiet)
    asset_data_list = []
    for i in range(unique_asset_count):
        asset_data = decode_asset(asset_list[i * asset_list_entry_length: (i + 1) * asset_list_entry_length], verbose,
                                  quiet)
        asset_data_list.append(asset_data)

    # decode asset positions
    print_info("info_quiet", "  - Decoding asset position list", verbose, quiet)
    dec_asset_count = 0
    while len(asset_position_list[dec_asset_count * asset_position_entry_length:]) > asset_position_entry_length:
        list_start = dec_asset_count * asset_position_entry_length
        list_end = (dec_asset_count + 1) * asset_position_entry_length
        asset_position_data = asset_position_list[list_start:list_end]

        position = decode_asset_position(asset_position_data, asset_data_list, dec_asset_count, verbose, quiet)
        asset_data_list[position[0]]["instances"].append(position[1])
        dec_asset_count += 1

    print_info("info_quiet", "  - Results", verbose, quiet)
    print_info("info_quiet", str(asset_data_list), verbose, quiet)

    out_json = {
        "unique_asset_count": unique_asset_count,
        "asset_data": asset_data_list
    }

    return out_json
