import vtk

# Hardcode for testing
filename = 'SUB_AXX\\SUB_AXX\\ses-20180322\\sub-AXXX123_ses-20180322_flair.nii.gz'

# Set up the source
reader_src = vtk.vtkNIFTIImageReader()
reader_src.SetFileName(filename)
reader_src.Update()

# Create renderers for each plane
renderer = vtk.vtkRenderer()
renderer.SetBackground(0., 0., 0.)

# Create render window and interactor
render_window = vtk.vtkRenderWindow()
render_window.AddRenderer(renderer)

render_interactor = vtk.vtkRenderWindowInteractor()
render_interactor.SetRenderWindow(render_window)

# Create an outline of the dataset
outline = vtk.vtkOutlineFilter()
outline.SetInputConnection(reader_src.GetOutputPort())

outline_mapper = vtk.vtkPolyDataMapper()
outline_mapper.SetInputConnection(outline.GetOutputPort())

outline_actor = vtk.vtkActor()
outline_actor.SetMapper(outline_mapper)

renderer.AddActor(outline_actor)
# X plane widget
plane_widget_x = vtk.vtkImagePlaneWidget()
plane_widget_x.SetInputConnection(reader_src.GetOutputPort())
plane_widget_x.SetPlaneOrientationToXAxes()
plane_widget_x.SetSliceIndex(reader_src.GetOutput().GetDimensions()[0] // 2)
plane_widget_x.DisplayTextOn()

picker_x = vtk.vtkCellPicker()
picker_x.SetTolerance(0.005)
plane_widget_x.SetPicker(picker_x)

plane_widget_x.SetKeyPressActivationValue("x")
plane_widget_x.SetInteractor(render_interactor)
plane_widget_x.On()

# Y plane widget
plane_widget_y = vtk.vtkImagePlaneWidget()
plane_widget_y.SetInputConnection(reader_src.GetOutputPort())
plane_widget_y.SetPlaneOrientationToYAxes()
plane_widget_y.SetSliceIndex(reader_src.GetOutput().GetDimensions()[1] // 2)
plane_widget_y.DisplayTextOn()

picker_y = vtk.vtkCellPicker()
picker_y.SetTolerance(0.005)
plane_widget_y.SetPicker(picker_y)

plane_widget_y.SetKeyPressActivationValue("y")
plane_widget_y.SetInteractor(render_interactor)
plane_widget_y.On()

# Z plane widget
plane_widget_z = vtk.vtkImagePlaneWidget()
plane_widget_z.SetInputConnection(reader_src.GetOutputPort())
plane_widget_z.SetPlaneOrientationToZAxes()
plane_widget_z.SetSliceIndex(reader_src.GetOutput().GetDimensions()[2] // 2)
plane_widget_z.DisplayTextOn()

picker_z = vtk.vtkCellPicker()
picker_z.SetTolerance(0.005)
plane_widget_z.SetPicker(picker_z)

plane_widget_z.SetKeyPressActivationValue("z")
plane_widget_z.SetInteractor(render_interactor)
plane_widget_z.On()


# Set up camera
camera = vtk.vtkCamera()
camera.SetViewUp(0., 1., 0.)
camera.SetPosition(-500, 100, 100)
camera.SetFocalPoint(100, 100, 100)
renderer.SetActiveCamera(camera)

# Render and start interaction
render_window.Render()
render_interactor.Start()
