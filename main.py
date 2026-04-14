import os
import sys
import io
import base64
from datetime import datetime

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, StringProperty
from kivy.lang import Builder
from kivy.core.window import Window

from PIL import Image
try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import RectangleObject
except ImportError:
    try:
        from PyPDF2 import PdfReader, PdfWriter
    except ImportError:
        HAS_PYPDF = False
    else:
        HAS_PYPDF = True
else:
    HAS_PYPDF = True

ANDROID = sys.platform == 'android'
if ANDROID:
    from androidstorage4kivy import AndroidStorage
    from jnius import autoclass, cast
    from android import mActivity
    from android.permissions import request_permission, check_permission
    Environment = autoclass('android.os.Environment')


class HomeScreen(Screen):
    pass

class MergeScreen(Screen):
    selected_files = []
    
    def add_file(self, path):
        if path not in self.selected_files:
            self.selected_files.append(path)
            self.update_file_list()
    
    def remove_file(self, path):
        if path in self.selected_files:
            self.selected_files.remove(path)
            self.update_file_list()
    
    def update_file_list(self):
        layout = self.ids.file_list
        layout.clear_widgets()
        for f in self.selected_files:
            btn = Button(text=os.path.basename(f), size_hint_y=None, height=40)
            btn.bind(on_release=lambda x, p=f: self.remove_file(p))
            layout.add_widget(btn)
    
    def merge_pdfs(self):
        if not HAS_PYPDF:
            self.ids.status.text = "Error: pypdf not installed"
            return
        if len(self.selected_files) < 2:
            self.ids.status.text = "Select at least 2 PDFs"
            return
        
        try:
            writer = PdfWriter()
            for pdf in self.selected_files:
                reader = PdfReader(pdf)
                for page in reader.pages:
                    writer.add_page(page)
            
            output = os.path.join(self.get_output_dir(), f"merged_{int(datetime.now().timestamp())}.pdf")
            with open(output, 'wb') as f:
                writer.write(f)
            self.ids.status.text = f"Saved: {os.path.basename(output)}"
        except Exception as e:
            self.ids.status.text = f"Error: {str(e)}"
    
    def get_output_dir(self):
        if ANDROID:
            return os.path.join(Environment.getExternalStorageDirectory().getAbsolutePath(), 'PDF Tools')
        return os.path.expanduser('~/Documents/PDF Tools')

class SplitScreen(Screen):
    selected_pdf = StringProperty("")
    
    def select_pdf(self, path):
        self.selected_pdf = path
        self.ids.pdf_name.text = os.path.basename(path)
        self.ids.status.text = ""
    
    def split_all(self):
        if not self.selected_pdf:
            self.ids.status.text = "Select a PDF first"
            return
        
        try:
            reader = PdfReader(self.selected_pdf)
            output_dir = os.path.join(self.get_output_dir(), f"split_{int(datetime.now().timestamp())}")
            os.makedirs(output_dir, exist_ok=True)
            
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                out_file = os.path.join(output_dir, f"page_{i+1}.pdf")
                with open(out_file, 'wb') as f:
                    writer.write(f)
            
            self.ids.status.text = f"Split to {len(reader.pages)} files"
        except Exception as e:
            self.ids.status.text = f"Error: {str(e)}"
    
    def split_range(self):
        if not self.selected_pdf:
            self.ids.status.text = "Select a PDF first"
            return
        
        try:
            range_text = self.ids.page_range.text
            parts = range_text.split(',')
            pages = []
            for p in parts:
                if '-' in p:
                    start, end = map(int, p.split('-'))
                    pages.extend(range(start, end+1))
                else:
                    pages.append(int(p))
            
            reader = PdfReader(self.selected_pdf)
            output_dir = os.path.join(self.get_output_dir(), f"split_{int(datetime.now().timestamp())}")
            os.makedirs(output_dir, exist_ok=True)
            
            writer = PdfWriter()
            for p in pages:
                if 0 < p <= len(reader.pages):
                    writer.add_page(reader.pages[p-1])
            
            out_file = os.path.join(output_dir, "split_pages.pdf")
            with open(out_file, 'wb') as f:
                writer.write(f)
            self.ids.status.text = f"Saved: {os.path.basename(out_file)}"
        except Exception as e:
            self.ids.status.text = f"Error: {str(e)}"
    
    def get_output_dir(self):
        if ANDROID:
            return os.path.join(Environment.getExternalStorageDirectory().getAbsolutePath(), 'PDF Tools')
        return os.path.expanduser('~/Documents/PDF Tools')

class ScannerScreen(Screen):
    selected_image = StringProperty("")
    processed_image = StringProperty("")
    
    def select_image(self, path):
        self.selected_image = path
        self.ids.img_name.text = os.path.basename(path)
        self.ids.status.text = ""
    
    def process_image(self, mode):
        if not self.selected_image:
            self.ids.status.text = "Select an image first"
            return
        
        try:
            if HAS_OPENCV:
                img = cv2.imread(self.selected_image)
                if img is None:
                    raise ValueError("Could not load image")
                
                if mode == 'grayscale':
                    processed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
                elif mode == 'blackwhite':
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    _, processed = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                    processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
                elif mode == 'enhance':
                    processed = cv2.detailEnhance(img, sigma_s=10, sigma_r=0.15)
                elif mode == 'denoise':
                    processed = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
                else:
                    processed = img
                
                output = os.path.join(self.get_output_dir(), f"scanned_{int(datetime.now().timestamp())}.jpg")
                cv2.imwrite(output, processed)
                self.ids.status.text = f"Saved: {os.path.basename(output)}"
            else:
                img = Image.open(self.selected_image)
                if mode == 'grayscale':
                    img = img.convert('L')
                    img = img.convert('RGB')
                elif mode == 'blackwhite':
                    img = img.convert('L').point(lambda x: 255 if x > 127 else 0, '1')
                    img = img.convert('RGB')
                elif mode == 'enhance' or mode == 'denoise':
                    from PIL import ImageEnhance
                    enh = ImageEnhance.Contrast(img)
                    img = enh.enhance(1.5)
                
                output = os.path.join(self.get_output_dir(), f"scanned_{int(datetime.now().timestamp())}.jpg")
                img.save(output, 'JPEG')
                self.ids.status.text = f"Saved: {os.path.basename(output)}"
        except Exception as e:
            self.ids.status.text = f"Error: {str(e)}"
    
    def convert_to_pdf(self):
        if not self.selected_image:
            self.ids.status.text = "Select an image first"
            return
        
        try:
            img = Image.open(self.selected_image)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            output = os.path.join(self.get_output_dir(), f"scanned_{int(datetime.now().timestamp())}.pdf")
            img.save(output, 'PDF')
            self.ids.status.text = f"Saved: {os.path.basename(output)}"
        except Exception as e:
            self.ids.status.text = f"Error: {str(e)}"
    
    def get_output_dir(self):
        if ANDROID:
            return os.path.join(Environment.getExternalStorageDirectory().getAbsolutePath(), 'PDF Tools')
        return os.path.expanduser('~/Documents/PDF Tools')

class ResizeScreen(Screen):
    selected_pdf = StringProperty("")
    selected_image = StringProperty("")
    
    def select_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext == '.pdf':
            self.selected_pdf = path
            self.ids.file_name.text = os.path.basename(path)
        else:
            self.selected_image = path
            self.ids.file_name.text = os.path.basename(path)
        self.ids.status.text = ""
    
    def resize_pdf(self):
        if not self.selected_pdf:
            self.ids.status.text = "Select a PDF first"
            return
        
        try:
            scale = float(self.ids.scale.text) / 100.0
            
            reader = PdfReader(self.selected_pdf)
            writer = PdfWriter()
            
            for page in reader.pages:
                page.scale_to(page.mediabox.width * scale, page.mediabox.height * scale)
                writer.add_page(page)
            
            output = os.path.join(self.get_output_dir(), f"resized_{int(datetime.now().timestamp())}.pdf")
            with open(output, 'wb') as f:
                writer.write(f)
            self.ids.status.text = f"Saved: {os.path.basename(output)}"
        except Exception as e:
            self.ids.status.text = f"Error: {str(e)}"
    
    def resize_image(self):
        if not self.selected_image:
            self.ids.status.text = "Select an image first"
            return
        
        try:
            percent = int(self.ids.scale.text)
            img = Image.open(self.selected_image)
            new_w = img.width * percent // 100
            new_h = img.height * percent // 100
            resized = img.resize((new_w, new_h), Image.LANCZOS)
            
            output = os.path.join(self.get_output_dir(), f"resized_{int(datetime.now().timestamp())}.jpg")
            resized.save(output, img.format or 'JPEG')
            self.ids.status.text = f"Saved: {os.path.basename(output)}"
        except Exception as e:
            self.ids.status.text = f"Error: {str(e)}"
    
    def get_output_dir(self):
        if ANDROID:
            return os.path.join(Environment.getExternalStorageDirectory().getAbsolutePath(), 'PDF Tools')
        return os.path.expanduser('~/Documents/PDF Tools')

class FilePickerPopup(Popup):
    callback = ObjectProperty(None)
    
    def select(self, path):
        self.callback(path)
        self.dismiss()

class PDFApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(MergeScreen(name='merge'))
        sm.add_widget(SplitScreen(name='split'))
        sm.add_widget(ScannerScreen(name='scanner'))
        sm.add_widget(ResizeScreen(name='resize'))
        return sm
    
    def show_file_picker(self, screen, callback):
        def on_select(path):
            callback(path)
        
        content = BoxLayout(orientation='vertical')
        chooser = FileChooserIconView(path=os.path.expanduser('~'))
        content.add_widget(chooser)
        
        btns = BoxLayout(size_hint_y=None, height=50, spacing=10)
        select_btn = Button(text='Select')
        select_btn.bind(on_release=lambda x: on_select(chooser.selection[0]) if chooser.selection else None)
        cancel_btn = Button(text='Cancel')
        cancel_btn.bind(on_release=lambda x: popup.dismiss())
        btns.add_widget(select_btn)
        btns.add_widget(cancel_btn)
        content.add_widget(btns)
        
        popup = Popup(title='Select File', content=content, size_hint=(0.9, 0.9))
        popup.open()

kv = '''
<HomeScreen>:
    GridLayout:
        cols: 2
        padding: 20
        spacing: 20
        Button:
            text: 'PDF Merge'
            on_release: app.root.current = 'merge'
        Button:
            text: 'PDF Split'
            on_release: app.root.current = 'split'
        Button:
            text: 'PDF Scanner'
            on_release: app.root.current = 'scanner'
        Button:
            text: 'PDF Resize'
            on_release: app.root.current = 'resize'

<MergeScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        Label:
            text: 'PDF Merge'
            size_hint_y: None
            height: 50
        Button:
            text: 'Add PDF Files'
            on_release: app.show_file_picker(root, root.add_file)
        ScrollView:
            id: file_list
            size_hint_y: 0.5
        Button:
            text: 'Merge PDFs'
            on_release: root.merge_pdfs()
        Label:
            id: status
            text: ''
            size_hint_y: None
            height: 40
        Button:
            text: 'Back'
            on_release: app.root.current = 'home'

<SplitScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        Label:
            text: 'PDF Split'
            size_hint_y: None
            height: 50
        Button:
            text: 'Select PDF'
            on_release: app.show_file_picker(root, root.select_pdf)
        Label:
            id: pdf_name
            text: ''
        TextInput:
            id: page_range
            hint_text: 'e.g., 1-3,5,7-10'
            size_hint_y: None
            height: 40
        Button:
            text: 'Split All Pages'
            on_release: root.split_all()
        Button:
            text: 'Split Range'
            on_release: root.split_range()
        Label:
            id: status
            text: ''
            size_hint_y: None
            height: 40
        Button:
            text: 'Back'
            on_release: app.root.current = 'home'

<ScannerScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        Label:
            text: 'PDF Scanner'
            size_hint_y: None
            height: 50
        Button:
            text: 'Select Image'
            on_release: app.show_file_picker(root, root.select_image)
        Label:
            id: img_name
            text: ''
        GridLayout:
            cols: 2
            spacing: 10
            Button:
                text: 'Grayscale'
                on_release: root.process_image('grayscale')
            Button:
                text: 'B&W'
                on_release: root.process_image('blackwhite')
            Button:
                text: 'Enhance'
                on_release: root.process_image('enhance')
            Button:
                text: 'Denoise'
                on_release: root.process_image('denoise')
        Button:
            text: 'Convert to PDF'
            on_release: root.convert_to_pdf()
        Label:
            id: status
            text: ''
            size_hint_y: None
            height: 40
        Button:
            text: 'Back'
            on_release: app.root.current = 'home'

<ResizeScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        Label:
            text: 'PDF/Image Resize'
            size_hint_y: None
            height: 50
        Button:
            text: 'Select File (PDF or Image)'
            on_release: app.show_file_picker(root, root.select_file)
        Label:
            id: file_name
            text: ''
        TextInput:
            id: scale
            text: '100'
            hint_text: 'Scale % (e.g., 50)'
            input_filter: 'int'
            size_hint_y: None
            height: 40
        Button:
            text: 'Resize'
            on_release: root.resize_pdf() if root.selected_pdf else root.resize_image()
        Label:
            id: status
            text: ''
            size_hint_y: None
            height: 40
        Button:
            text: 'Back'
            on_release: app.root.current = 'home'
'''

if __name__ == '__main__':
    PDFApp().run()
