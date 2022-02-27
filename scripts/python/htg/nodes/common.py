import hou


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

    def cook_database_node(self):
        database_node = self.get_database_node()
        database_node.cook(force=True)
