
import numpy

from PySide6.QtGui import QImage, QPixmap


def cvImageToPixmap(image: numpy.ndarray) -> QPixmap:
    """Convert a cv2 BGR(A)/grayscale ndarray into a QPixmap."""

    if image is None:
        return QPixmap()

    height, width = image.shape[:2]
    channels = image.shape[2] if image.ndim == 3 else 1

    if channels == 3:
        qImage = QImage(image.data, width, height, image.strides[0], QImage.Format.Format_BGR888)
    elif channels == 4:
        qImage = QImage(image.data, width, height, image.strides[0], QImage.Format.Format_ARGB32)
    else:
        qImage = QImage(image.data, width, height, image.strides[0], QImage.Format.Format_Grayscale8)

    # deep-copy pixel data into a Qt-owned buffer since `image` may be freed
    return QPixmap.fromImage(qImage.copy())
