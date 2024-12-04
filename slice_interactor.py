


import vtk

class SliceInteractor(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, mapper, renderer, extent, slice_thickness, slice_direction, parent=None):
        """
        Initialize the SliceInteractor with the ability to slice in X, Y, or Z direction.
        :param mapper: vtkMapper for rendering slices
        :param renderer: vtkRenderer
        :param extent: Tuple specifying the data extent (output of GetExtent())
        :param slice_thickness: Thickness of each slice
        :param slice_direction: Direction of slicing ('x', 'y', 'z')
        :param parent: Parent class (if any)
        """
        super().__init__(parent)
        self.AddObserver("MouseWheelForwardEvent", self.on_scroll_forward)
        self.AddObserver("MouseWheelBackwardEvent", self.on_scroll_backward)
        
        self.mapper = mapper
        self.renderer = renderer
        self.extent = extent
        self.slice_thickness = slice_thickness
        self.slice_direction = slice_direction.lower()
        self.zoom_factor = 1.1  # Adjust for zoom speed
        
        # Determine the slice range based on the direction
        if self.slice_direction == 'x':
            self.slice_min = extent[0]
            self.slice_max = extent[1]
            self.other_axes = [extent[2], extent[3], extent[4], extent[5]]
        elif self.slice_direction == 'y':
            self.slice_min = extent[2]
            self.slice_max = extent[3]
            self.other_axes = [extent[0], extent[1], extent[4], extent[5]]
        elif self.slice_direction == 'z':
            self.slice_min = extent[4]
            self.slice_max = extent[5]
            self.other_axes = [extent[0], extent[1], extent[2], extent[3]]
        else:
            raise ValueError("slice_direction must be 'x', 'y', or 'z'")
        
        # Start at the middle of the range
        self.current_slice = (self.slice_min + self.slice_max - self.slice_thickness) / 2
        self.step = slice_thickness / 2

        # Initialize the cropping planes to reflect the starting position
        self.set_cropping_planes()

    def is_shift_pressed(self):
        """Check if Shift is pressed."""
        return self.GetInteractor().GetShiftKey()

    def set_cropping_planes(self):
        """Set the cropping planes based on the current slice and direction."""
        if self.slice_direction == 'x':
            self.mapper.SetCroppingRegionPlanes(
                self.current_slice, self.current_slice + self.slice_thickness,
                self.other_axes[0], self.other_axes[1],
                self.other_axes[2], self.other_axes[3]
            )
        elif self.slice_direction == 'y':
            self.mapper.SetCroppingRegionPlanes(
                self.other_axes[0], self.other_axes[1],
                self.current_slice, self.current_slice + self.slice_thickness,
                self.other_axes[2], self.other_axes[3]
            )
        elif self.slice_direction == 'z':
            self.mapper.SetCroppingRegionPlanes(
                self.other_axes[0], self.other_axes[1],
                self.other_axes[2], self.other_axes[3],
                self.current_slice, self.current_slice + self.slice_thickness
            )

    def on_scroll_forward(self, obj, event):
        if self.is_shift_pressed():
            # Zoom in
            camera = self.renderer.GetActiveCamera()
            camera.Zoom(self.zoom_factor)
        else:
            # Move slice forward
            self.current_slice = min(self.current_slice + self.step, self.slice_max - self.slice_thickness)
            self.set_cropping_planes()
        self.renderer.GetRenderWindow().Render()

    def on_scroll_backward(self, obj, event):
        if self.is_shift_pressed():
            # Zoom out
            camera = self.renderer.GetActiveCamera()
            camera.Zoom(1 / self.zoom_factor)
        else:
            # Move slice backward
            self.current_slice = max(self.current_slice - self.step, self.slice_min)
            self.set_cropping_planes()
        self.renderer.GetRenderWindow().Render()
