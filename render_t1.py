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



from slice_interactor import slice_interactor
def t1_renderPlaneVolume(instance, filename, slice_thickness=12):

    # Set up the VTK rendering context
    widget = QVTKRenderWindowInteractor(instance.t1_frame)
    instance.t1_layout.addWidget(widget)
    ren_window = widget.GetRenderWindow()
    iren = ren_window.GetInteractor()

    # Read the NIFTI image
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(filename)
    reader.Update()

    # Compute volume center and slice bounds
    extent = reader.GetOutput().GetExtent()
    x_min, x_max, y_min, y_max, z_min, z_max = extent[0], extent[1], extent[2], extent[3], extent[4], extent[5]
    x_center, y_center, z_center = (x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2
    slice_min, slice_max = z_center - slice_thickness / 2, z_center + slice_thickness / 2

    # Set camera parameters
    distance = max(x_max - x_min, y_max - y_min, z_max - z_min) * 1.5
    instance.set_view(focalPoint=(x_center, y_center, z_center), position=(x_center, y_center, z_center + distance))

    # Configure the volume mapper
    mapper = vtk.vtkGPUVolumeRayCastMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    mapper.CroppingOn()
    mapper.SetCroppingRegionPlanes(
        float("-inf"), float("inf"),  # Full range in X
        float("-inf"), float("inf"),  # Full range in Y
        slice_min, slice_max          # Slicing range in Z
    )
    mapper.SetCroppingRegionFlags(vtk.VTK_CROP_SUBVOLUME)

    # Define color and opacity transfer functions
    color_transfer = vtk.vtkColorTransferFunction()
    color_transfer.SetColorSpaceToRGB()
    color_transfer.AddRGBPoint(0, 0, 0, 0)
    color_transfer.AddRGBPoint(512, 1, 1, 1)

    scalar_transfer = vtk.vtkPiecewiseFunction()
    scalar_transfer.AddPoint(0, 0)
    scalar_transfer.AddPoint(256, 0.15)

    # Create the volume property and actor
    volume_property = vtk.vtkVolumeProperty()
    volume_property.SetColor(color_transfer)
    volume_property.SetScalarOpacity(scalar_transfer)
    volume_property.ShadeOn()

    volume = vtk.vtkVolume()
    volume.SetMapper(mapper)
    volume.SetProperty(volume_property)

    # Configure the renderer
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.0, 0.0, 0.0)
    renderer.SetActiveCamera(instance.camera)
    renderer.AddVolume(volume)
    ren_window.AddRenderer(renderer)

    # Set up the interactive slice interactor
    interactor_style = slice_interactor(
        mapper=mapper,
        renderer=renderer,
        slice_min=slice_min,
        slice_max=slice_max,
        slice_thickness=slice_thickness,
        z_min=z_min,
        z_max=z_max
    )
    iren.SetInteractorStyle(interactor_style)
    iren.Initialize()
    iren.Start()

    return ren_window
