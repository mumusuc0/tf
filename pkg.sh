#!/bin/env bash

function get_url() {
    name="$1"
    repo=$(apt show "$name" 2>/dev/null | grep -m1 "APT-Sources:" | awk '{print $2}')
    if [ -z "$repo" ]; then
        echo "错误: 无法找到包 '$name' 的仓库地址。请确认包名正确且已更新APT缓存。"
        exit 1
    fi
    path=$(apt-cache show "$name" 2>/dev/null | grep -m1 "Filename:" | awk '{print $2}')
    if [ -z "$path" ]; then
        echo "错误: 无法找到包 '$name' 的Filename信息。"
        exit 1
    fi
    echo "$repo/$path"
}

function get_deps() {
    local pkg="$1"
    if ! grep -q "^$pkg$" deps.txt; then
        echo "$pkg@$(get_url $pkg)" 
        echo "$pkg" >> deps.txt
        get_url $pkg >> packages.txt

        for dep in $(apt-cache show "$pkg" | grep -E "Depends:|Pre-Depends:" | cut -d':' -f2- | tr ',' '\n' | sed 's/ ([^)]*)//g; s/ | .*//g; s/^ *//; s/ *$//'); do
            get_deps "$dep"
        done
    fi
}

> deps.txt
> packages.txt
for pkg in $@; do
    get_deps $pkg
done
