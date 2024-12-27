import vtk


class SlicePlanes(vtk.vtkPlanes):
    """
    Initilize slice planes across modalities for 'sync' rendering.
    Keeps track of the slice planes for each modality and is updated via SliceInteractor.
    """
    def __init__(self, slice_thickness = 12, slice_direction = 'z', zoom_factor = 1.1):
        """ 
        Initlize the slice planes, direction, thickness and zoom factor.
        """
        super().__init__()

        self.setSliceThickness(slice_thickness)
        self.setSliceDirection(slice_direction)
        self.setSliceZoomFactor(zoom_factor)

        self.windows = []

    def setSliceThickness(self, thickness):
        """
        Set the thickness of each slice.
        :param thickness: The thickness of each slice.
        """
        self.slice_thickness = thickness

    def setSliceDirection(self, direction):
        """
        Set the slicing direction.
        :param direction: The slicing direction ('x', 'y', or 'z').
        """
        # replace with 'axial', 'coronal', 'sagittal'
        self.slice_direction = direction.lower()

    def setSliceZoomFactor(self, factor):
        """
        Set the zoom factor for the slice.
        :param factor: The zoom factor for the slice.
        """
        self.zoom_factor = factor
        
    def addWindow(self, mapper, renderer, bounds):
        """
        Add a renderer, mapper, and bounds for interaction.
        :param mapper: vtkMapper for rendering slices
        :param renderer: vtkRenderer
        :param bounds: Tuple specifying the data bounds (output of GetBounds())
        """

        # Determine the slice range based on the direction in global coordinates
        if self.slice_direction == 'x':
            slice_min, slice_max = bounds[0], bounds[1]
            other_axes = [bounds[2], bounds[3], bounds[4], bounds[5]]
        elif self.slice_direction == 'y':
            slice_min, slice_max = bounds[2], bounds[3]
            other_axes = [bounds[0], bounds[1], bounds[4], bounds[5]]
        elif self.slice_direction == 'z':
            slice_min, slice_max = bounds[4], bounds[5]
            other_axes = [bounds[0], bounds[1], bounds[2], bounds[3]]

        current_slice = (slice_min + slice_max - self.slice_thickness) / 2
        step = self.slice_thickness / 2

        # Add to the list of windows
        self.windows.append({
            'mapper': mapper,
            'renderer': renderer,
            'bounds': bounds,
            'slice_min': slice_min,
            'slice_max': slice_max,
            'other_axes': other_axes,
            'current_slice': current_slice,
            'step': step
        })

        # Set initial cropping planes
        self.set_cropping_planes()

    def findBounds(self):
        """
        Finds the lower and upper bounds of the data for all windows.
        Takes the max and min of the bounds of all windows.
        """
        bounds_list = [window['bounds'] for window in self.windows]

        # Initialize global bounds with extreme values
        global_bounds = [float('inf'), float('-inf'),
                        float('inf'), float('-inf'),
                        float('inf'), float('-inf')]

        for bounds in bounds_list:
            global_bounds[0] = min(global_bounds[0], bounds[0])
            global_bounds[1] = max(global_bounds[1], bounds[1])
            global_bounds[2] = min(global_bounds[2], bounds[2])
            global_bounds[3] = max(global_bounds[3], bounds[3])
            global_bounds[4] = min(global_bounds[4], bounds[4])
            global_bounds[5] = max(global_bounds[5], bounds[5])



        return bounds
    
    def set_cropping_planes(self):
        """Set the cropping planes based on the current slice and direction for all windows."""

        for window in self.windows:
            mapper = window['mapper']
            current_slice = window['current_slice']
            other_axes = window['other_axes']

            if self.slice_direction == 'x':
                mapper.SetCroppingRegionPlanes(
                    current_slice, current_slice + self.slice_thickness,
                    other_axes[0], other_axes[1],
                    other_axes[2], other_axes[3]
                )
            elif self.slice_direction == 'y':
                mapper.SetCroppingRegionPlanes(
                    other_axes[0], other_axes[1],
                    current_slice, current_slice + self.slice_thickness,
                    other_axes[2], other_axes[3]
                )
            elif self.slice_direction == 'z':
                mapper.SetCroppingRegionPlanes(
                    other_axes[0], other_axes[1],
                    other_axes[2], other_axes[3],
                    current_slice, current_slice + self.slice_thickness
                )


        

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
            self.instance.camera.Zoom(self.SlicePlane.zoom_factor)
        else:
            for window in self.SlicePlanes.windows:
                # Move slice forward
                window['current_slice'] = min(
                    window['current_slice'] + window['step'],
                    window['slice_max'] - self.SlicePlanes.slice_thickness
                )
                self.SlicePlanes.set_cropping_planes()
            window['renderer'].GetRenderWindow().Render()

    def on_scroll_backward(self, obj, event):
        
        if self.is_shift_pressed():
            # Zoom out
            self.instance.camera.Zoom(1 / self.SlicePlanes.zoom_factor)
        else:
            for window in self.SlicePlanes.windows:
                # Move slice backward
                window['current_slice'] = max(
                    window['current_slice'] - window['step'],
                    window['slice_min']
                )
                self.SlicePlanes.set_cropping_planes()
            window['renderer'].GetRenderWindow().Render()
