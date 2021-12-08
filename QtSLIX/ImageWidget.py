import numpy
from PyQt5.QtWidgets import QWidget, QScrollBar, QHBoxLayout, QVBoxLayout, QSizePolicy, QLabel
from PyQt5.QtGui import QImage, QPixmap, qRgb, QResizeEvent
from PyQt5.QtCore import QCoreApplication, QObject, QThread, pyqtSignal, Qt


def convert_numpy_to_qimage(image: numpy.array) -> [QImage]:
    # copy and normalize image
    image = image.copy().astype(numpy.float32)
    image = 255 * (image - image.min()) / (image.max() - image.min())
    image = image.astype(numpy.uint8)

    if len(image.shape) > 2:
        num_measurements = image.shape[2]
    else:
        num_measurements = 1

    return_list = []
    gray_color_table = [qRgb(i, i, i) for i in range(256)]

    # Convert image to QImage
    for i in range(num_measurements):
        if num_measurements > 1:
            image_i = image[..., i].copy()
        else:
            image_i = image.copy()
        qimage = QImage(image_i.data, image_i.shape[1], image_i.shape[0], image_i.strides[0], QImage.Format_Indexed8)
        qimage.setColorTable(gray_color_table)
        return_list.append(qimage.copy())
    return return_list


class ImageWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = None
        self.image_label = None
        self.image_scroll_bar = None
        self.image: [QImage] = None
        self.pixmap = None

        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        self.pixmap = QPixmap.fromImage(QImage(self.maximumWidth(), self.maximumHeight(),
                                               QImage.Format_Grayscale8))
        self.image_label = QLabel()
        self.image_label.setPixmap(self.pixmap)
        self.image_label.setScaledContents(False)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.image_label)

        self.image_scroll_bar = QScrollBar(Qt.Horizontal)
        self.image_scroll_bar.setRange(0, 0)
        self.image_scroll_bar.setSingleStep(1)
        self.image_scroll_bar.setPageStep(1)
        self.image_scroll_bar.setTracking(True)
        self.image_scroll_bar.valueChanged.connect(self.scroll_bar_changed)
        self.layout.addWidget(self.image_scroll_bar)

        self.setLayout(self.layout)

    def scroll_bar_changed(self):
        self.pixmap = QPixmap.fromImage(self.image[self.image_scroll_bar.value()])
        self.image_label.setPixmap(self.pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))

    def set_image(self, image: [QImage]):
        self.image = image
        self.pixmap = QPixmap.fromImage(self.image[0])
        self.image_label.setPixmap(self.pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))
        self.image_scroll_bar.setRange(0, len(self.image) - 1)
        self.image_scroll_bar.setValue(0)

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.image_label.setPixmap(self.pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))
        super().resizeEvent(a0)
