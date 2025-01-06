# MRI Viewer

A sophisticated medical imaging application for visualizing and analyzing multi-modal MRI scans with advanced visualization capabilities and tumor progression tracking.

## Features

- **Multi-Modal Visualization**: Simultaneous viewing of T1, FLAIR, SWI Magnitude, and SWI Phase images
- **Dynamic Slice Navigation**: Interactive slice-by-slice navigation with adjustable thickness
- **Advanced Rendering**: GPU-accelerated volume rendering with customizable lighting and shading
- **Mask Overlays**: Support for lesion and PRL (Perivascular Rim Lesions) mask visualization
- **Tumor Progression Analysis**: Color-coded visualization of tumor evolution across sessions
- **Synchronized Views**: All modalities remain synchronized during navigation and zooming
- **Quality Control**: Built-in tools for marking scan quality and annotating findings
- **Dark Theme**: Eye-friendly interface optimized for medical imaging

## Installation

1. Ensure Python 3.7+ is installed
2. Install required dependencies:
```bash
pip install PyQt5 vtk numpy nibabel
```

## Usage

Launch the viewer by providing a subject directory:

```bash
python render.py /path/to/subject/directory
```

The directory should contain session folders with the following file structure:
```
subject/
├── ses-20230501/
│   ├── *Lreg_t1.nii.gz
│   ├── *Lreg_flair.nii.gz
│   ├── *Lreg_swiMag.nii.gz
│   ├── *Lreg_swiPhase.nii.gz
│   ├── *Lreg_lesionmask.nii.gz
│   └── *Lreg_PRLmask.nii.gz
└── ses-20230801/
    └── ...
```

Note: Session folders should follow the format `ses-YYYYMMDD` for proper chronological ordering in the tumor progression animation.

## Controls

### Main Viewer
- **Mouse Wheel**: Navigate through slices
- **Shift + Mouse Wheel**: Zoom in/out
- **Left Mouse**: Rotate view
- **Middle Mouse**: Pan view
- **Right Mouse**: Window/level adjustment

### Tumor Animation Window
- **Play/Pause**: Control animation playback
- **Timeline Slider**: Manually select specific timepoints
- **Speed Control**: Adjust animation playback speed
- **Frame Counter**: Track progression through the sequence
- **Visibility Toggles**: Control display of different tumor regions

## Tumor Progression Analysis

The tumor animation feature provides sophisticated visualization of tumor evolution through color-coded regions:

### Color-Coding System
- **Magenta Regions**: Stable tumor areas that persist between timepoints
- **Red Regions**: New tumor growth since the previous timepoint
- **Blue Regions**: Areas of tumor reduction since the previous timepoint

### Calculation Methodology

The system performs voxel-by-voxel analysis between consecutive timepoints to identify different types of tumor regions:

1. **Stable Regions Calculation**:
   ```python
   stable = np.logical_and(previous_timepoint > 0, current_timepoint > 0)
   ```
   A voxel is considered stable if it contains tumor tissue (value > 0) in both the previous and current timepoints. These regions represent the consistent tumor core.

2. **Growth Regions Calculation**:
   ```python
   growth = np.logical_and(current_timepoint > 0, previous_timepoint == 0)
   ```
   Growth is identified where a voxel contains tumor tissue in the current timepoint (value > 0) but was healthy tissue in the previous timepoint (value = 0). This highlights new tumor expansion.

3. **Reduction Regions Calculation**:
   ```python
   reduction = np.logical_and(previous_timepoint > 0, current_timepoint == 0)
   ```
   Reduction is detected where a voxel contained tumor tissue in the previous timepoint (value > 0) but shows healthy tissue in the current timepoint (value = 0). This indicates areas where the tumor has decreased.

The calculations use binary masks where:
- 0 represents healthy tissue
- 1 represents tumor tissue
- Logical operations are performed on matching voxel positions between timepoints

This analysis ensures:
- Every voxel is classified into exactly one category (stable, growth, or reduction)
- Changes are tracked relative to the immediately preceding timepoint
- Spatial relationships between different regions are preserved
- Accurate visualization of tumor evolution patterns

### Visualization Controls
- Individual toggles for showing/hiding:
  - Stable tumor regions
  - Areas of growth
  - Areas of reduction
- Adjustable opacity for each region type
- Synchronized playback across all tumor components

### Analysis Features
- Frame-by-frame comparison of tumor changes
- Automatic calculation of growth and reduction regions
- Enhanced depth perception through optimized lighting
- Consistent spatial registration across timepoints
- Interactive timeline navigation
- Adjustable playback speed for detailed analysis
- Real-time region visibility toggling

## Interface Components

- **View Settings**: Toggle between axial, coronal, and sagittal views
- **Slice Controls**: Adjust slice thickness and step size
- **Mask Controls**: Toggle visibility and opacity of lesion/PRL masks
- **Lighting Controls**: Customize volume rendering appearance
- **Case Navigation**: Browse through multiple scanning sessions
- **Quality Markers**: Flag scans for quality issues and add notes
- **Tumor Analysis**: Launch color-coded tumor progression visualization

## Technical Details

- Built with PyQt5 for the user interface
- Uses VTK for 3D rendering and visualization
- Supports NIFTI format medical images
- Implements GPU-accelerated volume rendering
- Features synchronized multi-planar reconstruction
- Automatic chronological ordering of scanning sessions
- Real-time difference computation between timepoints

## Project Structure

- `ui.py`: Main user interface implementation
- `render.py`: Core rendering and application logic
- `volume_multimodal.py`: Volume rendering and transfer function management
- `slice_interactor.py`: Slice navigation and interaction handling
- `mask_overlay.py`: Mask visualization and management
- `tumor_animation.py`: Color-coded tumor progression analysis implementation

## Basic Requirements

- Python 3.7+
- PyQt5
- VTK 9.0+
- NumPy
- nibabel

