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

    return ren_window,iren


def t1_renderPlane(instance, filename):
    
    widget = QVTKRenderWindowInteractor(instance.t1_frame)
    instance.t1_layout.addWidget(widget)

    # Set up the renderer and camera
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0., 0., 0.)
    renderer.SetActiveCamera(instance.camera)

    ren_window =  widget.GetRenderWindow()
    ren_window.AddRenderer(renderer)

    interactor = ren_window.GetInteractor()

    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(filename)
    reader.Update()

    # Create an outline of the dataset
    outline = vtk.vtkOutlineFilter()
    outline.SetInputConnection(reader.GetOutputPort())
    
    outline_mapper = vtk.vtkPolyDataMapper()
    outline_mapper.SetInputConnection(outline.GetOutputPort())

    outline_actor = vtk.vtkActor()
    outline_actor.SetMapper(outline_mapper)
    

    # Set up the Volume mapper
    volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
    volume_mapper.SetInputConnection(reader.GetOutputPort())

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
    volume_actor = vtk.vtkVolume()
    volume_actor.SetMapper(volume_mapper)
    volume_actor.SetProperty(volume_property)
        
    # X plane widget
    plane_widget_x = vtk.vtkImagePlaneWidget()
    plane_widget_x.SetInputConnection(reader.GetOutputPort())
    plane_widget_x.SetPlaneOrientationToXAxes()
    plane_widget_x.SetSliceIndex(reader.GetOutput().GetDimensions()[0] // 2)
    plane_widget_x.DisplayTextOn()

    picker_x = vtk.vtkCellPicker()
    picker_x.SetTolerance(0.005)
    plane_widget_x.SetPicker(picker_x)

    plane_widget_x.SetKeyPressActivationValue("x")
    plane_widget_x.SetInteractor(interactor)
    plane_widget_x.On()
    


    # Add the actors to the renderer
    renderer.AddActor(outline_actor)
    renderer.AddActor(volume_actor)

    return ren_window,interactor
