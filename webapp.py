from flask import Flask, render_template_string, request, send_file, redirect, url_for
import os
import io
import base64
from datetime import datetime

from PIL import Image, ImageEnhance
try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    try:
        from PyPDF2 import PdfReader, PdfWriter
    except ImportError:
        HAS_PYPDF = False
    else:
        HAS_PYPDF = True
else:
    HAS_PYPDF = True

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

OUTPUT_FOLDER = os.path.join(os.path.expanduser('~'), 'PDF Tools')
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>PDF Tools</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               background: #f5f5f5; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; 
                     overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: #2196F3; color: white; padding: 20px; text-align: center; }
        .nav { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1px; background: #ddd; }
        .nav button { padding: 15px; border: none; background: white; cursor: pointer; font-size: 14px;
                     transition: background 0.2s; }
        .nav button:hover { background: #e3f2fd; }
        .nav button.active { background: #2196F3; color: white; }
        .content { padding: 20px; }
        .section { display: none; }
        .section.active { display: block; }
        h2 { margin-bottom: 15px; color: #333; }
        .file-select { border: 2px dashed #ccc; padding: 30px; text-align: center; 
                      border-radius: 8px; cursor: pointer; margin-bottom: 15px; }
        .file-select:hover { border-color: #2196F3; background: #f5f5f5; }
        input[type="file"] { display: none; }
        .btn { display: block; width: 100%; padding: 14px; background: #2196F3; color: white; 
               border: none; border-radius: 8px; font-size: 16px; cursor: pointer; margin: 8px 0; }
        .btn:hover { background: #1976D2; }
        .btn.secondary { background: #757575; }
        .btn.green { background: #4CAF50; }
        .btn.orange { background: #FF9800; }
        input[type="number"], input[type="text"] { width: 100%; padding: 12px; margin: 8px 0;
                                                   border: 1px solid #ddd; border-radius: 6px; font-size: 16px; }
        .file-list { margin: 10px 0; max-height: 150px; overflow-y: auto; }
        .file-item { padding: 10px; background: #f5f5f5; margin: 5px 0; border-radius: 4px;
                     display: flex; justify-content: space-between; align-items: center; }
        .file-item span { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .remove-btn { color: red; cursor: pointer; padding: 5px 10px; }
        .status { padding: 12px; margin: 10px 0; border-radius: 6px; }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .info { font-size: 12px; color: #666; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>PDF Tools</h1>
        </div>
        <div class="nav">
            <button class="active" onclick="show('merge')">Merge</button>
            <button onclick="show('split')">Split</button>
            <button onclick="show('scanner')">Scanner</button>
            <button onclick="show('resize')">Resize</button>
        </div>
        
        <div class="content">
            <!-- MERGE -->
            <div id="merge" class="section active">
                <h2>PDF Merge</h2>
                <div class="file-select" onclick="document.getElementById('mergeFiles').click()">
                    Tap to select PDF files
                </div>
                <input type="file" id="mergeFiles" multiple accept=".pdf" onchange="handleMergeSelect()">
                <div class="file-list" id="mergeList"></div>
                <button class="btn green" onclick="mergePDFs()">Merge PDFs</button>
                <div id="mergeStatus"></div>
            </div>
            
            <!-- SPLIT -->
            <div id="split" class="section">
                <h2>PDF Split</h2>
                <div class="file-select" onclick="document.getElementById('splitFile').click()">
                    Tap to select PDF
                </div>
                <input type="file" id="splitFile" accept=".pdf" onchange="handleSplitSelect()">
                <div id="splitName"></div>
                <input type="text" id="pageRange" placeholder="e.g., 1-3,5,7-10 (leave empty for all)">
                <button class="btn" onclick="splitPDF()">Split PDF</button>
                <div id="splitStatus"></div>
            </div>
            
            <!-- SCANNER -->
            <div id="scanner" class="section">
                <h2>PDF Scanner</h2>
                <div class="file-select" onclick="document.getElementById('scanFile').click()">
                    Tap to select image
                </div>
                <input type="file" id="scanFile" accept="image/*" onchange="handleScanSelect()">
                <div id="scanName"></div>
                <div class="grid-2">
                    <button class="btn secondary" onclick="processScan('grayscale')">Grayscale</button>
                    <button class="btn secondary" onclick="processScan('blackwhite')">B&W</button>
                    <button class="btn secondary" onclick="processScan('enhance')">Enhance</button>
                    <button class="btn secondary" onclick="processScan('denoise')">Denoise</button>
                </div>
                <button class="btn green" onclick="convertToPDF()">Convert to PDF</button>
                <div id="scanStatus"></div>
            </div>
            
            <!-- RESIZE -->
            <div id="resize" class="section">
                <h2>PDF/Image Resize</h2>
                <div class="file-select" onclick="document.getElementById('resizeFile').click()">
                    Tap to select file (PDF or Image)
                </div>
                <input type="file" id="resizeFile" accept=".pdf,.jpg,.jpeg,.png" onchange="handleResizeSelect()">
                <div id="resizeName"></div>
                <input type="number" id="scalePercent" value="100" placeholder="Scale % (e.g., 50)">
                <button class="btn orange" onclick="resizeFile()">Resize</button>
                <div id="resizeStatus"></div>
            </div>
        </div>
    </div>
    
    <script>
        let mergeFiles = [];
        let splitFile = null;
        let scanFile = null;
        let resizeFile = null;
        
        function show(id) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            event.target.classList.add('active');
        }
        
        function handleMergeSelect() {
            const input = document.getElementById('mergeFiles');
            mergeFiles = Array.from(input.files);
            updateMergeList();
        }
        
        function updateMergeList() {
            const list = document.getElementById('mergeList');
            list.innerHTML = mergeFiles.map((f, i) => 
                '<div class="file-item"><span>' + f.name + '</span><span class="remove-btn" onclick="removeMerge(' + i + ')">✕</span></div>'
            ).join('');
        }
        
        function removeMerge(i) {
            mergeFiles.splice(i, 1);
            updateMergeList();
        }
        
        async function mergePDFs() {
            if (mergeFiles.length < 2) {
                showStatus('mergeStatus', 'Select at least 2 PDFs', 'error');
                return;
            }
            const formData = new FormData();
            mergeFiles.forEach(f => formData.append('files', f));
            showStatus('mergeStatus', 'Processing...', '');
            const res = await fetch('/merge', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.success) showStatus('mergeStatus', 'Saved: ' + data.filename, 'success');
            else showStatus('mergeStatus', 'Error: ' + data.error, 'error');
        }
        
        function handleSplitSelect() {
            const input = document.getElementById('splitFile');
            splitFile = input.files[0];
            document.getElementById('splitName').textContent = splitFile ? splitFile.name : '';
        }
        
        async function splitPDF() {
            if (!splitFile) { showStatus('splitStatus', 'Select a PDF', 'error'); return; }
            const formData = new FormData();
            formData.append('file', splitFile);
            formData.append('range', document.getElementById('pageRange').value);
            showStatus('splitStatus', 'Processing...', '');
            const res = await fetch('/split', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.success) showStatus('splitStatus', 'Saved: ' + data.filename, 'success');
            else showStatus('splitStatus', 'Error: ' + data.error, 'error');
        }
        
        function handleScanSelect() {
            const input = document.getElementById('scanFile');
            scanFile = input.files[0];
            document.getElementById('scanName').textContent = scanFile ? scanFile.name : '';
        }
        
        async function processScan(mode) {
            if (!scanFile) { showStatus('scanStatus', 'Select an image', 'error'); return; }
            const formData = new FormData();
            formData.append('file', scanFile);
            formData.append('mode', mode);
            showStatus('scanStatus', 'Processing...', '');
            const res = await fetch('/scanner', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.success) showStatus('scanStatus', 'Saved: ' + data.filename, 'success');
            else showStatus('scanStatus', 'Error: ' + data.error, 'error');
        }
        
        async function convertToPDF() {
            if (!scanFile) { showStatus('scanStatus', 'Select an image', 'error'); return; }
            const formData = new FormData();
            formData.append('file', scanFile);
            showStatus('scanStatus', 'Processing...', '');
            const res = await fetch('/to_pdf', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.success) showStatus('scanStatus', 'Saved: ' + data.filename, 'success');
            else showStatus('scanStatus', 'Error: ' + data.error, 'error');
        }
        
        function handleResizeSelect() {
            const input = document.getElementById('resizeFile');
            resizeFile = input.files[0];
            document.getElementById('resizeName').textContent = resizeFile ? resizeFile.name : '';
        }
        
        async function resizeFile() {
            if (!resizeFile) { showStatus('resizeStatus', 'Select a file', 'error'); return; }
            const formData = new FormData();
            formData.append('file', resizeFile);
            formData.append('scale', document.getElementById('scalePercent').value);
            showStatus('resizeStatus', 'Processing...', '');
            const res = await fetch('/resize', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.success) showStatus('resizeStatus', 'Saved: ' + data.filename, 'success');
            else showStatus('resizeStatus', 'Error: ' + data.error, 'error');
        }
        
        function showStatus(id, msg, type) {
            const el = document.getElementById(id);
            el.textContent = msg;
            el.className = 'status ' + type;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/merge', methods=['POST'])
def merge_pdfs():
    try:
        files = request.files.getlist('files')
        if len(files) < 2:
            return {'success': False, 'error': 'Need at least 2 files'}
        
        writer = PdfWriter()
        for f in files:
            reader = PdfReader(f)
            for page in reader.pages:
                writer.add_page(page)
        
        output = os.path.join(OUTPUT_FOLDER, f"merged_{int(datetime.now().timestamp())}.pdf")
        with open(output, 'wb') as f:
            writer.write(f)
        
        return {'success': True, 'filename': os.path.basename(output)}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/split', methods=['POST'])
def split_pdf():
    try:
        file = request.files['file']
        page_range = request.form.get('range', '').strip()
        
        reader = PdfReader(file)
        
        if not page_range:
            output_dir = os.path.join(OUTPUT_FOLDER, f"split_{int(datetime.now().timestamp())}")
            os.makedirs(output_dir, exist_ok=True)
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                out_file = os.path.join(output_dir, f"page_{i+1}.pdf")
                with open(out_file, 'wb') as f:
                    writer.write(f)
            return {'success': True, 'filename': f'Split to {len(reader.pages)} files'}
        else:
            pages = []
            parts = page_range.split(',')
            for p in parts:
                if '-' in p:
                    start, end = map(int, p.split('-'))
                    pages.extend(range(start, end + 1))
                else:
                    pages.append(int(p))
            
            writer = PdfWriter()
            for p in pages:
                if 0 < p <= len(reader.pages):
                    writer.add_page(reader.pages[p - 1])
            
            output = os.path.join(OUTPUT_FOLDER, f"split_{int(datetime.now().timestamp())}.pdf")
            with open(output, 'wb') as f:
                writer.write(f)
            
            return {'success': True, 'filename': os.path.basename(output)}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/scanner', methods=['POST'])
def scanner():
    try:
        file = request.files['file']
        mode = request.form.get('mode', 'original')
        
        img = Image.open(file)
        
        if HAS_OPENCV:
            cv_img = cv2.imread(np.frombuffer(file.read(), np.uint8))
            file.seek(0)
            
            if mode == 'grayscale':
                processed = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
            elif mode == 'blackwhite':
                gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                _, processed = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
            elif mode == 'enhance':
                processed = cv2.detailEnhance(cv_img, sigma_s=10, sigma_r=0.15)
            elif mode == 'denoise':
                processed = cv2.fastNlMeansDenoisingColored(cv_img, None, 10, 10, 7, 21)
            else:
                processed = cv_img
            
            output = os.path.join(OUTPUT_FOLDER, f"scanned_{int(datetime.now().timestamp())}.jpg")
            cv2.imwrite(output, processed)
        else:
            if mode == 'grayscale':
                img = img.convert('L').convert('RGB')
            elif mode == 'blackwhite':
                img = img.convert('L').point(lambda x: 255 if x > 127 else 0, '1').convert('RGB')
            elif mode == 'enhance':
                img = ImageEnhance.Contrast(img).enhance(1.5)
            
            output = os.path.join(OUTPUT_FOLDER, f"scanned_{int(datetime.now().timestamp())}.jpg")
            img.save(output, 'JPEG')
        
        return {'success': True, 'filename': os.path.basename(output)}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/to_pdf', methods=['POST'])
def to_pdf():
    try:
        file = request.files['file']
        img = Image.open(file)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        output = os.path.join(OUTPUT_FOLDER, f"scanned_{int(datetime.now().timestamp())}.pdf")
        img.save(output, 'PDF')
        
        return {'success': True, 'filename': os.path.basename(output)}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/resize', methods=['POST'])
def resize_file():
    try:
        file = request.files['file']
        scale = int(request.form.get('scale', 100))
        
        ext = os.path.splitext(file.filename)[1].lower()
        
        if ext == '.pdf':
            reader = PdfReader(file)
            writer = PdfWriter()
            
            for page in reader.pages:
                page.scale_to(page.mediabox.width * scale / 100, page.mediabox.height * scale / 100)
                writer.add_page(page)
            
            output = os.path.join(OUTPUT_FOLDER, f"resized_{int(datetime.now().timestamp())}.pdf")
            with open(output, 'wb') as f:
                writer.write(f)
        else:
            img = Image.open(file)
            new_w = img.width * scale // 100
            new_h = img.height * scale // 100
            resized = img.resize((new_w, new_h), Image.LANCZOS)
            
            output = os.path.join(OUTPUT_FOLDER, f"resized_{int(datetime.now().timestamp())}.jpg")
            resized.save(output, img.format or 'JPEG')
        
        return {'success': True, 'filename': os.path.basename(output)}
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    print(f"Output folder: {OUTPUT_FOLDER}")
    print(f"OpenCV available: {HAS_OPENCV}")
    print(f"PyPDF available: {HAS_PYPDF}")
    app.run(host='0.0.0.0', port=5000, debug=True)
