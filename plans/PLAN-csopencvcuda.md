# PLAN: csopencvcuda, back into the chain and beyond

Date: 2026-11-22 · Status: **low priority** (csopencvcuda is unused for now): C0 rc1 built 2026-11-22 (run 45030290737), its result to
check when convenient (2026-11-23 or later); C1 onwards when a consumer needs it · Org plan: `PLAN-cscosine-org.md` §8 ("Next")

csopencvcuda builds OpenCV with CUDA / cuDNN for Linux x64 (Ubuntu 22.04 / 24.04, GCC and Clang) and Windows x64
(MSVC 2022). It was set aside during stable-dev and the finals round (old csCMake / third_party_base_libs pins, no
template, OpenCV 5.0.0). C0 is the minimum to put it level with csopencvcpu; C1 onwards is the real work, in order.

## Measured (tag build `v5.0.1-rc3`, 2026-11-12, run 43262753895)

| Job | CUDA install | cuDNN install | OpenCV build (debug + release) | Total |
|---|---|---|---|---|
| Ubuntu 22.04 GCC / Clang | 7 m | 2 m | 130 / 138 m | ~2 h 30 |
| Ubuntu 24.04 GCC / Clang | 4 m | < 2 m | 99 / 138 m | ~1 h 50 / 2 h 30 |
| Windows MSVC 2022 | 8 m | 3 m | 221 m | ~4 h 10 (the critical path) |

So the toolkit download is slow but not where the time goes: **~90 % is the compile** (nvcc, 4 architectures × 2
configs). Both are worth fixing, the compile first.

## Steps

| # | Step | Content | Status |
|---|---|---|---|
| C0 | **Level with csopencvcpu** | OpenCV 5.1.0 (the forks' `cuda` branch: upstream 5.1.0 + the common stack + the CUDA setup commit, prepared 2026-11-20), fork tags `v5.1.0-cuda.1`; cs-project-template v1.1.4 (vendored `cmake/FindCUDA*` excluded from the hooks); csCMake 1.0.0, third_party_base_libs v0.1.0 (eigen3 5.0.1), workflow regenerated with csorchestrator v0.1.0; `v5.1.0-cuda.1-rc1` (the test build), then `v5.1.0-cuda.1` + `stable`. Same matrix, same CUDA install | doing: fork tags `v5.1.0-cuda.1` pushed, csopencvcuda PR #1 merged, `v5.1.0-cuda.1-rc1` building (2026-11-22, run 45030290737). **Left:** green → tag `v5.1.0-cuda.1` on the same commit, `stable` to it, ECOSYSTEM.md no longer flags it; red → fix in the fork's `cuda` (or `main`, then rebase `cuda`), tag `v5.1.0-cuda.2`, pin it, `-rc2` (`cuda.1` stays as "never released" in the fork CHANGELOG) |
| C1 | **Compile time** | (a) `CUDA_ARCH_BIN`: drop `87` (Jetson Orin only, useless on x64: it belongs to C4) → 75;86;89 on both systems, add `120` (Blackwell, RTX 50) + PTX of the newest for forward compatibility; decide the supported GPUs explicitly. (b) Debug + Release both compile every kernel: build the CUDA debug config with release device code, or ship Release only for CUDA (decide). (c) Compiler cache (sccache/ccache with `actions/cache`, a csorchestrator step) for the weekly runs. Target: Windows < 2 h | todo |
| C2 | **Getting CUDA** | Today: the local-repo `.deb` (~3 GB) + the whole `cuda-toolkit` meta-package; on Windows the full installer. Options: (a) the network repo and only the components OpenCV needs (`cuda-nvcc`, `cuda-cudart-dev`, `libcublas-dev`, `libcufft-dev`, `libnpp-dev`, `cuda-nvrtc-dev`, …); Windows: the network installer with sub-package selection (`-s nvcc_13.3 cudart_13.3 …`); (b) the job in a container, `nvidia/cuda:<ver>-cudnn-devel-ubuntu<ver>` (CUDA + cuDNN preinstalled, pulled from a registry, cacheable); (c) `actions/cache` of the install dir. **Proposal: (b) on Linux** (same mechanism C4 needs for Jetson, and the image *is* the documented toolchain for consumers), **(a) on Windows**. (b) needs csorchestrator: a job `container:` per context | todo |
| C3 | **Matrix** | Ubuntu 26.04 (when NVIDIA ships CUDA for it), VS 2026 (the cuDNN download failed on `windows-2025-vs2026`), Windows cuDNN: the presets point at the `12.9` layout with CUDA 13.3, check that cuDNN 9.x for CUDA 13 is used; Linux arm64 SBSA (Grace / DGX-class servers, GitHub `ubuntu-24.04-arm` runners) as a step towards C4 | todo |
| C4 | **Jetson (arm64, JetPack)** | Build inside NVIDIA's JetPack containers (`nvcr.io/nvidia/l4t-jetpack:<r36.x>` for JetPack 6 = Ubuntu 22.04, CUDA 12.x, Orin `87`; JetPack 7 = Ubuntu 24.04, CUDA 13, Thor: check the versions when starting) on GitHub's arm64 runners (free for public repositories; compiling needs no GPU). The CUDA / cuDNN versions become **per platform** (JetPack fixes them), not one constant in `csopencvcuda_config.py`. The context: `arm64` + an `architecture_variant` per JetPack (e.g. `jetpack6`), so consumers on a Jetson map to it (`opencv_mapping`). Needs csorchestrator: container jobs (C2), arm64 runner per variant, variant in the archive names. Fork: the `cuda` setup gets a Jetson preset (arch list, paths). Alternative if containers on hosted runners are not enough: cross-compile on x64 with the JetPack cross toolchain (harder, last resort) | todo |
| C5 | **Tests** | A GPU-less smoke test of every archive (`find_package(OpenCV)` + link a `cv::cuda` call; csorchestrator smoke runs); a GPU run is out of reach on hosted runners (note it) | todo |
| C6 | **Local build / consumers** | The Ubuntu 22.04 local configure picks a stale `/usr/bin/nvcc` (README caution): set `CUDAToolkit_ROOT` / `CMAKE_CUDA_COMPILER` from the environment in the preset; with C2 (b) the container is the local recipe too. The shipped `cmake/FindCUDA.cmake` (removed from CMake, CMP0146): move consumers to `CUDAToolkit` when OpenCV allows | todo |

## Order and dependencies

C0 now (it only rejoins the chain). Then C1 (fork + recipe only, cuts every later build) and C2 (a) on Windows. C2 (b),
C3 arm64 and C4 wait for the csorchestrator features (container jobs, arm64 variants): record them in
`PLAN-csorchestrator-architecture.md` when C1 is done, ideally as part of R4 (builders), not as patches to the
current generator. The weekly slot (Sun 14:30 CET, ~4 h today) stays before the queue at 20:00; with C4 the run
grows by the Jetson jobs (arm64 runners do not count against the macOS limit).
