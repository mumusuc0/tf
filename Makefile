.PHONY: sync config build release test publish

TAG      = $(shell $(GIT) -C $(FLUTTER) describe --tags)
ARGS     =
ROOT     = $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
RUNTIME  = debug

ifeq ($(filter "$(RUNTIME)", "debug" "profile" "release"),)
$(error Invalid runtime mode `$(RUNTIME)`, possible values are [debug|profile|release])
endif

#ifeq ($(shell command -v vpython3),)
#$(error env `PATH` not set. Consider running `export PATH=$$(pwd):$$PATH`)
#endif

override CONFIGURE += 						\
	--target-os linux 						\
	--linux-cpu arm64 						\
	--embedder-for-target 					\
	--enable-fontconfig 					\
	--target-triple aarch64-linux-android34 	\
	--clang --no-goma --no-backtrace 		\
	--no-enable-unittests 					\
	--no-prebuilt-dart-sdk 					\
	--no-build-embedder-examples 			\
	--target-toolchain $(ROOT)toolchain 			\
	--target-sysroot $(ROOT)sysroot 			\
	--no-lto 			\
	--runtime-mode $(RUNTIME)

override GN_ARGS += 							\
	toolchain_prefix="aarch64-linux-android-" 	\
	use_default_linux_sysroot=false				\
	is_desktop_linux=false 						\
	dart_platform_sdk=false \
        test_enable_gl=false \
        test_enable_vulkan=false \
        test_enable_software=false

OUTPUT  = $(ROOT)src/out/linux_$(RUNTIME)_arm64
FLUTTER = $(ROOT)flutter/engine/src/flutter

config:
	$(FLUTTER)/tools/gn $(CONFIGURE) --gn-args '$(GN_ARGS)' $(ARGS)
