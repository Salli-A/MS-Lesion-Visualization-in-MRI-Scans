import vtk
import sys
import pyvista as pv


# hardcode for testnig
filename = 'SUB_AXX\SUB_AXX\ses-20180322\sub-AXXX123_ses-20180322_flair.nii.gz'


# 2 set up the source
reader_src = vtk.vtkNIFTIImageReader()
reader_src.SetFileName(filename)


# 3 set up the volume mapper
vol_map = vtk.vtkGPUVolumeRayCastMapper()
vol_map.SetInputConnection(reader_src.GetOutputPort())

# 4 create a transfer function for color 
#   for now: map value 0   -> black: (0., 0., 0.) 
#                      512 -> black: (1., 1., 1.) 

color_transfer = vtk.vtkColorTransferFunction()
color_transfer.SetColorSpaceToRGB()
color_transfer.AddRGBPoint(0, 0, 0, 0)
color_transfer.AddRGBPoint(512, 1, 1, 1)


# 5 create a scalar transfer function for opacity
#   for now: map value 0   -> 0. 
#                      256 -> .01

scalar_transfer = vtk.vtkPiecewiseFunction() 
scalar_transfer.AddPoint(0, 0)
scalar_transfer.AddPoint(256, 0.035)


# 6 set up the volume properties with linear interpolation 
volume_property = vtk.vtkVolumeProperty()
volume_property.SetColor(color_transfer)
volume_property.SetScalarOpacity(scalar_transfer)

# 7 set up the actor and connect it to the mapper and the volume properties
vol_act = vtk.vtkVolume()
vol_act.SetMapper(vol_map)
vol_act.SetProperty(volume_property)

# 8 set up the camera
#   for now: up-vector:       (0., 1., 0.)
#            camera position: (-500, 100, 100)
#            focal point:     (100, 100, 100)

camera = vtk.vtkCamera()
camera.SetViewUp(0.,0.,1.)
camera.SetPosition(-500,100,100)
camera.SetFocalPoint(100,100,100)

# 9 create a renderer and set the color of the renderers background to black (0., 0., 0.)
renderer = vtk.vtkRenderer()
renderer.SetBackground(0., 0., 0.)

# 10 set the renderers camera as active
renderer.SetActiveCamera(camera)

# 11 add the volume actor to the renderer
renderer.AddActor(vol_act)

# 12 create a render window
ren_win = vtk.vtkRenderWindow()

# 13 add renderer to the render window
ren_win.AddRenderer(renderer)

# 14 create an interactor
iren = vtk.vtkRenderWindowInteractor()

# 15 connect interactor to the render window
iren.SetRenderWindow(ren_win)

# 16 start displaying the render window
ren_win.Render()

# 17 make the window interactive (start the interactor)
iren.Start()

