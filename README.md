# MRI Viewer

A sophisticated medical imaging application for visualizing and analyzing multi-modal MRI scans with advanced visualization capabilities and tumor progression tracking.

## Features

- **Multi-Modal Visualization**: Simultaneous viewing of T1, FLAIR, SWI Magnitude, and SWI Phase images
- **Dynamic Slice Navigation**: Interactive slice-by-slice navigation with adjustable thickness
- **Advanced Rendering**: GPU-accelerated volume rendering with customizable lighting and shading
- **Mask Overlays**: Support for lesion and PRL (Perivascular Rim Lesions) mask visualization
- **Tumor Progression Animation**: Chronological visualization of tumor development across sessions
- **Synchronized Views**: All modalities remain synchronized during navigation and zooming
- **Quality Control**: Built-in tools for marking scan quality and annotating findings
- **Dark Theme**: Eye-friendly interface optimized for medical imaging

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

## Interface Components

- **View Settings**: Toggle between axial, coronal, and sagittal views
- **Slice Controls**: Adjust slice thickness and step size
- **Mask Controls**: Toggle visibility and opacity of lesion/PRL masks
- **Lighting Controls**: Customize volume rendering appearance
- **Case Navigation**: Browse through multiple scanning sessions
- **Quality Markers**: Flag scans for quality issues and add notes
- **Tumor Animation**: Launch chronological visualization of tumor progression

## Tumor Progression Visualization

The tumor animation feature provides:
- Chronological display of tumor development across scanning sessions
- Interactive timeline control for detailed analysis
- Adjustable playback speed for presentation or analysis
- Automatic volume rendering optimization for tumor visualization
- Frame-by-frame navigation capabilities
- Consistent spatial registration across timepoints

## Technical Details

- Built with PyQt5 for the user interface
- Uses VTK for 3D rendering and visualization
- Supports NIFTI format medical images
- Implements GPU-accelerated volume rendering
- Features synchronized multi-planar reconstruction
- Automatic chronological ordering of scanning sessions

## Project Structure

- `ui.py`: Main user interface implementation
- `render.py`: Core rendering and application logic
- `volume_multimodal.py`: Volume rendering and transfer function management
- `slice_interactor.py`: Slice navigation and interaction handling
- `mask_overlay.py`: Mask visualization and management
- `tumor_animation.py`: Tumor progression animation implementation

## Main Requirements

- Python 3.7+
- PyQt5
- VTK 9.0+
- NumPy
- nibabel

