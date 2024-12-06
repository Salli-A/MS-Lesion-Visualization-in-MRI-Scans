import vtk
import sys
import pyvista as pv



from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QFrame,
    QApplication, QCheckBox, QLineEdit, QSlider)
from PyQt5.QtCore import Qt


from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage



def phase_renderWindow(instance, filename):

    frame = instance.phase_frame
    layout = instance.phase_layout

    widget = QVTKRenderWindowInteractor(frame)
    layout.addWidget(widget)

    ren_window = widget.GetRenderWindow()
    iren = ren_window.GetInteractor()

    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(filename)
    reader.Update()

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



def phase_renderPlane(instance, filename):

    frame = instance.phase_frame
    layout = instance.phase_layout

    widget = QVTKRenderWindowInteractor(frame)
    layout.addWidget(widget)

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
    viewer.SetSliceOrientationToYZ()
    viewer.GetRenderer().SetBackground(0, 0, 0)
    
    # Set initial slice
    num_slices = reader.GetOutput().GetDimensions()[0]  # Use the X-axis for sagittal view
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
            self.num_slices = viewer.GetInput().GetDimensions()[0]  # Use the X-axis for sagittal view
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


from slice_interactor import SliceInteractor

def phase_renderPlaneVolume(instance, filename, slice_thickness=12, show_bounds=True, slice_direction='z'):
    
    frame = instance.phase_frame
    layout = instance.phase_layout
    
    

    # Set up the VTK rendering context
    widget = QVTKRenderWindowInteractor(frame)
    layout.addWidget(widget)

    ren_window = widget.GetRenderWindow()
    iren = ren_window.GetInteractor()

    # Read the NIFTI image
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(filename)
    reader.Update()

    # Get original bounds for repositioning
    original_bounds = reader.GetOutput().GetBounds()
    center_x = (original_bounds[1] + original_bounds[0]) / 2
    center_y = (original_bounds[3] + original_bounds[2]) / 2
    center_z = (original_bounds[5] + original_bounds[4]) / 2

    # Configure the volume mapper
    mapper = vtk.vtkGPUVolumeRayCastMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    mapper.CroppingOn()
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

    # Apply rotation and translation to maintain position
    transform = vtk.vtkTransform()
    transform.Translate(center_x, center_y, center_z)
    transform.RotateZ(-90)
    transform.RotateY(90)
    transform.Translate(-center_x, -center_y, -center_z)
    volume.SetUserTransform(transform)

    # Configure the renderer
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.0, 0.0, 0.0)
    renderer.SetActiveCamera(instance.camera)
    renderer.AddVolume(volume)

    # Add bounds display if show_bounds is True
    if show_bounds:
        outline_filter = vtk.vtkOutlineFilter()
        outline_filter.SetInputConnection(reader.GetOutputPort())

        # Transform the bounding box
        outline_transform = vtk.vtkTransformPolyDataFilter()
        outline_transform.SetTransform(transform)
        outline_transform.SetInputConnection(outline_filter.GetOutputPort())
        outline_transform.Update()

        outline_mapper = vtk.vtkPolyDataMapper()
        outline_mapper.SetInputConnection(outline_transform.GetOutputPort())

        outline_actor = vtk.vtkActor()
        outline_actor.SetMapper(outline_mapper)
        outline_actor.GetProperty().SetColor(1.0, 1.0, 1.0)  # White color for bounds

        renderer.AddActor(outline_actor)

    ren_window.AddRenderer(renderer)

    # Update slicing direction based on rotation
    slice_mapping = {'x': 'y', 'y': 'z', 'z': 'x'}  # Example mapping
    mapped_slice_direction = slice_mapping.get(slice_direction, slice_direction)

    # Set up the interactive slice interactor
    bounds = reader.GetOutput().GetBounds()  # Original bounds for slicing
    interactor_style = SliceInteractor(
        mapper=mapper,
        renderer=renderer,
        bounds=bounds,
        slice_thickness=slice_thickness,
        slice_direction=mapped_slice_direction
    )
    iren.SetInteractorStyle(interactor_style)

    iren.Initialize()
    iren.Start()

    return ren_window
