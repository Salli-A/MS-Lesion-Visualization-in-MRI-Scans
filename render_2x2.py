
import vtk
import sys
import pyvista as pv

from render_t1 import t1_renderWindow, t1_renderPlane
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
          
          # Setup the buttons, text field etc.
          self.layout_setup()
          
          # One camera for all modalities
          self.setup_camera()
          
          self.show()

          # Need a better way for deciding files
          # Render all modalities, files = (t1,flair,swi,phase)
          self.render_modalities(files)
          
          # Timer for rendering across modalities for 'sync' - noticable delay when doing 'fast' movements
          self.timer = QTimer(self)
          self.timer.timeout.connect(self.render_all)
          self.timer.start(8) # msec per frame

          
     
     def render_modalities(self,filename):
          # Indivual rendering code for modalities
          # (Can be combined into one function if it takes into account the transfer function and stuff)
          self.t1_window = t1_renderWindow(self,filename[0])
          self.flair_window = flair_renderWindow(self,filename[1])
          self.swi_window = swi_renderWindow(self,filename[2])
          self.phase_window = phase_renderWindow(self,filename[3])
          
     
     def render_all(self):
          # Force rendering for camera sync

          self.t1_window.Render()
          self.flair_window.Render()
          self.swi_window.Render()
          self.phase_window.Render()

     
     def layout_setup(self):
          
          uic.loadUi('MVis.ui', self)

          self.setWindowTitle("Multi-modality viewer")

          # Set placeholder text in text field
          self.comments_textfield.setPlaceholderText("Text field")
          self.comments_textfield.clear()

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
          self.reset_view()

          # to-do: go to next image?


     def reset_view(self):
          self.camera.SetViewUp(0., -1., 0.)     
          self.camera.SetPosition(-500, 100, 200)
          self.camera.SetFocalPoint(100, 100, 100)

     def setup_camera(self):
          self.camera = vtk.vtkCamera()
          self.reset_view()

    






app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()

