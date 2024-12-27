import vtk
import sys
import pyvista as pv



from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QFrame,
    QApplication, QCheckBox, QLineEdit, QSlider, QLabel)
from PyQt5.QtCore import Qt


from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage

from slice_interactor import SlicePlanes

def renderPlaneVolume(self, frame, layout, filename, show_bounds=True, swi_phase_modality = False):
    """
    Render a volume using the SliceInteractor to allow interactive slicing.

    :param self: The main self containing the layout and frame.
    :param filename: The file path of the NIFTI image to render.
    :param slice_thickness: The thickness of each slice.
    :param show_bounds: Whether to display the bounds of the volume.
    :param slice_direction: The slicing direction ('x', 'y', or 'z').
    :return: The render window.
    """

    # Set up the VTK rendering context
    widget = QVTKRenderWindowInteractor(frame)
    layout.addWidget(widget)

    ren_window = widget.GetRenderWindow()
    iren = ren_window.GetInteractor()

    # Read the NIFTI image
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(filename)
    reader.Update()
    
    # Compute volume center and slice bounds
    bounds = reader.GetOutput().GetBounds()


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

    # rotate the volume for SWI / phase modality
    # When rotating using this code it rotates the plane as well...
    if swi_phase_modality:        
        x_min, x_max, y_min, y_max, z_min, z_max = bounds
        x_center, y_center, z_center = (x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2
        
        transform = vtk.vtkTransform()
        transform.Translate(x_center, y_center, z_center)
        transform.RotateZ(-90)
        transform.RotateY(90)
        transform.Translate(-x_center, -y_center, -z_center)
        volume.SetUserTransform(transform)

    # Configure the renderer
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.0, 0.0, 0.0)
    renderer.SetActiveCamera(self.camera)
    renderer.AddVolume(volume)

    # Add bounds display if show_bounds is True
    if show_bounds:
        outline_filter = vtk.vtkOutlineFilter()
        outline_filter.SetInputConnection(reader.GetOutputPort())
        outline_filter.Update()

        outline_mapper = vtk.vtkPolyDataMapper()
        outline_mapper.SetInputConnection(outline_filter.GetOutputPort())

        outline_actor = vtk.vtkActor()
        outline_actor.SetMapper(outline_mapper)
        outline_actor.GetProperty().SetColor(1.0, 1.0, 1.0)  # White color for bounds

        renderer.AddActor(outline_actor)

    ren_window.AddRenderer(renderer)

    self.SlicePlanes.addWindow(
        mapper=mapper,
        renderer=renderer,
        bounds = bounds
    )


    return ren_window, iren


