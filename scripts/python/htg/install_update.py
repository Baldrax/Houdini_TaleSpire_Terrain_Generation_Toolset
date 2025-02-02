import json
import os
import sys

from pathlib import Path

import hou

from PySide2.QtWidgets import (
    QPushButton, QDialog, QStackedWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QCheckBox
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


class InstallDialog(QDialog):

    def __init__(self, cmd_path=None):
        parent = hou.qt.mainWindow()
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("HTG Toolset Install/Update")
        self.setMinimumWidth(400)

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

        self.pages.append("CopyingFiles")
        self.init_progress_page()

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
        pass

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
        label = QLabel("Update Page")
        page_setup.addWidget(label)
        widget = QDialog()
        widget.setLayout(page_setup)
        self.stack.addWidget(widget)

    def init_progress_page(self):
        page_setup = QVBoxLayout()
        label = QLabel("Progress Page")
        page_setup.addWidget(label)
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
    show()
except NameError:
    open_dialog = False

if __name__ == "__main__":
    try:
        cmd_base_dir = sys.argv[1]
        show(cmd_path=cmd_base_dir)
    except IndexError:
        show()
