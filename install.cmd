# Toolset Installation
#
# To run installation, launch Houdini, goto File->Run Script...
# Select this file and click "Run"

set base_dir = `strreplace($arg0, "/install.cmd", "")`
python ${base_dir}/scripts/python/htg/install_update.py $base_dir
