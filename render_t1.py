import vtk
import sys
import pyvista as pv



from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QFrame,
    QApplication, QCheckBox, QLineEdit, QSlider, QLabel)
from PyQt5.QtCore import Qt


from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage



def t1_renderWindow(instance, filename):

    frame = instance.t1_frame
    layout = instance.t1_layout

    widget = QVTKRenderWindowInteractor(frame)
    layout.addWidget(widget)

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

    frame = instance.t1_frame
    layout = instance.t1_layout

    widget = QVTKRenderWindowInteractor(frame)
    layout.addWidget(widget)

    ren_window = widget.GetRenderWindow()
    iren = ren_window.GetInteractor()

    # Reader for the NIfTI file
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(filename)
    reader.Update()

    # Flip the image along the desired axis
    flip_y = vtk.vtkImageFlip()
    flip_y.SetInputConnection(reader.GetOutputPort())
    flip_y.SetFilteredAxis(1)  # Flip along the Y-axis
    flip_y.Update()

    flip_z = vtk.vtkImageFlip()
    flip_z.SetInputConnection(flip_y.GetOutputPort())
    flip_z.SetFilteredAxis(2)  # Flip along the Z-axis
    flip_z.Update()

    # Image viewer for slice rendering
    viewer = vtk.vtkImageViewer2()
    viewer.SetInputConnection(flip_z.GetOutputPort())
    viewer.SetRenderWindow(ren_window)
    viewer.SetSliceOrientationToXY()  # Saggital view
    viewer.GetRenderer().SetBackground(0, 0, 0)
    
    # Set initial slice
    num_slices = flip_z.GetOutput().GetDimensions()[2]
    viewer.SetSlice(num_slices // 2)

    # Zoom in by adjusting the camera
    renderer = viewer.GetRenderer()
    camera = renderer.GetActiveCamera()
    camera.Zoom(1.5)  # Adjust this factor to zoom in or out (1.0 = no zoom, >1 = zoom in)

    # Custom interactor style to suppress zooming on scroll
    class CustomInteractorStyle(vtk.vtkInteractorStyleImage):
        def __init__(self, viewer):
            super().__init__()
            self.viewer = viewer
            self.num_slices = viewer.GetInput().GetDimensions()[2]
            self.AddObserver("MouseWheelForwardEvent", self.on_scroll_event)
            self.AddObserver("MouseWheelBackwardEvent", self.on_scroll_event)
        
        def on_scroll_event(self, obj, event):
            current_slice = self.viewer.GetSlice()
            delta = 1 if event == "MouseWheelForwardEvent" else -1
            new_slice = max(0, min(self.num_slices - 1, current_slice + delta))
            self.viewer.SetSlice(new_slice)
            self.viewer.Render()

    # Create and set the custom interactor style
    style = CustomInteractorStyle(viewer)
    iren.SetInteractorStyle(style)

    # Initialize interactor
    iren.Initialize()
    viewer.Render()

    return ren_window


import vtkmodules.all as vtk

def t1_renderPlaneVolume(instance, filename, slice_thickness=12):
    frame = instance.t1_frame
    layout = instance.t1_layout

    widget = QVTKRenderWindowInteractor(frame)
    layout.addWidget(widget)

    ren_window = widget.GetRenderWindow()
    iren = ren_window.GetInteractor()

    # Read the NIFTI image
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(filename)
    reader.Update()

    # Get the dimensions of the volume to calculate the center
    extent = reader.GetOutput().GetExtent()
    z_min, z_max = extent[4], extent[5]
    z_center = (z_min + z_max) / 2  # Center along the Z-axis

    y_min, y_max = extent[2], extent[3]
    y_center = (y_min + y_max) / 2

    x_min, x_max = extent[0], extent[1]
    x_center = (x_min + x_max) / 2

    # Initial slice bounds
    slice_min = z_center - slice_thickness / 2
    slice_max = z_center + slice_thickness / 2

    # Update camera parameters
    distance = max(x_max - x_min, y_max - y_min, z_max - z_min) * 1.5

    focalPoint = (x_center, y_center, z_center)
    position = (x_center, y_center, z_center + distance)

    instance.set_view(focalPoint=focalPoint, position=position)

    # Set up the mapper
    mapper = vtk.vtkGPUVolumeRayCastMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    # Restrict the mapper to the initial slice bounds
    mapper.CroppingOn()
    mapper.SetCroppingRegionPlanes(
        float("-inf"), float("inf"),  # X-axis (full range)
        float("-inf"), float("inf"),  # Y-axis (full range)
        slice_min, slice_max          # Z-axis (slice range)
    )
    mapper.SetCroppingRegionFlags(vtk.VTK_CROP_SUBVOLUME)

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
    volume_property.ShadeOn()

    # Create the volume actor
    volume = vtk.vtkVolume()
    volume.SetMapper(mapper)
    volume.SetProperty(volume_property)

    # Set up the renderer and camera
    renderer = vtk.vtkRenderer()
    ren_window.AddRenderer(renderer)

    renderer.SetBackground(0.0, 0.0, 0.0)
    renderer.SetActiveCamera(instance.camera)

    # Add the volume actor to the renderer
    renderer.AddVolume(volume)

    # Custom interactor style to disable zoom
    class CustomInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
        def __init__(self, parent=None):
            self.AddObserver("MouseWheelForwardEvent", self.scroll_forward)
            self.AddObserver("MouseWheelBackwardEvent", self.scroll_backward)
            self.mapper = mapper
            self.slice_min = slice_min
            self.slice_max = slice_max
            self.step = slice_thickness / 2

        def scroll_forward(self, obj, event):
            self.slice_min = min(self.slice_min + self.step, z_max - slice_thickness)
            self.slice_max = self.slice_min + slice_thickness
            self.mapper.SetCroppingRegionPlanes(
                float("-inf"), float("inf"),  # X-axis (full range)
                float("-inf"), float("inf"),  # Y-axis (full range)
                self.slice_min, self.slice_max
            )
            ren_window.Render()

        def scroll_backward(self, obj, event):
            self.slice_min = max(self.slice_min - self.step, z_min)
            self.slice_max = self.slice_min + slice_thickness
            self.mapper.SetCroppingRegionPlanes(
                float("-inf"), float("inf"),  # X-axis (full range)
                float("-inf"), float("inf"),  # Y-axis (full range)
                self.slice_min, self.slice_max
            )
            ren_window.Render()

    # Set the custom interactor style
    interactor_style = CustomInteractorStyle()
    interactor_style.mapper = mapper
    iren.SetInteractorStyle(interactor_style)

    iren.Initialize()
    iren.Start()

    return ren_window
