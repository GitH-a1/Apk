[app]

# (str) Title of your application
title = High Fidelity Stamp Engine

# (str) Package name
package.name = stampengine

# (str) Package domain (needed for android/ios packaging)
package.domain = org.enterprise.stamp

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,ttf

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# Note: opencv is handled via buildozer recipes on android
requirements = python3,kivy==2.3.0,opencv,numpy,pillow,android,pyjnius

# (str) Supported orientations (landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE, INTERNET

# (int) Target Android API level
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (int) Android NDK version
android.ndk = 25b

# (bool) Use --private data storage (1) or --dir public storage (0)
android.private_storage = 1

# (list) Android application meta-data
android.meta_data = android.max_aspect=2.1

# (list) Android architectures to build for (arm64-v8a for modern phones, armeabi-v7a for older)
android.archs = arm64-v8a, armeabi-v7a

# (bool) Enable AndroidX support
android.androidx = true

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = disable, 1 = enable)
warn_on_root = 1
