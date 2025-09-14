# Sarcopenia Detection Tool 🩺💪
**AI-powered application for automated sarcopenia detection using CT scans**  

---

## 📖 Overview  
This project provides a deep learning–based diagnostic tool for detecting **sarcopenia**, a condition of progressive skeletal muscle loss.  
The tool automates the pipeline:  

1. **DICOM → NIfTI conversion**  
2. **Muscle & fat segmentation** using deep learning  
3. **Skeletal Muscle Index (SMI) calculation**  
4. **Clinician-friendly reports** with visualization overlays  

The goal is to reduce manual analysis time, improve accuracy, and support clinicians with early sarcopenia detection.  

---

## 🚀 Features  
- Automatic DICOM to NIfTI conversion  
- Deep learning segmentation for muscle & fat regions  
- Rule-based sarcopenia analysis (SMI calculation)  
- Generates CSV reports and visual overlays  
- Lightweight, user-friendly desktop interface  
- Cross-platform (tested on macOS & Windows)  

---

## 🛠 Installation  

1. Clone this repository:  
   ```bash
   git clone https://github.com/yourusername/sarcopenia-detection-tool.git
   cd sarcopenia-detection-tool
   ```

2. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:  
   ```bash
   python sarc_app.py
   ```

---

## 📂 Usage Guide  

1. **Open the app**  
   Launch the interface with:  
   ```bash
   python sarc_app.py
   ```

2. **Upload scans**  
   Select a folder containing **DICOM CT images**.  

3. **Run analysis**  
   - Converts DICOM → NIfTI  
   - Runs segmentation  
   - Calculates SMI  
   - Generates reports in `/results/`  

4. **View results**  
   - CSV file with measurements  
   - Segmentation masks & overlays  
   - Diagnostic report  

---

## 📊 Example Output  
- **Input**: CT scan (DICOM)  
- **Output**:  
  - NIfTI file  
  - Segmentation overlay  
  - Sarcopenia report (CSV)  

---
## 🔑 Hugging Face Token (Important)

This project previously included a Hugging Face API token, but for security reasons it has been revoked.  
If you wish to run the Hugging Face–related functionality (e.g., loading pretrained models), you will need to provide **your own token**.

### How to set it up
1. Go to [Hugging Face Settings → Access Tokens](https://huggingface.co/settings/tokens).  
2. Create a **new token** with "read" (or "write" if required) permissions.  
3. Add it to ai_api.py
----

## 📌 Citation  
If you use this tool in your research, please cite this repository.  

---

## 📧 Contact  
For questions or contributions, feel free to:  
- Open an **issue** on GitHub  
- Or reach out via email: jishaansayyed46@gmail.com 
