import vtk

class SlicePlanes:
    """Controls synchronized slice planes across multiple MRI modalities."""
    
    def __init__(self, instance):
        self.windows = []
        self.thickness = 10
        self.step = self.thickness / 2
        self.zoom_factor = 1.2
        self.initial_zoom_factor= 0.6
        self.instance = instance
        self.slice_direction = 'y'
        self.current_slice = None
        self.global_bounds = None
        self.renderer_instances = []
        
    def initPlanes(self, slice_direction='y'):
        """Initialize slice planes after windows are added."""
        self.findBounds()
        self.setSliceDirection(slice_direction)
        self.setSliceThickness(self.thickness)
        
    def findBounds(self):
        """Calculate global bounds across all windows."""
        if not self.windows:
            return
            
        # Get bounds from all windows
        bounds_list = [list(window['bounds']) for window in self.windows]
        
        # Initialize with first window's bounds
        self.global_bounds = list(bounds_list[0])
        
        # Find min/max across all windows
        for i in range(0, 6, 2):  # Process x,y,z pairs
            self.global_bounds[i] = min(bounds[i] for bounds in bounds_list)
            self.global_bounds[i + 1] = max(bounds[i + 1] for bounds in bounds_list)
            
        # Update camera center and distance
        self._updateCameraPosition()
        
    def _updateCameraPosition(self):
        """Update camera position based on current bounds with improved zoom."""
        if not self.global_bounds:
            return
            
        x_min, x_max, y_min, y_max, z_min, z_max = self.global_bounds
        center = [(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2]
        
        # Calculate dimensions
        dimensions = [
            x_max - x_min,
            y_max - y_min,
            z_max - z_min
        ]
        
        # Calculate optimal camera distance based on volume size and view direction
        direction_map = {'x': 0, 'y': 1, 'z': 2}
        main_axis = direction_map[self.slice_direction]
        
        # Get the two dimensions perpendicular to viewing direction
        other_dims = [dim for i, dim in enumerate(dimensions) if i != main_axis]
        max_dim = max(other_dims)
        
        # Calculate distance to fit the volume in view
        # The factor 0.8 brings the volume closer to fill more of the view
        distance = max_dim * 0.8
        
        # Set up camera positions based on view direction
        camera_positions = {
            'x': ([center[0] + distance, center[1], center[2]], (0, -1, 0)),  # Coronal
            'y': ([center[0], center[1] + distance, center[2]], (0, 0, -1)),  # Axial
            'z': ([center[0], center[1], center[2] + distance], (0, -1, 0))   # Sagittal
        }
        
        position, view_up = camera_positions[self.slice_direction]
        self.instance.set_view(viewUp=view_up, position=position, focalPoint=center)
        
        # Update all renderers to use parallel projection
        for window in self.windows:
            renderer = window['renderer']
            camera = renderer.GetActiveCamera()
            camera.ParallelProjectionOn()
            
            # Set parallel scale to fit the view
            # The factor 0.4 provides a good initial zoom level
            camera.SetParallelScale(max_dim * self.initial_zoom_factor)
        
    def setSliceDirection(self, direction):
        """Set slicing direction (x/y/z) and update view."""
        self.slice_direction = direction.lower()
        
        # Map direction to bounds indices
        direction_indices = {'x': (0, 1), 'y': (2, 3), 'z': (4, 5)}
        self.direction_min, self.direction_max = direction_indices[self.slice_direction]
        
        # Initialize slice position if needed
        if self.current_slice is None:
            self.slice_min = self.global_bounds[self.direction_min]
            self.slice_max = self.global_bounds[self.direction_max]
            self.current_slice = self.slice_min + (self.slice_max - self.slice_min) / 2
            
        self._updateCameraPosition()
        self._updateCroppingPlanes()
        
    def setSliceThickness(self, thickness):
        """Update slice thickness and notify renderers."""
        self.thickness = thickness
        self._updateCroppingPlanes()

        
    def setStepSize(self, step_size):
        """Update step size adjust view."""
        self.step = step_size
        self._updateCroppingPlanes()
        
        
        # Update volume properties in all renderers
        for renderer in self.renderer_instances:
            renderer.update_volume_property(thickness)
        
    def _updateCroppingPlanes(self):
        """Update cropping planes for all windows and masks."""
        if not self.global_bounds:
            return
            
        # Create cropping plane bounds
        cropping_bounds = list(self.global_bounds)
        cropping_bounds[self.direction_min] = self.current_slice
        cropping_bounds[self.direction_max] = self.current_slice + self.thickness
        
        # Update main volume windows
        for window in self.windows:
            window['mapper'].SetCroppingRegionPlanes(cropping_bounds)
            
        # Update mask overlays if they exist
        if hasattr(self.instance, 'mask_overlay') and self.instance.mask_overlay:
            self.instance.mask_overlay.update_clipping_bounds()
            
    def addWindow(self, mapper, renderer, bounds):
        """Add a new window for synchronized viewing."""
        self.windows.append({
            'mapper': mapper,
            'renderer': renderer,
            'bounds': bounds
        })
    
    def addRenderer(self, renderer_instance):
        """Add a renderer instance for property updates."""
        self.renderer_instances.append(renderer_instance)

class SliceInteractor(vtk.vtkInteractorStyleTrackballCamera):
    """Handles mouse interaction for slice navigation."""
    
    def __init__(self, instance):
        super().__init__()
        self.AddObserver("MouseWheelForwardEvent", self.onScroll)
        self.AddObserver("MouseWheelBackwardEvent", self.onScroll)
        self.instance = instance
        self.planes = instance.SlicePlanes
        
    def onScroll(self, obj, event):
        """Handle scroll events for slice navigation and zooming."""
        is_forward = event == "MouseWheelForwardEvent"
        is_shift = self.GetInteractor().GetShiftKey()
        
        if is_shift:
            # Handle zooming
            zoom = self.planes.zoom_factor if is_forward else 1 / self.planes.zoom_factor
            self.instance.camera.Zoom(zoom)
        else:
            # Handle slice movement
            direction = 1 if is_forward else -1
            step = self.planes.step * direction
            
            new_slice = self.planes.current_slice + step
            min_slice = self.planes.slice_min - self.planes.thickness
            max_slice = self.planes.slice_max - self.planes.thickness
            
            self.planes.current_slice = max(min_slice, min(new_slice, max_slice))
            self.planes._updateCroppingPlanes()
            
        self.instance.render_all()