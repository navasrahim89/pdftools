[app]

title = PDF Tools
package.name = pdftools
package.domain = org.pdftools

source.dir = .
source.include_exts = py,png,jpg,kv,ttf

version = 1.0

requirements = python3,kivy,pillow,pypdf

orientation = portrait

fullscreen = 0

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 31
android.minapi = 21

android.archs = arm64-v8a,armeabi-v7a

android.allow_repackaged_sdk = 0
android.accept_sdk_license = 1
