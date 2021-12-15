import time

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, \
    QFileDialog, QCheckBox, QPushButton, QProgressDialog, QSizePolicy, QTabWidget, QComboBox, QLabel, QMessageBox, \
    QDoubleSpinBox
from PyQt5.QtCore import QCoreApplication, QThread, QLocale

import SLIX._cmd.VisualizeParameter
from .ImageWidget import ImageWidget, convert_numpy_to_qimage
from .ThreadWorkers.Visualization import FOMWorker
import numpy
import matplotlib
from matplotlib import pyplot as plt


class VisualizationWidget(QWidget):
    """
    This class is the main widget for the visualization of the SLIX data.
    """

    def __init__(self):
        super().__init__()
        self.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))

        self.layout = None
        self.sidebar = None
        self.sidebar_tabbar = None
        self.image_widget = None
        self.filename = None

        self.parameter_map = None
        self.parameter_map_color_map = None
        self.parameter_map_tab_button_save = None

        self.directions = None
        self.inclinations = None

        self.fom = None
        self.fom_checkbox_weight_saturation = None
        self.fom_checkbox_weight_value = None
        self.fom_tab_button_generate = None
        self.fom_tab_save_button = None
        self.fom_color_map = None
        self.saturation_weighting = None
        self.value_weighting = None

        self.vector_field = None
        self.vector_checkbox_weight_value = None
        self.vector_tab_alpha_parameter = None
        self.vector_tab_thinout_parameter = None
        self.vector_tab_scale_parameter = None
        self.vector_tab_vector_width_parameter = None
        self.vector_tab_dpi_parameter = None
        self.vector_tab_button_generate = None
        self.vector_tab_save_button = None
        self.vector_checkbox_activate_distribution = None
        self.vector_tab_threshold_parameter = None
        self.vector_background = None
        self.vector_weighting = None
        self.vector_color_map = None

        self.setup_ui()

    def setup_ui_image_widget(self) -> None:
        """
        This method sets up the image widget.

        Returns:
            None
        """
        self.image_widget = ImageWidget()
        self.image_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def setup_ui(self) -> None:
        """
        This method sets up the main widget.

        Returns:
            None
        """
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

    def setup_fom_tab(self) -> QWidget:
        """
        This method sets up the FOM tab.

        Returns:
            QWidget: The FOM tab.
        """
        fom_tab = QWidget()
        fom_tab.layout = QVBoxLayout()

        fom_tab_button_open_measurement = QPushButton("Open Directions")
        fom_tab_button_open_measurement.clicked.connect(self.open_direction)
        fom_tab.layout.addWidget(fom_tab_button_open_measurement)

        fom_tab_button_open_inclination = QPushButton("Open Inclination")
        fom_tab_button_open_inclination.clicked.connect(self.open_inclination)
        fom_tab.layout.addWidget(fom_tab_button_open_inclination)

        fom_tab.layout.addStretch(3)

        fom_tab.layout.addWidget(QLabel("Color map:"))
        self.fom_color_map = QComboBox()
        for cmap in SLIX._cmd.VisualizeParameter.available_colormaps.keys():
            self.fom_color_map.addItem(cmap)
        fom_tab.layout.addWidget(self.fom_color_map)

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

    def setup_vector_tab(self) -> QWidget:
        """
        This method sets up the vector tab.

        Returns:
            QWidget: The vector tab.
        """
        vector_tab = QWidget()
        vector_tab.layout = QVBoxLayout()

        vector_tab_button_open_measurement = QPushButton("Open Directions")
        vector_tab_button_open_measurement.clicked.connect(self.open_direction)
        vector_tab.layout.addWidget(vector_tab_button_open_measurement)

        vector_tab_button_open_background = QPushButton("Open Background Image")
        vector_tab_button_open_background.clicked.connect(self.open_vector_background)
        vector_tab.layout.addWidget(vector_tab_button_open_background)

        vector_tab.layout.addStretch(3)

        vector_tab.layout.addWidget(QLabel("<b>Options:</b>"))
        vector_tab.layout.addWidget(QLabel("Color map:"))
        self.vector_color_map = QComboBox()
        for cmap in SLIX._cmd.VisualizeParameter.available_colormaps.keys():
            self.vector_color_map.addItem(cmap)
        vector_tab.layout.addWidget(self.vector_color_map)

        self.vector_checkbox_weight_value = QCheckBox("Weight Vector Length")
        self.vector_checkbox_weight_value.setChecked(False)
        vector_tab_button_open_value = QPushButton("Open Weighting")
        vector_tab_button_open_value.setEnabled(False)
        vector_tab_button_open_value.clicked.connect(self.open_vector_weighting)
        vector_tab.layout.addWidget(self.vector_checkbox_weight_value)
        vector_tab.layout.addWidget(vector_tab_button_open_value)
        self.vector_checkbox_weight_value.stateChanged.connect(vector_tab_button_open_value.setEnabled)

        vector_tab.layout.addWidget(QLabel("Alpha:"))
        self.vector_tab_alpha_parameter = QDoubleSpinBox()
        self.vector_tab_alpha_parameter.setRange(0, 1)
        self.vector_tab_alpha_parameter.setSingleStep(0.001)
        self.vector_tab_alpha_parameter.setValue(1)
        self.vector_tab_alpha_parameter.setDecimals(3)
        vector_tab.layout.addWidget(self.vector_tab_alpha_parameter)

        vector_tab.layout.addWidget(QLabel("Thinout:"))
        self.vector_tab_thinout_parameter = QDoubleSpinBox()
        self.vector_tab_thinout_parameter.setRange(0, 100)
        self.vector_tab_thinout_parameter.setSingleStep(1)
        self.vector_tab_thinout_parameter.setValue(1)
        self.vector_tab_thinout_parameter.setDecimals(0)
        vector_tab.layout.addWidget(self.vector_tab_thinout_parameter)

        vector_tab.layout.addWidget(QLabel("Scale:"))
        self.vector_tab_scale_parameter = QDoubleSpinBox()
        self.vector_tab_scale_parameter.setRange(0, 100)
        self.vector_tab_scale_parameter.setSingleStep(1)
        self.vector_tab_scale_parameter.setValue(1)
        self.vector_tab_scale_parameter.setDecimals(0)
        vector_tab.layout.addWidget(self.vector_tab_scale_parameter)

        vector_tab.layout.addWidget(QLabel("Vector width:"))
        self.vector_tab_vector_width_parameter = QDoubleSpinBox()
        self.vector_tab_vector_width_parameter.setRange(0, 100)
        self.vector_tab_vector_width_parameter.setSingleStep(0.1)
        self.vector_tab_vector_width_parameter.setValue(1)
        self.vector_tab_vector_width_parameter.setDecimals(1)
        vector_tab.layout.addWidget(self.vector_tab_vector_width_parameter)

        vector_tab.layout.addWidget(QLabel("DPI:"))
        self.vector_tab_dpi_parameter = QDoubleSpinBox()
        self.vector_tab_dpi_parameter.setRange(100, 2000)
        self.vector_tab_dpi_parameter.setSingleStep(100)
        self.vector_tab_dpi_parameter.setValue(100)
        self.vector_tab_dpi_parameter.setDecimals(0)
        vector_tab.layout.addWidget(self.vector_tab_dpi_parameter)

        self.vector_checkbox_activate_distribution = QCheckBox("Activate Distribution")
        self.vector_checkbox_activate_distribution.setChecked(True)
        vector_tab.layout.addWidget(self.vector_checkbox_activate_distribution)

        vector_tab.layout.addWidget(QLabel("Threshold:"))
        self.vector_tab_threshold_parameter = QDoubleSpinBox()
        self.vector_tab_threshold_parameter.setRange(0, 1)
        self.vector_tab_threshold_parameter.setSingleStep(0.01)
        self.vector_tab_threshold_parameter.setValue(0)
        self.vector_tab_threshold_parameter.setDecimals(2)
        self.vector_tab_threshold_parameter.setEnabled(False)
        self.vector_checkbox_activate_distribution.stateChanged.connect(self.vector_tab_threshold_parameter.setDisabled)
        vector_tab.layout.addWidget(self.vector_tab_threshold_parameter)

        vector_tab.layout.addStretch(3)

        self.vector_tab_button_generate = QPushButton("Generate")
        self.vector_tab_button_generate.clicked.connect(self.generate_vector)
        self.vector_tab_button_generate.setEnabled(False)
        vector_tab.layout.addWidget(self.vector_tab_button_generate)

        self.vector_tab_save_button = QPushButton("Save")
        self.vector_tab_save_button.clicked.connect(self.save_vector)
        self.vector_tab_save_button.setEnabled(False)
        vector_tab.layout.addWidget(self.vector_tab_save_button)

        vector_tab.setLayout(vector_tab.layout)
        return vector_tab

    def setup_parameter_map_tab(self) -> QWidget:
        """
        Set up the parameter map tab.

        Returns:
            QWidget: The parameter map tab.
        """
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

    def show_error_message(self, message: str) -> None:
        """
        Shows an error message.

        Returns:
            None
        """
        QMessageBox.warning(self, "Error", message)

    def open_direction(self) -> None:
        """
        Open one or more direction files.

        Returns:
            None
        """
        filename = QFileDialog.getOpenFileNames(self, 'Open Directions', '.', '*.tiff;; *.h5;; *.nii')[0]
        if len(filename) == 0:
            return

        try:
            direction_image = None
            filename.sort()
            for file in filename:
                # Arrange the direction images in a NumPy stack
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
            self.inclinations = None
            self.fom_tab_button_generate.setEnabled(True)
            self.vector_tab_button_generate.setEnabled(True)
        except ValueError as e:
            QMessageBox.critical(self, 'Error',
                                 f'Could not load directions. Check your input files. Error message:\n{e}')

    def __open_direction_single(self):
        pass

    def __open_direction_multiple(self):
        pass

    def open_inclination(self) -> None:
        """
        Open one or more direction files.

        Returns:
            None
        """
        filename = QFileDialog.getOpenFileNames(self, 'Open Inclinations', '.', '*.tiff;; *.h5;; *.nii')[0]
        if len(filename) == 0:
            return

        try:
            inclination_image = None
            filename.sort()
            for file in filename:
                # Arrange the direction images in a NumPy stack
                single_inclination_image = SLIX.io.imread(file)
                if inclination_image is None:
                    inclination_image = single_inclination_image
                else:
                    if len(inclination_image.shape) == 2:
                        inclination_image = numpy.stack((inclination_image,
                                                         single_inclination_image),
                                                        axis=-1)
                    else:
                        inclination_image = numpy.concatenate((inclination_image,
                                                               single_inclination_image
                                                               [:, :, numpy.newaxis]),
                                                              axis=-1)
            self.inclinations = inclination_image
        except ValueError as e:
            QMessageBox.critical(self, 'Error',
                                 f'Could not load directions. Check your input files. Error message:\n{e}')

    def open_parameter_map(self) -> None:
        """
        Open a parameter map.

        Returns:
            None
        """
        filename = QFileDialog.getOpenFileName(self, 'Open Parameter Map', '.', '*.tiff;; *.h5;; *.nii')[0]
        if len(filename) == 0:
            return

        self.parameter_map = SLIX.io.imread(filename)
        self.parameter_map_tab_button_save.setEnabled(True)
        self.parameter_map_color_map.setEnabled(True)
        self.generate_parameter_map()

    def open_saturation_weighting(self) -> None:
        """
        Open a saturation weighting map.

        Returns:
            None
        """
        filename = QFileDialog.getOpenFileName(self, 'Open Saturation weight', '.', '*.tiff;; *.h5;; *.nii')[0]
        if len(filename) == 0:
            return
        self.saturation_weighting = SLIX.io.imread(filename)

    def open_value_weighting(self) -> None:
        """
        Open a value weighting map.

        Returns:
            None
        """
        filename = QFileDialog.getOpenFileName(self, 'Open Value weight', '.', '*.tiff;; *.h5;; *.nii')[0]
        if len(filename) == 0:
            return
        self.value_weighting = SLIX.io.imread(filename)

    def open_vector_background(self) -> None:
        """
        Open a vector background map.

        Returns:
            None
        """
        filename = QFileDialog.getOpenFileName(self, 'Open Background Image', '.', '*.tiff;; *.h5;; *.nii')[0]
        if len(filename) == 0:
            return
        self.vector_background = SLIX.io.imread(filename)
        while len(self.vector_background.shape) > 2:
            self.vector_background = numpy.mean(self.vector_background, axis=-1)

    def open_vector_weighting(self) -> None:
        """
        Open a vector weighting map.

        Returns:
            None
        """
        filename = QFileDialog.getOpenFileName(self, 'Open Weight for vector', '.', '*.tiff;; *.h5;; *.nii')[0]
        if len(filename) == 0:
            return
        # Open and normalize the weighting image
        self.vector_weighting = SLIX.io.imread(filename)
        self.vector_weighting = (self.vector_weighting - self.vector_weighting.min()) / (
                numpy.percentile(self.vector_weighting, 99) - self.vector_weighting.min())

    def generate_fom(self) -> None:
        """
        Generate fiber orientation map based on the current settings.
        The generated FOM is saved in the self.fom attribute and will be
        shown to the user in the image viewer.

        Returns:
             None
        """
        # If the FOM should be weighted by the saturation weighting,
        # set the parameter saturation_weighting to the loaded image
        if self.fom_checkbox_weight_saturation.isChecked():
            saturation_weighting = self.saturation_weighting
        # If not, set it to None disabling any weighting.
        else:
            saturation_weighting = None
        # Repeat for value channel
        if self.fom_checkbox_weight_value.isChecked():
            value_weighting = self.value_weighting
        else:
            value_weighting = None
        # Get the color map which will be used in the FOM generation method.
        color_map = SLIX._cmd.VisualizeParameter.available_colormaps[self.fom_color_map.currentText()]

        # Show a progress bar while the parameter maps are generated
        dialog = QProgressDialog("Generating...", "Cancel", 0, 0, self)
        # Move the main workload to another thread to prevent freezing the GUI
        worker_thread = QThread()
        worker = FOMWorker(saturation_weighting, value_weighting, color_map, self.directions, self.inclinations)
        # Update the progress bar whenever a step is finished
        worker.currentStep.connect(dialog.setLabelText)
        worker.finishedWork.connect(worker_thread.quit)
        worker.finishedWork.connect(self.set_fom)
        worker.errorMessage.connect(self.show_error_message)
        worker.moveToThread(worker_thread)
        # Show the progress bar
        dialog.show()

        worker_thread.started.connect(worker.process)
        worker_thread.finished.connect(dialog.close)
        dialog.canceled.connect(worker_thread.requestInterruption)
        worker_thread.start()

        # Wait until the thread is finished
        while not worker_thread.isFinished():
            QCoreApplication.processEvents()
            time.sleep(0.1)

        del worker
        del worker_thread

    def set_fom(self, fom: numpy.ndarray) -> None:
        self.fom = fom
        if self.fom is not None:
            self.image_widget.set_image(convert_numpy_to_qimage(self.fom))
            self.fom_tab_save_button.setEnabled(True)

    def generate_vector(self) -> None:
        """
        Generate vector map based on the current settings.

        Returns:
            None
        """
        # This method only works when a direction is loaded. If not, do nothing.
        if self.directions is None:
            return

        # Completely clear matplotlib figure to ensure that the plot is not left in a weird state
        plt.clf()
        plt.cla()
        plt.axis('off')

        # Generate unit vectors from direction images
        UnitX, UnitY = SLIX.toolbox.unit_vectors(self.directions, use_gpu=False)
        color_map = SLIX._cmd.VisualizeParameter.available_colormaps[self.vector_color_map.currentText()]

        # Get parameters from interface
        alpha = self.vector_tab_alpha_parameter.value()
        thinout = int(self.vector_tab_thinout_parameter.value())
        scale = self.vector_tab_scale_parameter.value()
        vector_width = self.vector_tab_vector_width_parameter.value()
        threshold = self.vector_tab_threshold_parameter.value()

        # Show the loaded background image
        if self.vector_background is not None:
            plt.imshow(self.vector_background, cmap='gray')
        if self.vector_checkbox_weight_value.isChecked():
            value_weighting = self.vector_weighting
        else:
            value_weighting = None

        # Generate either the distrubution of vectors or the vector field
        # depending on the selected option. This method might fail if the
        # parameters are not valid or a measurement is missing.
        # If it fails, show an error message.
        try:
            if self.vector_checkbox_activate_distribution.isChecked():
                SLIX.visualization.unit_vector_distribution(UnitX, UnitY,
                                                            thinout=thinout,
                                                            alpha=alpha,
                                                            scale=scale,
                                                            vector_width=vector_width,
                                                            colormap=color_map,
                                                            weighting=value_weighting)
            else:
                SLIX.visualization.unit_vectors(UnitX, UnitY,
                                                thinout=thinout,
                                                alpha=alpha,
                                                scale=scale,
                                                vector_width=vector_width,
                                                background_threshold=threshold,
                                                colormap=color_map,
                                                weighting=value_weighting)
        except ValueError as e:
            QMessageBox.critical(self, 'Error', f'Could not generate vector. Check your input files.\n'
                                                f'Error message:\n{e}')
            return

        # Set dpi
        plt.gcf().set_dpi(self.vector_tab_dpi_parameter.value())
        plt.gcf().subplots_adjust(0, 0, 1, 1)
        # Convert current plot to NumPy array
        plt.gcf().canvas.draw()
        vector_image = numpy.array(plt.gcf().canvas.buffer_rgba(), dtype=float)
        vector_image = vector_image[:, :, :3]
        self.vector_field = vector_image
        self.image_widget.set_image(convert_numpy_to_qimage(vector_image))
        self.vector_tab_save_button.setEnabled(True)

    def generate_parameter_map(self) -> None:
        """
        Generate parameter map based on the current settings.
        Show the result in the image widget.

        Returns:
            None
        """
        # Get color map from matplotlib
        colormap = matplotlib.cm.get_cmap(self.parameter_map_color_map.currentText())
        # Normalize the image to the range [0, 1]
        shown_image = self.parameter_map.copy()
        shown_image = shown_image.astype(numpy.float32)
        shown_image = (shown_image - shown_image.min()) / (shown_image.max() - shown_image.min())
        # Apply colormap on normalized image
        shown_image = colormap(shown_image)
        # Convert NumPy RGBA array to RGB array
        shown_image = shown_image[:, :, :3]
        self.image_widget.set_image(convert_numpy_to_qimage(shown_image))

    def save_fom(self) -> None:
        """
        Save the current FOM image to a file.

        Returns:
             None
        """
        filename, datatype = QFileDialog.getSaveFileName(self, 'Save FOM', '.', '*.tiff;; *.h5')
        if len(filename) > 0:
            datatype = datatype[1:]
            if not filename.endswith(datatype):
                filename += datatype
            SLIX.io.imwrite_rgb(filename, self.fom)

    def save_vector(self) -> None:
        """
        Save the current vector field image to a file.

        Returns:
             None
        """
        filename, datatype = QFileDialog.getSaveFileName(self, 'Save Vector Image', '.', '*.tiff;; *.h5')
        if len(filename) > 0:
            datatype = datatype[1:]
            if not filename.endswith(datatype):
                filename += datatype
            SLIX.io.imwrite_rgb(filename, self.vector_field)

    def save_parameter_map(self) -> None:
        """
        Save the current parameter map image to a file.

        Returns:
             None
        """
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
            # Convert NumPy RGBA array to RGB array
            shown_image = (255 * shown_image[:, :, :3]).astype(numpy.uint8)
            SLIX.io.imwrite_rgb(filename, shown_image)
