import json
import os
import sys

from distutils.version import LooseVersion
from pathlib import Path

import hou

from PySide2.QtWidgets import (
    QPushButton, QDialog, QStackedWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QCheckBox,
    QComboBox, QSizePolicy, QTextEdit
)
from PySide2.QtCore import Qt


def make_package_file(htg_dir=None):
    user_pref_dir = os.environ.get("HOUDINI_USER_PREF_DIR")
    package_filename = f"{user_pref_dir}/packages/HTTGT.json"
    package_file = Path(package_filename)
    package_file.mkdir(exist_ok=True, parents=True)

    json_data = { "package_path": f"{htg_dir}/packages" }

    with package_file.open("w", encoding="UTF-8") as f:
        json.dump(json_data, f, indent=4)


def get_branches():
    import requests
    if hasattr(hou.session, "htg_branches") and hou.session.htg_branches is not None:
        return hou.session.htg_branches
    else:
        repo_url = os.environ.get("HTG_REPO_URL")
        if repo_url:
            branches_url = f"{repo_url}/branches"

            response = requests.get(branches_url)
            if response.status_code == 200:
                branches = response.json()
                branch_list = []
                for branch in branches:
                    branch_list.append(branch["name"])
                hou.session.htg_branches = branch_list
                return branch_list


def get_releases():
    import requests
    if hasattr(hou.session, "htg_releases") and hou.session.htg_releases is not None:
        return hou.session.htg_releases
    else:
        repo_url = os.environ.get("HTG_REPO_URL")
        if repo_url:
            repo = f"{repo_url}/releases?per_page=10&page=1"
            response = requests.get(repo)
            releases = response.json()
            hou.session.htg_releases = releases
            return releases


def get_current_version():
    from version import version as current_version
    return current_version


def version_text(branch="dev", new_version="00.00.00"):
    current_version = get_current_version()
    is_newer = LooseVersion(new_version.lstrip("v")) > LooseVersion(current_version)
    if is_newer:
        ver_color = "green"
    else:
        ver_color = "red"

    text = f"""<p>Current Version: <span style="color:yellow; font-weight:bold;">v{current_version}</span></p>"""

    if branch == "release":
        text +=    f"""<p>Release Version: <span style="color:{ver_color}; font-weight:bold;">{new_version}</span></p>"""
    else:
        text += f"""<p>Branch Version: <span style="color:red; font-weight:bold;">Unknown</span>-<span 
        style="font-weight:bold;">{branch}</span></p>"""
        text += f"""<p></p><p><span style="color:red; font-weight:bold;">Warning!</span> 
        Branch versions could be older than your current version.</p>"""
    return text

class InstallDialog(QDialog):

    LABEL_WIDTH = 50

    def __init__(self, cmd_path=None):
        parent = hou.qt.mainWindow()
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("HTG Toolset Install/Update")
        self.setMinimumWidth(600)

        hou.session.install_dialog = self

        if cmd_path:
            self.ran_from_cmd = True
            self.cmd_path = cmd_path
        else:
            self.ran_from_cmd = False
            self.cmd_path = None

        self.install_exists = False
        htg_basedir = os.environ.get("HTG_BASEDIR")
        try:
            htg_path = Path(htg_basedir)
        except TypeError:
            htg_path = None

        if htg_path and htg_path.is_dir():
            self.install_exists = True

        if self.ran_from_cmd and self.install_exists:
            if htg_path == self.cmd_path:
                self.start_page = "ManualUpdate"
            else:
                self.start_page = "AlreadyInstalled"
        elif self.ran_from_cmd:
            self.start_page = "NewInstall"
        else:
            self.start_page = "Update"

        self.install_in_place = None
        self.install_location = None
        self.browse_button = None
        self.branch_combo = None
        self.release_combo = None
        self.version_label = None
        self.install_window = None
        self.done_button = None

        self.pages = []
        self.stack = QStackedWidget(self)
        self.pages.append("ManualUpdate")
        self.init_manual_update_page()

        self.pages.append("AlreadyInstalled")
        self.init_already_installed_page()

        self.pages.append("NewInstall")
        self.init_setup_page()

        self.pages.append("Update")
        self.init_update_page()

        self.pages.append("Installation")
        self.init_installation_page()

        self.stack.setCurrentIndex(self.pages.index(self.start_page))

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

    def init_setup_page(self):
        page_setup = QVBoxLayout()
        self.install_in_place = QCheckBox("Install in Place")
        self.install_in_place.setChecked(False)
        self.install_in_place.stateChanged.connect(self.toggle_install_location)

        install_location_label = QLabel("Install Location:")
        self.install_location = QLineEdit()
        self.install_location.setReadOnly(True)
        self.browse_button = QPushButton(text="Browse")
        self.browse_button.clicked.connect(self.select_directory)

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.install_location)
        h_layout.addWidget(self.browse_button)

        ok_button = QPushButton("Okay")
        ok_button.clicked.connect(self.start_installation)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(ok_button)
        btn_layout.addWidget(cancel_button)

        page_setup.addWidget(self.install_in_place)
        page_setup.addWidget(install_location_label)
        page_setup.addLayout(h_layout)
        page_setup.addLayout(btn_layout)

        widget = QDialog()
        widget.setLayout(page_setup)
        self.stack.addWidget(widget)

        self.toggle_install_location()

    def toggle_install_location(self):
        is_checked = self.install_in_place.isChecked()
        self.install_location.setEnabled(not is_checked)
        self.browse_button.setEnabled(not is_checked)

    def select_directory(self):
        directory = hou.ui.selectFile(file_type=hou.fileType.Directory)
        if directory:
            self.install_location.setText(directory)

    def start_installation(self):
        self.stack.setCurrentIndex(self.pages.index("Installation"))

    def init_manual_update_page(self):
        page_setup = QVBoxLayout()
        label = QLabel("Manual Update Page")
        page_setup.addWidget(label)
        widget = QDialog()
        widget.setLayout(page_setup)
        self.stack.addWidget(widget)

    def init_already_installed_page(self):
        page_setup = QVBoxLayout()
        label = QLabel("install.cmd ran from existing Install.")
        page_setup.addWidget(label)
        widget = QDialog()
        widget.setLayout(page_setup)
        self.stack.addWidget(widget)

    def init_update_page(self):
        page_setup = QVBoxLayout()
        page_setup.setAlignment(Qt.AlignTop)

        branch_layout = QHBoxLayout()
        branch_label = QLabel("Branch:")
        branch_label.setFixedWidth(self.LABEL_WIDTH)
        label_height = branch_label.sizeHint().height()
        branch_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.branch_combo = QComboBox()
        self.branch_combo.addItem("Current Release")
        self.branch_combo.addItem("Older Release")
        skip_branches = ("master", "main")
        skip_branches = ()
        for branch in get_branches():
            if branch not in skip_branches:
                self.branch_combo.addItem(branch)
        self.branch_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.branch_combo.setFixedHeight(label_height+10)

        self.release_combo = QComboBox()
        for release in get_releases():
            self.release_combo.addItem(release["name"])
        self.release_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.release_combo.setFixedHeight(label_height + 10)
        self.release_combo.setVisible(False)

        self.branch_combo.currentIndexChanged.connect(self.branch_updated)
        self.release_combo.currentIndexChanged.connect(self.branch_updated)

        branch_layout.addWidget(branch_label)
        branch_layout.addWidget(self.branch_combo)
        branch_layout.addWidget(self.release_combo)
        branch_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        page_setup.addLayout(branch_layout)

        self.version_label = QLabel("")
        self.version_label.setAlignment(Qt.AlignLeft)

        page_setup.addWidget(self.version_label)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        dl_cancel_button = QPushButton("Cancel")
        dl_cancel_button.clicked.connect(self.reject)
        dl_install_button = QPushButton("Download/Install")
        dl_install_button.clicked.connect(self.start_installation)
        button_layout.addWidget(dl_cancel_button)
        button_layout.addWidget(dl_install_button)

        page_setup.addStretch()
        page_setup.addLayout(button_layout)

        widget = QDialog()
        widget.setLayout(page_setup)
        self.stack.addWidget(widget)

        self.branch_updated()

    def branch_updated(self):
        branch_value = self.branch_combo.currentText()
        release_visible = branch_value == "Older Release"

        self.release_combo.setVisible(release_visible)

        branch = branch_value
        if branch in ["Current Release", "Older Release"]:
            branch = "release"

        new_version = self.release_combo.currentText()
        if branch_value == "Current Release":
            new_version = get_releases()[0]["name"]
        self.version_label.setText(version_text(branch=branch, new_version=new_version))

    def init_installation_page(self):
        page_setup = QVBoxLayout()
        page_setup.setAlignment(Qt.AlignTop)
        label = QLabel("Installing...")
        self.install_window = QTextEdit()
        self.install_window.setReadOnly(True)

        page_setup.addWidget(label)
        page_setup.addWidget(self.install_window)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignRight)
        self.done_button = QPushButton("Done")
        self.done_button.setEnabled(False)
        button_layout.addWidget(self.done_button)

        page_setup.addLayout(button_layout)

        widget = QDialog()
        widget.setLayout(page_setup)
        self.stack.addWidget(widget)


def show(cmd_path=None):
    if hasattr(hou.session, "install_dialog") and hou.session.install_dialog is not None:
        try:
            hou.session.install_dialog.close()
        except:
            pass

    dialog = InstallDialog(cmd_path=cmd_path)
    hou.session.install_dialog = dialog
    dialog.show()

# This checks to see if this script was executed from a menu within Houdini, if so it launches the dialog.
try:
    open_dialog = "toolname" in kwargs
except NameError:
    open_dialog = False

if open_dialog:
    show()

# This runs if executed from the Run command in Houdini or from the command line.
if __name__ == "__main__":
    try:
        cmd_base_dir = sys.argv[1]
        show(cmd_path=cmd_base_dir)
    except IndexError:
        show()
