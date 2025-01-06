from functools import partial
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QGroupBox, QRadioButton, QPushButton, QSlider,
    QCheckBox, QPlainTextEdit, QFrame, QSizePolicy, QScrollArea,
    QApplication, QToolButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor

class MainWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.shader_sliders = {}
        self.control_panel_visible = True
        self.shading_visible = False
        self.setupUi()

    def setupUi(self):
        # Set dark theme and configure window
        self.setup_dark_theme()
        self.setWindowTitle("MRI Viewer")
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumSize(int(screen.width() * 0.7), int(screen.height() * 0.7))
        
        # Set default font
        self.setFont(QFont("Segoe UI", 10))
        
        # Main layout setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create main panels
        self.createControlPanel()
        self.createRenderPanel()

    def setup_dark_theme(self):
        """Configure dark theme with improved contrast"""
        palette = QPalette()
        background = QColor("#1E1E1E")
        alternate_background = QColor("#2D2D2D")
        highlight = QColor("#0078D7")
        text = QColor("#FFFFFF")
        disabled_text = QColor("#808080")
        
        # Set color scheme
        palette.setColor(QPalette.Window, background)
        palette.setColor(QPalette.WindowText, text)
        palette.setColor(QPalette.Base, alternate_background)
        palette.setColor(QPalette.AlternateBase, background)
        palette.setColor(QPalette.ToolTipBase, text)
        palette.setColor(QPalette.ToolTipText, background)
        palette.setColor(QPalette.Text, text)
        palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
        palette.setColor(QPalette.Button, alternate_background)
        palette.setColor(QPalette.ButtonText, text)
        palette.setColor(QPalette.Highlight, highlight)
        palette.setColor(QPalette.HighlightedText, text)
        self.setPalette(palette)

    def create_group_box(self, title):
        """Create a styled group box"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                color: #FFFFFF;
                border: 2px solid #404040;
                border-radius: 6px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
        """)
        return group


    def createControlPanel(self):
        """Create collapsible control panel with scrollable content"""
        # Container for control panel and collapse button
        control_container = QWidget()
        control_container.setMaximumWidth(400)
        container_layout = QHBoxLayout(control_container)
        container_layout.setSpacing(0)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Collapse button
        self.collapse_button = QToolButton()
        self.collapse_button.setText("◀")
        self.collapse_button.setCheckable(True)
        self.collapse_button.setFixedSize(20, 60)
        self.collapse_button.setStyleSheet("""
            QToolButton {
                background-color: #404040;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QToolButton:checked {
                background-color: #0078D7;
            }
        """)
        self.collapse_button.clicked.connect(self.toggleControlPanel)

        # Scrollable control panel
        self.control_scroll = QScrollArea()
        self.control_scroll.setWidgetResizable(True)
        self.control_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.control_scroll.setStyleSheet("QScrollArea { border: none; }")

        # Control panel content
        control_panel = QWidget()
        control_panel.setMinimumWidth(300)
        layout = QVBoxLayout(control_panel)
        layout.setSpacing(15)

        # Add all control groups
        self.addCaseInfo(layout)
        self.addViewSettings(layout)
        self.addThicknessControls(layout)
        self.addStepControls(layout)
        self.addMarkScan(layout)
        self.addMaskControls(layout)

        # Add stretch at the end
        layout.addStretch()

        # Set up control panel hierarchy
        self.control_scroll.setWidget(control_panel)
        container_layout.addWidget(self.collapse_button)
        container_layout.addWidget(self.control_scroll)
        self.main_layout.addWidget(control_container)

    def toggleControlPanel(self, checked):
        """Toggle control panel visibility"""
        if checked:
            self.control_scroll.setMaximumWidth(0)
            self.collapse_button.setText("▶")
        else:
            self.control_scroll.setMaximumWidth(400)
            self.collapse_button.setText("◀")

    def createRenderPanel(self):
        """Create render panel with maximizable viewports"""
        render_panel = QWidget()
        render_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vlayout = QVBoxLayout(render_panel)
        vlayout.setSpacing(10)
        vlayout.setContentsMargins(0, 0, 0, 0)

        # Create viewport grid
        view_grid = QGridLayout()
        view_grid.setSpacing(10)

        # Define viewports
        viewports = [
            ("t1", "T1-Weighted", 0, 0),
            ("swi", "SWI Magnitude", 0, 1),
            ("flair", "FLAIR", 1, 0),
            ("phase", "SWI Phase", 1, 1)
        ]

        # Create each viewport
        for name, title, row, col in viewports:
            group = self.createViewport(name, title)
            view_grid.addWidget(group, row, col)

        # Set uniform grid stretching
        for i in range(2):
            view_grid.setColumnStretch(i, 1)
            view_grid.setRowStretch(i, 1)

        # Create collapsible shading controls
        self.shading_toggle = QPushButton("Show Shading Controls")
        self.shading_toggle.setCheckable(True)
        self.shading_toggle.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                border: none;
                padding: 8px;
                font-size: 11pt;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #0078D7;
            }
        """)

        # Create shading grid
        self.shading_grid = QGridLayout()
        self.shading_grid.setSpacing(10)
        self.shading_grid.addWidget(self.createModalityShaderPanel("t1"), 0, 0)
        self.shading_grid.addWidget(self.createModalityShaderPanel("swi"), 0, 1)
        self.shading_grid.addWidget(self.createModalityShaderPanel("flair"), 1, 0)
        self.shading_grid.addWidget(self.createModalityShaderPanel("phase"), 1, 1)

        # Hide shading controls initially
        self.shading_container = QWidget()
        self.shading_container.setLayout(self.shading_grid)
        self.shading_container.setVisible(False)
        self.shading_toggle.clicked.connect(self.shading_container.setVisible)

        # Add all components to render panel
        vlayout.addLayout(view_grid)
        vlayout.addWidget(self.shading_toggle)
        vlayout.addWidget(self.shading_container)
        self.main_layout.addWidget(render_panel, stretch=1)

    def createViewport(self, name, title):
        """Create a viewport with maximize button"""
        group = QGroupBox(title)
        group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        group.setStyleSheet("""
            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                color: #FFFFFF;
                border: 2px solid #404040;
                border-radius: 6px;
                padding: 10px;
                background-color: #1E1E1E;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }
        """)

        # Create layout for viewport
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(5, 15, 5, 5)

        # Add maximize button
        maximize_btn = QToolButton()
        maximize_btn.setText("⛶")
        maximize_btn.setFixedSize(24, 24)
        maximize_btn.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                color: white;
                border: none;
            }
            QToolButton:hover {
                background-color: #404040;
            }
        """)
        
        # Create header layout
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        header_layout.addWidget(maximize_btn)
        group_layout.addLayout(header_layout)

        # Create frame for rendering
        frame = QFrame()
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame.setStyleSheet("""
            QFrame {
                background-color: #000000;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)

        # Store references
        setattr(self, f"{name}_frame", frame)
        setattr(self, f"{name}_layout", frame_layout)
        
        group_layout.addWidget(frame)
        return group
    
    def addCaseInfo(self, layout):
        """Create the case information section of the control panel."""
        case_info_group = self.create_group_box("Case Information")
        case_info_layout = QVBoxLayout(case_info_group)
        
        # Subject ID section
        subject_layout = QHBoxLayout()
        subject_label = QLabel("Subject:")
        subject_label.setStyleSheet("font-weight: bold; font-size: 11pt; color: #FFFFFF;")
        self.subject_id = QLabel()
        self.subject_id.setStyleSheet("font-size: 11pt; color: #FFFFFF;")
        subject_layout.addWidget(subject_label)
        subject_layout.addWidget(self.subject_id)
        subject_layout.addStretch()
        
        # Session navigation section
        session_layout = QHBoxLayout()
        
        # Navigation buttons
        self.prev_button = QPushButton("←")
        self.next_button = QPushButton("→")
        for button in [self.prev_button, self.next_button]:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #404040;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    font-size: 14pt;
                    border-radius: 4px;
                    min-width: 30px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #303030;
                }
                QPushButton:disabled {
                    background-color: #2D2D2D;
                    color: #808080;
                }
            """)

        # Session label
        session_label = QLabel("Session:")
        session_label.setStyleSheet("font-weight: bold; font-size: 11pt; color: #FFFFFF;")
        self.session_id = QLabel()
        self.session_id.setStyleSheet("font-size: 11pt; color: #FFFFFF;")

        session_layout.addWidget(self.prev_button)
        session_layout.addWidget(session_label)
        session_layout.addWidget(self.session_id)
        session_layout.addWidget(self.next_button)
        session_layout.addStretch()

        case_info_layout.addLayout(subject_layout)
        case_info_layout.addLayout(session_layout)
        layout.addWidget(case_info_group)

    def addViewSettings(self, layout):
        """Create the view settings section of the control panel."""
        view_group = self.create_group_box("View Settings")
        view_layout = QVBoxLayout(view_group)
        
        radio_style = """
            QRadioButton {
                font-size: 11pt;
                color: #FFFFFF;
                padding: 5px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:unchecked {
                background-color: #404040;
                border: 2px solid #606060;
                border-radius: 9px;
            }
            QRadioButton::indicator:checked {
                background-color: #0078D7;
                border: 2px solid #0078D7;
                border-radius: 9px;
            }
            QRadioButton::indicator:hover {
                border-color: #808080;
            }
        """
        
        for text in ["Axial", "Coronal", "Sagittal"]:
            radio = QRadioButton(text)
            radio.setStyleSheet(radio_style)
            setattr(self, f"{text.lower()}_button", radio)
            view_layout.addWidget(radio)
        
        self.reset_button = QPushButton("Reset View")
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                padding: 8px;
                font-size: 11pt;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1984D8;
            }
            QPushButton:pressed {
                background-color: #006CC1;
            }
        """)
        view_layout.addWidget(self.reset_button)
        layout.addWidget(view_group)

    def addThicknessControls(self, layout):
        """Create the slice thickness control section."""
        thickness_group = self.create_group_box("Slice Thickness")
        thickness_layout = QVBoxLayout(thickness_group)
        
        thickness_controls = QHBoxLayout()
        
        self.thickness_slider = QSlider(Qt.Horizontal)
        self.thickness_slider.setStyleSheet("""
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
        self.thickness_slider.setRange(1, 30)
        self.thickness_slider.setValue(10)
        
        self.thickness_value = QLabel("10")
        self.thickness_value.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 11pt;
                min-width: 30px;
                padding: 0 5px;
            }
        """)
        
        thickness_controls.addWidget(self.thickness_slider)
        thickness_controls.addWidget(self.thickness_value)
        thickness_layout.addLayout(thickness_controls)
        layout.addWidget(thickness_group)

        # Connect the value change signal
        self.thickness_slider.valueChanged.connect(
            lambda value: self.thickness_value.setText(str(value))
        )

    def addStepControls(self, layout):
        """Create the step size control section."""
        step_group = self.create_group_box("Step size")
        step_layout = QVBoxLayout(step_group)
        
        step_controls = QHBoxLayout()
        
        self.step_slider = QSlider(Qt.Horizontal)
        self.step_slider.setStyleSheet("""
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
        self.step_slider.setRange(1, 15)
        self.step_slider.setValue(5)
        
        self.step_value = QLabel("5")
        self.step_value.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 11pt;
                min-width: 30px;
                padding: 0 5px;
            }
        """)
        
        step_controls.addWidget(self.step_slider)
        step_controls.addWidget(self.step_value)
        step_layout.addLayout(step_controls)
        layout.addWidget(step_group)

        # Connect the value change signal
        self.step_slider.valueChanged.connect(
            lambda value: self.step_value.setText(str(value))
        )

    def addMarkScan(self, layout):
        """Create the scan marking section."""
        mark_group = self.create_group_box("Mark Scan")
        mark_layout = QVBoxLayout(mark_group)
        
        checkbox_style = """
            QCheckBox {
                font-size: 11pt;
                color: #FFFFFF;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #404040;
                border: 2px solid #606060;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #0078D7;
                border-color: #0078D7;
                image: url(checkmark.png);
            }
            QCheckBox::indicator:hover {
                border-color: #808080;
            }
        """
        
        self.prl_checkbox = QCheckBox("Perivascular Rim Lesions (PRL)")
        self.cvs_checkbox = QCheckBox("Central Vein Signs (CVS)")
        self.quality_checkbox = QCheckBox("Bad quality MRI")
        
        for checkbox in [self.prl_checkbox, self.cvs_checkbox, self.quality_checkbox]:
            checkbox.setStyleSheet(checkbox_style)
            mark_layout.addWidget(checkbox)
        
        self.notes_field = QPlainTextEdit()
        self.notes_field.setStyleSheet("""
            QPlainTextEdit {
                background-color: #404040;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 11pt;
            }
        """)
        self.notes_field.setPlaceholderText("Add notes here...")
        self.notes_field.setMaximumHeight(100)
        mark_layout.addWidget(self.notes_field)
        
        self.submit_button = QPushButton("Submit")
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                padding: 8px;
                font-size: 11pt;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1984D8;
            }
            QPushButton:pressed {
                background-color: #006CC1;
            }
        """)
        mark_layout.addWidget(self.submit_button)
        layout.addWidget(mark_group)

    def addMaskControls(self, layout):
        """Create the mask controls section."""
        mask_group = self.create_group_box("Mask Controls")
        mask_layout = QVBoxLayout(mask_group)

        # Lesion Mask Controls
        lesion_controls = QVBoxLayout()
        lesion_header = QHBoxLayout()
        
        self.lesion_toggle = QPushButton("Lesion Mask")
        self.lesion_toggle.setCheckable(True)
        self.lesion_toggle.setChecked(True)
        self.lesion_toggle.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                border: none;
                padding: 8px;
                font-size: 11pt;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #0078D7;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:checked:hover {
                background-color: #1984D8;
            }
        """)
        lesion_header.addWidget(self.lesion_toggle)

        lesion_slider_layout = QHBoxLayout()
        self.lesion_opacity_slider = QSlider(Qt.Horizontal)
        self.lesion_opacity_slider.setStyleSheet("""
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
        self.lesion_opacity_slider.setRange(0, 100)
        self.lesion_opacity_slider.setValue(40)  # Default 0.4 opacity * 100
        
        self.lesion_opacity_value = QLabel("0.4")
        self.lesion_opacity_value.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 11pt;
                min-width: 30px;
                padding: 0 5px;
            }
        """)
        
        lesion_slider_layout.addWidget(QLabel("Opacity:"))
        lesion_slider_layout.addWidget(self.lesion_opacity_slider)
        lesion_slider_layout.addWidget(self.lesion_opacity_value)
        
        lesion_controls.addLayout(lesion_header)
        lesion_controls.addLayout(lesion_slider_layout)
        
        # PRL Mask Controls
        prl_controls = QVBoxLayout()
        prl_header = QHBoxLayout()
        
        self.prl_toggle = QPushButton("PRL Mask")
        self.prl_toggle.setCheckable(True)
        self.prl_toggle.setChecked(True)
        self.prl_toggle.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                border: none;
                padding: 8px;
                font-size: 11pt;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #0078D7;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:checked:hover {
                background-color: #1984D8;
            }
        """)
        prl_header.addWidget(self.prl_toggle)

        prl_slider_layout = QHBoxLayout()
        self.prl_opacity_slider = QSlider(Qt.Horizontal)
        self.prl_opacity_slider.setStyleSheet("""
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
        self.prl_opacity_slider.setRange(0, 100)
        self.prl_opacity_slider.setValue(40)  # Default 0.4 opacity * 100
        
        self.prl_opacity_value = QLabel("0.4")
        self.prl_opacity_value.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 11pt;
                min-width: 30px;
                padding: 0 5px;
            }
        """)
        
        prl_slider_layout.addWidget(QLabel("Opacity:"))
        prl_slider_layout.addWidget(self.prl_opacity_slider)
        prl_slider_layout.addWidget(self.prl_opacity_value)
        
        prl_controls.addLayout(prl_header)
        prl_controls.addLayout(prl_slider_layout)

        # Add spacings between controls
        mask_layout.addSpacing(10)
        
        # Add both control sets to the mask layout
        mask_layout.addLayout(lesion_controls)
        mask_layout.addSpacing(15)  # Add space between lesion and PRL controls
        mask_layout.addLayout(prl_controls)
        mask_layout.addSpacing(10)

        # Connect signals for opacity sliders
        self.lesion_opacity_slider.valueChanged.connect(
            lambda value: self.lesion_opacity_value.setText(f"{value/100:.1f}")
        )
        self.prl_opacity_slider.valueChanged.connect(
            lambda value: self.prl_opacity_value.setText(f"{value/100:.1f}")
        )
        
        # Add the mask group to the main layout
        layout.addWidget(mask_group)

        # Store references for external access if needed
        self.mask_controls = {
            'lesion': {
                'toggle': self.lesion_toggle,
                'opacity_slider': self.lesion_opacity_slider,
                'opacity_label': self.lesion_opacity_value
            },
            'prl': {
                'toggle': self.prl_toggle,
                'opacity_slider': self.prl_opacity_slider,
                'opacity_label': self.prl_opacity_value
            }
        }
        
    def createModalityShaderPanel(self, modality_name):
        """
        Create a shader control panel for a specific modality with ambient, diffuse,
        specular, and specular power controls.
        
        Args:
            modality_name (str): Name of the modality (t1, swi, flair, phase)
        
        Returns:
            QGroupBox: Grouped shader controls for the modality
        """
        group_box = self.create_group_box(f"{modality_name.upper()} Lighting")
        layout = QVBoxLayout(group_box)
        layout.setSpacing(8)

        # Initialize storage for this modality's sliders
        self.shader_sliders[modality_name] = {}

        def create_styled_slider():
            """Create a consistently styled slider for shader controls"""
            slider = QSlider(Qt.Horizontal)
            slider.setStyleSheet("""
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
            return slider

        # Configure shader parameters
        shader_params = [
            ("Ambient", "ambient", 40),     # Default 0.40
            ("Diffuse", "diffuse", 60),     # Default 0.60
            ("Specular", "specular", 20),   # Default 0.20
            ("Spec. Power", "spec_power", 10)  # Default 10
        ]

        # Create controls for each shader parameter
        for label_text, param_name, default_value in shader_params:
            param_layout = QHBoxLayout()
            
            # Create and style label
            label = QLabel(f"{label_text}:")
            label.setStyleSheet("color: white; font-size: 11pt;")
            
            # Create and configure slider
            slider = create_styled_slider()
            
            # Set appropriate range based on parameter
            if param_name == "spec_power":
                slider.setRange(1, 50)
            else:
                slider.setRange(0, 100)
            
            slider.setValue(default_value)
            
            # Add to layout
            param_layout.addWidget(label)
            param_layout.addWidget(slider)
            layout.addLayout(param_layout)
            
            # Store slider reference
            self.shader_sliders[modality_name][param_name] = slider

        # Create reset button with consistent styling
        reset_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                font-size: 11pt;
                border: 1px solid #707070;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        reset_layout.addStretch()
        reset_layout.addWidget(reset_btn)
        layout.addLayout(reset_layout)

        # Store reset button reference
        self.shader_sliders[modality_name]["reset_btn"] = reset_btn

        # Connect all signals for this modality
        for param_name in ["ambient", "diffuse", "specular", "spec_power"]:
            slider = self.shader_sliders[modality_name][param_name]
            slider.valueChanged.connect(
                partial(self.update_volume_lighting, modality_name)
            )
        
        reset_btn.clicked.connect(
            partial(self.reset_shading, modality_name)
        )

        return group_box