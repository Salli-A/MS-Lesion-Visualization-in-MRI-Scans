
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

fname_t1 = 'UB_AXX\SUB_AXX\ses-20180322\sub-AXXX123_ses-20180322_t1.nii.gz'




class Ui(QtWidgets.QMainWindow):
     def __init__(self):
          
          super(Ui, self).__init__()
          uic.loadUi('MVis.ui', self)

          # Load qt designer layout
          uic.loadUi('MVis.ui', self)

          # Set placeholder text in text field
          # Not sure why this doesn't work
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
          
          self.iren = self.flair_widget.GetRenderWindow().GetInteractor()
          self.ren = vtk.vtkRenderer()
          self.flair_widget.GetRenderWindow().AddRenderer(self.ren)

          self.source = vtk.vtkNIFTIImageReader()
          self.source.SetFileName(fname_flair)
          self.source.Update()

          self.vol_map = vtk.vtkGPUVolumeRayCastMapper()
          self.vol_map.SetInputConnection(self.source.GetOutputPort())
          
          self.color_transfer = vtk.vtkColorTransferFunction()
          self.color_transfer.SetColorSpaceToRGB()
          self.color_transfer.AddRGBPoint(0, 0, 0, 0)
          self.color_transfer.AddRGBPoint(512, 1, 1, 1)

          self.scalar_transfer = vtk.vtkPiecewiseFunction() 
          self.scalar_transfer.AddPoint(0, 0)
          self.scalar_transfer.AddPoint(256, 0.035)

          
          self.volume_property = vtk.vtkVolumeProperty()
          self.volume_property.SetColor(self.color_transfer)
          self.volume_property.SetScalarOpacity(self.scalar_transfer)

          
          self.vol_act = vtk.vtkVolume()
          self.vol_act.SetMapper(self.vol_map)
          self.vol_act.SetProperty(self.volume_property)

          
          self.camera = vtk.vtkCamera()
          self.camera.SetViewUp(0.,-1.,0.)
          self.camera.SetPosition(-500,100,100)
          self.camera.SetFocalPoint(100,100,100)

          self.ren.SetBackground(0., 0., 0.)
          
          self.ren.SetActiveCamera(self.camera)

          self.ren.AddActor(self.vol_act)

          self.show()
          
          self.iren.Initialize()
          self.iren.Start()


     

     def submit(self):

          print("Submitted")

          prl = self.prl_checkbox.isChecked()
          cvs = self.cvs_checkbox.isChecked()
          bad_quality = self.badQuality_checkbox.isChecked()

          print("bad_quality: " + str(bad_quality))
          print("prl: " + str(prl))
          print("cvs: " + str(cvs))

          comment = self.comments_textfield.toPlainText()
          print(comment)
    






app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()

