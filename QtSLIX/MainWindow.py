from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, \
                            QMessageBox
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from .ClusterWidget import ClusterWidget
from .ParameterGeneratorWidget import ParameterGeneratorWidget
from .VisualizationWidget import VisualizationWidget

__all__ = ['MainWindow']


class MainWindow(QMainWindow):
    """
    MainWindow class.
    """
    def __init__(self):
        super().__init__()

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.layout = None
        self.helpmenu = None
        self.tab_bar = None

        self.setWindowTitle('QtSLIX')
        self.setMinimumSize(1280, 720)

        # Prevent that the window becomes too large. This
        # might happen if Qt loads an image into a QLabel
        # Check all screens in case that one screen is larger than
        # the other.
        screens = QApplication.screens()
        max_width = 0
        max_height = 0
        for screen in screens:
            max_width = max(screen.availableSize().width(), max_width)
            max_height = max(screen.availableSize().height(), max_height)
        self.setMaximumSize(max_width, max_height)

        self.setup_ui()
        self.show()

    def setup_ui(self) -> None:
        """
        Set up the user interface.

        Returns:
             None
        """
        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)

        self.tab_bar = QTabWidget()
        self.tab_bar.addTab(ParameterGeneratorWidget(), 'Parameter Generator')
        self.tab_bar.addTab(VisualizationWidget(), 'Visualization')
        self.tab_bar.addTab(ClusterWidget(), 'Clustering')
        self.layout.addWidget(self.tab_bar)

        self.create_menu_bar()

    def create_menu_bar(self) -> None:
        """
        Create the menu bar.

        Returns:
             None
        """
        self.helpmenu = self.menuBar().addMenu('&Help')
        self.helpmenu.addAction('&About', self.about)
        self.helpmenu.addAction('&License', self.license)
        self.helpmenu.addAction('&Credits', self.credits)
        self.helpmenu.addAction('&About Qt', self.about_qt)

    def close(self) -> None:
        """
        Close the application.

        Returns:
             None
        """
        QApplication.quit()

    def about(self) -> None:
        """
        Show information about the application.

        Returns:
             None
        """
        pass

    def license(self) -> None:
        """
        Show information about the license.

        Returns:
             None
        """
        url = QUrl('https://jugit.fz-juelich.de/inm-1/fa/sli/tools/qtslix/-/blob/main/LICENSE')
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(self, 'Open Url', 'Could not open url')

    def credits(self) -> None:
        """
        Show information about the authors.

        Returns:
             None
        """
        QMessageBox.information(self, 'Credits', '')

    def about_qt(self) -> None:
        """
        Show information about Qt.

        Returns:
             None
        """
        QApplication.aboutQt()
