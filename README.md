# PDF Tools - Android App

Python-based Android app for PDF operations with OpenCV image processing.

## Features

- **PDF Merge** - Combine multiple PDFs
- **PDF Split** - Split by page or range
- **PDF Scanner** - Image processing (grayscale, B&W, enhance, denoise)
- **PDF/Image Resize** - Scale by percentage

## Build APK

### Option 1: GitHub Actions (Automatic)

1. Create a new repository on GitHub
2. Push this code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/pdftools.git
   git push -u origin main
   ```

3. Go to **Actions** tab on GitHub
4. Click **Build Android APK** workflow → **Run workflow**
5. Download APK from **Actions → Artifacts**

### Option 2: Local (WSL required)

```bash
# Install WSL
wsl --install

# In Ubuntu:
sudo apt update && sudo apt install -y python3-pip git openjdk-17-jdk
pip3 install buildozer

# Set up Android SDK and build
cd /path/to/pdfkivy
buildozer android debug
```

APK will be at `bin/pdftools-1.0-debug.apk`

## Requirements

- Python 3.8+
- pillow
- pypdf
- opencv-python (optional)
- numpy (optional)
- kivy
