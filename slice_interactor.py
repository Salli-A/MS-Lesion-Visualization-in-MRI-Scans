import vtk

class SlicePlanes(vtk.vtkPlanes):
    """
    Initilize slice planes across modalities for 'sync' rendering.
    Keeps track of the slice planes for each modality and is updated via SliceInteractor.
    """
    def __init__(self):
        """ 
        Initlize the slice planes, direction, thickness and zoom factor.
        """
        super().__init__()

        self.windows = []

        self.thickness = 10
        self.step = self.thickness / 2 
        self.direction = (4,5)
        self.zoom_factor = 1.1
    
    def initPlanes(self, slice_thickness = 10, slice_direction = 'z', zoom_factor = 1.1):
        """
        Initialize the slice planes with the thickness, direction, and zoom factor after all windows have been added via addWindow.
        """
        self.findBounds()
        self.setSliceDirection(slice_direction)
        self.setSliceThickness(slice_thickness)
        self.setSliceZoomFactor(zoom_factor)

    def findBounds(self):
        """
        Finds the lower and upper bounds of the data for all windows.
        Takes the max and min of the bounds of all windows.
        """

        bounds_list = [list(window['bounds']) for window in self.windows]

        # Initialize global bounds with the first window's bounds
        global_bounds = bounds_list[0]
        for bounds in bounds_list[1:]:
            global_bounds[0] = min(global_bounds[0], bounds[0])
            global_bounds[1] = max(global_bounds[1], bounds[1])
            global_bounds[2] = min(global_bounds[2], bounds[2])
            global_bounds[3] = max(global_bounds[3], bounds[3])
            global_bounds[4] = min(global_bounds[4], bounds[4])
            global_bounds[5] = max(global_bounds[5], bounds[5])
            
        self.global_bounds = global_bounds

    def setSliceDirection(self, direction):
        """
        Set the slicing direction.
        """

        # replace with 'axial', 'coronal', 'sagittal'
        self.slice_direction = direction.lower()

        if self.slice_direction == 'x':
            self.direction_min = 0
            self.direction_max = 1
        elif self.slice_direction == 'y':
            self.direction_min = 2
            self.direction_max = 3
        elif self.slice_direction == 'z':
            self.direction_min = 4
            self.direction_max = 5
        
        
        slice_min, slice_max = self.global_bounds[self.direction_min], self.global_bounds[self.direction_max]
        self.current_slice = slice_min + (slice_max - slice_min) / 2
        self.croppingPlane = self.global_bounds
        self.set_cropping_planes()

    def setSliceThickness(self, thickness):
        """
        Set the thickness of each slice.
        """
        self.thickness = thickness
        self.step = self.thickness / 2  
        self.set_cropping_planes()

    def setSliceZoomFactor(self, factor):
        """
        Set the zoom factor for the slice.
        :param factor: The zoom factor for the slice.
        """
        self.zoom_factor = factor
        
    
    def set_cropping_planes(self):
        """Set the cropping planes based on the current slice and direction for all windows."""

        self.croppingPlane[self.direction_min], self.croppingPlane[self.direction_max] = self.current_slice, self.current_slice + self.thickness

        for window in self.windows:
            mapper = window['mapper']
            
            mapper.SetCroppingRegionPlanes(
                self.croppingPlane
            )

    def addWindow(self, mapper, renderer, bounds):
        """
        Add a renderer, mapper, and bounds for interaction.
        :param mapper: vtkMapper for rendering slices
        :param renderer: vtkRenderer
        :param bounds: Tuple specifying the data bounds (output of GetBounds())
        """


        # Add to the list of windows
        self.windows.append({
            'mapper': mapper,
            'renderer': renderer,
            'bounds': bounds
        })



        

class SliceInteractor(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, instance):
        """
        Initialize the SliceInteractor to interact with SlicePlane.
        """
        super().__init__()
        self.AddObserver("MouseWheelForwardEvent", self.on_scroll_forward)
        self.AddObserver("MouseWheelBackwardEvent", self.on_scroll_backward)
        self.instance = instance
        self.SlicePlanes = instance.SlicePlanes
        

        
    def is_shift_pressed(self):
        """Check if Shift is pressed."""
        return self.GetInteractor().GetShiftKey()


    def on_scroll_forward(self, obj, event):
        if self.is_shift_pressed():
            # Zoom in
            self.instance.camera.Zoom(self.SlicePlanes.zoom_factor)
        else:
            for window in self.SlicePlanes.windows:

                # Move slice forward
                self.SlicePlanes.current_slice = min(
                    self.SlicePlanes.current_slice + self.SlicePlanes.step,
                    self.SlicePlanes.current_slice - self.SlicePlanes.thickness)
                self.SlicePlanes.set_cropping_planes()
            window['renderer'].GetRenderWindow().Render()

    def on_scroll_backward(self, obj, event):
        
        if self.is_shift_pressed():
            # Zoom out
            self.instance.camera.Zoom(1 / self.SlicePlanes.zoom_factor)
        else:
            for window in self.SlicePlanes.windows:

                # Move slice backward
                self.SlicePlanes.current_slice = max(
                    self.SlicePlanes.current_slice - self.SlicePlanes.step,
                    self.SlicePlanes.current_slice + self.SlicePlanes.thickness)
                self.SlicePlanes.set_cropping_planes()

            window['renderer'].GetRenderWindow().Render()
