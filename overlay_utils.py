import os
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt

def save_overlay_slices(ct_folder, seg_folder, output_dir, num_slices=3):
    """
    Save multiple overlay slices (CT + segmentation) as PNGs.

    Args:
        ct_folder (str): Folder containing CT .nii.gz
        seg_folder (str): Folder containing segmentation .nii.gz
        output_dir (str): Folder to save PNGs
        num_slices (int): Number of slices to save (default 3)
    """
    def find_nii(folder):
        for root, _, files in os.walk(folder):
            for f in files:
                if f.endswith(".nii.gz") or f.endswith(".nii"):
                    return os.path.join(root, f)
        return None

    # Find files
    ct_path = find_nii(ct_folder)
    seg_path = find_nii(seg_folder)

    if not ct_path or not seg_path:
        raise FileNotFoundError(
            f"Could not find CT in {ct_folder} or segmentation in {seg_folder}"
        )

    # Load volumes
    ct_img = nib.load(ct_path).get_fdata()
    seg_img = nib.load(seg_path).get_fdata()

    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Pick evenly spaced slices across the volume
    total_slices = ct_img.shape[2]
    slice_indices = np.linspace(total_slices // 4,
                                3 * total_slices // 4,
                                num_slices,
                                dtype=int)

    for i, slice_idx in enumerate(slice_indices):
        ct_slice = ct_img[:, :, slice_idx]
        seg_slice = seg_img[:, :, slice_idx]

        plt.figure(figsize=(6, 6))
        plt.imshow(ct_slice, cmap="gray")
        plt.imshow(seg_slice, cmap="jet", alpha=0.4)
        plt.axis("off")

        output_path = os.path.join(output_dir, f"overlay_slice_{i+1}.png")
        plt.savefig(output_path, bbox_inches="tight", pad_inches=0)
        plt.close()

    print(f"Saved {num_slices} overlay slices to {output_dir}")