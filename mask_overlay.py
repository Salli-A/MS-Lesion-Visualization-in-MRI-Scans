import os
import glob
import vtk

class MaskOverlay:
    """Handles loading and visualization of lesion and PRL masks with slice synchronization."""
    
    def __init__(self, session_path):
        self.session_path = session_path
        self.lesion_mask = None
        self.prl_mask = None
        self.actors = {}
        self.volume_mappers = {}
        self.slice_planes = None
        # Add state tracking for visibility
        self.lesion_visible = True
        self.prl_visible = True
        # Add individual opacity tracking
        self.lesion_opacity = 0.4
        self.prl_opacity = 0.4
        
    def set_slice_planes(self, slice_planes):
        """Set reference to SlicePlanes instance for synchronization."""
        self.slice_planes = slice_planes
        
    def load_masks(self):
        """Load lesion and PRL masks for the current session."""
        lesion_pattern = os.path.join(self.session_path, "*Lreg_lesionmask.nii.gz")
        prl_pattern = os.path.join(self.session_path, "*Lreg_PRLmask.nii.gz")
        
        lesion_files = glob.glob(lesion_pattern)
        prl_files = glob.glob(prl_pattern)
        
        if not lesion_files or not prl_files:
            raise FileNotFoundError(f"Mask files not found in {self.session_path}")
            
        self.lesion_mask = lesion_files[0]
        self.prl_mask = prl_files[0]
        
    def create_mask_actor(self, mask_file, mask_type):
        """Create a VTK actor for solid mask visualization using volume rendering."""
        reader = vtk.vtkNIFTIImageReader()
        reader.SetFileName(mask_file)
        reader.Update()
        
        mapper = vtk.vtkGPUVolumeRayCastMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        mapper.CroppingOn()
        mapper.SetCroppingRegionFlags(vtk.VTK_CROP_SUBVOLUME)
        
        # Brighter colors for maximum visibility
        mask_colors = {
            'lesion': (1.0, 0.2, 1.0),  # Bright magenta
            'prl': (0.0, 1.0, 0.0)      # Pure bright green
        }
        
        color = mask_colors[mask_type]
        
        color_tf = vtk.vtkColorTransferFunction()
        color_tf.AddRGBPoint(0, 0, 0, 0)
        color_tf.AddRGBPoint(1, *color)
        
        opacity_tf = vtk.vtkPiecewiseFunction()
        opacity_tf.AddPoint(0, 0)
        opacity_tf.AddPoint(1, 1)
        
        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetColor(color_tf)
        volume_property.SetScalarOpacity(opacity_tf)
        volume_property.SetInterpolationTypeToLinear()
        volume_property.ShadeOn()
        volume_property.SetAmbient(1.0)    # Maximum ambient light
        volume_property.SetDiffuse(1.0)    # Maximum diffuse reflection
        volume_property.SetSpecular(0.3)   # Slightly increased specular
        volume_property.SetSpecularPower(6) # Adjusted for broader highlights
        
        volume = vtk.vtkVolume()
        volume.SetMapper(mapper)
        volume.SetProperty(volume_property)
        
        return volume, mapper
        
    def add_to_renderer(self, renderer, modality):
        """Add mask overlays to a specific renderer."""
        # Remove existing actors if any
        if modality in self.actors:
            for actor in self.actors[modality]:
                renderer.RemoveVolume(actor)
        
        # Create new volumes with proper mapping
        lesion_volume, lesion_mapper = self.create_mask_actor(
            self.lesion_mask, 'lesion')  
        prl_volume, prl_mapper = self.create_mask_actor(
            self.prl_mask, 'prl')      
        
        # Add to renderer
        renderer.AddVolume(lesion_volume)
        renderer.AddVolume(prl_volume)
        
        # Store volumes and mappers
        self.actors[modality] = [lesion_volume, prl_volume]
        self.volume_mappers[modality] = {
            'lesion': lesion_mapper,
            'prl': prl_mapper
        }
        
        # Apply current visibility and opacity settings
        self.set_lesion_visibility(self.lesion_visible, modality)
        self.set_prl_visibility(self.prl_visible, modality)
        self.set_lesion_opacity(self.lesion_opacity, modality)
        self.set_prl_opacity(self.prl_opacity, modality)
        
        # Update cropping if we have slice information
        if self.slice_planes and self.slice_planes.global_bounds:
            self.update_clipping_bounds(modality)
        
    def remove_from_renderer(self, renderer, modality):
        """Remove mask overlays from a specific renderer."""
        if modality in self.actors:
            for actor in self.actors[modality]:
                renderer.RemoveVolume(actor)
            del self.actors[modality]
            if modality in self.volume_mappers:
                del self.volume_mappers[modality]
                
    def update_clipping_bounds(self, modality=None):
        """Update clipping bounds based on current slice position."""
        if not self.slice_planes or not self.slice_planes.global_bounds:
            return
            
        # Get current slice information
        direction = self.slice_planes.slice_direction
        current_slice = self.slice_planes.current_slice
        thickness = self.slice_planes.thickness
        bounds = list(self.slice_planes.global_bounds)
        
        # Update bounds based on slice direction
        if direction == 'x':
            bounds[0] = current_slice
            bounds[1] = current_slice + thickness
        elif direction == 'y':
            bounds[2] = current_slice
            bounds[3] = current_slice + thickness
        elif direction == 'z':
            bounds[4] = current_slice
            bounds[5] = current_slice + thickness
        
        # Update all modalities if none specified
        modalities = [modality] if modality else self.volume_mappers.keys()
        
        for mod in modalities:
            if mod in self.volume_mappers:
                for mask_type in ['lesion', 'prl']:
                    mapper = self.volume_mappers[mod][mask_type]
                    mapper.SetCroppingRegionPlanes(bounds)
                    mapper.Modified()
                    
    def set_lesion_visibility(self, visible, modality=None):
        """Set visibility of lesion mask."""
        self.lesion_visible = visible
        modalities = [modality] if modality else self.actors.keys()
        
        for mod in modalities:
            if mod in self.actors:
                self.actors[mod][0].SetVisibility(visible)

    def set_prl_visibility(self, visible, modality=None):
        """Set visibility of PRL mask."""
        self.prl_visible = visible
        modalities = [modality] if modality else self.actors.keys()
        
        for mod in modalities:
            if mod in self.actors:
                self.actors[mod][1].SetVisibility(visible)

    def set_lesion_opacity(self, opacity, modality=None):
        """Set opacity for lesion mask."""
        self.lesion_opacity = opacity
        modalities = [modality] if modality else self.actors.keys()
        
        for mod in modalities:
            if mod in self.actors:
                volume_property = self.actors[mod][0].GetProperty()
                opacity_tf = volume_property.GetScalarOpacity()
                opacity_tf.RemoveAllPoints()
                opacity_tf.AddPoint(0, 0)
                opacity_tf.AddPoint(0.5, opacity)
                opacity_tf.AddPoint(1.0, opacity)

    def set_prl_opacity(self, opacity, modality=None):
        """Set opacity for PRL mask."""
        self.prl_opacity = opacity
        modalities = [modality] if modality else self.actors.keys()
        
        for mod in modalities:
            if mod in self.actors:
                volume_property = self.actors[mod][1].GetProperty()
                opacity_tf = volume_property.GetScalarOpacity()
                opacity_tf.RemoveAllPoints()
                opacity_tf.AddPoint(0, 0)
                opacity_tf.AddPoint(0.5, opacity)
                opacity_tf.AddPoint(1.0, opacity)