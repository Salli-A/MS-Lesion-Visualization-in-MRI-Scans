
import vtk
import sys
import pyvista as pv


from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QFrame,
    QApplication, QCheckBox, QLineEdit)

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


# get data path from the first argument given
#fname = sys.argv[1]

# Hardcode paths for testing multiwindow qt design
fname_flair = 'SUB_AXX\SUB_AXX\ses-20180322\sub-AXXX123_ses-20180322_flair.nii.gz'

fname_swi = 'SUB_AXX\SUB_AXX\ses-20180322\sub-AXXX123_ses-20180322_swiMag.nii.gz'

fname_phase = 'SUB_AXX\SUB_AXX\ses-20180322\sub-AXXX123_ses-20180322_swiPhase.nii.gz'

fname_t1 = 'SUB_AXX\SUB_AXX\ses-20180322\sub-AXXX123_ses-20180322_t1.nii.gz'





class Ui(QtWidgets.QMainWindow):
     def __init__(self):
          
          super(Ui, self).__init__()
          uic.loadUi('MVis.ui', self)

          # Load qt designer layout
          uic.loadUi('MVis.ui', self)

          # Set placeholder text in text field
          # Not sure why this doesn't work - only works after 1st press?
          self.comments_textfield.clear()
          self.comments_textfield.setPlaceholderText("Text field")

          # Display case 'id' (only relative path minus the image mode and file type)
          self.case_id.setText(fname_flair[:-13])

          # Submit button action
          self.submit_button.clicked.connect(self.submit)
          
          self.t1_widget = QVTKRenderWindowInteractor(self.t1_frame)
          self.flair_widget = QVTKRenderWindowInteractor(self.flair_frame)
          self.swi_widget = QVTKRenderWindowInteractor(self.swi_frame)
          self.phase_widget = QVTKRenderWindowInteractor(self.phase_frame)
          
          self.t1_layout.addWidget(self.t1_widget)
          self.flair_layout.addWidget(self.flair_widget)
          self.swi_layout.addWidget(self.swi_widget)
          self.phase_layout.addWidget(self.phase_widget)
          
          self.t1_iren = self.t1_widget.GetRenderWindow().GetInteractor()
          self.flair_iren = self.flair_widget.GetRenderWindow().GetInteractor()
          self.swi_iren = self.swi_widget.GetRenderWindow().GetInteractor()
          self.phase_iren = self.phase_widget.GetRenderWindow().GetInteractor()
          

          # Issue: Same camera position, focal point, etc. Different camera positions/rotations for each modalitity.
          # Possible reason: Different data, voxel size, intital orientation?
          # Solution: ?
          self.camera = vtk.vtkCamera()
          self.camera.SetViewUp(0., -1., 0.)     
          self.camera.SetPosition(-500, 100, 100)
          self.camera.SetFocalPoint(100, 100, 100)
          
          self.t1_renderer = self.setup_renderer(fname_t1, self.t1_widget)
          self.flair_renderer = self.setup_renderer(fname_flair, self.flair_widget)
          self.swi_renderer = self.setup_renderer(fname_swi, self.swi_widget)
          self.phase_renderer = self.setup_renderer(fname_phase, self.phase_widget)

          self.show()
          
          self.t1_iren.Initialize()
          self.flair_iren.Initialize()
          self.swi_iren.Initialize()
          self.phase_iren.Initialize()

          self.t1_iren.Start()
          self.flair_iren.Start()
          self.swi_iren.Start()
          self.phase_iren.Start()


     def setup_renderer(self, fname, render_widget):

          # Setup renderers.
          # Issue: Handles all modalaties the same w/ regards to opacity and color.
          # Solution: Indivual setups for modalities.
          
          # Create the reader
          reader = vtk.vtkNIFTIImageReader()
          reader.SetFileName(fname)
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

          # Set up the renderer and camera
          renderer = vtk.vtkRenderer()
          render_widget.GetRenderWindow().AddRenderer(renderer)

          renderer.SetBackground(0., 0., 0.)
          renderer.SetActiveCamera(self.camera)

          # Add the volume actor to the renderer
          renderer.AddActor(volume)

          # Return the renderer to allow interaction
          return renderer

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
    






app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()

