import hou
import os
import tempfile
from cryptography.fernet import Fernet


# Menu Functions
def ts_assets_menu():
    """Get a menu list of specific TaleSpire Asset IDs."""
    # TODO: For implementation
    pass


# Shared Data Node
def get_ts_database_node():
    shared_data_node = SharedData()
    return shared_data_node.get_database_node()


class SharedData:

    def __init__(self):
        """This class accesses and creates the TaleSpire_Shared_Data node containing the TS database
        needed from various nodes. This keeps the data in one place where it is cached for efficiency."""
        self.node_name = '_TaleSpire_Shared_Data_'
        self.shared_data_node = hou.node('/obj/{}'.format(self.node_name))
        if not self.shared_data_node:
            self.shared_data_node = hou.node('/obj').createNode('TaleSpire_Shared_Data', node_name=self.node_name)
            self.hide()

    def hide(self, state=True):
        self.shared_data_node.hide(state)

    def get_database_node(self):
        database_node = hou.node('{}/data/TS_Database'.format(self.shared_data_node.path()))
        return database_node

    def get_data_node(self):
        data_node = hou.node('{}/data'.format(self.shared_data_node.path()))
        return data_node

    def cook_database_node(self):
        database_node = self.get_database_node()
        database_node.cook(force=True)


# Network IO
def network_loading():
    """
    Gets the state from the Shared Data node if the contents of user editable networks should be loaded when a new
    node is placed.

    Returns:
        bool: The network loading state.
    """
    shared_data = SharedData()
    state = shared_data.shared_data_node.cachedUserData('network_loading')
    if state is None:
        state = True
    return state


def set_network_loading(state=True):
    """
    Sets the state on the Shared Data node of whether the loading of contents of user editable networks should be done.
    This information is not saved with the hip file, so new scenes will default to True.
    Args:
        state(bool):
    """
    shared_data = SharedData()
    shared_data.shared_data_node.setCachedUserData('network_loading', state)


def clear_network(net_node):
    """
    This clears all of the nodes and items inside of the given network node.
    Args:
        net_node: The hou.Node object of the node to clear.
    """
    net_node.deleteItems(net_node.allItems())


def load_networks(node=None, network_dict=None):
    htg_basedir = os.getenv('HTG_BASEDIR')

    if network_loading():
        for network in network_dict:
            net_node = hou.node(node.path() + '/' + network)
            filename = network_dict[network]
            # TODO: This is a placeholder for biome loading, it will likely need to be re-worked.
            if filename.endswith('.biome'):
                rel_path = 'scripts/data/biomes'
            else:
                rel_path = 'scripts/data/nodes'
            filepath = '/'.join((htg_basedir, rel_path, filename))
            nio = NetworkIO(net_node, filepath)
            nio.read_network()


def save_network(net_node=None, filename=None, mode='node', warn=True):
    htg_basedir = os.getenv('HTG_BASEDIR')

    if mode == 'node':
        file_path = '/'.join((htg_basedir, 'scripts/data/nodes', filename))
    elif mode == 'user':
        file_path = filename
    else:
        # TODO: Raise an execption
        file_path = None

    do_write = True

    if warn:
        if os.path.isfile(file_path):
            button_result = hou.ui.displayMessage('Warning: you are about to overwrite this network file.\n'
                                                  'Are you sure you want to do this?',
                                                  buttons=('OK', 'Cancel'),
                                                  details=file_path)
            if button_result != 0:
                do_write = False

    if do_write:
        hou.ui.displayMessage('overwritting')
        # net_io = NetworkIO(net_node, file_path)
        # net_io.add_all()
        # net_io.write_network()


class NetworkIO:

    def __init__(self, nodenet, data_file=None):
        self.nodenet = nodenet
        self.item_list = []
        self.file_descriptor = None
        self.temp_file = None
        self.shared_data = SharedData()
        self.data_file = data_file

    def clear_network(self):
        self.nodenet.deleteItems(self.item_list)

    def write_network(self):
        self.make_temp_file()
        os.close(self.file_descriptor)
        self.nodenet.saveItemsToFile(self.item_list, self.temp_file)
        with open(self.temp_file, 'rb') as f:
            file_data = f.read()
        self.clean_temp_file()
        encoded_data = self.encode_data(file_data)
        with open(self.data_file, 'wb') as f:
            f.write(encoded_data)

    def read_network(self):
        with open(self.data_file, 'rb') as f:
            file_data = f.read()
        decoded_data = self.decode_data(file_data)
        self.make_temp_file()
        os.close(self.file_descriptor)
        with open(self.temp_file, 'wb') as f:
            f.write(decoded_data)
        self.nodenet.loadItemsFromFile(self.temp_file, ignore_load_warnings=True)
        self.clean_temp_file()

    def add_all(self):
        self.item_list = self.nodenet.allItems()

    def add_item(self, item):
        self.item_list.append(item)

    def make_temp_file(self):
        self.file_descriptor, self.temp_file = tempfile.mkstemp()
        self.temp_file = self.temp_file.replace('\\', '/')

    def clean_temp_file(self):
        os.remove(self.temp_file)

    def encode_data(self, data):
        key = self.get_key()
        fernet = Fernet(key)
        encoded_data = fernet.encrypt(data)
        return encoded_data

    def decode_data(self, data):
        key = self.get_key()
        fernet = Fernet(key)
        decoded_data = fernet.decrypt(data)
        return decoded_data

    def get_key(self):
        data_node = self.shared_data.get_data_node()
        key = data_node.userData('ekey')
        return bytes(key, 'utf-8')

