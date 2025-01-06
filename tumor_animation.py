import vtk
import numpy as np
from vtk.util import numpy_support
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFrame, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class TumorAnimationWindow(QMainWindow):
    def __init__(self, parent=None, tumor_files=None):
        super().__init__(parent)
        self.tumor_files = tumor_files or []
        self.current_frame = 0
        self.is_playing = False
        self.frame_delay = 500  # milliseconds between frames
        
        # Store the processed volumes
        self.stable_volumes = []
        self.growth_volumes = []
        self.reduction_volumes = []
        
        # Track visibility states
        self.show_stable = True
        self.show_growth = True
        self.show_reduction = True
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        
        self.setupUI()
        self.initializeVTK()
        self.loadTumorData()
        
        # Connect destroyed signal for cleanup
        self.destroyed.connect(self.cleanup)

    def setupUI(self):
        """Create the animation window UI with enhanced controls."""
        self.setWindowTitle("Tumor Progression Analysis")
        self.setMinimumSize(800, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # VTK visualization frame
        self.vtk_frame = QFrame()
        self.vtk_frame.setMinimumHeight(500)
        self.vtk_frame.setStyleSheet("""
            QFrame {
                background-color: #000000;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
        self.vtk_layout = QVBoxLayout(self.vtk_frame)
        self.vtk_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.vtk_frame)
        
        # Controls container
        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.setSpacing(10)
        
        # Visibility controls
        visibility_layout = QHBoxLayout()
        
        # Create checkboxes for each type of region
        self.stable_check = QCheckBox("Stable Regions")
        self.stable_check.setChecked(True)
        self.stable_check.setStyleSheet("""
            QCheckBox {
                color: #FF80FF;  /* Magenta */
                font-size: 11pt;
            }
        """)
        self.stable_check.toggled.connect(lambda checked: self.toggle_visibility('stable', checked))
        
        self.growth_check = QCheckBox("Growth")
        self.growth_check.setChecked(True)
        self.growth_check.setStyleSheet("""
            QCheckBox {
                color: #FF4040;  /* Red */
                font-size: 11pt;
            }
        """)
        self.growth_check.toggled.connect(lambda checked: self.toggle_visibility('growth', checked))
        
        self.reduction_check = QCheckBox("Reduction")
        self.reduction_check.setChecked(True)
        self.reduction_check.setStyleSheet("""
            QCheckBox {
                color: #4080FF;  /* Blue */
                font-size: 11pt;
            }
        """)
        self.reduction_check.toggled.connect(lambda checked: self.toggle_visibility('reduction', checked))
        
        visibility_layout.addWidget(self.stable_check)
        visibility_layout.addWidget(self.growth_check)
        visibility_layout.addWidget(self.reduction_check)
        visibility_layout.addStretch()
        
        # Timeline slider
        slider_layout = QHBoxLayout()
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #404040;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0078D7;
                border: none;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
        self.frame_slider.valueChanged.connect(self.on_slider_change)
        
        self.frame_label = QLabel("Timepoint: 0/0")
        self.frame_label.setStyleSheet("color: white; font-size: 11pt;")
        
        slider_layout.addWidget(self.frame_slider)
        slider_layout.addWidget(self.frame_label)
        
        # Playback controls
        playback_layout = QHBoxLayout()
        
        self.play_button = QPushButton("Play")
        self.play_button.setCheckable(True)
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                border: none;
                padding: 8px;
                font-size: 11pt;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:checked {
                background-color: #0078D7;
            }
        """)
        
        self.speed_label = QLabel("Speed:")
        self.speed_label.setStyleSheet("color: white; font-size: 11pt;")
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(20)
        self.speed_slider.setValue(10)
        self.speed_slider.valueChanged.connect(self.update_speed)
        self.speed_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #404040;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0078D7;
                border: none;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
        
        playback_layout.addWidget(self.play_button)
        playback_layout.addWidget(self.speed_label)
        playback_layout.addWidget(self.speed_slider)
        playback_layout.addStretch()
        
        # Add all controls to layout
        controls_layout.addLayout(visibility_layout)
        controls_layout.addLayout(slider_layout)
        controls_layout.addLayout(playback_layout)
        layout.addWidget(controls)

    def initializeVTK(self):
        """Initialize VTK pipeline with proper resource management."""
        if hasattr(self, 'vtk_widget'):
            self.cleanup()
            
        # Create VTK widget
        self.vtk_widget = QVTKRenderWindowInteractor(self.vtk_frame)
        self.vtk_layout.addWidget(self.vtk_widget)
        
        # Set up renderer
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.0, 0.0, 0.0)
        
        self.window = self.vtk_widget.GetRenderWindow()
        self.window.AddRenderer(self.renderer)
        
        # Set up camera
        self.camera = vtk.vtkCamera()
        self.renderer.SetActiveCamera(self.camera)
        
        # Initialize interactor
        self.interactor = self.window.GetInteractor()
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)
        
        self.interactor.Initialize()
        self.interactor.Start()

    def create_volume_property(self, color, opacity=0.6):
        """Create a volume property with specified color and opacity."""
        volume_property = vtk.vtkVolumeProperty()
        volume_property.ShadeOn()
        
        # Create color transfer function
        color_tf = vtk.vtkColorTransferFunction()
        color_tf.AddRGBPoint(0, 0, 0, 0)  # Transparent for 0 values
        color_tf.AddRGBPoint(1, *color)   # Specified color for mask values
        
        # Create opacity transfer function
        opacity_tf = vtk.vtkPiecewiseFunction()
        opacity_tf.AddPoint(0, 0)         # Transparent for 0 values
        opacity_tf.AddPoint(1, opacity)    # Semi-transparent for mask values
        
        volume_property.SetColor(color_tf)
        volume_property.SetScalarOpacity(opacity_tf)
        volume_property.SetInterpolationTypeToLinear()
        
        # Enhanced lighting for better depth perception
        volume_property.SetAmbient(0.4)
        volume_property.SetDiffuse(0.6)
        volume_property.SetSpecular(0.2)
        volume_property.SetSpecularPower(10)
        
        return volume_property

    def compute_difference_volumes(self):
        """
        Compute difference volumes between consecutive timepoints.
        Creates three sets of volumes: stable regions, growth, and reduction.
        """
        self.stable_volumes = []
        self.growth_volumes = []
        self.reduction_volumes = []
        
        # Load first timepoint to get dimensions and initial data
        prev_reader = vtk.vtkNIFTIImageReader()
        prev_reader.SetFileName(self.tumor_files[0])
        prev_reader.Update()
        
        # Store the image dimensions for reuse
        self.image_dims = prev_reader.GetOutput().GetDimensions()
        
        # Get the data and reshape it to match image dimensions
        prev_data = numpy_support.vtk_to_numpy(
            prev_reader.GetOutput().GetPointData().GetScalars()
        ).reshape(self.image_dims)
        
        # Store first timepoint as initial stable volume
        self.stable_volumes.append(self.create_volume_from_array(prev_data))
        self.growth_volumes.append(None)  # No growth for first timepoint
        self.reduction_volumes.append(None)  # No reduction for first timepoint
        
        # Process subsequent timepoints
        for i in range(1, len(self.tumor_files)):
            curr_reader = vtk.vtkNIFTIImageReader()
            curr_reader.SetFileName(self.tumor_files[i])
            curr_reader.Update()
            
            # Reshape the current data to match dimensions
            curr_data = numpy_support.vtk_to_numpy(
                curr_reader.GetOutput().GetPointData().GetScalars()
            ).reshape(self.image_dims)
            
            # Compute differences
            stable = np.logical_and(prev_data > 0, curr_data > 0)
            growth = np.logical_and(curr_data > 0, prev_data == 0)
            reduction = np.logical_and(prev_data > 0, curr_data == 0)
            
            # Create volumes
            self.stable_volumes.append(self.create_volume_from_array(stable))
            self.growth_volumes.append(self.create_volume_from_array(growth))
            self.reduction_volumes.append(self.create_volume_from_array(reduction))
            
            prev_data = curr_data
            
        # Configure frame slider
        self.frame_slider.setMaximum(len(self.tumor_files) - 1)
        self.frame_slider.setValue(0)
        self.frame_label.setText(f"Timepoint: 1/{len(self.tumor_files)}")

    def create_volume_from_array(self, numpy_array):
        """
        Create a VTK volume from a numpy array.
        
        Args:
            numpy_array: 3D numpy array with the same dimensions as the original image
            
        Returns:
            vtk.vtkVolume: Volume ready for rendering
        """
        if numpy_array is None:
            return None
            
        # Create VTK array from flattened numpy array
        vtk_data = numpy_support.numpy_to_vtk(
            numpy_array.ravel().astype(np.float32),
            deep=True,
            array_type=vtk.VTK_FLOAT
        )
        
        # Create image data with proper dimensions
        img = vtk.vtkImageData()
        img.SetDimensions(self.image_dims)  # Use stored dimensions
        img.GetPointData().SetScalars(vtk_data)
        
        # Set proper spacing and origin
        img.SetSpacing(1.0, 1.0, 1.0)  # Use actual spacing if available from NIFTI
        img.SetOrigin(0.0, 0.0, 0.0)   # Use actual origin if available from NIFTI
        
        # Create mapper
        mapper = vtk.vtkGPUVolumeRayCastMapper()
        mapper.SetInputData(img)
        
        # Create volume
        volume = vtk.vtkVolume()
        volume.SetMapper(mapper)
        
        return volume

    def loadTumorData(self):
        """Load and process tumor mask data for animation."""
        if not self.tumor_files:
            return
            
        # Compute difference volumes
        self.compute_difference_volumes()
        
        # Show first timepoint
        self.show_frame(0)
        
        # Reset camera to show full volume
        self.reset_camera()
        
    def reset_camera(self):
        """Reset camera to show full volume."""
        if self.stable_volumes:
            volume = self.stable_volumes[0]
            bounds = volume.GetBounds()
            
            # Set up camera for optimal viewing
            self.camera.SetViewUp(0, 0, -1)
            center = [
                (bounds[1] + bounds[0])/2,
                (bounds[3] + bounds[2])/2,
                (bounds[5] + bounds[4])/2
            ]
            position = [
                center[0],
                bounds[3] + (bounds[3] - bounds[2]),
                center[2]
            ]
            
            self.camera.SetPosition(position)
            self.camera.SetFocalPoint(center)
            self.renderer.ResetCamera()
            self.window.Render()

    def show_frame(self, frame_index):
        """Display the specified animation frame with difference visualization."""
        # Remove current volumes
        self.renderer.RemoveAllViewProps()
        
        # Add volumes for current frame if they exist and are visible
        if self.stable_volumes[frame_index] and self.show_stable:
            volume = self.stable_volumes[frame_index]
            volume.SetProperty(self.create_volume_property((1.0, 0.5, 1.0)))  # Magenta
            self.renderer.AddVolume(volume)
            
        if frame_index > 0:  # Show growth/reduction only for frames after first
            if self.growth_volumes[frame_index] and self.show_growth:
                volume = self.growth_volumes[frame_index]
                volume.SetProperty(self.create_volume_property((1.0, 0.25, 0.25)))  # Red
                self.renderer.AddVolume(volume)
                
            if self.reduction_volumes[frame_index] and self.show_reduction:
                volume = self.reduction_volumes[frame_index]
                volume.SetProperty(self.create_volume_property((0.25, 0.5, 1.0)))  # Blue
                self.renderer.AddVolume(volume)
        
        self.current_frame = frame_index
        self.frame_label.setText(f"Timepoint: {frame_index + 1}/{len(self.tumor_files)}")
        self.window.Render()

    def toggle_visibility(self, region_type, visible):
        """Toggle visibility of specific region type."""
        if region_type == 'stable':
            self.show_stable = visible
        elif region_type == 'growth':
            self.show_growth = visible
        elif region_type == 'reduction':
            self.show_reduction = visible
            
        # Update current frame to reflect visibility changes
        self.show_frame(self.current_frame)

    def on_slider_change(self, value):
        """Handle manual frame selection."""
        self.show_frame(value)

    def toggle_playback(self, checked):
        """Start or stop animation playback."""
        self.is_playing = checked
        if checked:
            self.play_button.setText("Pause")
            self.timer.start(self.frame_delay)
        else:
            self.play_button.setText("Play")
            self.timer.stop()

    def update_speed(self, value):
        """Update animation playback speed."""
        self.frame_delay = 1000 // value  # Convert slider value to milliseconds
        if self.is_playing:
            self.timer.setInterval(self.frame_delay)

    def next_frame(self):
        """Advance to next frame in animation sequence."""
        next_frame = (self.current_frame + 1) % len(self.tumor_files)
        self.frame_slider.setValue(next_frame)
        
        # Stop at end of sequence
        if next_frame == 0 and self.is_playing:
            self.play_button.click()

    def cleanup(self):
        """Properly clean up VTK resources."""
        if self.is_playing:
            self.toggle_playback(False)
            
        # Clean up all volumes
        self.renderer.RemoveAllViewProps()
        
        self.stable_volumes.clear()
        self.growth_volumes.clear()
        self.reduction_volumes.clear()
        
        # Clean up VTK widget and renderer
        if hasattr(self, 'interactor'):
            self.interactor.GetRenderWindow().Finalize()
            self.interactor.TerminateApp()
            
        if hasattr(self, 'vtk_widget'):
            self.vtk_widget.close()
            self.vtk_widget.deleteLater()
            
        self.vtk_widget = None
        self.renderer = None
        self.window = None
        self.interactor = None

    def closeEvent(self, event):
        """Handle window close event."""
        self.cleanup()
        event.accept()