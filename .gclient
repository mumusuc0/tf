solutions = [
  {
    "managed": False,
    "name": ".",
    "url": "https://github.com/flutter/flutter.git",
    "deps_file": "DEPS",
    "safesync_url": "",
    "custom_deps": {
      "engine/src/flutter/buildtools/linux-x64/clang": None,
      "engine/src/fuchsia/sdk/linux": None,
      "engine/src/third_party/google_fonts_for_unit_tests": None,
    },
    "custom_vars" : {
      "setup_githooks" : False,
      "use_cipd_goma" : False,
      "download_emsdk" : False,
      "download_dart_sdk" : False,
      "download_linux_deps" : False,
      "download_fuchsia_sdk" : False,
      "download_android_deps" : False,
      "download_windows_deps" : False,
      "download_fuchsia_deps" : False,
    },
    "custom_hooks" : [
    ],
  },
]
