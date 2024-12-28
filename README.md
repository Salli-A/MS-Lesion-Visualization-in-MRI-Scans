# MS-Lesion-Visualization-in-MRI-Scans


# Needs to be done:


- Change camera view with coronal/axial (look into findBounds and setSLiceDirection on slice_interactor.py)
- Fix rotations of swi and phase (not orientated in the same way as t1 and flair)
-- Applying userTransformations changes slicing plane rotation as well (causing a mix up between axial, coronal, sagittal between modalities - seen by putting true on swi_phase_modality in renderPlaneVolume), possible fixes:
--- Seperate handling of t1/flair and swi/phase with seperate volume renders and slice interactor functions?
--- Apply rotation/ change axis before inserting into rendering pipeline?
-- Make sure that the modalities are registered since the SWI/phase had different orientation?
- Fix color and opacity transfer functions for modalities
-- Seperate transfer functions for each modality
-- Automatic based on histogram? Adjustable?
- Needs animation (technically the way the camera sync is done is an animation as it makes use of timers?)
- Add lesion segmentation



## MVis.ui
Qt Designer UI.

## render.py
Code for rendering all modalaties in the Qt UI.

- Synced camera across modalities
- Volume slices
- Axial, Coronal, Sagittal views
- Adjustable slice thickness
- Shared slicing plane across modalities
- Reset view button
- Fields for marking scans (PRL, CVS, bad scan, text field)
- Control instructions


## volume_multimodal.py
Function for the rendering pipeline for all modalities for simplicity. Might needs seperate functions. 

Commit 508c511243ffdb0483074662855e0f1113eced8b had seperate functions (the only difference was between t1/flair and swi/phase with rotations and transfer functions), was deleted for simplicity.

## histogram_plot.py
Code for viewing histogram across modalities. Just for viewing the data for comparison.

