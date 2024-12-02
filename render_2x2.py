
import vtk
import sys
import pyvista as pv

from render_t1 import t1_renderWindow
from render_flair import flair_renderWindow
from render_swi import swi_renderWindow
from render_phase import phase_renderWindow

from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QFrame,
    QApplication, QCheckBox, QLineEdit)
from PyQt5.QtCore import QTimer


from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


# get data path from the first argument given
#file = sys.argv[1]

# Hardcode paths for testing multiwindow qt design
file_t1 = 'SUB_AXX\SUB_AXX\ses-20180322\sub-AXXX123_ses-20180322_t1.nii.gz'
file_flair = 'SUB_AXX\SUB_AXX\ses-20180322\sub-AXXX123_ses-20180322_flair.nii.gz'
file_swi = 'SUB_AXX\SUB_AXX\ses-20180322\sub-AXXX123_ses-20180322_swiMag.nii.gz'
file_phase = 'SUB_AXX\SUB_AXX\ses-20180322\sub-AXXX123_ses-20180322_swiPhase.nii.gz'

files = [file_t1, file_flair, file_swi, file_phase]


class Ui(QtWidgets.QMainWindow):
     def __init__(self):
          
          super(Ui, self).__init__()
          
          
          self.layout_setup()
         

          # Issue: Same camera position, focal point, etc. Different camera positions/rotations for each modalitity.
          # Possible reason: Different data, voxel size, intital orientation?
          self.camera = vtk.vtkCamera()
          self.camera.SetViewUp(0., -1., 0.)     
          self.camera.SetPosition(-500, 100, 100)
          self.camera.SetFocalPoint(100, 100, 100)

          self.render_modalities(files)
          
          self.timer = QTimer(self)
          self.timer.timeout.connect(self.render_all)
          self.timer.start(8) # msec per frame

          self.show()
          
          
          self.t1_iren.Initialize()
          self.flair_iren.Initialize()
          self.swi_iren.Initialize()
          self.phase_iren.Initialize()

          self.t1_iren.Start()
          self.flair_iren.Start()
          self.swi_iren.Start()
          self.phase_iren.Start()
     
     def render_modalities(self,filename):
          self.t1_widget, self.t1_iren = t1_renderWindow(self,filename[0])
          self.flair_widget, self.flair_iren = flair_renderWindow(self,filename[1])
          self.swi_widget, self.swi_iren = swi_renderWindow(self,filename[2])
          self.phase_widget, self.phase_iren = phase_renderWindow(self,filename[3])
          


     def setup_renderer(self, fname, widget):

          # Setup renderers.
          # Issue: Handles all modalaties the same w/ regards to opacity and color.
          # Solution: Indivual setups for modalities.
          
          # Create the reader
          reader = vtk.vtkNIFTIImageReader()
          reader.SetFileName(fname)

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
          renderer.SetActiveCamera(self.camera)

          # Add the volume actor to the renderer
          renderer.AddActor(volume)

          # Return the renderer to allow interaction
          return renderer
     
     def render_all(self):
          self.t1_widget.GetRenderWindow().Render()
          self.flair_widget.GetRenderWindow().Render()
          self.swi_widget.GetRenderWindow().Render()
          self.phase_widget.GetRenderWindow().Render()

     
     def layout_setup(self):
          
          uic.loadUi('MVis.ui', self)

          self.setWindowTitle("Multi-modality viewer")

          # Set placeholder text in text field
          # Not sure why this doesn't work - only works after 1st 'submit'
          self.comments_textfield.clear()
          self.comments_textfield.setPlaceholderText("Text field")

          # Display case 'id' (only relative path minus the image mode and file type)
          self.case_id.setText(file_t1[:-10])

          # Submit button action
          self.submit_button.clicked.connect(self.submit)

          # Reset view button action
          
          self.reset_button.clicked.connect(self.reset_view)

     def submit(self):

          print("Submitted")

          bad_quality = self.badQuality_checkbox.isChecked()
          prl = self.prl_checkbox.isChecked()
          cvs = self.cvs_checkbox.isChecked()

          print("bad_quality: " + str(bad_quality))
          print("prl: " + str(prl))
          print("cvs: " + str(cvs))

          comment = self.comments_textfield.toPlainText()
          print(comment)

          # Reset states
          self.comments_textfield.clear()
          self.badQuality_checkbox.setCheckState(False)
          self.prl_checkbox.setCheckState(False)
          self.cvs_checkbox.setCheckState(False)

     def reset_view(self):
          self.camera.SetViewUp(0., -1., 0.)     
          self.camera.SetPosition(-500, 100, 100)
          self.camera.SetFocalPoint(100, 100, 100)

    






app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()

