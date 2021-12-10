from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, \
    QFileDialog, QCheckBox, QPushButton, QProgressDialog, QSizePolicy, QComboBox, QDoubleSpinBox, QLabel
from PyQt5.QtCore import QCoreApplication, QObject, QThread, pyqtSignal, QLocale

from .ImageWidget import ImageWidget, convert_numpy_to_qimage

import SLIX
import numpy
import os
import time

if SLIX.toolbox.gpu_available:
    import cupy


class ParameterGeneratorWorker(QObject):
    """
    Worker class for the parameter generator.
    This class gets called from the ParameterGeneratorWidget when the user clicks the "Generate" button.
    """
    # Signal to inform the ParameterGeneratorWidget that the worker has finished
    finishedWork = pyqtSignal()
    # Signal to inform the ParameterGeneratorWidget what step the worker is currently working on
    currentStep = pyqtSignal(str)

    def __init__(self, filename: str, image: numpy.array,
                 output_folder: str, filtering: str,
                 filtering_parm_1: float, filtering_parm_2: float,
                 use_gpu: bool, detailed: bool, min: bool, max: bool,
                 avg: bool, direction: bool, nc_direction: bool,
                 peaks: bool, peak_width: bool, peak_distance: bool,
                 peak_prominence: bool, dir_correction: float):
        """
        Initialize the worker.

        Args:
            filename: Filename of the measurement image

            image: NumPy array of the measurement image

            output_folder: Folder to save the generated images

            filtering: Filtering method to use

            filtering_parm_1: Parameter 1 of the filtering method

            filtering_parm_2: Parameter 2 of the filtering method

            use_gpu: Use GPU for calculations

            detailed: Use detailed mode

            min: Generate minima image

            max: Generate maxima image

            avg: Generate average image

            direction: Generate direction image

            nc_direction: Generate non crossing direction image

            peaks: Generate peaks image

            peak_width: Generate peak width image

            peak_distance: Generate peak distance image

            peak_prominence: Generate peak prominence image

            dir_correction: Direction correction in degree
        """
        super().__init__()
        self.filename = filename
        self.image = image
        self.output_folder = output_folder
        self.gpu = use_gpu
        self.detailed = detailed
        self.min = min
        self.max = max
        self.avg = avg
        self.direction = direction
        self.nc_direction = nc_direction
        self.peaks = peaks
        self.peak_width = peak_width
        self.peak_distance = peak_distance
        self.peak_prominence = peak_prominence
        self.filtering = filtering
        self.filtering_parameter_1 = filtering_parm_1
        self.filtering_parameter_2 = filtering_parm_2
        self.dir_correction = dir_correction

    def process(self) -> None:
        """
        Process the image. This method is called from the ParameterGeneratorWidget.

        Returns:
             None
        """
        output_data_type = ".tiff"

        # Get the filename without the extension to determine the output file names
        if os.path.isdir(self.filename):
            filename_without_extension = SLIX._cmd.ParameterGenerator.get_file_pattern(self.filename)
        else:
            filename_without_extension = \
                os.path.splitext(os.path.basename(self.filename))[0]
        output_path_name = f'{self.output_folder}/{filename_without_extension}'
        # Create the output folder if it does not exist
        if os.path.isdir(self.filename):
            SLIX.io.imwrite(f'{output_path_name}_Stack{output_data_type}', self.image)

        gpu = self.gpu
        detailed = self.detailed
        detailed_str = "_detailed" if detailed else ""

        # If the thread is stopped, return
        if QThread.currentThread().isInterruptionRequested():
            self.finishedWork.emit()
            return

        # Apply filtering
        if self.filtering != "None":
            self.currentStep.emit(f"Filtering: {self.filtering} "
                                  f"{self.filtering_parameter_1} "
                                  f"{self.filtering_parameter_2}")
            if self.filtering == "Fourier":
                self.image = SLIX.preparation.low_pass_fourier_smoothing(self.image,
                                                                         self.filtering_parameter_1,
                                                                         self.filtering_parameter_2)
            elif self.filtering == "Savitzky-Golay":
                self.image = SLIX.preparation.savitzky_golay_smoothing(self.image,
                                                                       self.filtering_parameter_1,
                                                                       self.filtering_parameter_2)

        if QThread.currentThread().isInterruptionRequested():
            self.finishedWork.emit()
            return
        # Generate minima image
        if self.min:
            self.currentStep.emit("Generating minima...")
            min_img = numpy.min(self.image, axis=-1)
            SLIX.io.imwrite(f'{output_path_name}_min'
                            f'{output_data_type}', min_img)

        if QThread.currentThread().isInterruptionRequested():
            self.finishedWork.emit()
            return
        # Generate maxima image
        if self.max:
            self.currentStep.emit("Generating maxima...")
            max_img = numpy.max(self.image, axis=-1)
            SLIX.io.imwrite(f'{output_path_name}_max'
                            f'{output_data_type}', max_img)

        if QThread.currentThread().isInterruptionRequested():
            self.finishedWork.emit()
            return
        # Generate average image
        if self.avg:
            self.currentStep.emit("Generating average...")
            avg_img = numpy.mean(self.image, axis=-1)
            SLIX.io.imwrite(f'{output_path_name}_avg'
                            f'{output_data_type}', avg_img)

        if QThread.currentThread().isInterruptionRequested():
            self.finishedWork.emit()
            return
        # The following steps require the significant peaks of the measurement ...
        self.currentStep.emit("Generating significant peaks...")
        peaks = SLIX.toolbox.significant_peaks(self.image, use_gpu=gpu, return_numpy=True)

        if QThread.currentThread().isInterruptionRequested():
            self.finishedWork.emit()
            return
        # ... as well as the centroids
        self.currentStep.emit("Generating centroids...")
        centroids = SLIX.toolbox.centroid_correction(self.image, peaks, use_gpu=gpu, return_numpy=True)

        if QThread.currentThread().isInterruptionRequested():
            self.finishedWork.emit()
            return
        # Generate all peaks to write low and high prominence peaks
        if self.peaks:
            self.currentStep.emit("Generating all peaks...")
            all_peaks = SLIX.toolbox.peaks(self.image, use_gpu=gpu, return_numpy=True)
            if not detailed:
                SLIX.io.imwrite(f'{output_path_name}_high_prominence_peaks'
                                f'{output_data_type}',
                                numpy.sum(peaks, axis=-1,
                                          dtype=numpy.uint16))
                SLIX.io.imwrite(f'{output_path_name}_low_prominence_peaks'
                                f'{output_data_type}',
                                numpy.sum(all_peaks, axis=-1, dtype=numpy.uint16) -
                                numpy.sum(peaks, axis=-1,
                                          dtype=numpy.uint16))
            else:
                SLIX.io.imwrite(f'{output_path_name}_all_peaks_detailed'
                                f'{output_data_type}', all_peaks)
                SLIX.io.imwrite(
                    f'{output_path_name}_high_prominence_peaks_detailed'
                    f'{output_data_type}',
                    peaks
                )

        if QThread.currentThread().isInterruptionRequested():
            self.finishedWork.emit()
            return
        # Generate the direction images
        if self.direction:
            self.currentStep.emit("Generating direction...")
            direction = SLIX.toolbox.direction(peaks, centroids, use_gpu=gpu, number_of_directions=3,
                                               correction_angle=self.dir_correction, return_numpy=True)
            for dim in range(direction.shape[-1]):
                SLIX.io.imwrite(f'{output_path_name}_dir_{dim + 1}'
                                f'{output_data_type}',
                                direction[:, :, dim])
            del direction

        if QThread.currentThread().isInterruptionRequested():
            self.finishedWork.emit()
            return
        # Generate the non-crossing direction images
        if self.nc_direction:
            self.currentStep.emit("Generating non crossing direction...")
            nc_direction = SLIX.toolbox.direction(peaks, centroids, use_gpu=gpu,
                                                  number_of_directions=1, return_numpy=True)
            SLIX.io.imwrite(f'{output_path_name}_dir'
                            f'{output_data_type}',
                            nc_direction[:, :])
            del nc_direction

        if QThread.currentThread().isInterruptionRequested():
            self.finishedWork.emit()
            return
        # Generate the peak distance
        if self.peak_distance:
            self.currentStep.emit("Generating peak distance...")
            if detailed:
                peak_distance = SLIX.toolbox.peak_distance(peaks, centroids, use_gpu=gpu, return_numpy=True)
            else:
                peak_distance = SLIX.toolbox.mean_peak_distance(peaks, centroids, use_gpu=gpu, return_numpy=True)
            SLIX.io.imwrite(f'{output_path_name}_peakdistance{detailed_str}'
                            f'{output_data_type}', peak_distance)
            del peak_distance

        if QThread.currentThread().isInterruptionRequested():
            self.finishedWork.emit()
            return
        # Generate the peak width
        if self.peak_width:
            self.currentStep.emit("Generating peak width...")
            if detailed:
                peak_width = SLIX.toolbox.peak_width(self.image, peaks, use_gpu=gpu, return_numpy=True)
            else:
                peak_width = SLIX.toolbox.mean_peak_width(self.image, peaks, use_gpu=gpu)
            SLIX.io.imwrite(f'{output_path_name}_peakwidth{detailed_str}'
                            f'{output_data_type}', peak_width)
            del peak_width

        if QThread.currentThread().isInterruptionRequested():
            self.finishedWork.emit()
            return
        # Generate the peak prominence
        if self.peak_prominence:
            self.currentStep.emit("Generating peak prominence...")
            if detailed:
                prominence = SLIX.toolbox.peak_prominence(self.image, peaks, use_gpu=gpu, return_numpy=True)
            else:
                prominence = SLIX.toolbox.mean_peak_prominence(self.image, peaks, use_gpu=gpu, return_numpy=True)
            SLIX.io.imwrite(f'{output_path_name}_peakprominence{detailed_str}'
                            f'{output_data_type}', prominence)
            del prominence

        # Tell connected components that we are done
        self.finishedWork.emit()


class ParameterGeneratorWidget(QWidget):
    """
    Widget for generating parameters.
    """
    def __init__(self):
        super().__init__()

        self.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))

        self.layout = None
        self.sidebar = None
        self.sidebar_button_open_measurement = None
        self.sidebar_button_open_folder = None
        self.sidebar_checkbox_filtering = None
        self.sidebar_filtering_algorithm = None
        self.sidebar_filtering_parameter_1 = None
        self.sidebar_filtering_parameter_2 = None
        self.sidebar_checkbox_average = None
        self.sidebar_checkbox_minimum = None
        self.sidebar_checkbox_maximum = None
        self.sidebar_checkbox_crossing_direction = None
        self.sidebar_checkbox_non_crossing_direction = None
        self.sidebar_checkbox_peak_distance = None
        self.sidebar_checkbox_peak_width = None
        self.sidebar_checkbox_peak_prominence = None
        self.sidebar_checkbox_peaks = None
        self.sidebar_checkbox_detailed = None
        self.sidebar_checkbox_use_gpu = None
        self.sidebar_dir_correction_parameter = None
        self.sidebar_button_generate = None
        self.image_widget = None

        self.filename = None
        self.image = None

        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Set up the user interface.

        Returns:
            None
        """
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.setup_ui_sidebar()
        self.setup_ui_image_widget()

        self.layout.addWidget(self.image_widget, stretch=7)
        self.layout.addLayout(self.sidebar, stretch=2)

    def setup_ui_sidebar(self) -> None:
        """
        Set up the sidebar.

        Returns:
            None
        """
        self.sidebar = QVBoxLayout()

        # Open part
        self.sidebar.addWidget(QLabel("<b>Open:</b>"))
        self.sidebar_button_open_measurement = QPushButton(" Measurement")
        self.sidebar_button_open_measurement.clicked.connect(self.open_measurement)
        self.sidebar.addWidget(self.sidebar_button_open_measurement)

        self.sidebar_button_open_folder = QPushButton("Folder")
        self.sidebar_button_open_folder.clicked.connect(self.open_folder)
        self.sidebar.addWidget(self.sidebar_button_open_folder)

        self.sidebar.addStretch(5)

        # Filtering part
        self.sidebar.addWidget(QLabel("<b>Filtering:</b>"))
        # Set filtering algorithm
        self.sidebar_checkbox_filtering = QCheckBox("Enable")
        self.sidebar_checkbox_filtering.setChecked(False)
        self.sidebar.addWidget(self.sidebar_checkbox_filtering)
        self.sidebar_filtering_algorithm = QComboBox()
        self.sidebar_filtering_algorithm.setEnabled(False)
        self.sidebar_filtering_algorithm.addItems(["Fourier", "Savitzky-Golay"])
        self.sidebar_filtering_algorithm.setCurrentIndex(0)
        self.sidebar.addWidget(self.sidebar_filtering_algorithm)
        self.sidebar_checkbox_filtering.stateChanged.connect(self.sidebar_filtering_algorithm.setEnabled)
        # Set filtering window size
        self.sidebar_filtering_parameter_1 = QDoubleSpinBox()
        self.sidebar_filtering_parameter_1.setEnabled(False)
        self.sidebar_filtering_parameter_1.setRange(0, 1)
        self.sidebar_filtering_parameter_1.setSingleStep(0.001)
        self.sidebar_filtering_parameter_1.setValue(0)
        self.sidebar_filtering_parameter_1.setDecimals(3)
        self.sidebar.addWidget(self.sidebar_filtering_parameter_1)
        self.sidebar_checkbox_filtering.stateChanged.connect(self.sidebar_filtering_parameter_1.setEnabled)
        # Set filtering order / magnitude
        self.sidebar_filtering_parameter_2 = QDoubleSpinBox()
        self.sidebar_filtering_parameter_2.setEnabled(False)
        self.sidebar_filtering_parameter_2.setRange(0, 1)
        self.sidebar_filtering_parameter_2.setSingleStep(0.001)
        self.sidebar_filtering_parameter_2.setValue(0)
        self.sidebar_filtering_parameter_2.setDecimals(3)
        self.sidebar.addWidget(self.sidebar_filtering_parameter_2)
        self.sidebar_checkbox_filtering.stateChanged.connect(self.sidebar_filtering_parameter_2.setEnabled)

        self.sidebar.addStretch(1)
        # Parameter map part
        self.sidebar.addWidget(QLabel("<b>Parameter Maps:</b>"))

        self.sidebar_checkbox_average = QCheckBox("Average")
        self.sidebar_checkbox_average.setChecked(False)
        self.sidebar.addWidget(self.sidebar_checkbox_average)

        self.sidebar_checkbox_minimum = QCheckBox("Minimum")
        self.sidebar_checkbox_minimum.setChecked(False)
        self.sidebar.addWidget(self.sidebar_checkbox_minimum)

        self.sidebar_checkbox_maximum = QCheckBox("Maximum")
        self.sidebar_checkbox_maximum.setChecked(False)
        self.sidebar.addWidget(self.sidebar_checkbox_maximum)

        self.sidebar_checkbox_crossing_direction = QCheckBox("Crossing Direction")
        self.sidebar_checkbox_crossing_direction.setChecked(True)
        self.sidebar.addWidget(self.sidebar_checkbox_crossing_direction)

        self.sidebar_checkbox_non_crossing_direction = QCheckBox("Non Crossing Direction")
        self.sidebar_checkbox_non_crossing_direction.setChecked(False)
        self.sidebar.addWidget(self.sidebar_checkbox_non_crossing_direction)

        self.sidebar_checkbox_peak_distance = QCheckBox("Peak Distance")
        self.sidebar_checkbox_peak_distance.setChecked(True)
        self.sidebar.addWidget(self.sidebar_checkbox_peak_distance)

        self.sidebar_checkbox_peak_width = QCheckBox("Peak Width")
        self.sidebar_checkbox_peak_width.setChecked(True)
        self.sidebar.addWidget(self.sidebar_checkbox_peak_width)

        self.sidebar_checkbox_peak_prominence = QCheckBox("Peak Prominence")
        self.sidebar_checkbox_peak_prominence.setChecked(True)
        self.sidebar.addWidget(self.sidebar_checkbox_peak_prominence)

        self.sidebar_checkbox_peaks = QCheckBox("Peaks")
        self.sidebar_checkbox_peaks.setChecked(True)
        self.sidebar.addWidget(self.sidebar_checkbox_peaks)

        self.sidebar.addStretch(1)

        # Additional option part
        self.sidebar.addWidget(QLabel("<b>Other options:</b>"))

        self.sidebar.addWidget(QLabel("Correction direction (°):"))
        self.sidebar_dir_correction_parameter = QDoubleSpinBox()
        self.sidebar_dir_correction_parameter.setRange(0, 180)
        self.sidebar_dir_correction_parameter.setSingleStep(0.1)
        self.sidebar_dir_correction_parameter.setValue(0)
        self.sidebar_dir_correction_parameter.setDecimals(2)
        self.sidebar.addWidget(self.sidebar_dir_correction_parameter)

        self.sidebar_checkbox_detailed = QCheckBox("Detailed")
        self.sidebar_checkbox_detailed.setChecked(False)
        self.sidebar.addWidget(self.sidebar_checkbox_detailed)

        self.sidebar_checkbox_use_gpu = QCheckBox("Use GPU")
        # Disable the gpu checkbox if no compatible GPU was found by SLIX
        self.sidebar_checkbox_use_gpu.setEnabled(SLIX.toolbox.gpu_available)
        self.sidebar_checkbox_use_gpu.setChecked(SLIX.toolbox.gpu_available)
        self.sidebar.addWidget(self.sidebar_checkbox_use_gpu)

        self.sidebar.addStretch(5)

        self.sidebar_button_generate = QPushButton("Generate")
        self.sidebar_button_generate.clicked.connect(self.generate)
        self.sidebar_button_generate.setEnabled(False)
        self.sidebar.addWidget(self.sidebar_button_generate)

    def setup_ui_image_widget(self) -> None:
        """
        Set up the image widget.

        Returns:
            None
        """
        self.image_widget = ImageWidget()
        self.image_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def open_measurement(self) -> None:
        """
        Called when pressing a button. Opens a file dialog to select a measurement file.
        The measurement will then be loaded and the image widget will be updated.

        Returns:
             None
        """
        file = QFileDialog.getOpenFileName(self, "Open Measurement", "",
                                           "*.tiff ;; *.tif ;; *.h5 ;; *.nii ;; *.nii.gz")[0]
        if not file:
            return
        self.filename = file
        self.image = SLIX.io.imread(file)
        self.sidebar_button_generate.setEnabled(True)

        if self.image_widget:
            self.image_widget.set_image(convert_numpy_to_qimage(self.image))

    def open_folder(self) -> None:
        """
        Called when pressing a button. Opens a file dialog to select a measurement folder.
        The measurement will then be loaded and the image widget will be updated.

        Returns:
            None
        """
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", "")

        if not folder:
            return

        self.filename = folder
        self.image = SLIX.io.imread(folder)
        self.sidebar_button_generate.setEnabled(True)

        if self.image_widget:
            self.image_widget.set_image(convert_numpy_to_qimage(self.image))

    def generate(self) -> None:
        """
        Called when pressing a button. Generates the parameter maps and saves them to disk.

        Returns:
            None
        """
        # Prevent the button from being pressed multiple times
        self.sidebar_button_generate.setEnabled(False)
        output_folder = QFileDialog.getExistingDirectory(self, "Save files in folder", "")

        if not output_folder:
            self.sidebar_button_generate.setEnabled(True)
            return

        # Show a progress bar while the parameter maps are generated
        dialog = QProgressDialog("Generating...", "Cancel", 0, 0, self)

        if self.sidebar_checkbox_filtering.isChecked():
            filtering_algorithm = self.sidebar_filtering_algorithm.currentText()
        else:
            filtering_algorithm = "None"

        # Move the main workload to another thread to prevent freezing the GUI
        worker_thread = QThread()
        worker = ParameterGeneratorWorker(self.filename, self.image, output_folder,
                                          filtering_algorithm,
                                          self.sidebar_filtering_parameter_1.value(),
                                          self.sidebar_filtering_parameter_2.value(),
                                          self.sidebar_checkbox_use_gpu.isChecked(),
                                          self.sidebar_checkbox_detailed.isChecked(),
                                          self.sidebar_checkbox_minimum.isChecked(),
                                          self.sidebar_checkbox_maximum.isChecked(),
                                          self.sidebar_checkbox_average.isChecked(),
                                          self.sidebar_checkbox_crossing_direction.isChecked(),
                                          self.sidebar_checkbox_non_crossing_direction.isChecked(),
                                          self.sidebar_checkbox_peaks.isChecked(),
                                          self.sidebar_checkbox_peak_width.isChecked(),
                                          self.sidebar_checkbox_peak_distance.isChecked(),
                                          self.sidebar_checkbox_peak_prominence.isChecked(),
                                          self.sidebar_dir_correction_parameter.value())
        # Update the progress bar whenever a step is finished
        worker.currentStep.connect(dialog.setLabelText)
        worker.finishedWork.connect(worker_thread.quit)
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

        # Free the memory on the GPU to allow other applications to use it
        if SLIX.toolbox.gpu_available:
            mempool = cupy.get_default_memory_pool()
            mempool.free_all_blocks()

        # Reenable the button after calculations are finished
        self.sidebar_button_generate.setEnabled(True)
