from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, \
    QFileDialog, QCheckBox, QPushButton, QProgressDialog, QSizePolicy, QTabWidget, QComboBox, QLabel, QMessageBox
from PyQt5.QtCore import QCoreApplication, QObject, QThread, pyqtSignal

import SLIX._cmd.VisualizeParameter
from .ImageWidget import ImageWidget, convert_numpy_to_qimage
import numpy
import matplotlib
from matplotlib import pyplot as plt


class VisualizationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = None
        self.sidebar = None
        self.sidebar_tabbar = None
        self.image_widget = None
        self.filename = None
        self.color_map = None

        self.parameter_map = None
        self.parameter_map_color_map = None
        self.parameter_map_tab_button_save = None

        self.fom = None
        self.fom_checkbox_weight_saturation = None
        self.fom_checkbox_weight_value = None
        self.fom_tab_button_generate = None
        self.fom_tab_save_button = None

        self.vector_field = None

        self.directions = None
        self.saturation_weighting = None
        self.value_weighting = None

        self.setup_ui()

    def setup_ui_image_widget(self):
        self.image_widget = ImageWidget()
        self.image_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def setup_ui(self):
        self.layout = QHBoxLayout()
        self.sidebar = QVBoxLayout()
        self.sidebar_tabbar = QTabWidget()
        self.sidebar_tabbar.addTab(self.setup_fom_tab(), 'FOM')
        self.sidebar_tabbar.addTab(self.setup_vector_tab(), 'Vector')
        self.sidebar_tabbar.addTab(self.setup_parameter_map_tab(), 'Parameter Map')
        self.sidebar.addWidget(self.sidebar_tabbar)

        self.setup_ui_image_widget()

        self.layout.addWidget(self.image_widget, stretch=7)
        self.layout.addLayout(self.sidebar, stretch=2)
        self.setLayout(self.layout)

    def setup_fom_tab(self):
        fom_tab = QWidget()
        fom_tab.layout = QVBoxLayout()

        fom_tab_button_open_measurement = QPushButton("Open Directions")
        fom_tab_button_open_measurement.clicked.connect(self.open_direction)
        fom_tab.layout.addWidget(fom_tab_button_open_measurement)

        fom_tab.layout.addStretch(3)

        fom_tab.layout.addWidget(QLabel("Color map:"))
        self.color_map = QComboBox()
        for cmap in SLIX._cmd.VisualizeParameter.available_colormaps.keys():
            self.color_map.addItem(cmap)
        fom_tab.layout.addWidget(self.color_map)

        fom_tab.layout.addStretch(1)

        self.fom_checkbox_weight_saturation = QCheckBox("Weight FOM by Saturation")
        self.fom_checkbox_weight_saturation.setChecked(False)
        fom_tab_button_open_saturation = QPushButton("Open Saturation weighting")
        fom_tab_button_open_saturation.setEnabled(False)
        fom_tab_button_open_saturation.clicked.connect(self.open_saturation_weighting)
        self.fom_checkbox_weight_saturation.stateChanged.connect(fom_tab_button_open_saturation.setEnabled)
        fom_tab.layout.addWidget(self.fom_checkbox_weight_saturation)
        fom_tab.layout.addWidget(fom_tab_button_open_saturation)

        fom_tab.layout.addStretch(1)

        self.fom_checkbox_weight_value = QCheckBox("Weight FOM by Value")
        self.fom_checkbox_weight_value.setChecked(False)
        fom_tab_button_open_value = QPushButton("Open Value weighting")
        fom_tab_button_open_value.setEnabled(False)
        fom_tab_button_open_value.clicked.connect(self.open_value_weighting)
        fom_tab.layout.addWidget(self.fom_checkbox_weight_value)
        fom_tab.layout.addWidget(fom_tab_button_open_value)
        self.fom_checkbox_weight_value.stateChanged.connect(fom_tab_button_open_value.setEnabled)

        fom_tab.layout.addStretch(3)

        self.fom_tab_button_generate = QPushButton("Generate")
        self.fom_tab_button_generate.clicked.connect(self.generate_fom)
        self.fom_tab_button_generate.setEnabled(False)
        fom_tab.layout.addWidget(self.fom_tab_button_generate)

        self.fom_tab_save_button = QPushButton("Save")
        self.fom_tab_save_button.clicked.connect(self.save_fom)
        self.fom_tab_save_button.setEnabled(False)
        fom_tab.layout.addWidget(self.fom_tab_save_button)

        fom_tab.setLayout(fom_tab.layout)
        return fom_tab

    def setup_vector_tab(self):
        vector_tab = QWidget()
        vector_tab.layout = QVBoxLayout()
        vector_tab.layout.addWidget(QCheckBox('Show Vector'))

        vector_tab.setLayout(vector_tab.layout)
        return vector_tab

    def setup_parameter_map_tab(self):
        parameter_map_tab = QWidget()
        parameter_map_tab.layout = QVBoxLayout()

        parameter_map_button_open = QPushButton("Open parameter map")
        parameter_map_button_open.clicked.connect(self.open_parameter_map)
        parameter_map_tab.layout.addWidget(parameter_map_button_open)

        parameter_map_tab.layout.addWidget(QLabel("Color map:"))
        self.parameter_map_color_map = QComboBox()
        for cmap in matplotlib.cm.cmap_d.keys():
            self.parameter_map_color_map.addItem(cmap)
        parameter_map_tab.layout.addWidget(self.parameter_map_color_map)
        self.parameter_map_color_map.setEnabled(False)
        self.parameter_map_color_map.currentIndexChanged.connect(self.generate_parameter_map)

        self.parameter_map_tab_button_save = QPushButton("Save preview")
        self.parameter_map_tab_button_save.clicked.connect(self.save_parameter_map)
        self.parameter_map_tab_button_save.setEnabled(False)
        parameter_map_tab.layout.addWidget(self.parameter_map_tab_button_save)

        parameter_map_tab.layout.addStretch()

        parameter_map_tab.setLayout(parameter_map_tab.layout)
        return parameter_map_tab

    def open_direction(self):
        filename = QFileDialog.getOpenFileNames(self, 'Open Directions', '.', '*.tiff;; *.h5;; *.nii')[0]
        if len(filename) > 0:
            try:
                direction_image = None
                filename.sort()
                for file in filename:
                    single_direction_image = SLIX.io.imread(file)
                    if direction_image is None:
                        direction_image = single_direction_image
                    else:
                        if len(direction_image.shape) == 2:
                            direction_image = numpy.stack((direction_image,
                                                           single_direction_image),
                                                          axis=-1)
                        else:
                            direction_image = numpy.concatenate((direction_image,
                                                                 single_direction_image
                                                                 [:, :, numpy.newaxis]),
                                                                axis=-1)
                self.directions = direction_image
                self.fom_tab_button_generate.setEnabled(True)
            except ValueError as e:
                QMessageBox.critical(self, 'Error',
                                     f'Could not load directions. Check your input files. Error message:\n{e}')

    def open_parameter_map(self):
        filename = QFileDialog.getOpenFileName(self, 'Open Parameter Map', '.', '*.tiff;; *.h5;; *.nii')[0]
        if len(filename) > 0:
            self.parameter_map = SLIX.io.imread(filename)
            self.parameter_map_tab_button_save.setEnabled(True)
            self.parameter_map_color_map.setEnabled(True)
            self.generate_parameter_map()

    def open_saturation_weighting(self):
        filename = QFileDialog.getOpenFileName(self, 'Open Saturation weight', '.', '*.tiff;; *.h5;; *.nii')[0]
        if len(filename) > 0:
            self.saturation_weighting = SLIX.io.imread(filename)

    def open_value_weighting(self):
        filename = QFileDialog.getOpenFileName(self, 'Open Value weight', '.', '*.tiff;; *.h5;; *.nii')[0]
        if len(filename) > 0:
            self.value_weighting = SLIX.io.imread(filename)

    def generate_fom(self):
        if self.fom_checkbox_weight_saturation.isChecked():
            saturation_weighting = self.saturation_weighting
        else:
            saturation_weighting = None
        if self.fom_checkbox_weight_value.isChecked():
            value_weighting = self.value_weighting
        else:
            value_weighting = None
        color_map = SLIX._cmd.VisualizeParameter.available_colormaps[self.color_map.currentText()]

        try:
            self.fom = SLIX.visualization.direction(self.directions, saturation=saturation_weighting,
                                                    value=value_weighting, colormap=color_map)

            self.image_widget.set_image(convert_numpy_to_qimage(self.fom))
            self.fom_tab_save_button.setEnabled(True)
        except ValueError as e:
            QMessageBox.critical(self, 'Error', f'Could not generate FOM. Check your input files.\n'
                                                f'Error message:\n{e}')

    def generate_parameter_map(self):
        colormap = matplotlib.cm.get_cmap(self.parameter_map_color_map.currentText())
        shown_image = self.parameter_map.copy()
        shown_image = shown_image.astype(numpy.float32)
        shown_image = (shown_image - shown_image.min()) / (shown_image.max() - shown_image.min())
        shown_image = colormap(shown_image)
        # Convert NumPy RGBA array to RGB array
        shown_image = shown_image[:, :, :3]
        self.image_widget.set_image(convert_numpy_to_qimage(shown_image))

    def save_fom(self):
        filename, datatype = QFileDialog.getSaveFileName(self, 'Save FOM', '.', '*.tiff;; *.h5')
        if len(filename) > 0:
            datatype = datatype[1:]
            if not filename.endswith(datatype):
                filename += datatype
            SLIX.io.imwrite_rgb(filename, self.fom)

    def save_parameter_map(self):
        filename, datatype = QFileDialog.getSaveFileName(self, 'Save Parameter Map', '.', '*.tiff;; *.h5')
        if len(filename) > 0:
            datatype = datatype[1:]
            if not filename.endswith(datatype):
                filename += datatype

            colormap = matplotlib.cm.get_cmap(self.parameter_map_color_map.currentText())
            shown_image = self.parameter_map.copy()
            shown_image = shown_image.astype(numpy.float32)
            shown_image = (shown_image - shown_image.min()) / (shown_image.max() - shown_image.min())
            shown_image = colormap(shown_image)
            shown_image = (255 * shown_image[:, :, :3]).astype(numpy.uint8)
            SLIX.io.imwrite_rgb(filename, shown_image)
