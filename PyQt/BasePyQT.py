import numpy as np
from PIL import Image
import nibabel as nib
import SimpleITK as sitk
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSlider, QPushButton, QFileDialog
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtCore import Qt
from MainWindow import MainWindowSegment


class SlicerWidget(QWidget):
    def __init__(self, data_path, sitk_image):
        super().__init__()
        self.data_path = data_path
        self.nibabel_data = nib.load(self.data_path).get_fdata()
        self.sitk_image = sitk_image
        self.slices = {
            'sagittal': sitk_image[:, :, :],
            'coronal': sitk_image[:, :, :],
            'axial': sitk_image[:, :, :],
        }
        self.current_view = 'sagittal'
        self.slice_index = self.slices[self.current_view].GetSize()[2] // 2
        self.image_path = None
        self.slice_data_nibabel = None

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.current_view == 'sagittal':
            slice_data = sitk.GetArrayViewFromImage(self.slices[self.current_view])[:, :, self.slice_index]
            self.slice_data_nibabel = self.nibabel_data[:, :, self.slice_index]
        if self.current_view == 'coronal':
            slice_data = sitk.GetArrayViewFromImage(self.slices[self.current_view])[:, self.slice_index, :]
            self.slice_data_nibabel = self.nibabel_data[:, self.slice_index, :]
        if self.current_view == 'axial':
            slice_data = sitk.GetArrayViewFromImage(self.slices[self.current_view])[self.slice_index, :, :]
            self.slice_data_nibabel = self.nibabel_data[self.slice_index, :, :]
        slice_data = ((slice_data - slice_data.min()) / (slice_data.max() - slice_data.min()) * 255).astype('uint8')
        height, width = slice_data.shape
        bytes_per_line = width
        image = QImage(slice_data.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(image)
        painter.drawPixmap(0, 0, self.width(), self.height(), pixmap)

    def set_current_view(self, view):
        self.current_view = view
        self.slice_index = self.slices[self.current_view].GetSize()[2] // 2
        self.update()

    def set_slice_index(self, index):
        self.slice_index = index
        self.update()

    def save_current_view_as_jpg(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getSaveFileName(self, f"Save {self.current_view.capitalize()} View as JPG", "",
                                                   "JPEG Image Files (*.jpg);;All Files (*)", options=options)
        rescaled = (255.0 / self.slice_data_nibabel.max() * (self.slice_data_nibabel - self.slice_data_nibabel.min())).astype(np.uint8)
        im = Image.fromarray(rescaled)
        im.save(file_path)
        self.image_path = file_path


class MainWindow(QMainWindow):
    def __init__(self, data_path):
        super().__init__()
        self.data_path = data_path
        self.setWindowTitle("3D Slicer")
        self.setGeometry(100, 100, 800, 600)
        sitk_image = sitk.ReadImage(self.data_path)
        self.slicer_widget = SlicerWidget(self.data_path, sitk_image)

        self.scrollbar = QSlider(Qt.Horizontal)
        self.scrollbar.setMaximum(sitk_image.GetSize()[2] - 1)
        self.scrollbar.valueChanged.connect(self.slicer_widget.set_slice_index)

        self.save_button = QPushButton("Save as JPG")
        self.save_button.clicked.connect(self.slicer_widget.save_current_view_as_jpg)

        self.view_buttons = {
            'Sagittal': 'sagittal',
            'Coronal': 'coronal',
            'Axial': 'axial',
        }

        self.start_button = QPushButton("Start Segment")
        self.start_button.clicked.connect(self.close_window)

        for button_text, view in self.view_buttons.items():
            button = QPushButton(button_text)
            button.clicked.connect(lambda _, view=view: self.slicer_widget.set_current_view(view))
            self.view_buttons[button_text] = button

        layout = QVBoxLayout()
        layout.addWidget(self.slicer_widget)
        layout.addWidget(self.scrollbar)
        layout.addWidget(self.save_button)
        for button_text, button in self.view_buttons.items():
            layout.addWidget(button)
        layout.addWidget(self.start_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def close_window(self):
        self.close()

    def get_image_path(self):
        return self.slicer_widget.image_path
