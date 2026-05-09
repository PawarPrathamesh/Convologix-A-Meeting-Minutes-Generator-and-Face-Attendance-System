# 🧠 ConvoLogix
### Automated Meeting Minutes Generation & Face Attendance System

> Transforming how teams capture knowledge and track attendance — powered by deep learning, speech recognition, and computer vision.

---

## 📌 Overview

**ConvoLogix** is an end-to-end ML/DL pipeline that eliminates the inefficiencies of manual meeting processes. It automatically:

- **Transcribes** spoken audio from meeting recordings into text
- **Summarizes** conversations into concise, structured meeting minutes
- **Identifies** attendees using real-time face recognition
- **Delivers** a unified report with attendance logs and meeting notes via email

Whether you're managing remote teams or in-person sessions, ConvoLogix handles the busywork so you can focus on what matters.

---

## 🚩 Problem Statement

Traditional meeting workflows suffer from:

| Pain Point | Impact |
|---|---|
| Manual note-taking | Critical points get missed or misrecorded |
| Paper sign-in sheets | Prone to forgery, errors, and loss |
| Post-meeting summaries | Time-consuming and inconsistent |
| Siloed data | Hard to extract insights across meetings |

ConvoLogix addresses all of these with a single automated system.

---

## 🎯 Key Features

### 🎙️ Meeting Summarization
- Extracts audio tracks from video recordings
- Converts speech to text using automatic speech recognition (ASR)
- Generates concise meeting minutes using state-of-the-art NLP models
- Supports multiple summarization strategies (extractive & abstractive)

### 👤 Face Attendance Tracking
- Builds a dataset of attendee face images
- Detects and recognizes faces directly from meeting video
- Auto-marks attendance with timestamps
- Achieves **98% recognition accuracy** using LBPH

### 📊 Integrated Reporting
- Merges minutes and attendance into a single structured report
- Delivers reports via email (SMTP)
- Clean Tkinter-based GUI for ease of use

---

## 🛠️ Tech Stack

### Core Languages & Frameworks
| Category | Tools |
|---|---|
| Language | Python 3.11 |
| Deep Learning | TensorFlow, PyTorch, Keras |
| Computer Vision | OpenCV (cv2) |
| NLP | SpaCy, Hugging Face Transformers |
| Audio Processing | MoviePy, Spleeter, SpeechRecognition, Pydub |
| GUI | Tkinter |
| Notifications | SMTP / Email |
| Utilities | NumPy, OS, Datetime |

### Algorithms

**Face Recognition:**
- Convolutional Neural Networks (CNNs)
- Local Binary Pattern Histograms (LBPH) — *98% accuracy*

**Text Summarization:**
- LexRank (graph-based extractive)
- TextRank (graph-based extractive)
- Transformer-based (abstractive, via Hugging Face)

### Development Tools
- VS Code, Google Colab

---

## 📁 Repository Structure

```
ConvoLogix/
│
├── Code/                    # Source code for all modules
├── Dataset/                 # Face recognition image dataset
├── Extracted Audio/         # Audio files separated from video
├── Minutes of Meeting/      # Auto-generated meeting summaries
├── Trained Model/           # Pre-trained CNN & LBPH model files
├── Test Accuracy/           # Model evaluation metrics & results
├── Video Screenshots/       # Sample output screenshots
├── images/                  # Test images
├── Requirement.txt          # Python dependencies
└── README.md                # Project documentation
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.11+
- pip
- A webcam or pre-recorded meeting video

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/shritej21/Convologix-A-Meeting-Minutes-Generator-and-Face-Attendance-System.git
cd Convologix-A-Meeting-Minutes-Generator-and-Face-Attendance-System
```

**2. Install dependencies**
```bash
pip install -r Requirement.txt
```

**3. Launch the application**
```bash
python main.py
```

---

## 🔭 Objectives Breakdown

```
ConvoLogix
├── 1. Meeting Summarization
│   ├── Extract audio from video
│   ├── Speech-to-text conversion
│   ├── Text summarization (LexRank / TextRank / Transformers)
│   └── [Future] Speaker diarization ("who said what")
│
├── 2. Face Attendance
│   ├── Prepare face image dataset
│   ├── Train face recognition model (CNN / LBPH)
│   └── Detect & mark attendance from video
│
└── 3. Integration & Delivery
    ├── Merge minutes + attendance into unified report
    ├── GUI interface (Tkinter)
    └── Email delivery (SMTP)
```

---

## 🔮 Future Scope

- **Speaker Diarization** — Attribute specific quotes and points to individual speakers
- **Real-time Processing** — Live transcription and attendance during ongoing meetings
- **Cloud Integration** — Upload reports to Google Drive / Notion / Slack
- **Multi-language Support** — Extend ASR and summarization to non-English meetings
- **Analytics Dashboard** — Track attendance trends and meeting engagement over time

---

## ⚠️ Privacy & Data Notice

The `Dataset/` folder in this repository contains **personal biometric facial images** used solely for training and demonstration purposes.

**The following are strictly prohibited:**
- Copying, sharing, or redistributing any images from the dataset
- Using these images to train other models or systems
- Reproducing or repurposing the data in any commercial or non-academic context

This data is restricted to running this project locally for **academic evaluation only**.

### 🔒 For Contributors & Forks
> If you are forking or deploying this project, **do not commit real personal photos** to your repository.  
> Populate the `Dataset/` folder locally and add it to `.gitignore` to keep your biometric data off public servers.

Add the following to your `.gitignore`:
```
Dataset/
```

---

## 📄 License

This project is for academic and educational purposes. Please review the repository for licensing details before use in production or commercial applications.

---

> Built with ❤️ to make meetings smarter, not harder.
