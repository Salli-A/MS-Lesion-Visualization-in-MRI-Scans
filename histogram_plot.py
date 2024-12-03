import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt

# Define file paths
files = {
    "T1": 'SUB_AXX/SUB_AXX/ses-20180322/sub-AXXX123_ses-20180322_t1.nii.gz',
    "FLAIR": 'SUB_AXX/SUB_AXX/ses-20180322/sub-AXXX123_ses-20180322_flair.nii.gz',
    "SWI": 'SUB_AXX/SUB_AXX/ses-20180322/sub-AXXX123_ses-20180322_swiMag.nii.gz',
    "PHASE": 'SUB_AXX/SUB_AXX/ses-20180322/sub-AXXX123_ses-20180322_swiPhase.nii.gz'
}

# Dictionary to store maximum values and histogram data
max_values = {}
histograms = {}

# Process all files
for name, file_path in files.items():
    try:
        # Load the .nii.gz file
        nii = nib.load(file_path)
        
        # Extract the image data as a NumPy array
        data = nii.get_fdata()
        
        # Compute and store the maximum value
        max_values[name] = np.max(data)
        
        # Flatten the data to 1D for histogram
        histograms[name] = data.flatten()
    except Exception as e:
        print(f"Error processing {name}: {e}")

# Plot all histograms in a single figure
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
axes = axes.flatten()

for idx, (name, data) in enumerate(histograms.items()):
    axes[idx].hist(data, bins=100, color='blue', alpha=0.7)
    axes[idx].set_title(f'Histogram of {name} Data')
    axes[idx].set_xlabel('Intensity Values')
    axes[idx].set_ylabel('Frequency')
    axes[idx].grid(True)

# Adjust layout
plt.tight_layout()
plt.show()
