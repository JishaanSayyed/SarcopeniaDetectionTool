import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import threading
import os
import shutil
import csv
import pydicom
import traceback
import matplotlib
from ai_api import generate_ai_explanation
import platform, subprocess
from overlay_utils import save_overlay_slices

matplotlib.use("Agg")  # prevents GUI conflicts on macOS

def app_base_dir():
    """Return base directory for saving results, works in dev and PyInstaller bundle."""
    if getattr(sys, "frozen", False):  # running as bundle
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")

MAX_PATIENTS = 5
RESULTS_DIR = os.path.join(app_base_dir(), "results")


import sys

def resource_path(relative_path):
    """Get absolute path to resource for PyInstaller bundle or dev mode."""
    if getattr(sys, 'frozen', False):  # Running in bundle
        base_path = sys._MEIPASS
    else:  # Running in normal Python
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)



class SarcopeniaApp:
    def __init__(self, master):
        self.master = master
        master.title("Sarcopenia Detection App")
        master.geometry("750x600")

        # Patient Info Section
        tk.Label(master, text="Enter Patient Details", font=("Arial", 14, "bold")).pack(pady=10)

        self.patient_name_var = tk.StringVar()
        tk.Label(master, text="Name:").pack()
        tk.Entry(master, textvariable=self.patient_name_var).pack(pady=5)

        self.age_var = tk.StringVar()
        tk.Label(master, text="Age (years):").pack()
        tk.Entry(master, textvariable=self.age_var).pack(pady=5)

        self.weight_var = tk.StringVar()
        tk.Label(master, text="Weight (kg):").pack()
        tk.Entry(master, textvariable=self.weight_var).pack(pady=5)

        self.gender_var = tk.StringVar()
        tk.Label(master, text="Gender:").pack()
        tk.Entry(master, textvariable=self.gender_var).pack(pady=5)

        self.height_var = tk.StringVar()
        tk.Label(master, text="Height (cm):").pack()
        tk.Entry(master, textvariable=self.height_var).pack(pady=5)

        # File selection
        self.label = tk.Label(master, text="Select DICOM Folder")
        self.label.pack(pady=10)

        self.select_button = tk.Button(master, text="Browse", command=self.select_input)
        self.select_button.pack(pady=5)

        self.input_file = None

        # Run pipeline button
        self.run_button = tk.Button(master, text="Run Sarcopenia Analysis", command=self.run_pipeline, state=tk.DISABLED)
        self.run_button.pack(pady=10)

        # Log output
        self.log_text = tk.Text(master, height=15, width=90, bg="black", fg="lime")
        self.log_text.pack(pady=10)
        self.log_text.tag_config("error", foreground="red")  # red text for errors

        # Make sure results dir exists
        os.makedirs(RESULTS_DIR, exist_ok=True)

    def select_input(self):
        folder_selected = filedialog.askdirectory(title="Select DICOM Folder")
        if folder_selected:
            self.input_file = folder_selected
            self.log_text.insert(tk.END, f" Selected input folder: {self.input_file}\n")
            self.run_button.config(state=tk.NORMAL)

    def run_pipeline(self):
        try:
            if not self.input_file:
                messagebox.showerror("Error", "Please select an input folder first.")
                return

            patient_name = self.patient_name_var.get().strip()
            if not patient_name:
                messagebox.showerror("Error", "Please enter a patient name.")
                return

            patient_output = os.path.join(RESULTS_DIR, patient_name)
            os.makedirs(patient_output, exist_ok=True)

            dicom_meta = extract_dicom_metadata(self.input_file)
            print(dicom_meta)

            # Merge user-provided info with DICOM metadata
            row_data = {
                "ID": patient_name,
                "Age": self.age_var.get(),
                "Weight": self.weight_var.get(),
                "Gender": self.gender_var.get(),
                "Height": self.height_var.get(),
                **dicom_meta
            }

            # Save metadata with dynamic columns
            metadata_file = os.path.join(patient_output, "segmentation", "metadata.csv")
            os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
            with open(metadata_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=row_data.keys())
                writer.writeheader()
                writer.writerow(row_data)

            self.log_text.insert(tk.END, f" Saved patient metadata: {metadata_file}\n")

            # Example pipeline commands (replace with your scripts)
            commands = [
                # Step 1: Convert DICOM to NIfTI
                [
                    "bash", resource_path("DiCOM_to_nifti.sh"),
                    self.input_file,
                    os.path.abspath(RESULTS_DIR),   # base results dir
                    patient_name                    # patient ID
                ],

                # Step 2: Run segmentation
                {
                    "cmd": [
                        "python", "predict_muscle_fat.py",
                        "--input", os.path.abspath(os.path.join(patient_output, "nifti")),
                        "--output", os.path.abspath(os.path.join(patient_output, "segmentation")),
                        "--checkpoint_type", "best",
                        "--body_composition_type", "2D",
                        "--overwrite", "True"
                    ],
                    "cwd": resource_path("CT-Muscle-and-Fat-Segmentation")
                },

                # Step 3: Rule-based sarcopenia detection
             [
                "python", resource_path("rule_based_sarcopenia.py"),
                os.path.abspath(patient_output),   # patient_folder
                os.path.abspath(os.path.join(patient_output, "report.csv"))  # output_csv
            ]
        ]


            threading.Thread(target=self.run_commands, args=(commands, patient_output)).start()
        except Exception as e:
            self.log_text.insert(tk.END, f"\nERROR: {e}\n", "error")
            self.log_text.insert(tk.END, traceback.format_exc(), "error")
            self.log_text.see(tk.END)

    def run_commands(self, commands, patient_output):
        for cmd_info in commands:
            if isinstance(cmd_info, dict):
                cmd = cmd_info["cmd"]
                cwd = cmd_info.get("cwd", None)
            else:
                cmd = cmd_info
                cwd = None

            self.log_text.insert(tk.END, f"\nRunning: {' '.join(cmd)}\n")
            if cwd:
                self.log_text.insert(tk.END, f"   Working directory: {cwd}\n")
            self.log_text.insert(tk.END, f"   Input: {self.input_file}\n   📂 Output: {patient_output}\n")
            self.log_text.see(tk.END)

            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=cwd  # run in the right folder
                )

                for line in iter(process.stdout.readline, ''):
                    line = line.strip()

                    if "\r" in line or "%" in line:  
                        # tqdm or carriage return style update
                        self.log_text.delete("end-2l", "end-1l")  # remove last line
                        self.log_text.insert(tk.END, line + "\n")
                    elif line:
                        self.log_text.insert(tk.END, line + "\n")

                    self.log_text.see(tk.END)

                process.stdout.close()
                ret = process.wait()

                if ret != 0:
                    self.log_text.insert(tk.END, f"\nCommand failed: {' '.join(cmd)}\n", "error")
            except Exception as e:
                self.log_text.insert(tk.END, f"\nSubprocess error: {e}\n", "error")
                self.log_text.insert(tk.END, traceback.format_exc(), "error")

        self.log_text.insert(tk.END, "\nPipeline finished!\n")
        # After pipeline commands finish
        ct_folder = os.path.join(patient_output, "nifti")
        seg_folder = os.path.join(patient_output, "segmentation")
        overlay_dir = os.path.join(patient_output, "overlays")

        try:
            save_overlay_slices(ct_folder, seg_folder, overlay_dir, num_slices=3)
            self.log_text.insert(tk.END, f"\n Overlay images saved in {overlay_dir}\n")
            self.log_text.see(tk.END)
        except Exception as e:
            self.log_text.insert(tk.END, f"\n Overlay generation failed: {e}\n")
            self.log_text.see(tk.END)

        try:
            ai_doc = generate_ai_explanation(patient_output)
            self.log_text.insert(tk.END, f"AI Explanation saved: {ai_doc}\n")
            self.log_text.see(tk.END)

            if platform.system() == "Darwin":  # macOS
                subprocess.call(["open", ai_doc])
            elif platform.system() == "Windows":
                os.startfile(ai_doc)
            else:  # Linux
                subprocess.call(["xdg-open", ai_doc])

        except Exception as e:
            self.log_text.insert(tk.END, f" Failed to generate AI explanation: {e}\n", "error")

        self.log_text.see(tk.END)

        self.enforce_patient_limit()
        

    def enforce_patient_limit(self):
        patients = sorted(
            [os.path.join(RESULTS_DIR, d) for d in os.listdir(RESULTS_DIR) if os.path.isdir(os.path.join(RESULTS_DIR, d))],
            key=os.path.getmtime
        )

        if len(patients) > MAX_PATIENTS:
            oldest = patients[0]
            shutil.rmtree(oldest)
            self.log_text.insert(tk.END, f"\nDeleted oldest patient folder: {os.path.basename(oldest)}\n")
            self.log_text.see(tk.END)

def parse_patient_age(age_str):
    """Convert PatientAge (e.g., '042Y', '055M') into years as float."""
    if not age_str or age_str == "NA":
        return None
    try:
        num = int(age_str[:3])
        unit = age_str[-1].upper()
        if unit == "Y":  # years
            return num
        elif unit == "M":  # months
            return round(num / 12, 2)
        elif unit == "W":  # weeks
            return round(num / 52, 2)
        elif unit == "D":  # days
            return round(num / 365, 2)
        else:
            return num  # fallback
    except Exception:
        return None

DICOM_TAGS = {
    "SOPInstanceUID": "NA",
    "SeriesInstanceUID": "NA",
    "StudyInstanceUID": "NA",
    "InstanceNumber": "NA",
    "ImagePositionPatient": "NA",
    "Rows": "NA",
    "Columns": "NA",
    "PixelSpacing": "NA",
    "RescaleIntercept": "NA",
    "RescaleSlope": "NA",
    "SliceThickness": "NA",
    "ConvolutionKernel": "NA",
    "ContrastBolusAgent": "NA",
    "PatientSex": "NA",
    "PatientAge": "NA",
    "TableHeight": "NA"
}

def extract_dicom_metadata(dicom_folder):
    """Extract metadata from the first valid DICOM file found (recursively)."""
    first_file = None

    # Walk through all subdirectories to find the first valid dicom
    for root, _, files in os.walk(dicom_folder):
        for f in files:
            if f.startswith("."):  # skip hidden files like .DS_Store
                continue
            file_path = os.path.join(root, f)
            try:
                dcm = pydicom.dcmread(file_path, stop_before_pixels=True, force=True)
                first_file = file_path
                break
            except Exception:
                continue
        if first_file:
            break

    if not first_file:
        print("No valid DICOM files found.")
        return {}

    try:
        dcm = pydicom.dcmread(first_file, stop_before_pixels=True, force=True)

        metadata = {}
        for tag in DICOM_TAGS.keys():
            value = getattr(dcm, tag, "NA")
            if tag == "PatientAge":
                value = parse_patient_age(value)  # normalize age
            metadata[tag] = value

        return metadata

    except Exception as e:
        print(f"Could not read DICOM metadata from {first_file}: {e}")
        return {}

if __name__ == "__main__":
    root = tk.Tk()
    app = SarcopeniaApp(root)
    root.mainloop()
