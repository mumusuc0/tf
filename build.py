#!/usr/bin/env python3

import os
import shutil
import tomllib
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
FLUTTER = ROOT/'flutter'
SYSROOT = ROOT/'sysroot'
# SYSROOT = Path('/data/data/com.termux/files')


def target_triple(arch, api):
    api = str(api)
    if arch == 'arm':
        return 'arm-linux-androideabi' + api
    if arch == 'arm64':
        return 'aarch64-linux-android' + api
    if arch == 'x86':
        return 'i686-linux-android' + api
    if arch == 'x86_64':
        return 'x86_64-linux-android' + api
    if arch == 'riscv64':
        return 'riscv64-linux-android' + api
    raise ValueError(f"unsupport arch: {arch}")


def target_output(arch, runtime):
    return f"linux_{runtime}_{arch}"


def sysroot():
    cmd = ['bash', 'sysroot.sh', str(SYSROOT)]
    subprocess.run(cmd, check=True, stderr=True)


def clone(version):
    cmd = [
        'git', 'clone', '--depth=1',
        'https://github.com/flutter/flutter',
        '-b', version, str(FLUTTER)
    ]
    subprocess.run(cmd, check=True, stderr=True)


def sync(cfg):
    assert FLUTTER.is_dir(), f"flutter source dir not exist: {FLUTTER}"
    assert cfg.exists(), f".gclient not exist: {cfg}"

    os.chdir(FLUTTER)
    shutil.copy(cfg, '.gclient')
    cmd = [
        'gclient', 'sync', '-DR',
        '--with_branch_heads',
        '--with_tags',
        '--no-history',
    ]
    subprocess.run(cmd, check=True, stdout=True, stderr=True)


def config(arch, api, ndk, runtime, version):
    cmd = [
        'vpython3',
        'flutter/tools/gn',
        '--linux',
        '--linux-cpu', arch,
        '--embedder-for-target',
        '--target-triple', target_triple(arch, api),
        '--no-goma',
        '--no-backtrace',
        '--clang',
        '--no-enable-unittests',
        '--no-build-embedder-examples',
        '--no-prebuilt-dart-sdk',
        '--target-toolchain', str(ndk/'toolchains/llvm/prebuilt/linux-x86_64'),
        '--target-sysroot', str(SYSROOT),
        '--runtime-mode', runtime,
        '--gn-args', 'is_termux=true',
        '--gn-args', 'is_desktop_linux=false',
        '--gn-args', 'use_default_linux_sysroot=false',
        '--gn-args', 'dart_support_perfetto=false',
        '--gn-args', 'skia_support_perfetto=false',
        '--gn-args', 'custom_sysroot=""',
    ]
    subprocess.run(cmd, check=True, stderr=True)


def build(arch, runtime):
    cmd = [
        'ninja', '-C', target_output(arch, runtime),
        'flutter/build/archives:artifacts',
        'flutter/build/archives:dart_sdk_archive',
        'flutter/build/archives:flutter_patched_sdk',
        'flutter/shell/platform/linux:flutter_gtk',
        'flutter/tools/font_subset',
    ]
    subprocess.run(cmd, check=True, stdout=True, stderr=True)


if __name__ == '__main__':
    with open(ROOT/'build.toml', 'rb') as f:
        cfg = tomllib.load(f)
    mode = cfg.get('runtime', ['debug'])
    arch = cfg.get('arch', ['arm64'])
    api = cfg.get('api', 26)
    ver = cfg.get('tag')
    assert ver is not None, 'require flutter version'

    ndk = os.environ.get('ANDROID_NDK')
    assert ndk is not None, 'require ANDROID_NDK'

    ndk = Path(ndk).expanduser()
    assert ndk.is_dir(), f"invalid ndk path:\"{ndk}\""

    sysroot()
    clone(ver)
    sync(ROOT/'.gclient')
    os.chdir(FLUTTER/'engine/src')
    # os.chdir(ROOT/'src')
    for arch in arch:
        for mode in mode:
            config(arch, api, ndk, mode, ver)
            build(arch, mode)
