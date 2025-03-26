#!/usr/bin/env python3

import os
import pathlib
import asyncio
import aiohttp
import tempfile
import subprocess
import urllib.parse


async def _download(sess, url, dst):
    path = urllib.parse.urlparse(url).path
    name = pathlib.Path(path).name
    path = pathlib.Path(dst, name)
    try:
        async with sess.get(url) as resp:
            resp.raise_for_status()
            with open(path, 'wb') as f:
                async for chunk in resp.content.iter_chunked(8192):
                    f.write(chunk)
            print(f"✓ 成功下载 {name}")
            return path
    except Exception:
        print(f"✗ 下载失败 {name}")
        raise


async def _spawn(tasks):
    if not tasks:
        return []
    tasks = [asyncio.create_task(t) for t in tasks]
    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_EXCEPTION)
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)
    return [r.result() for r in done]


async def _download_packages(packages, output):
    with open(packages, 'r') as f:
        urls = [url.strip() for url in f.readlines() if url.strip()]

    timeout = aiohttp.ClientTimeout(total=500)
    async with aiohttp.ClientSession(timeout=timeout) as sess:
        return await _spawn([_download(sess, url, output) for url in urls])


def _extract(pkg, out):
    subprocess.run(['dpkg', '-x', str(pkg), str(out)], check=True, stderr=True)
    print(f"✓ 成功安装 {pkg.name}")


async def _work(out, pkg):
    with tempfile.TemporaryDirectory() as tmp:
        for pkg in await _download_packages(pkg, tmp):
            _extract(pkg, out)
    usr = out/'usr'
    dst = 'data/data/com.termux/files/usr'
    try:
        usr.symlink_to(dst, True)
    except FileExistsError:
        if not usr.samefile(out/dst):
            raise
    pthread = out/'usr/lib/libpthread.so'
    pthread.write_bytes(b'INPUT(-lc)')


def main(out, pkg='packages.txt'):
    out = pathlib.Path(out).expanduser()
    assert out.is_dir(), f'"{out}" is not an existing dir'

    asyncio.run(_work(out, pkg))


if __name__ == '__main__':
    assert len(os.sys.argv) > 1, 'require sysroot dir'

    main(out=os.sys.argv[1])
