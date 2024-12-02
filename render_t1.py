import vtk
import sys
import pyvista as pv



from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QFrame,
    QApplication, QCheckBox, QLineEdit)
from PyQt5.QtCore import QTimer


from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor



def t1_renderWindow(instance, filename):

    widget = QVTKRenderWindowInteractor(instance.t1_frame)
    instance.t1_layout.addWidget(widget)

    iren = widget.GetRenderWindow().GetInteractor()
    renderer = vtk.vtkRenderer()
    widget.GetRenderWindow().AddRenderer(renderer)

    
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
    widget.GetRenderWindow().AddRenderer(renderer)

    renderer.SetBackground(0., 0., 0.)
    renderer.SetActiveCamera(instance.camera)

    # Add the volume actor to the renderer
    renderer.AddActor(volume)

    return widget,iren





def t1_renderPlane(instance, filename):
    
    # Create the QVTKRenderWindowInteractor and add it to the layout
    widget = QVTKRenderWindowInteractor(instance.t1_frame)
    instance.t1_layout.addWidget(widget)

    # Get the interactor and renderer
    iren = widget.GetRenderWindow().GetInteractor()
    renderer = vtk.vtkRenderer()
    widget.GetRenderWindow().AddRenderer(renderer)

    # Load the NIfTI image
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(filename)
    reader.Update()

    # Create the image plane widget
    image_plane_widget = vtk.vtkImagePlaneWidget()
    image_plane_widget.SetInteractor(iren)
    image_plane_widget.SetInputData(reader.GetOutput())

    # Configure the image plane widget
    image_plane_widget.SetPlaneOrientationToZAxes()  # Default to Z-axis
    image_plane_widget.SetSliceIndex(reader.GetOutput().GetExtent()[5] // 2)  # Center slice
    image_plane_widget.DisplayTextOn()  # Display slice index info
    image_plane_widget.SetPicker(vtk.vtkCellPicker())  # Picker for interaction
    image_plane_widget.On()

    # Set up the renderer
    renderer.SetBackground(0.0, 0.0, 0.0)
    widget.GetRenderWindow().Render()

    return widget, iren
