import vtk
import sys
import os
import glob
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QDesktopWidget, QMessageBox

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from slice_interactor import SliceInteractor, SlicePlanes
from volume_multimodal import VolumeRenderer
from ui import MainWindowUI
from mask_overlay import MaskOverlay
from tumor_animation import TumorAnimationWindow

class MRIViewer(MainWindowUI):
    def __init__(self, base_path):
        super().__init__()
        
        # Initialize mask_overlay first
        self.mask_overlay = None
        
        # Set up camera FIRST
        self.setup_camera()
        
        # Set up SlicePlanes SECOND
        self.SlicePlanes = SlicePlanes(self)
        
        # Set up file paths and load initial session
        self.setup_file_paths(base_path)
        
        # Initialize UI components (after we have files loaded)
        self.initializeUI()
        
        # Connect mask control signals
        self.connect_mask_controls()
        
        self.animation_button.clicked.connect(self.show_tumor_animation)
        
        # Timer for rendering sync
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.render_all)
        self.timer.start(8)  # msec per frame
        
        self.show()
    

    def setup_mask_overlay(self, session_path):
        """Set up mask overlay for current session."""
        try:
            # Remove existing mask overlay if it exists
            if self.mask_overlay:
                self.remove_current_masks()
            
            self.mask_overlay = MaskOverlay(session_path)
            self.mask_overlay.set_slice_planes(self.SlicePlanes)  
            self.mask_overlay.load_masks()
            
            # Store current UI states
            lesion_visible = self.lesion_toggle.isChecked()
            prl_visible = self.prl_toggle.isChecked()
            lesion_opacity = self.lesion_opacity_slider.value() / 100.0
            prl_opacity = self.prl_opacity_slider.value() / 100.0
            
            # Add to all renderers with shared camera
            renderers = {
                't1': self.t1_window.GetRenderers().GetFirstRenderer(),
                'flair': self.flair_window.GetRenderers().GetFirstRenderer(),
                'swi_mag': self.swi_window.GetRenderers().GetFirstRenderer(),
                'swi_phase': self.phase_window.GetRenderers().GetFirstRenderer()
            }
            
            for modality, renderer in renderers.items():
                # Ensure renderer uses the shared camera
                renderer.SetActiveCamera(self.camera)
                self.mask_overlay.add_to_renderer(renderer, modality)
            
            # Apply stored states
            self.mask_overlay.set_lesion_visibility(lesion_visible)
            self.mask_overlay.set_prl_visibility(prl_visible)
            self.mask_overlay.set_lesion_opacity(lesion_opacity)
            self.mask_overlay.set_prl_opacity(prl_opacity)
            
        except FileNotFoundError as e:
            print(f"Warning: Could not load masks - {str(e)}")
            # Reset toggle buttons if mask loading fails
            self.lesion_toggle.setChecked(False)
            self.prl_toggle.setChecked(False)
        except Exception as e:
            print(f"Error setting up mask overlay: {str(e)}")
            
    def remove_current_masks(self):
        """Remove current mask overlays from all renderers."""
        if not self.mask_overlay:
            return
            
        renderers = {
            't1': self.t1_window.GetRenderers().GetFirstRenderer(),
            'flair': self.flair_window.GetRenderers().GetFirstRenderer(),
            'swi_mag': self.swi_window.GetRenderers().GetFirstRenderer(),
            'swi_phase': self.phase_window.GetRenderers().GetFirstRenderer()
        }
        
        for modality, renderer in renderers.items():
            self.mask_overlay.remove_from_renderer(renderer, modality)
    
    def find_image_files(self, session_path, modalities):
        """
        Find image files for specified modalities in a session directory.
        Prioritizes 'Lreg_' prefixed files over 'CSreg_' files.
        
        Args:
            session_path (str): Path to the session directory
            modalities (list): List of modality suffixes to look for (e.g., ['t1', 'flair'])
            
        Returns:
            dict: Mapping of modality to file path
        """
        found_files = {}
        for modality in modalities:
            # Define file patterns to search for each modality
            if modality == 't1':
                pattern = os.path.join(session_path, f"*Lreg_t1.nii.gz")
            elif modality == 'flair':
                pattern = os.path.join(session_path, f"*Lreg_flair.nii.gz")
            elif modality == 'swi_mag':
                pattern = os.path.join(session_path, f"*Lreg_swiMag.nii.gz")
            elif modality == 'swi_phase':
                pattern = os.path.join(session_path, f"*Lreg_swiPhase.nii.gz")
                
            matches = glob.glob(pattern)
            if matches:
                found_files[modality] = matches[0]
                print(f"Found {modality}: {os.path.basename(matches[0])}")
            else:
                raise FileNotFoundError(
                    f"No {modality} file found matching pattern: {pattern}\n"
                    f"in session directory: {session_path}"
                )
                
        return found_files

    def setup_file_paths(self, base_path):
        """
        Set up file paths based on the provided base directory.
        Sessions are sorted chronologically by their dates.
        
        Args:
            base_path (str): Base directory containing session folders
            
        Raises:
            ValueError: If no session directories found or invalid session directory names
        """
        try:
            # Find all session directories
            self.session_dirs = []
            for item in os.listdir(base_path):
                if item.startswith('ses-'):
                    full_path = os.path.join(base_path, item)
                    if os.path.isdir(full_path):
                        # Verify session directory name format
                        try:
                            # Extract date part after 'ses-'
                            date_str = item[4:]  
                            # Verify it's a valid 8-digit date (YYYYMMDD)
                            if len(date_str) == 8 and date_str.isdigit():
                                year = int(date_str[:4])
                                month = int(date_str[4:6])
                                day = int(date_str[6:])
                                # Basic date validation
                                if (1900 <= year <= 2100 and 
                                    1 <= month <= 12 and 
                                    1 <= day <= 31):
                                    self.session_dirs.append(item)
                                else:
                                    print(f"Warning: Skipping directory with invalid date: {item}")
                            else:
                                print(f"Warning: Skipping directory with invalid format: {item}")
                        except ValueError as ve:
                            print(f"Warning: Skipping directory with invalid date format: {item}")
                            continue
            
            if not self.session_dirs:
                raise ValueError(f"No valid session directories found in {base_path}")
            
            # Sort sessions chronologically
            self.session_dirs.sort(key=lambda x: x[4:])  # Sort by date part after 'ses-'
            
            # Store base path and initialize with first session
            self.base_path = base_path
            self.current_session_index = 0
            
            # Define the modalities we want to load
            self.modalities = ['t1', 'flair', 'swi_mag', 'swi_phase']
            
            # Load initial session
            self.load_session(self.current_session_index)
            
            # Print sorted sessions for verification
            print("\nSessions loaded in chronological order:")
            for session in self.session_dirs:
                date_str = session[4:]  # Extract date part
                formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                print(f"  {session} ({formatted_date})")
                
        except Exception as e:
            raise ValueError(f"Error setting up file paths: {str(e)}")

    def load_session(self, index):
        """Load a specific session by index"""
        try:
            session_dir = self.session_dirs[index]
            full_session_path = os.path.join(self.base_path, session_dir)
            
            # Store current session
            self.current_session = session_dir
            self.current_session_index = index
            
            # Find all matching files
            found_files = self.find_image_files(full_session_path, self.modalities)
            
            # Store the files in order
            self.files = [found_files[mod] for mod in self.modalities]
            
            # Update UI elements
            self.update_session_display()
            
            # Update navigation buttons
            self.update_navigation_buttons()
            
            # Re-render the views
            self.render_modalities(self.files)
            
            # Update Default UI Buttons
            self.axial_button.setChecked(True)
            self.mri_toggle.setChecked(True)
            self.change_slicing()
            self.update_stepsize()
            self.update_thickness()
            
            # Set up mask overlay for new session
            self.setup_mask_overlay(full_session_path)
            
        except Exception as e:
            raise ValueError(f"Error loading session: {str(e)}")

    def initializeUI(self):
        """Initialize UI components and connect signals"""
        # Get subject ID from base directory name
        subject_id = os.path.basename(os.path.dirname(os.path.dirname(self.files[0])))
        self.subject_id.setText(subject_id)
        
        # Set session ID
        self.session_id.setText(self.current_session)
        
        # Connect navigation buttons
        self.prev_button.clicked.connect(self.previous_session)
        self.next_button.clicked.connect(self.next_session)
        
        # Update navigation button states
        self.update_navigation_buttons()
        
        # Connect other signals
        self.submit_button.clicked.connect(self.submit)
        self.reset_button.clicked.connect(self.reset_view)
        self.axial_button.clicked.connect(self.change_slicing)
        self.coronal_button.clicked.connect(self.change_slicing)
        self.sagittal_button.clicked.connect(self.change_slicing)
        
        # Connect thickness controls
        self.thickness_slider.valueChanged.connect(self.update_thickness)
        
        # Conncct step size controls
        self.step_slider.valueChanged.connect(self.update_stepsize)

        # Set axial view as default
        self.axial_button.setChecked(True)
        
        
    def update_volume_lighting(self, modality_name):
        """
        Updates the lighting properties of the volume associated with the given modality.
        Retrieves the volume, adjusts its lighting properties based on the sliders, and re-renders.
        """
        # Retrieve the volume
        volume = getattr(self, f"{modality_name}_volume", None)
        if volume is None:
            raise ValueError(f"No volume found for modality: {modality_name}")
        # Retrieve the volume property
        volume_property = volume.GetProperty()

        # Retrieve slider values
        ambient_slider = self.lighting_sliders[modality_name]["ambient"]
        diffuse_slider = self.lighting_sliders[modality_name]["diffuse"]
        specular_slider = self.lighting_sliders[modality_name]["specular"]
        spec_power_slider = self.lighting_sliders[modality_name]["spec_power"]

        ambient_val = ambient_slider.value() / 100.0
        diffuse_val = diffuse_slider.value() / 100.0
        specular_val = specular_slider.value() / 100.0
        spec_pow_val = float(spec_power_slider.value())

        # Set the volume property lighting values
        volume_property.SetAmbient(ambient_val)
        volume_property.SetDiffuse(diffuse_val)
        volume_property.SetSpecular(specular_val)
        volume_property.SetSpecularPower(spec_pow_val)

        # Mark volume as modified and render the scene
        volume.Modified()
        self.render_all()

        

    def reset_shading(self, modality_name):
        """
        Resets the shading parameters for the given modality, or for all modalities
        if 'modality_name' is None.

        :param modality_name: One of ['t1', 'flair', 'swi', 'phase'] or None
        """

        volume = getattr(self, f"{modality_name}_volume", None)
        volume_property = volume.GetProperty()

        # Reset the volume's shading
        volume_property = volume.GetProperty()

        volume_property.SetAmbient(0.4)
        volume_property.SetDiffuse(0.6)
        volume_property.SetSpecular(0.2)
        volume_property.SetSpecularPower(0.1)

        self.lighting_sliders[modality_name]["ambient"].setValue(40)
        self.lighting_sliders[modality_name]["diffuse"].setValue(60)
        self.lighting_sliders[modality_name]["specular"].setValue(20)
        self.lighting_sliders[modality_name]["spec_power"].setValue(10)

        self.render_all()
        
    def next_session(self):
        """Load next session if available"""
        if self.current_session_index < len(self.session_dirs) - 1:
            self.load_session(self.current_session_index + 1)

    def previous_session(self):
        """Load previous session if available"""
        if self.current_session_index > 0:
            self.load_session(self.current_session_index - 1)

    def update_session_display(self):
        """Update UI elements with current session info"""
        self.session_id.setText(self.current_session)

    def update_navigation_buttons(self):
        """Update the enabled state of navigation buttons"""
        self.prev_button.setEnabled(self.current_session_index > 0)
        self.next_button.setEnabled(self.current_session_index < len(self.session_dirs) - 1)
    

    def render_modalities(self, filenames):
        """Render all modalities with enhanced visualization."""
        try:
            # Set up the slice planes
            self.SlicePlanes = SlicePlanes(self)
            
            # Create renderers for each modality
            self.renderer_instances = []
            
            # T1-weighted
            self.t1_renderer = VolumeRenderer(
                viewer_instance=self,
                frame=self.t1_frame,
                layout=self.t1_layout,
                filename=filenames[0],
                modality='t1'
            )
            self.t1_window, self.t1_iren, self.t1_volume  = self.t1_renderer.get_window_and_interactor()
            self.SlicePlanes.addRenderer(self.t1_renderer)
            
            # FLAIR
            self.flair_renderer = VolumeRenderer(
                viewer_instance=self,
                frame=self.flair_frame,
                layout=self.flair_layout,
                filename=filenames[1],
                modality='flair'
            )
            self.flair_window, self.flair_iren, self.flair_volume = self.flair_renderer.get_window_and_interactor()
            self.SlicePlanes.addRenderer(self.flair_renderer)
            
            # SWI Magnitude
            self.swi_renderer = VolumeRenderer(
                viewer_instance=self,
                frame=self.swi_frame,
                layout=self.swi_layout,
                filename=filenames[2],
                modality='swi_mag'
            )
            self.swi_window, self.swi_iren, self.swi_volume  = self.swi_renderer.get_window_and_interactor()
            self.SlicePlanes.addRenderer(self.swi_renderer)
            
            # SWI Phase
            self.phase_renderer = VolumeRenderer(
                viewer_instance=self,
                frame=self.phase_frame,
                layout=self.phase_layout,
                filename=filenames[3],
                modality='swi_phase'
            )
            self.phase_window, self.phase_iren, self.phase_volume = self.phase_renderer.get_window_and_interactor()
            self.SlicePlanes.addRenderer(self.phase_renderer)
            
            # Initialize slice planes
            self.SlicePlanes.initPlanes()
            
            # Set up interactors
            interactors = [self.t1_iren, self.flair_iren, self.swi_iren, self.phase_iren]
            for iren in interactors:
                style = SliceInteractor(self)
                iren.SetInteractorStyle(style)
                iren.Initialize()
                iren.Start()
                
        except Exception as e:
            print(f"Error in render_modalities: {str(e)}")
            raise
    
    def render_all(self):
        """Force rendering"""
        for window in [self.t1_window, self.flair_window, self.swi_window, self.phase_window]:
            if window:  # Check if window exists before rendering
                window.Render()
    
    def setup_camera(self):
        """Initialize camera settings"""
        self.camera = vtk.vtkCamera()
        viewUp = (0., -1., 0)
        position = (-500, 100, 200)
        focalPoint = (100, 100, 100)
        self.set_view(viewUp, position, focalPoint)
    
    def set_view(self, viewUp=None, position=None, focalPoint=None):
        """Set camera view parameters"""
        if viewUp is not None:
            self.camera_viewUp = viewUp
        if position is not None:
            self.camera_position = position
        if focalPoint is not None:
            self.camera_focalPoint = focalPoint
        self.reset_view()
    
    def reset_view(self):
        """Reset camera to initial view"""
        self.camera.SetViewUp(self.camera_viewUp)
        self.camera.SetPosition(self.camera_position)
        self.camera.SetFocalPoint(self.camera_focalPoint)

    def change_slicing(self):
        """Handle slice direction changes"""
        if not hasattr(self.SlicePlanes, 'global_bounds') or not self.SlicePlanes.global_bounds:
            return

        x_min, x_max, y_min, y_max, z_min, z_max = self.SlicePlanes.global_bounds
        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2
        center_z = (z_min + z_max) / 2
        
        # Calculate dimensions for proper camera distance
        dimensions = [
            x_max - x_min,
            y_max - y_min,
            z_max - z_min
        ]
        max_dim = max(dimensions) * 1.5  # Use 1.5x max dimension for better view
        
        if self.axial_button.isChecked():
            # Axial view (top-down)
            self.SlicePlanes.setSliceDirection('y')
            viewUp = (0, 0, -1)
            position = (center_x, center_y + max_dim, center_z)
            focalPoint = (center_x, center_y, center_z)
            
        elif self.coronal_button.isChecked():
            # Coronal view (front view)
            self.SlicePlanes.setSliceDirection('x')
            viewUp = (0, -1, 0)
            position = (center_x + max_dim, center_y, center_z)
            focalPoint = (center_x, center_y, center_z)
            
        elif self.sagittal_button.isChecked():
            # Sagittal view (side view)
            self.SlicePlanes.setSliceDirection('z')
            viewUp = (0, -1, 0)
            position = (center_x, center_y, center_z + max_dim)
            focalPoint = (center_x, center_y, center_z)
        
        # Update camera settings
        self.set_view(viewUp, position, focalPoint)
        
        # Reset slice position to center of volume
        direction_map = {'x': (0, 1), 'y': (2, 3), 'z': (4, 5)}
        current_direction = self.SlicePlanes.slice_direction
        min_idx, max_idx = direction_map[current_direction]
        
        # Set current slice to center of volume in current direction
        self.SlicePlanes.current_slice = (self.SlicePlanes.global_bounds[min_idx] + 
                                        self.SlicePlanes.global_bounds[max_idx]) / 2
        
        # Update cropping planes
        self.SlicePlanes._updateCroppingPlanes()
        
        # Force render update
        self.render_all()

    def update_thickness(self):
        """Update slice thickness with enhanced visualization."""
        thickness = self.thickness_slider.value()
        if hasattr(self, 'SlicePlanes'):
            self.SlicePlanes.setSliceThickness(thickness)
        self.render_all()  # Ensure all views are updated
      
    def update_stepsize(self):
        """Update slice thickness"""
        step_size = self.step_slider.value()
        self.SlicePlanes.setStepSize(step_size)

    def submit(self):
        """Handle form submission"""
        print("Submitting findings:")
        
        # Get checkbox states
        findings = {
            "Bad quality MRI": self.quality_checkbox.isChecked(),
            "Perivascular Rim Lesions (PRL)": self.prl_checkbox.isChecked(),
            "Central Vein Signs (CVS)": self.cvs_checkbox.isChecked()
        }
        
        # Get comments
        comments = self.notes_field.toPlainText().strip()
        
        # Print findings
        for finding, present in findings.items():
            if present:
                print(f"- {finding}: Yes")
        
        if comments:
            print(f"Comments: {comments}")
        
        # Reset form
        self.notes_field.clear()
        self.quality_checkbox.setChecked(False)
        self.prl_checkbox.setChecked(False)
        self.cvs_checkbox.setChecked(False)
        
        # Optional: save to file or database here
        
        print("Submission complete")
    
    def connect_mask_controls(self):
        """Connect mask control UI elements to their handlers."""
        # Connect toggle buttons
        self.lesion_toggle.clicked.connect(self.toggle_lesion_mask)
        self.prl_toggle.clicked.connect(self.toggle_prl_mask)
        self.mri_toggle.clicked.connect(self.toggle_mri_visibility)
        
        # Connect opacity sliders
        self.lesion_opacity_slider.valueChanged.connect(self.update_lesion_opacity)
        self.prl_opacity_slider.valueChanged.connect(self.update_prl_opacity)

    def toggle_lesion_mask(self, checked):
        """Toggle visibility of lesion mask."""
        if self.mask_overlay:
            self.mask_overlay.set_lesion_visibility(checked)
            self.render_all()

    def toggle_prl_mask(self, checked):
        """Toggle visibility of PRL mask."""
        if self.mask_overlay:
            self.mask_overlay.set_prl_visibility(checked)
            self.render_all()

    def update_lesion_opacity(self, value):
        """Update opacity of lesion mask."""
        if self.mask_overlay:
            opacity = value / 100.0  # Convert slider value to opacity
            self.mask_overlay.set_lesion_opacity(opacity)
            self.render_all()

    def update_prl_opacity(self, value):
        """Update opacity of PRL mask."""
        if self.mask_overlay:
            opacity = value / 100.0  # Convert slider value to opacity
            self.mask_overlay.set_prl_opacity(opacity)
            self.render_all()
    
    
    def toggle_mri_visibility(self, checked):
        """
        Toggle visibility of MRI volumes while keeping masks visible.
        Uses volume visibility instead of opacity manipulation to avoid texture size issues.
        """
        if checked:
            self.mri_toggle.setText("Show Masks Only")
        else:
            self.mri_toggle.setText("Show MRI + Masks")
            
        # Update visibility for all modality volumes
        volumes = [
            self.t1_volume,
            self.flair_volume, 
            self.swi_volume,
            self.phase_volume
        ]
        
        for volume in volumes:
            if volume:
                # Simply toggle the volume's visibility
                volume.SetVisibility(checked)
        
        # Force render update
        self.render_all()
        
    def show_tumor_animation(self):
        """
        Launch the tumor progression animation window with chronologically sorted tumor masks.
        Files are sorted based on session dates (YYYYMMDD) to show proper tumor progression over time.
        """
        try:
            # Create a list to store tuples of (session_date, file_path)
            tumor_data = []
            
            for session_dir in self.session_dirs:
                # Extract the date from session directory (after 'ses-')
                session_date = session_dir[4:]  # Gets YYYYMMDD portion
                
                # Find tumor mask in this session
                session_path = os.path.join(self.base_path, session_dir)
                mask_pattern = os.path.join(session_path, "*Lreg_lesionmask.nii.gz")
                matches = glob.glob(mask_pattern)
                
                if matches:
                    # Store tuple of (date, file_path) for sorting
                    tumor_data.append((session_date, matches[0]))
                    print(f"Found tumor mask for session {session_date}")
            
            if not tumor_data:
                raise FileNotFoundError("No tumor mask files found in any session")
            
            # Sort tumor files by session date
            # Since we store YYYYMMDD as strings, simple string sorting works for chronological order
            tumor_data.sort(key=lambda x: x[0])
            
            # Extract just the file paths in chronological order
            tumor_files = [file_path for _, file_path in tumor_data]
            
            # Print the chronological sequence for verification
            print("\nTumor masks loaded in chronological order:")
            for date, file in tumor_data:
                formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                print(f"  {formatted_date}: {os.path.basename(file)}")
            
            # Create new window instance every time
            if self.animation_window:
                self.animation_window.cleanup()
                self.animation_window.deleteLater()
            
            # Pass the chronologically sorted files to the animation window
            self.animation_window = TumorAnimationWindow(self, tumor_files)
            self.animation_window.show()
            self.animation_window.raise_()
            self.animation_window.activateWindow()
            
        except Exception as e:
            print(f"Error launching animation window: {str(e)}")
            QMessageBox.warning(
                self,
                "Animation Error",
                f"Could not load tumor progression animation: {str(e)}"
            )

def main():
    if len(sys.argv) != 2:
        print("Usage: python render.py <path_to_subject_directory>")
        sys.exit(1)
    
    subject_path = os.path.abspath(sys.argv[1])
    if not os.path.exists(subject_path):
        print(f"Error: Directory not found: {subject_path}")
        sys.exit(1)
    
    app = QtWidgets.QApplication(sys.argv)
    try:
        window = MRIViewer(subject_path)
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error initializing viewer: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()