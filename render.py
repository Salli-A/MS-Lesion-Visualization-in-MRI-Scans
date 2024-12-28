
import vtk
import sys
import pyvista as pv

from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import (QDesktopWidget, QButtonGroup)
from PyQt5.QtCore import QTimer


from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from slice_interactor import SliceInteractor, SlicePlanes

from volume_multimodal import renderPlaneVolume

# get data path from the first argument given
#file = sys.argv[1]

# Hardcode paths for testing multiwindow qt design
file_t1 = r'SUB_AXX\SUB_AXX\ses-20180322\sub-AXXX123_ses-20180322_t1.nii.gz'
file_flair = r'SUB_AXX\SUB_AXX\ses-20180322\sub-AXXX123_ses-20180322_flair.nii.gz'
file_swi = r'SUB_AXX\SUB_AXX\ses-20180322\sub-AXXX123_ses-20180322_swiMag.nii.gz'
file_phase = r'SUB_AXX\SUB_AXX\ses-20180322\sub-AXXX123_ses-20180322_swiPhase.nii.gz'


files = [file_t1, file_flair, file_swi, file_phase]


class Ui(QtWidgets.QMainWindow):
     def __init__(self):
          
          super(Ui, self).__init__()
          
          # Setup the buttons, text field etc.
          self.layout_setup()
          
          self.show()

          # Need a better way for deciding files
          # Render all modalities, files = (t1,flair,swi,phase)
          self.render_modalities(files)
          
          # Timer for rendering across modalities for 'sync' - noticable delay when doing 'fast' movements
          self.timer = QTimer(self)
          self.timer.timeout.connect(self.render_all)
          self.timer.start(8) # msec per frame

          
     
     def render_modalities(self,filename):

          
          # Setup camera for all modalities
          self.setup_camera()
          # Set up the slice planes for all modalities
          self.SlicePlanes = SlicePlanes(self)

          # Indivual rendering code for modalities
               # (Can be combined into one function if it takes into account the transfer function and stuff)
         

          # Volume slices

          self.t1_window, self.t1_iren = renderPlaneVolume(self, frame=self.t1_frame, layout=self.t1_layout, filename=filename[0])
          self.flair_window, self.flair_iren = renderPlaneVolume(self, frame=self.flair_frame, layout=self.flair_layout, filename=filename[1])
          # Applying the transoftrmation for SWI / phase applies i tto the croppingplane as well - skip for now.
          self.swi_window, self.swi_iren = renderPlaneVolume(self, frame=self.swi_frame, layout=self.swi_layout, filename=filename[2], swi_phase_modality=False)
          self.phase_window, self.phase_iren = renderPlaneVolume(self, frame=self.phase_frame, layout=self.phase_layout, filename=filename[3], swi_phase_modality=False)

          # Initate the slice planes
          self.SlicePlanes.initPlanes()
          
          interactor_t1 = SliceInteractor(self)
          interactor_flair = SliceInteractor(self)
          interactor_swi = SliceInteractor(self)
          interactor_phase = SliceInteractor(self)


          self.t1_iren.SetInteractorStyle(interactor_t1)
          self.flair_iren.SetInteractorStyle(interactor_flair)
          self.swi_iren.SetInteractorStyle(interactor_swi)
          self.phase_iren.SetInteractorStyle(interactor_phase)

          self.t1_iren.Initialize()
          self.flair_iren.Initialize()
          self.swi_iren.Initialize()
          self.phase_iren.Initialize()

          self.t1_iren.Start()
          self.flair_iren.Start()
          self.swi_iren.Start()
          self.phase_iren.Start()


          
     
     def render_all(self):
          # Force rendering for camera sync

          self.t1_window.Render()
          self.flair_window.Render()
          self.swi_window.Render()
          self.phase_window.Render()

     
     def layout_setup(self):
          uic.loadUi('MVis.ui', self)

          self.setWindowTitle("Multi-modality viewer")

          # Window size
          window_width = 1000
          window_height = 800
          self.resize(window_width, window_height)

          # Center the window on the screen
          screen_geometry = QDesktopWidget().availableGeometry()
          screen_center = screen_geometry.center()
          frame_geometry = self.frameGeometry()
          frame_geometry.moveCenter(screen_center)
          self.move(frame_geometry.topLeft())

          # Clear textfield for placegolder text
          self.text_field.clear()

          # Display case 'id' (only relative path minus the image mode and file type)
          self.case_id.setText(file_t1[:-10])

          # Submit button action
          self.submit_button.clicked.connect(self.submit)

          # Reset view button action
          self.reset_button.clicked.connect(self.reset_view)

          # Axial, coronal, sagittal buttons
          self.buttongroup_view = QButtonGroup()
          self.buttongroup_view.addButton(self.axial_button)
          self.buttongroup_view.addButton(self.coronal_button)
          self.buttongroup_view.addButton(self.sagittal_button) 
          self.buttongroup_view.setExclusive(True)
          self.axial_button.clicked.connect(self.change_slicing)
          self.coronal_button.clicked.connect(self.change_slicing)
          self.sagittal_button.clicked.connect(self.change_slicing)

          # Thickeness slider
          self.thickness_slider.setRange(1, 30)
          self.thickness_slider.valueChanged.connect(self.update_thickness)

     def submit(self):
          
          print("Submitted")

          bad_quality = self.quality_checkbox.isChecked()
          prl = self.prl_checkbox.isChecked()
          cvs = self.cvs_checkbox.isChecked()

          print("bad_quality: " + str(bad_quality))
          print("prl: " + str(prl))
          print("cvs: " + str(cvs))

          comment = self.text_field.toPlainText()
          print(comment)

          # Reset states
          self.text_field.clear()
          self.quality_checkbox.setCheckState(False)
          self.prl_checkbox.setCheckState(False)
          self.cvs_checkbox.setCheckState(False)
          self.reset_view()

          # to-do: go to next image?
          # to-do: save output to csv/something else

     def set_view(self, viewUp=None, position=None, focalPoint=None):
          if viewUp is not None:
               self.camera_viewUp = viewUp
          if position is not None:
               self.camera_position = position
          if focalPoint is not None:
               self.camera_focalPoint = focalPoint
          self.reset_view()

     def reset_view(self):
          self.camera.SetViewUp(self.camera_viewUp)
          self.camera.SetPosition(self.camera_position)
          self.camera.SetFocalPoint(self.camera_focalPoint)

     def setup_camera(self):
          self.camera = vtk.vtkCamera()
          viewUp = (0.,-1.,0)
          position = (-500, 100, 200)
          focalPoint = (100, 100, 100)
          self.set_view(viewUp, position, focalPoint)

     def change_slicing(self):
          
          if self.axial_button.isChecked():
               self.SlicePlanes.setSliceDirection('x')
          if self.coronal_button.isChecked():
               self.SlicePlanes.setSliceDirection('y')
          if self.sagittal_button.isChecked():
               self.SlicePlanes.setSliceDirection('z')

     def update_thickness(self):
          thickness = self.thickness_slider.value()
          self.SlicePlanes.setSliceThickness(thickness)





app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()
