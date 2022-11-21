# This is a configuration file for Houdini it runs whenever houdini launches or a scene is loaded.
import os
import hou

# Hide the TaleSpire Shared Data node from users, it is best if this node is handled by the system.
# To make this node available set an environment variable HTTGT_DEV = 1
dev_mode = os.getenv('HTTGT_DEV', '0') == '1'
data_node_type = hou.nodeType('Object/TaleSpire_Shared_Data')
data_node_type.setHidden(not dev_mode)
