import vtk
import math
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class VolumePropertyManager:
    """
    Manages volume rendering properties with automated range optimization and slice thickness compensation.
    Always uses optimized intensity ranges for consistent, high-quality visualization.
    """
    
    def __init__(self, modality):
        """
        Initialize the volume property manager with modality-specific settings.
        
        Args:
            modality (str): Imaging modality ('t1', 'flair', 'swi_mag', 'swi_phase')
        """
        self.modality = modality
        self.base_opacity_scale = 1.0
        self.reference_thickness = 10.0
        self.optimal_range = None
        
        self.volume_property = vtk.vtkVolumeProperty()
        self.volume_property.ShadeOn()
        self.volume_property.SetAmbient(0.4)
        self.volume_property.SetDiffuse(0.6)
        self.volume_property.SetSpecular(0.2)
        self.volume_property.SetSpecularPower(10)

    def set_optimal_range(self, min_val, max_val):
        """Store the calculated optimal range for consistent visualization."""
        self.optimal_range = (min_val, max_val)
        
    def create_volume_property(self, slice_thickness):
        """
        Create volume property with thickness-compensated transfer functions using optimal range.
        
        Args:
            slice_thickness (float): Current slice thickness
        """
        if not self.optimal_range and self.modality != 'swi_phase':
            raise ValueError("Optimal range must be set before creating volume property")
            
        opacity_scale = (self.reference_thickness / slice_thickness) * self.base_opacity_scale
        
        color_tf = vtk.vtkColorTransferFunction()
        opacity_tf = vtk.vtkPiecewiseFunction()
        
        if self.modality == 'swi_phase':
            self._setup_swi_phase_transfer_functions(color_tf, opacity_tf, opacity_scale)
        else:
            self._setup_transfer_functions(color_tf, opacity_tf, opacity_scale)
        
        self.volume_property.SetColor(color_tf)
        self.volume_property.SetScalarOpacity(opacity_tf)
        
        return self.volume_property
    
    def _setup_transfer_functions(self, color_tf, opacity_tf, opacity_scale):
        """Configure transfer functions based on modality using optimal ranges."""
        min_val, max_val = self.optimal_range
        mid_val = (min_val + max_val) / 2
        
        if self.modality == 't1':
            quarter_val = (min_val + mid_val) / 2
            three_quarter_val = (mid_val + max_val) / 2
            
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
            
        elif self.modality == 'flair':
            color_tf.AddRGBPoint(min_val, 0, 0, 0)
            color_tf.AddRGBPoint(mid_val * 0.8, 0.4, 0.4, 0.4)
            color_tf.AddRGBPoint(mid_val * 1.2, 0.8, 0.8, 0.8)
            color_tf.AddRGBPoint(max_val, 1, 1, 1)
            
            opacity_tf.AddPoint(min_val, 0)
            opacity_tf.AddPoint(mid_val * 0.8, 0.4 * opacity_scale)
            opacity_tf.AddPoint(mid_val * 1.2, 0.6 * opacity_scale)
            opacity_tf.AddPoint(max_val, 0.7 * opacity_scale)
            
        elif self.modality == 'swi_mag':
            color_tf.AddRGBPoint(min_val, 0, 0, 0)
            color_tf.AddRGBPoint(mid_val * 0.6, 0.2, 0.2, 0.2)
            color_tf.AddRGBPoint(mid_val, 0.5, 0.5, 0.5)
            color_tf.AddRGBPoint(max_val, 1, 1, 1)
            
            opacity_tf.AddPoint(min_val, 0.8 * opacity_scale)
            opacity_tf.AddPoint(mid_val * 0.6, 0.6 * opacity_scale)
            opacity_tf.AddPoint(mid_val, 0.4 * opacity_scale)
            opacity_tf.AddPoint(max_val, 0.3 * opacity_scale)
    
    def _setup_swi_phase_transfer_functions(self, color_tf, opacity_tf, opacity_scale):
        """Configure specialized transfer functions for SWI phase data."""
        phase_points = [
            (-math.pi, (0.0, 0.098, 0.349), 0.9),      # Dark blue
            (-math.pi/2, (0.0, 0.333, 0.647), 0.7),    # Medium blue
            (-math.pi/4, (0.475, 0.624, 0.816), 0.5),  # Light blue
            (0, (0.961, 0.961, 0.961), 0.4),           # White
            (math.pi/4, (0.992, 0.906, 0.498), 0.5),   # Light yellow
            (math.pi/2, (0.992, 0.753, 0.298), 0.7),   # Medium yellow
            (math.pi, (0.851, 0.647, 0.125), 0.9)      # Dark yellow
        ]
        
        for position, color, opacity in phase_points:
            color_tf.AddRGBPoint(position, *color)
            opacity_tf.AddPoint(position, opacity * opacity_scale)
        
        color_tf.SetColorSpace(vtk.VTK_CTF_RGB)


class VolumeRenderer:
    """Handles 3D volume rendering of NIFTI images with optimized visualization parameters."""
    
    def __init__(self, viewer_instance, frame, layout, filename, show_bounds=False, modality=None):
        self.modality = modality
        self.viewer = viewer_instance
        self.frame = frame
        self.layout = layout
        self.filename = filename
        self.show_bounds = show_bounds
        
        self.property_manager = VolumePropertyManager(self.modality)
        
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
        """Create and configure VTK widget."""
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
        """Create complete volume rendering pipeline with optimal visualization."""
        try:
            self.reader = vtk.vtkNIFTIImageReader()
            self.reader.SetFileName(self.filename)
            self.reader.Update()
            
            if self.modality == 'swi_phase':
                self._setup_phase_pipeline()
            else:
                self._setup_standard_pipeline()
            
            bounds = self.reader.GetOutput().GetBounds()
            current_thickness = self.viewer.SlicePlanes.thickness if hasattr(self.viewer, 'SlicePlanes') else 10.0
            
            volume_property = self.property_manager.create_volume_property(current_thickness)
            self.volume = vtk.vtkVolume()
            self.volume.SetMapper(self.volume_mapper)
            self.volume.SetProperty(volume_property)
            
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
            
    def _setup_standard_pipeline(self):
        """Set up pipeline for standard modalities using optimal range."""
        optimal_range = self._calculate_optimal_range()
        self.property_manager.set_optimal_range(*optimal_range)
        
        self.volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
        self.volume_mapper.SetInputConnection(self.reader.GetOutputPort())
        self.volume_mapper.CroppingOn()
        self.volume_mapper.SetCroppingRegionFlags(vtk.VTK_CROP_SUBVOLUME)
        
    def _setup_phase_pipeline(self):
        """Set up specialized pipeline for SWI phase data."""
        normalizer = vtk.vtkImageShiftScale()
        normalizer.SetInputConnection(self.reader.GetOutputPort())
        normalizer.SetOutputScalarTypeToFloat()
        normalizer.SetShift(math.pi)
        normalizer.SetScale(1.0/(2.0 * math.pi))
        normalizer.Update()
        
        self.volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
        self.volume_mapper.SetInputConnection(normalizer.GetOutputPort())
        self.volume_mapper.CroppingOn()
        self.volume_mapper.SetCroppingRegionFlags(vtk.VTK_CROP_SUBVOLUME)
        
    def _calculate_optimal_range(self):
        """Calculate optimal intensity range using percentile analysis."""
        data = self.reader.GetOutput()
        histogram = vtk.vtkImageAccumulate()
        histogram.SetInputData(data)
        histogram.SetComponentExtent(0, 255, 0, 0, 0, 0)
        
        scalar_range = data.GetScalarRange()
        histogram.SetComponentOrigin(scalar_range[0], 0, 0)
        histogram.SetComponentSpacing((scalar_range[1] - scalar_range[0])/255, 0, 0)
        histogram.Update()
        
        hist_output = histogram.GetOutput()
        total_voxels = sum(hist_output.GetScalarComponentAsFloat(i, 0, 0, 0) for i in range(256))
        
        cumsum = 0
        p1_value = scalar_range[0]
        p99_value = scalar_range[1]
        
        for i in range(256):
            cumsum += hist_output.GetScalarComponentAsFloat(i, 0, 0, 0)
            if cumsum >= total_voxels * 0.01 and p1_value == scalar_range[0]:
                p1_value = scalar_range[0] + (i/255.0) * (scalar_range[1] - scalar_range[0])
            if cumsum >= total_voxels * 0.99:
                p99_value = scalar_range[0] + (i/255.0) * (scalar_range[1] - scalar_range[0])
                break
                
        return p1_value, p99_value
        
    def _ensure_initial_cropping(self):
        """Set initial cropping planes."""
        if hasattr(self.viewer.SlicePlanes, 'global_bounds'):
            bounds = self.viewer.SlicePlanes.global_bounds
            if bounds:
                self.volume_mapper.SetCroppingRegionPlanes(bounds)
                self.volume_mapper.Modified()
                
    def _add_bounds_outline(self):
        """Add white outline showing volume bounds."""
        outline = vtk.vtkOutlineFilter()
        outline.SetInputConnection(self.reader.GetOutputPort())
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(outline.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1.0, 1.0, 1.0)
        
        self.renderer.AddActor(actor)
        
    def update_volume_property(self, thickness):
        """Update volume property when slice thickness changes."""
        if hasattr(self, 'volume') and self.modality:
            new_property = self.property_manager.create_volume_property(thickness)
            self.volume.SetProperty(new_property)
            self.window.Render()
        
    def get_window_and_interactor(self):
        """Return render window, interactor, and volume."""
        return self.window, self.interactor, self.volume