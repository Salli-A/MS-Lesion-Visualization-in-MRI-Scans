import vtk
import sys
import pyvista as pv



from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QFrame,
    QApplication, QCheckBox, QLineEdit)
from PyQt5.QtCore import QTimer


from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor



def swi_renderWindow(instance, filename):
    
    widget = QVTKRenderWindowInteractor(instance.swi_frame)
    instance.swi_layout.addWidget(widget)

    ren_window = widget.GetRenderWindow()
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

    # Compute the center of the volume
    reader.Update()
    bounds = reader.GetOutput().GetBounds()
    center_x = (bounds[0] + bounds[1]) / 2.0
    center_y = (bounds[2] + bounds[3]) / 2.0
    center_z = (bounds[4] + bounds[5]) / 2.0

    # Apply transformations to the volume
    transform = vtk.vtkTransform()
    transform.Translate(center_x, center_y, center_z)  # Move to center
    transform.RotateZ(-90)  # Rotate 90 degrees around the Z-axis
    transform.RotateY(90)  # Rotate 90 degrees around the Y-axis
    transform.Translate(-center_x, -center_y, -center_z)  # Move back
    volume.SetUserTransform(transform)

    # Set up the renderer and camera
    renderer = vtk.vtkRenderer()
    ren_window.AddRenderer(renderer)

    renderer.SetBackground(0.0, 0.0, 0.0)
    renderer.SetActiveCamera(instance.camera)

    # Add the volume actor to the renderer
    renderer.AddActor(volume)

    iren.Initialize()
    iren.Start()

    return ren_window
