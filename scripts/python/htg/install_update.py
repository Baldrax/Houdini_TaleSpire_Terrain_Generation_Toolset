from __future__ import annotations

import json
import os
import requests
import shutil
import sys
import tempfile
import warnings
import zipfile

warnings.filterwarnings("ignore", category=DeprecationWarning)
# TODO: distutils is deprecated and will likely not be available in python 3.13, will
#       need to find an alternative version comparison without installing python modules.
from distutils.version import LooseVersion
from pathlib import Path

import hou

from PySide2.QtWidgets import (
    QPushButton, QDialog, QStackedWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QCheckBox,
    QComboBox, QSizePolicy, QTextEdit
)
from PySide2.QtCore import Qt, QThread, Signal
from PySide2.QtGui import QTextCursor, QTextCharFormat, QColor

REPO_NAME = "Baldrax/Houdini_TaleSpire_Terrain_Generation_Toolset"

# Options for Development and Debugging
DEBUG = False
START_PAGE = None
INSTALL_EXISTS = False
REPORT_ONLY = True

# Log Colors
DATA = "#b38600" # Dark Amber
FILES = "gray"
STEP = "yellow"
DOTS = "default"
DONE = "green"
INFO = "cyan"
WARN = "red"

def make_package_file(htg_dir: str | None = None):
    user_pref_dir = os.environ.get("HOUDINI_USER_PREF_DIR")
    package_filename = f"{user_pref_dir}/packages/HTTGT.json"
    package_file = Path(package_filename)
    package_file.mkdir(exist_ok=True, parents=True)

    package_path = htg_dir / "packages"

    json_data = { "package_path": f"{package_path}" }

    with package_file.open("w", encoding="UTF-8") as f:
        json.dump(json_data, f, indent=4)


def get_branches() -> list:
    if hasattr(hou.session, "htg_branches") and hou.session.htg_branches is not None:
        return hou.session.htg_branches
    else:
        repo_name = os.environ.get("HTG_REPO_NAME")
        if repo_name is None:
            repo_name = REPO_NAME
        repo_url = f"https://api.github.com/repos/{repo_name}"
        branches_url = f"{repo_url}/branches"

        response = requests.get(branches_url)
        if response.status_code == 200:
            branches = response.json()
            branch_list = []
            for branch in branches:
                branch_list.append(branch["name"])
            hou.session.htg_branches = branch_list
            return branch_list


def get_releases() -> list:
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


def get_current_version() -> str:
    from version import version as current_version
    return current_version


def version_text(branch: str = "release", new_version: str | None = None) -> str:
    current_version = get_current_version()

    ver_color = "red"
    if new_version:
        is_newer = LooseVersion(new_version.lstrip("v")) > LooseVersion(current_version)
        if is_newer:
            ver_color = "green"

    text = f"""<p>Current Version: <span style="color:yellow; font-weight:bold;">v{current_version}</span></p>"""

    if branch == "release":
        text +=    f"""<p>Release Version: <span style="color:{ver_color}; font-weight:bold;">{new_version}</span></p>"""
    else:
        text += f"""<p>Branch Version: <span style="color:red; font-weight:bold;">Unknown</span>-<span 
        style="font-weight:bold;">{branch}</span></p>"""
        text += f"""<p></p><p><span style="color:red; font-weight:bold;">Warning!</span> 
        Branch versions could be older than your current version.</p>"""
    return text


class InstallationWorker(QThread):
    log_update = Signal(str, str)  # message, color
    completed = Signal()

    def __init__(
            self,
            install_type: str | None = None,
            new_install: bool = False,
            dl_url: str | None = None,
            source_dir: Path | None = None,
            destination_dir: Path | None = None
    ):
        super().__init__()
        # type: "download", "copy", "in-place"
        self.install_type = install_type
        self.new_install = new_install
        self.dl_url = dl_url
        self.source_dir = source_dir
        self.destination_dir = destination_dir

        self.do_download = self.install_type == "download"
        self.do_copy = self.do_download or self.install_type == "copy"

        self.report_only = False
        if DEBUG and REPORT_ONLY:
            self.report_only = True

    def run(self):
        source_dir = self.source_dir

        temp_dir = None
        if self.do_download:
            temp_dir = tempfile.TemporaryDirectory()
            self.log_update.emit(f"Temp File Created:\n", DATA)
            self.log_update.emit(f"{Path(temp_dir.name)}\n", FILES)

            zip_file = Path(temp_dir.name) / "sourcefile.zip"
            source_dir = Path(temp_dir.name) / "sourcedir"

            self.log_update.emit(f"Source URL:\n", DATA)
            self.log_update.emit(f" {self.dl_url}\n", FILES)
            self.log_update.emit(f"File Destination:\n", DATA)
            self.log_update.emit(f"{zip_file}\n", FILES)

            self.log_update.emit("Downloading ", STEP)
            if not self.report_only:
                self.download_file(self.dl_url, zip_file)
            self.log_update.emit(" Done\n\n", DONE)

            self.log_update.emit(f"Unzipping To:\n", DATA)
            self.log_update.emit(f"{source_dir}\n", FILES)
            self.log_update.emit("Unzipping ", STEP)
            self.log_update.emit("..", DOTS)
            if not self.report_only:
                with zipfile.ZipFile(zip_file, 'r') as zipf:
                    zipf.extractall(source_dir)
            self.log_update.emit(" Done\n\n", DONE)

            # Set the source_dir to the directory inside the unzipped directory
            unzipped_dir = None
            if not self.report_only:
                for item in source_dir.iterdir():
                    unzipped_dir = item
                if unzipped_dir:
                    source_dir = unzipped_dir

        if self.do_copy:
            self.log_update.emit("Copy Source:\n", DATA)
            self.log_update.emit(f"{source_dir}\n", FILES)
            self.log_update.emit("Copy Destination:\n", DATA)
            self.log_update.emit(f"{self.destination_dir}\n", FILES)

            if not self.report_only:
                self.destination_dir.mkdir(parents=True, exist_ok=True)

            self.log_update.emit("Copying Files ", STEP)
            files = list(source_dir.rglob("*"))
            file_counter = 0
            for file in files:
                dest_path = self.destination_dir / file.relative_to(source_dir)
                if file.is_dir():
                    if not self.report_only:
                        dest_path.mkdir(parents=True, exist_ok=True)
                else:
                    if not self.report_only:
                        shutil.copy2(file, dest_path)
                    if file_counter > 0:
                        # Emit a . every other file copied.
                        self.log_update.emit(".", DOTS)
                        file_counter = 0
                    else:
                        file_counter += 1
            self.log_update.emit(" Done\n\n", DONE)

        if self.new_install:
            self.log_update.emit("Creating Package File ", STEP)
            self.log_update.emit("..", DOTS)
            if not self.report_only:
                make_package_file(self.destination_dir)
            self.log_update.emit(" Done\n\n", DONE)

        if self.do_download:
            self.log_update.emit("Cleaning Up Temp Files ", STEP)
            self.log_update.emit("..", DOTS)
            if temp_dir:
                temp_dir.cleanup()
                self.log_update.emit("..", DOTS)
            self.log_update.emit(" Done\n\n", DONE)

        self.log_update.emit("Relaunch Houdini for changes to take effect.\n", INFO)

        self.completed.emit()

    def download_file(self, url: str, dest_path: Path):
        """
        Download a file with in-progress updates.
        Args:
            url:
            dest_path:
        """
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get("content-length", 0))
        chunk_size = 1024*100
        downloaded = 0

        with dest_path.open("wb") as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)
                    # percent_done = (downloaded / total_size) * 100
                    self.log_update.emit(".", DOTS)

class InstallDialog(QDialog):

    LABEL_WIDTH = 50

    def __init__(self, cmd_path: str | None = None):
        parent = hou.qt.mainWindow()
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("HTG Toolset Install/Update")
        self.setMinimumWidth(600)

        hou.session.install_dialog = self

        if cmd_path:
            self.ran_from_cmd = True
            self.cmd_path = Path(cmd_path)
        else:
            self.ran_from_cmd = False
            self.cmd_path = None

        self.install_exists = False
        htg_basedir = os.environ.get("HTG_BASEDIR")
        try:
            self.htg_path = Path(htg_basedir)
        except TypeError:
            self.htg_path = None

        if self.htg_path and self.htg_path.is_dir():
            self.install_exists = True

        if self.ran_from_cmd and self.install_exists:
            if self.htg_path == self.cmd_path:
                self.start_page = "AlreadyInstalled"
            else:
                self.start_page = "ManualUpdate"
        elif self.ran_from_cmd:
            self.start_page = "NewInstall"
        else:
            self.start_page = "Update"

        if DEBUG:
            if START_PAGE:
                self.start_page = START_PAGE
            if INSTALL_EXISTS:
                self.install_exists = INSTALL_EXISTS

        self.install_in_place = None
        self.install_location = None
        self.browse_button = None
        self.branch_combo = None
        self.install_directory_label = None
        self.toolset_directory_name_label = None
        self.release_combo = None
        self.version_label = None
        self.install_window = None
        self.install_color = None
        self.toolset_directory_name = None
        self.done_button = None
        self.worker = None

        # The pages list is used to keep track of the stack index,
        # so we can look up the page by name instead of index.
        self.pages = []
        self.stack = QStackedWidget(self)
        self.pages.append("ManualUpdate")
        self.init_manual_update_page()

        self.pages.append("AlreadyInstalled")
        self.init_already_installed_page()

        self.pages.append("NewInstall")
        self.init_new_install_page()

        self.pages.append("Update")
        self.init_update_page()

        # The Installation Page is the only page that should not be a start page.
        self.pages.append("Installation")
        self.init_installation_page()

        if self.start_page == "Update":
            # The Update page needs to check GitHub for updates and will not work during a new installation.
            #  This ensures that the update page is only activated when it is called for which should only
            #  be in an environment where the toolset is already installed.
            self.activate_update_page()
        else:
            self.stack.setCurrentIndex(self.pages.index(self.start_page))

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

    def init_new_install_page(self):
        # Base page layout
        page_setup = QVBoxLayout()
        page_setup.setAlignment(Qt.AlignTop)

        label = QLabel("<h3>New Install</h3><hr>")
        page_setup.addWidget(label)

        # Install in Place Toggle
        self.install_in_place = QCheckBox("Install in Place")
        self.install_in_place.setToolTip("If enabled the toolset will be used from its current location. "
                                         "No files will be moved.\n"
                                         "This can Also be used to set up the toolset to use with a new major version "
                                         "of Houdini.")
        self.install_in_place.setChecked(False)
        self.install_in_place.stateChanged.connect(self.toggle_install_location)
        page_setup.addWidget(self.install_in_place)

        # Install Directory Label
        self.install_directory_label = QLabel("Select the base directory where the toolset will be installed.\n"
                                         "The toolset directory will be created inside this directory:")
        page_setup.addWidget(self.install_directory_label)

        # Install Location Row
        h_layout = QHBoxLayout()
        self.install_location = QLineEdit()
        self.install_location.setText("$HOME/TaleSpire/")
        self.browse_button = QPushButton(text="Browse")
        self.browse_button.clicked.connect(self.select_directory)

        h_layout.addWidget(self.install_location)
        h_layout.addWidget(self.browse_button)
        page_setup.addLayout(h_layout)

        # Toolset Directory
        self.toolset_directory_name_label = QLabel("Toolset Directory Name:")
        self.toolset_directory_name = QLineEdit("Houdini_TaleSpire_Terrain_Generation_Toolset")
        self.toolset_directory_name.textChanged.connect(self.toolset_dir_name_changed)
        page_setup.addWidget(self.toolset_directory_name_label)
        page_setup.addWidget(self.toolset_directory_name)

        # Bottom Button Row
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignRight)

        ok_button = QPushButton("Okay")
        ok_button.clicked.connect(self.start_installation_from_new_install)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        btn_layout.addWidget(cancel_button)
        btn_layout.addWidget(ok_button)

        page_setup.addStretch()
        page_setup.addLayout(btn_layout)

        # Page Addition
        widget = QDialog()
        widget.setLayout(page_setup)
        self.stack.addWidget(widget)

        # Initialize Page
        self.toggle_install_location()

    def init_already_installed_page(self):
        page_setup = QVBoxLayout()
        page_setup.setAlignment(Qt.AlignTop)
        label = QLabel("<h3>Toolset Already Installed</h3>"
                       "<hr>"
                       "<p>It appears that this version of the toolset is already installed and ready to use. "
                       "If you've downloaded and unzipped a new version of the toolset, <b>Cancel</b> this dialog and "
                       "run the install.cmd file from that location. Otherwise you can <b>Check for Updates</b>.</p>")
        label.setWordWrap(True)
        page_setup.addWidget(label)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignRight)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        update_button = QPushButton("Check for Updates")
        update_button.clicked.connect(self.activate_update_page)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(update_button)

        page_setup.addStretch()
        page_setup.addLayout(button_layout)

        widget = QDialog()
        widget.setLayout(page_setup)
        self.stack.addWidget(widget)

    def init_manual_update_page(self):
        page_setup = QVBoxLayout()
        page_setup.setAlignment(Qt.AlignTop)
        label = QLabel("<h3>Manual Update</h3>"
                       "<hr>"
                       "<p>The toolset is already installed in another location. You can &quot;<b>Overwrite Existing "
                       "Version</b>&quot; with this version or &quot;<b>Install New</b>&quot;, installing this "
                       "version in-place or in a new location.")
        label.setWordWrap(True)
        page_setup.addWidget(label)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignRight)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        overwrite_button = QPushButton("Overwrite Existing Version")
        overwrite_button.clicked.connect(self.start_installation_from_manual_update)
        install_button = QPushButton("Install New")
        install_button.clicked.connect(lambda: self.stack.setCurrentIndex(self.pages.index("NewInstall")))

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(install_button)
        button_layout.addWidget(overwrite_button)

        page_setup.addStretch()
        page_setup.addLayout(button_layout)

        widget = QDialog()
        widget.setLayout(page_setup)
        self.stack.addWidget(widget)

    def init_update_page(self):
        page_setup = QVBoxLayout()
        page_setup.setAlignment(Qt.AlignTop)

        label = QLabel("<h3>Toolset Update</h3><hr>")
        page_setup.addWidget(label)

        branch_layout = QHBoxLayout()
        branch_label = QLabel("Branch:")
        branch_label.setFixedWidth(self.LABEL_WIDTH)
        label_height = branch_label.sizeHint().height()
        branch_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.branch_combo = QComboBox()
        self.branch_combo.addItem("Current Release")
        self.branch_combo.addItem("Older Release")
        skip_branches = ("master", "main")
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
        dl_install_button.clicked.connect(self.start_installation_from_update)
        button_layout.addWidget(dl_cancel_button)
        button_layout.addWidget(dl_install_button)

        page_setup.addStretch()
        page_setup.addLayout(button_layout)

        widget = QDialog()
        widget.setLayout(page_setup)
        self.stack.addWidget(widget)

    def init_installation_page(self):
        page_setup = QVBoxLayout()
        page_setup.setAlignment(Qt.AlignTop)
        label = QLabel("<h3>Installing...</h3>")
        self.install_window = QTextEdit()
        self.install_window.setReadOnly(True)
        self.install_color = self.install_window.palette().color(self.install_window.foregroundRole())

        page_setup.addWidget(label)
        page_setup.addWidget(self.install_window)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignRight)
        self.done_button = QPushButton("Done")
        self.done_button.setEnabled(False)
        self.done_button.clicked.connect(self.accept)
        button_layout.addWidget(self.done_button)

        page_setup.addLayout(button_layout)

        widget = QDialog()
        widget.setLayout(page_setup)
        self.stack.addWidget(widget)

    # New Install Page Functions
    def toggle_install_location(self):
        is_checked = self.install_in_place.isChecked()
        self.install_location.setEnabled(not is_checked)
        self.browse_button.setEnabled(not is_checked)
        self.toolset_directory_name.setEnabled(not is_checked)
        self.toolset_directory_name_label.setEnabled(not is_checked)
        self.install_directory_label.setEnabled(not is_checked)

    def select_directory(self):
        directory = hou.ui.selectFile(file_type=hou.fileType.Directory, start_directory=self.install_location.text())
        if directory:
            self.install_location.setText(directory)

    def toolset_dir_name_changed(self):
        dir_name = self.toolset_directory_name.text()
        char_list = ["/", "\\", " ", "|", "+", "@", "#", "!", "*", ";", ":", "'", '"']
        for char in char_list:
            if char in dir_name:
                dir_name = dir_name.replace(char, "_")
        self.toolset_directory_name.setText(dir_name)

    # Update Page Functions
    def activate_update_page(self):
        self.stack.setCurrentIndex(self.pages.index("Update"))
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

    # Installation Functions
    def start_installation(self,
                           install_type: str = "",
                           new_install: bool = False,
                           dl_url: str | None = None,
                           source_dir: Path | None = None,
                           destination_dir: Path | None = None):

        self.stack.setCurrentIndex(self.pages.index("Installation"))

        self.worker = InstallationWorker(
            install_type=install_type,
            new_install=new_install,
            dl_url=dl_url,
            source_dir=source_dir,
            destination_dir=destination_dir)

        self.worker.log_update.connect(self.update_install)
        self.worker.completed.connect(self.install_done)
        self.worker.start()

    def start_installation_from_new_install(self):
        # Gather Data
        if self.install_in_place.isChecked():
            install_type = "in-place"
            destination_dir = None
        else:
            install_type = "copy"
            base_dir = Path(hou.expandString(self.install_location.text()))
            dir_name = hou.expandString(self.toolset_directory_name.text())
            destination_dir = base_dir / dir_name

        self.start_installation(
            install_type=install_type,
            new_install=True,
            source_dir=self.cmd_path,
            destination_dir=destination_dir
        )

    def start_installation_from_update(self):
        # Gather Data
        branch = self.branch_combo.currentText()
        if branch == "Current Release":
            dl_url = hou.session.htg_releases[0]["zipball_url"]
        elif branch == "Older Release":
            dl_url = hou.session.htg_releases[self.release_combo.currentIndex()]["zipball_url"]
        else:
            repo_name = os.environ.get("HTG_REPO_NAME")
            if repo_name is None:
                repo_name = REPO_NAME
            repo_url = f"https://github.com/{repo_name}"
            dl_url = f"{repo_url}/archive/refs/heads/{branch}.zip"

        destination_dir = self.htg_path

        self.start_installation(
            install_type="download",
            dl_url=dl_url,
            destination_dir=destination_dir
        )

    def start_installation_from_manual_update(self):
        self.start_installation(
            install_type="copy",
            source_dir=self.cmd_path,
            destination_dir=self.htg_path
        )

    def update_install(self, message, color):
        cursor = self.install_window.textCursor()
        cursor.movePosition(QTextCursor.End)

        text_format = QTextCharFormat()
        if color == "default":
            text_format.setForeground(self.install_color)
        else:
            text_format.setForeground(QColor(color))
        cursor.setCharFormat(text_format)
        cursor.insertText(message)

        self.install_window.setTextCursor(cursor)
        self.install_window.ensureCursorVisible()

    def install_done(self):
        self.done_button.setEnabled(True)

    # Unused
    def insert_colored_text(self, widget, color, text):
        cursor = widget.textCursor()
        char_format = QTextCharFormat()

        if color == "default":
            char_format.setForeground(self.install_color)
        else:
            char_format.setForeground(QColor(color))

        cursor.setCharFormat(char_format)
        cursor.insertText(text)


def show(cmd_path: str | None = None):
    # If the dialog already exists in hou.session close it before opening another one.
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
