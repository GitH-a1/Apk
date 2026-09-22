[app]

# (str) Title of your application
title = Stamp Extractor Pro

# (str) Package name
package.name = stampextractorpro

# (str) Package domain (needed for android/ios packaging)
package.domain = org.stamp.extractor

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,jpeg,kv,atlas

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# مهم جداً: استخدام opencv بدلاً من opencv-python لمنع خطأ البناء
requirements = python3,kivy,numpy,opencv

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 21

# (list) The Android archs to build for (تغطي 99% من الهواتف الحديثة والقديمة)
android.archs = arm64-v8a, armeabi-v7a

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# (bool) Allow backup
android.allow_backup = True


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug with command output)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
