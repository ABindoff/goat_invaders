[app]

# App identity
title           = Goat Invaders
package.name    = goatinvaders
package.domain  = github.bindoffa

# Source
source.dir      = .
source.include_exts = py

# Version
version         = 1.0

# Dependencies
requirements    = python3==3.11.0,sdl2,pygame

# Screen
orientation     = portrait
fullscreen      = 1

[buildozer]
log_level  = 2
warn_on_root = 1

[app:android]
android.permissions   = VIBRATE
android.api           = 33
android.minapi        = 21
android.ndk           = 25b
android.accept_sdk_license = True
android.bootstrap     = sdl2
android.archs         = arm64-v8a,armeabi-v7a
