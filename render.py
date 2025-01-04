import vtk
import sys
import os
import glob
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QDesktopWidget, QMessageBox

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from slice_interactor import SliceInteractor, SlicePlanes
from volume_multimodal import renderPlaneVolume
from ui import MainWindowUI

class MRIViewer(MainWindowUI):
     def __init__(self, base_path):
        super().__init__()
        
        # Set up camera FIRST
        self.setup_camera()
        
        # Set up SlicePlanes SECOND
        self.SlicePlanes = SlicePlanes(self)
        
        # Set up file paths and load initial session
        self.setup_file_paths(base_path)
        
        # Initialize UI components (after we have files loaded)
        self.initializeUI()
        
        # Timer for rendering sync
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.render_all)
        self.timer.start(2)  # msec per frame
        
        self.show()
    
     def find_image_files(self, session_path):
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
        for modality in self.modalities:
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
        Looks for registered files with 'Lreg_' prefix.
        
        Args:
            base_path (str): Path to the base directory containing session folders
        """
        try:
            # Find all session directories and sort them
            self.session_dirs = []
            for item in os.listdir(base_path):
                if item.startswith('ses-'):
                    full_path = os.path.join(base_path, item)
                    if os.path.isdir(full_path):
                        self.session_dirs.append(item)
            
            if not self.session_dirs:
                raise ValueError(f"No session directories found in {base_path}")
            
            # Sort sessions chronologically
            self.session_dirs.sort()
            
            # Store base path and current session index
            self.base_path = base_path
            self.current_session_index = 0
            
            # Define the modalities we want to load
            self.modalities = ['t1', 'flair', 'swi_mag', 'swi_phase']
            
            # Load initial session
            self.load_session(self.current_session_index)
            
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
            found_files = self.find_image_files(full_session_path)
            
            # Store the files in order
            self.files = [found_files[mod] for mod in self.modalities]
            
            # Update UI elements
            self.update_session_display()
            
            # Update navigation buttons
            self.update_navigation_buttons()
            
            # Re-render the views
            self.render_modalities(self.files)
            
            # Set default view to axial
            self.axial_button.setChecked(True)
            self.change_slicing()
            
            # Reset camera to initial position
            self.reset_view()
            
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
          """Render all modalities"""
          try:
               # Set up the slice planes
               self.SlicePlanes = SlicePlanes(self)
               
               # Render each modality
               self.t1_window, self.t1_iren,self.t1_volume = renderPlaneVolume(
                    self, frame=self.t1_frame, layout=self.t1_layout, 
                    filename=filenames[0], modality='t1'
               )
               
               self.flair_window, self.flair_iren, self.flair_volume = renderPlaneVolume(
                    self, frame=self.flair_frame, layout=self.flair_layout, 
                    filename=filenames[1], modality='flair'
               )
               
               self.swi_window, self.swi_iren, self.swi_volume = renderPlaneVolume(
                    self, frame=self.swi_frame, layout=self.swi_layout, 
                    filename=filenames[2], modality='swi_mag'
               )
               
               self.phase_window, self.phase_iren, self.phase_volume = renderPlaneVolume(
                    self, frame=self.phase_frame, layout=self.phase_layout, 
                    filename=filenames[3], modality='swi_phase'
               )
               
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
        """Force rendering for camera sync"""
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
        """Update slice thickness"""
        thickness = self.thickness_slider.value()
        self.SlicePlanes.setSliceThickness(thickness)
      
     def update_stepsize(self):
        """Update slice thickness"""
        step_size = self.step_slider.value()
        self.SlicePlanes.setStepSize(step_size)

     def update_volume_lighting(self):
          for volume in [self.t1_volume, self.flair_volume, self.swi_volume, self.phase_volume]:
               volume_property =volume.GetProperty()
               if volume_property:
                    ambient  = self.ambient_slider.value()   / 100.0
                    diffuse  = self.diffuse_slider.value()   / 100.0
                    specular = self.specular_slider.value()  / 100.0
                    spec_pow = float(self.spec_power_slider.value())

                    volume_property.SetAmbient(ambient)
                    volume_property.SetDiffuse(diffuse)
                    volume_property.SetSpecular(specular)
                    volume_property.SetSpecularPower(spec_pow)
          self.render_all()

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