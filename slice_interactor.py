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

        self.slice_thickness = slice_thickness
        self.slice_direction = slice_direction.lower() # replace with 'axial', 'coronal', 'sagittal'
        self.zoom_factor = zoom_factor

        self.windows = []

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
        self.SlicePlane = instance.SlicePlanes
        

        
    def is_shift_pressed(self):
        """Check if Shift is pressed."""
        return self.GetInteractor().GetShiftKey()


    def on_scroll_forward(self, obj, event):
        if self.is_shift_pressed():
            # Zoom in
            self.instance.camera.Zoom(self.SlicePlane.zoom_factor)
        else:
            for window in self.SlicePlane.windows:
                # Move slice forward
                window['current_slice'] = min(
                    window['current_slice'] + window['step'],
                    window['slice_max'] - self.SlicePlane.slice_thickness
                )
                self.SlicePlane.set_cropping_planes()
            window['renderer'].GetRenderWindow().Render()

    def on_scroll_backward(self, obj, event):
        
        if self.is_shift_pressed():
            # Zoom out
            self.instance.camera.Zoom(1 / self.SlicePlane.zoom_factor)
        else:
            for window in self.SlicePlane.windows:
                # Move slice backward
                window['current_slice'] = max(
                    window['current_slice'] - window['step'],
                    window['slice_min']
                )
                self.SlicePlane.set_cropping_planes()
            window['renderer'].GetRenderWindow().Render()
