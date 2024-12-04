import vtk


class slice_interactor(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, mapper, renderer, slice_min, slice_max, slice_thickness, z_min, z_max, parent=None):
        
        super().__init__(parent)
        self.AddObserver("MouseWheelForwardEvent", self.on_scroll_forward)
        self.AddObserver("MouseWheelBackwardEvent", self.on_scroll_backward)
        self.mapper = mapper
        self.renderer = renderer
        self.slice_min = slice_min
        self.slice_max = slice_max
        self.slice_thickness = slice_thickness
        self.z_min = z_min
        self.z_max = z_max
        self.step = slice_thickness / 2
        self.zoom_factor = 1.1  # Adjust for zoom speed

    def is_shift_pressed(self):
        """Check if Shift is pressed."""
        return self.GetInteractor().GetShiftKey()

    def on_scroll_forward(self, obj, event):
        if self.is_shift_pressed():
            # Zoom in
            camera = self.renderer.GetActiveCamera()
            camera.Zoom(self.zoom_factor)
        else:
            # Move slice forward
            self.slice_min = min(self.slice_min + self.step, self.z_max - self.slice_thickness)
            self.slice_max = self.slice_min + self.slice_thickness
            self.mapper.SetCroppingRegionPlanes(
                float("-inf"), float("inf"),  # X-axis (full range)
                float("-inf"), float("inf"),  # Y-axis (full range)
                self.slice_min, self.slice_max
            )
        self.renderer.GetRenderWindow().Render()

    def on_scroll_backward(self, obj, event):
        if self.is_shift_pressed():
            # Zoom out
            camera = self.renderer.GetActiveCamera()
            camera.Zoom(1 / self.zoom_factor)
        else:
            # Move slice backward
            self.slice_min = max(self.slice_min - self.step, self.z_min)
            self.slice_max = self.slice_min + self.slice_thickness
            self.mapper.SetCroppingRegionPlanes(
                float("-inf"), float("inf"),  # X-axis (full range)
                float("-inf"), float("inf"),  # Y-axis (full range)
                self.slice_min, self.slice_max
            )
        self.renderer.GetRenderWindow().Render()
