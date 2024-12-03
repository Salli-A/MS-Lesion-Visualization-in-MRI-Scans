import vtk
import sys
import pyvista as pv



from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QFrame,
    QApplication, QCheckBox, QLineEdit, QSlider)
from PyQt5.QtCore import Qt


from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage



def t1_renderWindow(instance, filename):

    widget = QVTKRenderWindowInteractor(instance.t1_frame)
    instance.t1_layout.addWidget(widget)

    ren_window =  widget.GetRenderWindow()
    iren = ren_window.GetInteractor()

    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(filename)


    # Set up the mapper
    mapper = vtk.vtkGPUVolumeRayCastMapper()
    mapper.SetInputConnection(reader.GetOutputPort())


    # Set up the color transfer function
    color_transfer = vtk.vtkColorTransferFunction()
    color_transfer.SetColorSpaceToRGB()
    color_transfer.AddRGBPoint(0, 0, 0, 0)
    color_transfer.AddRGBPoint(512, 1, 1, 1)

    # Set up the opacity transfer function
    scalar_transfer = vtk.vtkPiecewiseFunction()
    scalar_transfer.AddPoint(0, 0)
    scalar_transfer.AddPoint(256, 0.035)

    # Create the volume property
    volume_property = vtk.vtkVolumeProperty()
    volume_property.SetColor(color_transfer)
    volume_property.SetScalarOpacity(scalar_transfer)

    # Create the volume actor
    volume = vtk.vtkVolume()
    volume.SetMapper(mapper)
    volume.SetProperty(volume_property)

    # Set up the renderer and camera
    renderer = vtk.vtkRenderer()
    ren_window.AddRenderer(renderer)

    renderer.SetBackground(0., 0., 0.)
    renderer.SetActiveCamera(instance.camera)

    # Add the volume actor to the renderer
    renderer.AddActor(volume)

    iren.Initialize()
    iren.Start()

    return ren_window


def t1_renderPlane(instance, filename):
    widget = QVTKRenderWindowInteractor(instance.t1_frame)
    instance.t1_layout.addWidget(widget)

    ren_window = widget.GetRenderWindow()
    iren = ren_window.GetInteractor()

    # Reader for the NIfTI file
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(filename)
    reader.Update()

    # Image viewer for slice rendering
    viewer = vtk.vtkImageViewer2()
    viewer.SetInputConnection(reader.GetOutputPort())
    viewer.SetRenderWindow(ren_window)
    viewer.SetSliceOrientationToXY()  # Axial view
    viewer.GetRenderer().SetBackground(0, 0, 0)
    
    # Set initial slice
    num_slices = reader.GetOutput().GetDimensions()[2]
    viewer.SetSlice(num_slices // 2)

    # Interactor style for image viewer
    style = vtkInteractorStyleImage()
    viewer.GetRenderWindow().GetInteractor().SetInteractorStyle(style)

    # Slider for scrolling slices
    slider = QSlider(instance.t1_frame)
    slider.setOrientation(Qt.Horizontal)
    slider.setMinimum(0)
    slider.setMaximum(num_slices - 1)
    slider.setValue(num_slices // 2)
    instance.t1_layout.addWidget(slider)

    # Slider value changed event
    def on_slider_value_changed(value):
        viewer.SetSlice(value)
        viewer.Render()

    slider.valueChanged.connect(on_slider_value_changed)

    # Initialize interactor
    iren.Initialize()
    viewer.Render()

    return ren_window