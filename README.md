# MS-Lesion-Visualization-in-MRI-Scans

## Project should include
- 3D visualization
- surface reconstruction and rendering methods
- volume rendering methods
- interaction methods
- fused visualization of different modalities or features
- stereo rendering
- animation
- a GUI for the application

## Needs to be done:

- Fix color and opacity transfer functions for modalities
    - Seperate transfer functions for each modality
    - Automatic based on histogram? Adjustable (pehaps could be good to do on per slice basis?)?
- Needs animation (maybe the way the camera sync is done qualifies as an animation as it makes use of timers?)
    - Animation of lesions growth (needs the lesion mask development)
- Needs surface reconstruction (Perhaps of the the lesion mask?)
- Fused visulization across modalities (phase omdatlity with swi?) or add features derived from the scans (gradients or derivatives?)
- Add scan to file (eg. csv) instead of just printing

Perhaps:
- Change basic control scheme from vtkInteractorStyleTrackballCamera to not allow for rotation, only zoom and paning.
    - vtkInteractorStyleImage? (should only need to change in the SLiceInteractor class in slicer_interactor.py)
    - Would need option to change "sides"



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

## slice_interactor.py
Classes for tracking shared slicing and bounds across modalities, and for interacting with it using interactor for each modalities.

## histogram_plot.py
Code for viewing histogram across modalities. Just for viewing the data for comparison.

