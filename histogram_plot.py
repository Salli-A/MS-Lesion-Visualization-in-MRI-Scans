import vtk
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from vtkmodules.util import numpy_support  # Ensure correct import

# Define file paths
files = {
    "T1": 'SUB_AXX/SUB_AXX/ses-20180322/sub-AXXX123_ses-20180322_t1.nii.gz',
    "FLAIR": 'SUB_AXX/SUB_AXX/ses-20180322/sub-AXXX123_ses-20180322_flair.nii.gz',
    "SWI": 'SUB_AXX/SUB_AXX/ses-20180322/sub-AXXX123_ses-20180322_swiMag.nii.gz',
    "PHASE": 'SUB_AXX/SUB_AXX/ses-20180322/sub-AXXX123_ses-20180322_swiPhase.nii.gz'
}

# Dictionary to store bounds and extent
vtk_bounds = {}
vtk_extent = {}

# Function to convert NIfTI to VTK image data
def convert_nifti_to_vtk(file_path):
    nii = nib.load(file_path)
    data = nii.get_fdata()
    vtk_image = vtk.vtkImageData()
    dims = data.shape
    spacing = nii.header.get_zooms()[:3]  # Get voxel spacing
    vtk_image.SetDimensions(dims)
    vtk_image.SetSpacing(spacing)
    vtk_image.AllocateScalars(vtk.VTK_FLOAT, 1)

    # Flatten data and convert to VTK array
    flat_data = data.flatten(order='F')  # Flatten in Fortran order (z, y, x)
    vtk_array = numpy_support.numpy_to_vtk(flat_data, deep=True, array_type=vtk.VTK_FLOAT)
    vtk_image.GetPointData().SetScalars(vtk_array)
    
    return vtk_image

# Process all files
for name, file_path in files.items():
    try:
        # Convert NIfTI to VTK image
        vtk_image = convert_nifti_to_vtk(file_path)
        
        # Compute bounds and extent
        vtk_bounds[name] = vtk_image.GetBounds()
        vtk_extent[name] = vtk_image.GetExtent()
    except Exception as e:
        print(f"Error processing {name}: {e}")

# Print bounds and extent
print("Bounds and Extent for each modality:")
for name in files.keys():
    if name in vtk_bounds and name in vtk_extent:
        print(f"{name} Bounds: {vtk_bounds[name]}")
        print(f"{name} Extent: {vtk_extent[name]}")
    else:
        print(f"{name}: Could not compute bounds or extent.")
    print()

# Histogram visualization using matplotlib
histograms = {}

# Extract histogram data using NIfTI
for name, file_path in files.items():
    try:
        nii = nib.load(file_path)
        data = nii.get_fdata()
        histograms[name] = data.flatten()
    except Exception as e:
        print(f"Error processing {name} for histogram: {e}")

# Plot all histograms
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
axes = axes.flatten()

for idx, (name, data) in enumerate(histograms.items()):
    axes[idx].hist(data, bins=100, color='blue', alpha=0.7)
    axes[idx].set_title(f'Histogram of {name} Data')
    axes[idx].set_xlabel('Intensity Values')
    axes[idx].set_ylabel('Frequency')
    axes[idx].grid(True)

plt.tight_layout()
plt.show()
