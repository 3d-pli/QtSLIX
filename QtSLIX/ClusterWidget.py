import matplotlib
import numpy
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, \
    QMessageBox, QFileDialog, QLabel, QPushButton, QCheckBox, QSizePolicy, QHBoxLayout, QComboBox

from .ImageWidget import ImageWidget, convert_numpy_to_qimage
import SLIX
from SLIX._cmd import Cluster


class ClusterWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.folder = None

        self.layout = None
        self.sidebar = None
        self.image_widget = None

        self.sidebar_checkbox_all = None
        self.sidebar_checkbox_flat = None
        self.sidebar_checkbox_crossing = None
        self.sidebar_checkbox_inclined = None

        self.sidebar_button_preview = None
        self.sidebar_button_generate = None
        self.sidebar_button_open_folder = None

        self.sidebar_color_map = None

        self.setup_ui()

    def setup_ui(self):
        self.setup_ui_image_widget()
        self.setup_ui_sidebar()

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.image_widget, stretch=7)
        self.layout.addLayout(self.sidebar, stretch=2)
        self.setLayout(self.layout)

    def setup_ui_image_widget(self):
        self.image_widget = ImageWidget()
        self.image_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def setup_ui_sidebar(self):
        self.sidebar = QVBoxLayout()

        self.sidebar.addWidget(QLabel("<b>Open:</b>"))
        self.sidebar_button_open_folder = QPushButton("Folder")
        self.sidebar_button_open_folder.clicked.connect(self.open_folder)
        self.sidebar.addWidget(self.sidebar_button_open_folder)

        self.sidebar.addWidget(QLabel("Color map:"))
        self.sidebar_color_map = QComboBox()
        for cmap in matplotlib.cm.cmap_d.keys():
            self.sidebar_color_map.addItem(cmap)
        self.sidebar.addWidget(self.sidebar_color_map)
        self.sidebar_color_map.currentIndexChanged.connect(self.generate_preview)

        self.sidebar.addStretch(5)

        self.sidebar.addWidget(QLabel("<b>Parameter Maps:</b>"))

        self.sidebar_checkbox_all = QCheckBox("All")
        self.sidebar_checkbox_all.setChecked(True)
        self.sidebar.addWidget(self.sidebar_checkbox_all)

        self.sidebar_checkbox_inclined = QCheckBox("Inclined")
        self.sidebar_checkbox_inclined.setChecked(False)
        self.sidebar.addWidget(self.sidebar_checkbox_inclined)

        self.sidebar_checkbox_flat = QCheckBox("Flat")
        self.sidebar_checkbox_flat.setChecked(False)
        self.sidebar.addWidget(self.sidebar_checkbox_flat)

        self.sidebar_checkbox_crossing = QCheckBox("Crossing")
        self.sidebar_checkbox_crossing.setChecked(False)
        self.sidebar.addWidget(self.sidebar_checkbox_crossing)

        self.sidebar.addStretch(5)

        self.sidebar_button_preview = QPushButton("Preview all")
        self.sidebar_button_preview.clicked.connect(self.generate_preview)
        self.sidebar_button_preview.setEnabled(False)
        self.sidebar.addWidget(self.sidebar_button_preview)

        self.sidebar_button_generate = QPushButton("Save")
        self.sidebar_button_generate.clicked.connect(self.save)
        self.sidebar_button_generate.setEnabled(False)
        self.sidebar.addWidget(self.sidebar_button_generate)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", "")

        if not folder:
            return

        self.folder = folder
        self.sidebar_button_preview.setEnabled(True)
        self.sidebar_button_generate.setEnabled(True)

    def generate_preview(self):
        if self.folder is None:
            return

        loaded_parameter_maps, _ = Cluster.load_parameter_maps(self.folder)
        result_mask = SLIX.classification.full_mask(loaded_parameter_maps['high_prominence_peaks'],
                                                    loaded_parameter_maps['low_prominence_peaks'],
                                                    loaded_parameter_maps['peakdistance'],
                                                    loaded_parameter_maps['max'])

        colormap = matplotlib.cm.get_cmap(self.sidebar_color_map.currentText())
        shown_image = result_mask.copy()
        shown_image = shown_image.astype(numpy.float32)
        shown_image = (shown_image - shown_image.min()) / (shown_image.max() - shown_image.min())
        shown_image = colormap(shown_image)
        # Convert NumPy RGBA array to RGB array
        shown_image = shown_image[:, :, :3]
        self.image_widget.set_image(convert_numpy_to_qimage(shown_image))

    def save(self):
        pass
