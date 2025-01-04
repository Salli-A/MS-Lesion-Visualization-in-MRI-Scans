from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QGroupBox, QRadioButton, QPushButton, QSlider,
    QCheckBox, QPlainTextEdit, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor

class MainWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        # Set dark theme color palette
        self.setup_dark_theme()
        
        # Main window configuration
        self.setWindowTitle("MRI Viewer")
        self.setMinimumSize(1400, 900)
        
        # Set default font
        default_font = QFont("Segoe UI", 10)
        self.setFont(default_font)
        
        # Central widget setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create panels
        self.createControlPanel()
        self.createRenderPanel()

    def setup_dark_theme(self):
        """Configure dark theme with improved contrast"""
        palette = QPalette()
        
        # Background colors
        background = QColor("#1E1E1E")  # Slightly lighter than pure black
        alternate_background = QColor("#2D2D2D")  # Even lighter for controls
        highlight = QColor("#0078D7")  # Windows blue for selection
        
        # Text colors
        text = QColor("#FFFFFF")  # White text
        disabled_text = QColor("#808080")  # Gray for disabled text
        
        # Set colors for various UI elements
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
        """Create the left control panel with improved styling"""
        control_panel = QWidget()
        control_panel.setFixedWidth(300)
        layout = QVBoxLayout(control_panel)
        layout.setSpacing(15)
        
        # Case Information
        case_info_group = self.create_group_box("Case Information")
        case_info_layout = QVBoxLayout(case_info_group)
        
        # Subject ID
        subject_layout = QHBoxLayout()
        subject_label = QLabel("Subject:")
        subject_label.setStyleSheet("font-weight: bold; font-size: 11pt; color: #FFFFFF;")
        self.subject_id = QLabel()
        self.subject_id.setStyleSheet("font-size: 11pt; color: #FFFFFF;")
        subject_layout.addWidget(subject_label)
        subject_layout.addWidget(self.subject_id)
        subject_layout.addStretch()
        
        # Session ID and Navigation
        session_layout = QHBoxLayout()

        # Previous button
        self.prev_button = QPushButton("←")
        self.prev_button.setStyleSheet("""
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

        # Next button
        self.next_button = QPushButton("→")
        self.next_button.setStyleSheet("""
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

        session_layout.addWidget(self.prev_button)
        session_layout.addWidget(session_label)
        session_layout.addWidget(self.session_id)
        session_layout.addWidget(self.next_button)
        session_layout.addStretch()

        case_info_layout.addLayout(subject_layout)
        case_info_layout.addLayout(session_layout)
        layout.addWidget(case_info_group)
        
        # View Settings
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
        
        # Slice Thickness
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

        
        # Step size
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
        
        # Mark Scan
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
        
        # Controls Help
        help_group = self.create_group_box("Controls")
        help_layout = QVBoxLayout(help_group)
        help_text = QLabel("""
            <p><b>Scroll:</b> Change slice</p>
            <p><b>Shift + Scroll:</b> Zoom</p>
            <p><b>Left mouse:</b> Rotate</p>
            <p><b>Middle mouse:</b> Pan</p>
        """)
        help_text.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 11pt;
                line-height: 1.5;
            }
        """)
        help_layout.addWidget(help_text)
        layout.addWidget(help_group)
        
        layout.addStretch()
        self.main_layout.addWidget(control_panel)

    def createRenderPanel(self):
        """Create the right panel with render views"""
        render_panel = QWidget()
        render_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        grid_layout = QGridLayout(render_panel)
        grid_layout.setSpacing(10)
        
        viewports = [
            ("t1", "T1-Weighted", 0, 0),
            ("swi", "SWI Magnitude", 0, 1),
            ("flair", "FLAIR", 1, 0),
            ("phase", "SWI Phase", 1, 1)
        ]
        
        for name, title, row, col in viewports:
            group = QGroupBox(title)
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
            
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(5, 15, 5, 5)
            
            frame = QFrame(group)
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
            
            setattr(self, f"{name}_frame", frame)
            setattr(self, f"{name}_layout", frame_layout)
            
            group_layout.addWidget(frame)
            grid_layout.addWidget(group, row, col)
        
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowStretch(0, 1)
        grid_layout.setRowStretch(1, 1)
        
        self.main_layout.addWidget(render_panel, stretch=1)

        # Connect thickness slider to value label
        self.thickness_slider.valueChanged.connect(
            lambda value: self.thickness_value.setText(str(value))
        )

        
        # Connect step slider to value label
        self.step_slider.valueChanged.connect(
            lambda value: self.step_value.setText(str(value))
        )