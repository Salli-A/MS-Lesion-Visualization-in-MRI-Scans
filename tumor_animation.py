import vtk
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from volume_multimodal import VolumePropertyManager

class TumorAnimationWindow(QMainWindow):
    def __init__(self, parent=None, tumor_files=None):
        super().__init__(parent)
        self.tumor_files = tumor_files or []
        self.current_frame = 0
        self.is_playing = False
        self.frame_delay = 500  # milliseconds between frames
        self.volumes = []
        self.mappers = []
        self.vtk_widget = None
        self.renderer = None
        self.window = None
        self.interactor = None
        self.current_volume = None
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        
        self.setupUI()
        self.initializeVTK()
        self.loadTumorData()
        
        # Connect destroyed signal for cleanup
        self.destroyed.connect(self.cleanup)

    def setupUI(self):
        """Create the animation window UI with controls."""
        self.setWindowTitle("Tumor Progression Animation")
        self.setMinimumSize(600, 500)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # VTK visualization frame
        self.vtk_frame = QFrame()
        self.vtk_frame.setMinimumHeight(400)
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
            QSlider::handle:horizontal:hover {
                background: #1984D8;
            }
        """)
        self.frame_slider.valueChanged.connect(self.on_slider_change)
        
        self.frame_label = QLabel("Frame: 0/0")
        self.frame_label.setStyleSheet("color: white; font-size: 11pt;")
        
        slider_layout.addWidget(self.frame_slider)
        slider_layout.addWidget(self.frame_label)
        
        # Playback controls
        playback_layout = QHBoxLayout()
        
        self.play_button = QPushButton("Play")
        self.play_button.setCheckable(True)
        self.play_button.clicked.connect(self.toggle_playback)
        
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
            QSlider::handle:horizontal:hover {
                background: #1984D8;
            }
        """)
        
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
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:checked {
                background-color: #0078D7;
            }
        """)
            
        playback_layout.addWidget(self.play_button)
        playback_layout.addWidget(self.speed_label)
        playback_layout.addWidget(self.speed_slider)
        playback_layout.addStretch()
        
        # Add controls to layout
        controls_layout.addLayout(slider_layout)
        controls_layout.addLayout(playback_layout)
        layout.addWidget(controls)

    def initializeVTK(self):
        """Initialize VTK pipeline with proper resource management."""
        if self.vtk_widget:
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
        
        # Initialize the interactor and start the event loop
        self.interactor.Initialize()
        self.interactor.Start()
        
        # Volume property manager for consistent visualization
        self.property_manager = VolumePropertyManager('tumor')

    def cleanup(self):
        """Properly clean up VTK resources."""
        if self.is_playing:
            self.toggle_playback(False)
            
        if self.renderer and self.current_volume:
            self.renderer.RemoveVolume(self.current_volume)
            
        # Clean up volumes and mappers
        for volume in self.volumes:
            if self.renderer:
                self.renderer.RemoveVolume(volume)
        
        self.volumes.clear()
        self.mappers.clear()
        
        # Clean up VTK widget and renderer
        if self.interactor:
            self.interactor.GetRenderWindow().Finalize()
            self.interactor.TerminateApp()
            
        if self.vtk_widget:
            self.vtk_widget.close()
            self.vtk_widget.deleteLater()
            
        self.vtk_widget = None
        self.renderer = None
        self.window = None
        self.interactor = None
        self.current_volume = None

    def closeEvent(self, event):
        """Handle window close event."""
        self.cleanup()
        event.accept()

    def loadTumorData(self):
        """Load and prepare tumor mask data for animation."""
        if not self.tumor_files:
            return
            
        # Clear existing volumes
        self.volumes.clear()
        self.mappers.clear()
        
        # Load each tumor mask
        for file in self.tumor_files:
            reader = vtk.vtkNIFTIImageReader()
            reader.SetFileName(file)
            reader.Update()
            
            # Create mapper
            mapper = vtk.vtkGPUVolumeRayCastMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
            
            # Create volume with enhanced visualization
            volume_property = self.property_manager.create_volume_property(
                slice_thickness=10,  # Default thickness
                optimal_range=(0, 1)  # Binary mask range
            )
            
            volume = vtk.vtkVolume()
            volume.SetMapper(mapper)
            volume.SetProperty(volume_property)
            
            self.volumes.append(volume)
            self.mappers.append(mapper)
        
        if self.volumes:
            # Configure slider
            self.frame_slider.setMaximum(len(self.volumes) - 1)
            self.frame_slider.setValue(0)
            self.frame_label.setText(f"Frame: 1/{len(self.volumes)}")
            
            # Show first frame
            self.show_frame(0)
            
            # Reset camera to show full volume
            bounds = self.volumes[0].GetBounds()
            self.camera.SetViewUp(0, 0, -1)
            self.camera.SetPosition(
                (bounds[1] - bounds[0])/2,
                bounds[3] + (bounds[3] - bounds[2]),
                (bounds[5] - bounds[4])/2
            )
            self.camera.SetFocalPoint(
                (bounds[1] - bounds[0])/2,
                (bounds[3] - bounds[2])/2,
                (bounds[5] - bounds[4])/2
            )
            self.renderer.ResetCamera()
            self.window.Render()

    def show_frame(self, frame_index):
        """Display the specified animation frame."""
        # Remove current volume
        if hasattr(self, 'current_volume'):
            self.renderer.RemoveVolume(self.current_volume)
        
        # Add new volume
        self.current_volume = self.volumes[frame_index]
        self.renderer.AddVolume(self.current_volume)
        self.current_frame = frame_index
        
        # Update label
        self.frame_label.setText(f"Frame: {frame_index + 1}/{len(self.volumes)}")
        
        # Render
        self.window.Render()

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
        """Advance to next frame in animation."""
        next_frame = (self.current_frame + 1) % len(self.volumes)
        self.frame_slider.setValue(next_frame)
        if next_frame == 0 and self.is_playing:
            self.play_button.click()  # Stop at end of sequence