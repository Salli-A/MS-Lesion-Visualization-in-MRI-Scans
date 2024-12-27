import vtk

class SliceInteractor(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, slice_thickness, slice_direction):
        """
        Initialize the SliceInteractor with the ability to slice in X, Y, or Z direction.
        :param slice_thickness: Thickness of each slice in global coordinates
        :param slice_direction: Direction of slicing ('x', 'y', 'z')
        """
        super().__init__()
        self.AddObserver("MouseWheelForwardEvent", self.on_scroll_forward)
        self.AddObserver("MouseWheelBackwardEvent", self.on_scroll_backward)

        self.slice_thickness = slice_thickness
        self.slice_direction = slice_direction.lower()
        self.windows = []  # Store renderer, mapper, and bounds for multiple windows
        self.zoom_factor = 1.1  # Adjust for zoom speed

        # Validate slice direction
        if self.slice_direction not in ('x', 'y', 'z'):
            raise ValueError("slice_direction must be 'x', 'y', or 'z'")

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
        self.set_cropping_planes(len(self.windows) - 1)

    def is_shift_pressed(self):
        """Check if Shift is pressed."""
        return self.GetInteractor().GetShiftKey()

    def set_cropping_planes(self, window_index):
        """Set the cropping planes based on the current slice and direction for a specific window."""
        window = self.windows[window_index]
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

    def on_scroll_forward(self, obj, event):
        for i, window in enumerate(self.windows):
            if self.is_shift_pressed():
                # Zoom in
                camera = window['renderer'].GetActiveCamera()
                camera.Zoom(self.zoom_factor)
            else:
                # Move slice forward
                window['current_slice'] = min(
                    window['current_slice'] + window['step'],
                    window['slice_max'] - self.slice_thickness
                )
                self.set_cropping_planes(i)
            window['renderer'].GetRenderWindow().Render()

    def on_scroll_backward(self, obj, event):
        for i, window in enumerate(self.windows):
            if self.is_shift_pressed():
                # Zoom out
                camera = window['renderer'].GetActiveCamera()
                camera.Zoom(1 / self.zoom_factor)
            else:
                # Move slice backward
                window['current_slice'] = max(
                    window['current_slice'] - window['step'],
                    window['slice_min']
                )
                self.set_cropping_planes(i)
            window['renderer'].GetRenderWindow().Render()
