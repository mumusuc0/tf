#!/usr/bin/env python3

import os
import fire
import shutil
import tomllib
import subprocess
import sysroot as sys
from pathlib import Path

ROOTDIR = Path(__file__).parent
FLUTTER = ROOTDIR/'flutter'
SYSROOT = ROOTDIR/'sysroot'
SRCROOT = FLUTTER/'engine/src'
ARCHENM = ['arm', 'arm64', 'x86_64', 'x86']
MODEENM = ['debug', 'release', 'profile']


def _target_triple(arch, api):
    api = str(api)
    if arch == 'arm':
        return 'arm-linux-androideabi' + api
    if arch == 'arm64':
        return 'aarch64-linux-android' + api
    if arch == 'x86':
        return 'i686-linux-android' + api
    if arch == 'x86_64':
        return 'x86_64-linux-android' + api
    raise ValueError(f"unsupport arch: {arch}")


def _target_output(arch, runtime):
    return str(SRCROOT/'out'/f"linux_{runtime}_{arch}")


class Build:
    def sysroot(self):
        sys.main(SYSROOT)

    def clone(self, tag: str):
        cmd = [
            'git', 'clone', '--depth=1',
            'https://github.com/flutter/flutter',
            '-b', tag, str(FLUTTER)
        ]
        subprocess.run(cmd, check=True, stderr=True)

    def sync(self, cfg: str | Path = '.gclient'):
        assert FLUTTER.is_dir(), f"flutter source dir not exist: {FLUTTER}"
        assert cfg.exists(), f".gclient not exist: {cfg}"

        shutil.copy(cfg, FLUTTER/'.gclient')
        cmd = ['gclient', 'sync', '-DR', '--no-history']
        subprocess.run(cmd, cwd=FLUTTER, check=True, stdout=True, stderr=True)

    def config(self, arch: str, api: int, ndk: str | Path, runtime: str, sysroot: str = SYSROOT):
        assert arch in ARCHENM, f'unknown arch "{arch}"'
        assert api >= 26, f'require api level({api}) >= 26'
        assert os.path.isdir(ndk), f'require an exists ndk: {ndk}'
        assert runtime in MODEENM, f'unknown runtime "{runtime}"'
        assert os.path.isdir(sysroot), f'require an exists sysroot: {sysroot}'

        toolchain = os.path.join(ndk, 'toolchains/llvm/prebuilt/linux-x86_64')
        cmd = [
            'vpython3',
            'engine/src/flutter/tools/gn',
            '--linux',
            '--linux-cpu', arch,
            '--embedder-for-target',
            '--target-triple', _target_triple(arch, api),
            '--no-goma',
            '--no-backtrace',
            '--clang',
            '--no-enable-unittests',
            '--no-build-embedder-examples',
            '--no-prebuilt-dart-sdk',
            '--target-toolchain', str(toolchain),
            '--target-sysroot', str(sysroot),
            '--runtime-mode', runtime,
            '--gn-args', 'is_termux=true',
            '--gn-args', 'is_desktop_linux=false',
            '--gn-args', 'use_default_linux_sysroot=false',
            '--gn-args', 'dart_support_perfetto=false',
            '--gn-args', 'skia_support_perfetto=false',
            '--gn-args', 'custom_sysroot=""',
        ]
        subprocess.run(cmd, cwd=FLUTTER, check=True, stderr=True)

    def build(self, arch: str, runtime: str):
        cmd = [
            'ninja', '-j4', '-C', _target_output(arch, runtime),
            'flutter/build/archives:artifacts',
            'flutter/build/archives:dart_sdk_archive',
            'flutter/build/archives:flutter_patched_sdk',
            'flutter/shell/platform/linux:flutter_gtk',
            'flutter/tools/font_subset',
        ]
        subprocess.run(cmd, cwd=FLUTTER, check=True, stdout=True, stderr=True)

    def __call__(self):
        return 0
        with open(ROOTDIR/'build.toml', 'rb') as f:
            cfg = tomllib.load(f)
        mode = cfg.get('runtime', ['debug'])
        arch = cfg.get('arch', ['arm64'])
        api = cfg.get('api', 26)
        tag = cfg.get('tag')
        assert tag is not None, 'require flutter tag'

        ndk = os.environ.get('ANDROID_NDK')
        assert ndk is not None, 'require ANDROID_NDK'

        ndk = Path(ndk).expanduser()
        assert ndk.is_dir(), f"invalid ndk path:\"{ndk}\""

        self.sysroot()
        self.clone(tag)
        self.sync(ROOTDIR/'.gclient')

        for arch in arch:
            for mode in mode:
                self.config(arch, api, ndk, mode)
                self.build(arch, mode)


if __name__ == '__main__':
    fire.Fire(Build)
