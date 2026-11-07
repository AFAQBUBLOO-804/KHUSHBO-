[app]
title = KHUSHBO
package.name = khushbo
package.domain = org.afaq
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy==2.3.0,pyjnius,android,plyer
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,CAMERA,CALL_PHONE,RECORD_AUDIO,FLASHLIGHT
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
