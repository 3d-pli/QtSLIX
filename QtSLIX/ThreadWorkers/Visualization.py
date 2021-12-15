import matplotlib.pyplot as plt
from PyQt5.QtCore import QObject, pyqtSignal
import numpy
import SLIX
from matplotlib import pyplot as plt


class FOMWorker(QObject):
    """
    Worker class for the visualization.
    This class gets called from the VisualizationWidget when the user clicks the "Generate" button.
    """
    # Signal to inform the ParameterGeneratorWidget that the worker has finished
    finishedWork = pyqtSignal(numpy.ndarray)
    # Signal to inform the ParameterGeneratorWidget what step the worker is currently working on
    currentStep = pyqtSignal(str)
    # Error message
    errorMessage = pyqtSignal(str)

    def __init__(self, saturation_weighting, value_weighting, color_map, directions, inclination):
        super().__init__()
        self.directions = directions
        self.inclinations = inclination
        self.saturation_weighting = saturation_weighting
        self.value_weighting = value_weighting
        self.color_map = color_map

    def process(self) -> None:
        image = None
        try:
            self.currentStep.emit("Generating FOM...")
            image = SLIX.visualization.direction(self.directions, inclination=self.inclinations,
                                                 saturation=self.saturation_weighting,
                                                 value=self.value_weighting, colormap=self.color_map)
        except ValueError as e:
            self.errorMessage.emit(f'Could not generate FOM. Check your input files.\n'
                                   f'Error message:\n{e}')
        self.finishedWork.emit(image)
