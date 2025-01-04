import vtk
from PyQt5.QtWidgets import QVBoxLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class VolumeRenderer:
    """Handles 3D volume rendering of NIFTI images in a Qt widget."""
    
    def __init__(self, viewer_instance, frame, layout, filename, show_bounds=True, modality=None):
    
        """
        Initialize and set up volume rendering.
        """
        self.modality = modality
        self.viewer = viewer_instance
        self.frame = frame
        self.layout = layout
        self.filename = filename
        self.show_bounds = show_bounds
        
        self._clear_layout()
        self._setup_vtk_widget()
        self._create_pipeline()
        
    def _clear_layout(self):
        """Clear existing widgets from layout."""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
    def _setup_vtk_widget(self):
        """Create and set up VTK widget in Qt frame."""
        self.vtk_widget = QVTKRenderWindowInteractor(self.frame, stereo=1)
        self.layout.addWidget(self.vtk_widget)
        
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.0, 0.0, 0.0)
        
        self.window = self.vtk_widget.GetRenderWindow()
        self.window.AddRenderer(self.renderer)

        # Enable stereo rendering - May need fine tuning for distance 
        self.window.SetStereoCapableWindow(True)
        self.window.SetStereoTypeToCrystalEyes()
        self.window.StereoRenderOn()
            
        self.interactor = self.window.GetInteractor()
        
    def _create_pipeline(self):
        """Set up complete VTK pipeline for volume rendering."""
        try:
            # Read NIFTI data
            self.reader = self._setup_reader()
            bounds = self.reader.GetOutput().GetBounds()
            
            # Create volume visualization pipeline
            self.volume_mapper = self._setup_mapper()  # Store mapper as instance variable
            volume_property = self._setup_volume_property()
            self._setup_volume(self.volume_mapper, volume_property)
             
            # Configure renderer
            self.renderer.SetActiveCamera(self.viewer.camera)
            self.renderer.AddVolume(self.volume)
            
            # Add bounds visualization if requested
            if self.show_bounds:
                self._add_bounds_outline()
            
            # Register with slice planes manager
            self.viewer.SlicePlanes.addWindow(
                mapper=self.volume_mapper,
                renderer=self.renderer,
                bounds=bounds
            )
            
            # Ensure initial cropping planes are set correctly
            self._ensure_initial_cropping()
            
        except Exception as e:
            raise RuntimeError(f"Error creating volume pipeline: {str(e)}")
    
    def _ensure_initial_cropping(self):
        """Ensure initial cropping planes are set correctly."""
        if hasattr(self.viewer.SlicePlanes, 'global_bounds'):
            bounds = self.viewer.SlicePlanes.global_bounds
            if bounds:
                # Set full volume bounds initially
                self.volume_mapper.SetCroppingRegionPlanes(bounds)
                self.volume_mapper.Modified()
                
    def _setup_reader(self):
        """Configure and return NIFTI reader."""
        reader = vtk.vtkNIFTIImageReader()
        reader.SetFileName(self.filename)
        reader.Update()
        return reader
        
    def _setup_mapper(self):
        """Configure and return volume mapper."""
        mapper = vtk.vtkGPUVolumeRayCastMapper()
        mapper.SetInputConnection(self.reader.GetOutputPort())
        mapper.CroppingOn()
        mapper.SetCroppingRegionFlags(vtk.VTK_CROP_SUBVOLUME)
        return mapper
        
    def _setup_volume_property(self):
        """
        Configure volume rendering properties based on modality.
        
        Args:
            modality (str): One of 't1', 'flair', 'swi_mag', 'swi_phase'
        """
        # Create transfer functions
        color_tf = vtk.vtkColorTransferFunction()
        opacity_tf = vtk.vtkPiecewiseFunction()
        
        if self.modality == 't1':
            # T1-weighted setup
            # CSF and lesions (dark) to white matter (bright)
            color_tf.AddRGBPoint(0, 0, 0, 0)      # Black
            color_tf.AddRGBPoint(500, 0.2, 0.2, 0.2)   # Dark gray (CSF)
            color_tf.AddRGBPoint(1000, 0.6, 0.6, 0.6)  # Gray matter
            color_tf.AddRGBPoint(1500, 0.9, 0.9, 0.9)  # White matter
            color_tf.AddRGBPoint(2000, 1, 1, 1)   # White (fat)
            
            opacity_tf.AddPoint(0, 0)       # Transparent
            opacity_tf.AddPoint(500, 0.15)  # More visible for brain tissue
            opacity_tf.AddPoint(1000, 0.3)  # Peak opacity for gray matter
            opacity_tf.AddPoint(1500, 0.25) # Slightly less for white matter
            opacity_tf.AddPoint(2000, 0.2)  # Reduced for very bright regions
            
        elif self.modality == 'flair':
            # FLAIR setup
            # Emphasis on lesions while suppressing CSF
            color_tf.AddRGBPoint(0, 0, 0, 0)      # Black (CSF)
            color_tf.AddRGBPoint(750, 0.4, 0.4, 0.4)   # Gray (normal tissue)
            color_tf.AddRGBPoint(1500, 0.8, 0.8, 0.8)  # Light gray
            color_tf.AddRGBPoint(2000, 1, 1, 1)   # White (lesions)
            
            opacity_tf.AddPoint(0, 0)       # Transparent (CSF)
            opacity_tf.AddPoint(750, 0.2)   # Semi-transparent normal tissue
            opacity_tf.AddPoint(1500, 0.3)  # More opaque
            opacity_tf.AddPoint(2000, 0.4)  # Most opaque for lesions
            
        elif self.modality == 'swi_mag':
            # SWI Magnitude setup
            # High contrast for veins and microbleeds
            color_tf.AddRGBPoint(0, 0, 0, 0)      # Black (veins)
            color_tf.AddRGBPoint(500, 0.3, 0.3, 0.3)   # Dark gray
            color_tf.AddRGBPoint(1000, 0.7, 0.7, 0.7)  # Light gray
            color_tf.AddRGBPoint(1500, 1, 1, 1)   # White (tissue)
            
            opacity_tf.AddPoint(0, 0.5)     # More opaque for veins
            opacity_tf.AddPoint(500, 0.3)   # Less opaque for transition
            opacity_tf.AddPoint(1000, 0.2)  # Semi-transparent tissue
            opacity_tf.AddPoint(1500, 0.1)  # Most transparent for bright tissue
            
        elif self.modality == 'swi_phase':
            # SWI Phase setup
            # Bidirectional contrast for phase information
            color_tf.AddRGBPoint(-4096, 0, 0, 1)    # Blue (negative phase)
            color_tf.AddRGBPoint(-2048, 0, 0.5, 0.5) # Cyan
            color_tf.AddRGBPoint(0, 0.5, 0.5, 0.5)   # Gray (zero phase)
            color_tf.AddRGBPoint(2048, 0.5, 0, 0)    # Dark red
            color_tf.AddRGBPoint(4096, 1, 0, 0)      # Red (positive phase)
            
            opacity_tf.AddPoint(-4096, 0.3)  # Moderate opacity for extremes
            opacity_tf.AddPoint(-2048, 0.2)  
            opacity_tf.AddPoint(0, 0.1)      # More transparent near zero
            opacity_tf.AddPoint(2048, 0.2)
            opacity_tf.AddPoint(4096, 0.3)
        
        
        # Create and configure volume property
        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetColor(color_tf)
        volume_property.SetScalarOpacity(opacity_tf)
        volume_property.SetInterpolationTypeToLinear()
        volume_property.ShadeOn()
        
        # Adjust lighting for better depth perception
        volume_property.SetAmbient(0.4)
        volume_property.SetDiffuse(0.6)
        volume_property.SetSpecular(0.2)
        volume_property.SetSpecularPower(10)
        
        return volume_property
        
    def _setup_volume(self, mapper, property):
        """Create and return volume with specified mapper and property."""
        self.volume = vtk.vtkVolume()
        self.volume.SetMapper(mapper)
        self.volume.SetProperty(property)

    def _add_bounds_outline(self):
        """Add white outline showing volume bounds."""
        outline = vtk.vtkOutlineFilter()
        outline.SetInputConnection(self.reader.GetOutputPort())
        
        outline_mapper = vtk.vtkPolyDataMapper()
        outline_mapper.SetInputConnection(outline.GetOutputPort())
        
        outline_actor = vtk.vtkActor()
        outline_actor.SetMapper(outline_mapper)
        outline_actor.GetProperty().SetColor(1.0, 1.0, 1.0)
        
        self.renderer.AddActor(outline_actor)
        
    def get_window_interactor_volume(self):
        """Return render window and interactor for external use."""
        return self.window, self.interactor, self.volume

def renderPlaneVolume(self, frame, layout, filename, show_bounds=True, modality=None):
    """
    Create volume rendering in Qt frame. Maintained for backward compatibility.
    Returns render window and interactor.
    """
    renderer = VolumeRenderer(
        viewer_instance=self,
        frame=frame,
        layout=layout,
        filename=filename,
        show_bounds=show_bounds,
        modality=modality
    )
    return renderer.get_window_interactor_volume()