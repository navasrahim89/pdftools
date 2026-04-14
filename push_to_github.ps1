# Run these commands in PowerShell

# Fix git ownership
git config --global --add safe.directory 'D:/Smart Detector/pdfkivy'

# Commit code
git add .
git commit -m "PDF Tools app"

# Create repo on github.com, then run:
git remote add origin https://github.com/YOUR_USERNAME/pdftools.git
git branch -M main
git push -u origin main
