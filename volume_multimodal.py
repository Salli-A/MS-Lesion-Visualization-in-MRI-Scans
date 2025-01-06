import vtk
import math
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class VolumePropertyManager:
    """Manages volume rendering properties with automated range optimization and slice thickness compensation."""
    
    def __init__(self, modality):
        self.modality = modality
        self.base_opacity_scale = 1.0
        self.reference_thickness = 10.0  # Reference thickness for normalization

        self.volume_property = vtk.vtkVolumeProperty()
        self.volume_property.ShadeOn()
        
                   
        # Enhanced lighting properties for better depth perception
        self.volume_property.SetAmbient(0.4)
        self.volume_property.SetDiffuse(0.6)
        self.volume_property.SetSpecular(0.2)
        self.volume_property.SetSpecularPower(10)
        
    def create_volume_property(self, slice_thickness, optimal_range=None):
        """
        Create volume property with thickness-compensated transfer functions and optimal range.
        
        Args:
            modality (str): Imaging modality ('t1', 'flair', 'swi_mag', 'swi_phase')
            slice_thickness (float): Current slice thickness
            optimal_range (tuple): Optional (min, max) values from histogram analysis
        """
        opacity_scale = self._calculate_opacity_scale(slice_thickness)
        
        color_tf = vtk.vtkColorTransferFunction()
        opacity_tf = vtk.vtkPiecewiseFunction()
        
        if self.modality == 't1':
            self._setup_t1_transfer_functions(color_tf, opacity_tf, opacity_scale, optimal_range)
        elif self.modality == 'flair':
            self._setup_flair_transfer_functions(color_tf, opacity_tf, opacity_scale, optimal_range)
        elif self.modality == 'swi_mag':
            self._setup_swi_mag_transfer_functions(color_tf, opacity_tf, opacity_scale, optimal_range)
        elif self.modality == 'swi_phase':
            self._setup_swi_phase_transfer_functions(color_tf, opacity_tf, opacity_scale)
        else:
            self._setup_default_transfer_functions(color_tf, opacity_tf, opacity_scale, optimal_range)
        
        self.volume_property.SetColor(color_tf)
        self.volume_property.SetScalarOpacity(opacity_tf)

        return self.volume_property
    
    def _calculate_opacity_scale(self, slice_thickness):
        """Calculate opacity scaling factor based on slice thickness."""
        return (self.reference_thickness / slice_thickness) * self.base_opacity_scale
    
    def _setup_t1_transfer_functions(self, color_tf, opacity_tf, opacity_scale, optimal_range=None):
        """Configure transfer functions for T1-weighted images with optional range optimization."""
        if optimal_range:
            min_val, max_val = optimal_range
            mid_val = (min_val + max_val) / 2
            quarter_val = (min_val + mid_val) / 2
            three_quarter_val = (mid_val + max_val) / 2
            
            # Enhanced gray-white matter contrast
            color_tf.AddRGBPoint(min_val, 0, 0, 0)
            color_tf.AddRGBPoint(quarter_val, 0.2, 0.2, 0.2)
            color_tf.AddRGBPoint(mid_val, 0.6, 0.6, 0.6)
            color_tf.AddRGBPoint(three_quarter_val, 0.8, 0.8, 0.8)
            color_tf.AddRGBPoint(max_val, 1, 1, 1)
            
            opacity_tf.AddPoint(min_val, 0)
            opacity_tf.AddPoint(quarter_val, 0.3 * opacity_scale)
            opacity_tf.AddPoint(mid_val, 0.5 * opacity_scale)
            opacity_tf.AddPoint(three_quarter_val, 0.4 * opacity_scale)
            opacity_tf.AddPoint(max_val, 0.3 * opacity_scale)
        else:
            # Default values for standard T1 contrast
            color_tf.AddRGBPoint(0, 0, 0, 0)
            color_tf.AddRGBPoint(500, 0.2, 0.2, 0.2)
            color_tf.AddRGBPoint(1000, 0.6, 0.6, 0.6)
            color_tf.AddRGBPoint(1500, 0.9, 0.9, 0.9)
            color_tf.AddRGBPoint(2000, 1, 1, 1)
            
            opacity_tf.AddPoint(0, 0)
            opacity_tf.AddPoint(500, 0.3 * opacity_scale)
            opacity_tf.AddPoint(1000, 0.5 * opacity_scale)
            opacity_tf.AddPoint(1500, 0.4 * opacity_scale)
            opacity_tf.AddPoint(2000, 0.3 * opacity_scale)
    
    def _setup_flair_transfer_functions(self, color_tf, opacity_tf, opacity_scale, optimal_range=None):
        """Configure transfer functions for FLAIR images with enhanced lesion visibility."""
        if optimal_range:
            min_val, max_val = optimal_range
            mid_val = (min_val + max_val) / 2
            
            # Enhanced lesion visibility
            color_tf.AddRGBPoint(min_val, 0, 0, 0)
            color_tf.AddRGBPoint(mid_val * 0.8, 0.4, 0.4, 0.4)
            color_tf.AddRGBPoint(mid_val * 1.2, 0.8, 0.8, 0.8)
            color_tf.AddRGBPoint(max_val, 1, 1, 1)
            
            # Increased opacity in higher ranges for better lesion visibility
            opacity_tf.AddPoint(min_val, 0)
            opacity_tf.AddPoint(mid_val * 0.8, 0.4 * opacity_scale)
            opacity_tf.AddPoint(mid_val * 1.2, 0.6 * opacity_scale)
            opacity_tf.AddPoint(max_val, 0.7 * opacity_scale)
        else:
            # Default FLAIR settings
            color_tf.AddRGBPoint(0, 0, 0, 0)
            color_tf.AddRGBPoint(750, 0.4, 0.4, 0.4)
            color_tf.AddRGBPoint(1500, 0.8, 0.8, 0.8)
            color_tf.AddRGBPoint(2000, 1, 1, 1)
            
            opacity_tf.AddPoint(0, 0)
            opacity_tf.AddPoint(750, 0.3 * opacity_scale)
            opacity_tf.AddPoint(1500, 0.5 * opacity_scale)
            opacity_tf.AddPoint(2000, 0.6 * opacity_scale)
    
    def _setup_swi_mag_transfer_functions(self, color_tf, opacity_tf, opacity_scale, optimal_range=None):
        """Configure transfer functions for SWI magnitude images with enhanced vessel contrast."""
        if optimal_range:
            min_val, max_val = optimal_range
            mid_val = (min_val + max_val) / 2
            
            # Enhanced vessel contrast
            color_tf.AddRGBPoint(min_val, 0, 0, 0)
            color_tf.AddRGBPoint(mid_val * 0.6, 0.2, 0.2, 0.2)
            color_tf.AddRGBPoint(mid_val, 0.5, 0.5, 0.5)
            color_tf.AddRGBPoint(max_val, 1, 1, 1)
            
            # Higher opacity in darker ranges for vessel visibility
            opacity_tf.AddPoint(min_val, 0.8 * opacity_scale)
            opacity_tf.AddPoint(mid_val * 0.6, 0.6 * opacity_scale)
            opacity_tf.AddPoint(mid_val, 0.4 * opacity_scale)
            opacity_tf.AddPoint(max_val, 0.3 * opacity_scale)
        else:
            # Default SWI magnitude settings
            color_tf.AddRGBPoint(0, 0, 0, 0)
            color_tf.AddRGBPoint(500, 0.3, 0.3, 0.3)
            color_tf.AddRGBPoint(1000, 0.7, 0.7, 0.7)
            color_tf.AddRGBPoint(1500, 1, 1, 1)
            
            opacity_tf.AddPoint(0, 0.7 * opacity_scale)
            opacity_tf.AddPoint(500, 0.5 * opacity_scale)
            opacity_tf.AddPoint(1000, 0.3 * opacity_scale)
            opacity_tf.AddPoint(1500, 0.2 * opacity_scale)
    
    def _setup_swi_phase_transfer_functions(self, color_tf, opacity_tf, opacity_scale):
        """Configure transfer functions for SWI phase images with improved vessel visualization."""
        # Phase data is already normalized to [-π, π]
        import math
        
        # Paramagnetic effects (negative phase) - cool colors
        color_tf.AddRGBPoint(-math.pi, 0.5, 0.0, 0.8)    # Purple
        color_tf.AddRGBPoint(-math.pi/2, 0.0, 0.4, 1.0)  # Blue
        
        # Near-zero phase - grayscale
        color_tf.AddRGBPoint(-math.pi/4, 0.4, 0.4, 0.4)  # Dark gray
        color_tf.AddRGBPoint(0, 0.5, 0.5, 0.5)           # Mid gray
        color_tf.AddRGBPoint(math.pi/4, 0.6, 0.6, 0.6)   # Light gray
        
        # Diamagnetic effects (positive phase) - warm colors
        color_tf.AddRGBPoint(math.pi/2, 1.0, 0.6, 0.0)   # Orange
        color_tf.AddRGBPoint(math.pi, 1.0, 0.9, 0.0)     # Yellow
        
        # Enhanced opacity for better phase contrast
        opacity_tf.AddPoint(-math.pi, 0.8 * opacity_scale)
        opacity_tf.AddPoint(-math.pi/2, 0.6 * opacity_scale)
        opacity_tf.AddPoint(0, 0.3 * opacity_scale)
        opacity_tf.AddPoint(math.pi/2, 0.6 * opacity_scale)
        opacity_tf.AddPoint(math.pi, 0.8 * opacity_scale)
        
        # Use HSV interpolation for smoother color transitions
        color_tf.SetColorSpace(vtk.VTK_CTF_HSV)
    
    def _setup_default_transfer_functions(self, color_tf, opacity_tf, opacity_scale, optimal_range=None):
        """Configure default transfer functions for unknown modalities."""
        if optimal_range:
            min_val, max_val = optimal_range
            mid_val = (min_val + max_val) / 2
            
            color_tf.AddRGBPoint(min_val, 0, 0, 0)
            color_tf.AddRGBPoint(mid_val, 0.5, 0.5, 0.5)
            color_tf.AddRGBPoint(max_val, 1, 1, 1)
            
            opacity_tf.AddPoint(min_val, 0)
            opacity_tf.AddPoint(mid_val, 0.3 * opacity_scale)
            opacity_tf.AddPoint(max_val, 0.6 * opacity_scale)
        else:
            color_tf.AddRGBPoint(0, 0, 0, 0)
            color_tf.AddRGBPoint(512, 1, 1, 1)
            
            opacity_tf.AddPoint(0, 0)
            opacity_tf.AddPoint(256, 0.3 * opacity_scale)

class VolumeRenderer:
    """Handles 3D volume rendering of NIFTI images in a Qt widget with enhanced visualization."""
    
    def __init__(self, viewer_instance, frame, layout, filename, show_bounds=False, modality=None):
        """
        Initialize the volume renderer with enhanced visualization capabilities.
        
        Args:
            viewer_instance: Parent viewer instance
            frame: Qt frame to contain the VTK widget
            layout: Qt layout for the frame
            filename: Path to NIFTI file
            show_bounds: Whether to display volume bounds
            modality: Imaging modality ('t1', 'flair', 'swi_mag', 'swi_phase')
        """
        self.modality = modality
        self.viewer = viewer_instance
        self.frame = frame
        self.layout = layout
        self.filename = filename
        self.show_bounds = show_bounds
        
        # Initialize volume property manager
        self.property_manager = VolumePropertyManager(self.modality)
        
        # Setup rendering pipeline
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
        """Create and setup VTK widget in Qt frame."""
        self.vtk_widget = QVTKRenderWindowInteractor(self.frame, stereo=1)
        self.layout.addWidget(self.vtk_widget)
        
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.0, 0.0, 0.0)
        
        self.window = self.vtk_widget.GetRenderWindow()
        self.window.AddRenderer(self.renderer)

        self.window.SetStereoCapableWindow(True)
        self.window.SetStereoTypeToCrystalEyes()
        self.window.StereoRenderOn()    
        
        self.interactor = self.window.GetInteractor()
        
    def _create_pipeline(self):
        """Set up complete VTK pipeline for volume rendering."""
        try:
            # Read NIFTI data
            self.reader = self._setup_reader()
            
            # Calculate optimal range before normalization
            self.reader.Update()
            scalar_range = list(self.reader.GetOutput().GetScalarRange())
            
            # Create histogram for range analysis
            histogram = vtk.vtkImageAccumulate()  
            histogram.SetInputConnection(self.reader.GetOutputPort())
            histogram.SetComponentExtent(0, 255, 0, 0, 0, 0)  # 256 bins, 1D histogram
            histogram.SetComponentOrigin(scalar_range[0], 0, 0)
            histogram.SetComponentSpacing((scalar_range[1] - scalar_range[0])/255, 0, 0)
            histogram.Update()
            
            # Get histogram data
            data = histogram.GetOutput()
            total_voxels = 0
            for i in range(256):
                total_voxels += data.GetScalarComponentAsFloat(i, 0, 0, 0)
                
            # Find 1st and 99th percentiles
            cumsum = 0
            p1_value = scalar_range[0]
            p99_value = scalar_range[1]
            target_p1 = total_voxels * 0.01
            target_p99 = total_voxels * 0.99
            
            for i in range(256):
                cumsum += data.GetScalarComponentAsFloat(i, 0, 0, 0)
                if cumsum >= target_p1 and p1_value == scalar_range[0]:
                    p1_value = scalar_range[0] + (i/255.0) * (scalar_range[1] - scalar_range[0])
                if cumsum >= target_p99:
                    p99_value = scalar_range[0] + (i/255.0) * (scalar_range[1] - scalar_range[0])
                    break
                    
            optimal_range = (p1_value, p99_value)
            
            # Add normalization for SWI phase data
            if self.modality == 'swi_phase':
                normalizer = vtk.vtkImageShiftScale()
                normalizer.SetInputConnection(self.reader.GetOutputPort())
                normalizer.SetOutputScalarTypeToFloat()
                normalizer.SetShift(math.pi)
                normalizer.SetScale(1.0/(2.0 * math.pi))
                normalizer.Update()
                
                self.volume_mapper = self._setup_mapper()
                self.volume_mapper.SetInputConnection(normalizer.GetOutputPort())
                optimal_range = (-math.pi, math.pi)  # Use full phase range for SWI phase
            else:
                self.volume_mapper = self._setup_mapper()
                self.volume_mapper.SetInputConnection(self.reader.GetOutputPort())
                
            bounds = self.reader.GetOutput().GetBounds()
            
            print(f'For {self.modality} optimal range: {optimal_range}')
            # Create volume visualization pipeline with optimal range
            current_thickness = self.viewer.SlicePlanes.thickness if hasattr(self.viewer, 'SlicePlanes') else 10.0
            volume_property = self.property_manager.create_volume_property(
                current_thickness,
                optimal_range
            )
            self.volume = self._setup_volume(self.volume_mapper, volume_property)
            
            # Rest of the existing pipeline setup...
            self.renderer.SetActiveCamera(self.viewer.camera)
            self.renderer.AddVolume(self.volume)
            
            if self.show_bounds:
                self._add_bounds_outline()
            
            self.viewer.SlicePlanes.addWindow(
                mapper=self.volume_mapper,
                renderer=self.renderer,
                bounds=bounds
            )
            
            self._ensure_initial_cropping()
            
        except Exception as e:
            raise RuntimeError(f"Error creating volume pipeline: {str(e)}")
    
    def _ensure_initial_cropping(self):
        """Ensure initial cropping planes are set correctly."""
        if hasattr(self.viewer.SlicePlanes, 'global_bounds'):
            bounds = self.viewer.SlicePlanes.global_bounds
            if bounds:
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
        
    def _setup_volume(self, mapper, property):
        """Create and return volume with specified mapper and property."""
        volume = vtk.vtkVolume()
        volume.SetMapper(mapper)
        volume.SetProperty(property)
        return volume
            
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
        
    def update_volume_property(self, thickness):
        """Update volume property when slice thickness changes."""
        
        if hasattr(self, 'volume') and self.modality:
            new_property = self.property_manager.create_volume_property(thickness)
            self.volume.SetProperty(new_property)
            self.window.Render()
        
    def get_window_and_interactor(self):
        """Return render window and interactor for external use."""
        return self.window, self.interactor, self.volume