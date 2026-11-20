# Licensing of the cscosine ecosystem

The licensing policy of the cscosine repositories: our own code, the third-party libraries we build and ship, Qt
under the LGPL. Open points and their proposals: [plans/PLAN-licensing.md](plans/PLAN-licensing.md).

> General information, not legal advice. Before a customer delivery or a device, have the final setup checked by a
> lawyer.

## 1. Decisions

| # | Decision |
|---|---|
| D1 | Own code of every cscosine repository: **MIT** (free use, commercial included, closed source included; the copyright notice and the license text must stay in copies). |
| D2 | Credit: MIT keeps the notice in copies but does not require visible credit. Kept as is; `CITATION.cff` in every repository for citations. (Apache-2.0 + `NOTICE` was the alternative for a stronger, visible attribution plus a patent grant.) |
| D3 | Qt is used under **LGPLv3**, dynamically linked; users get the sources of the Qt built, its build pipeline (csqt6) and the instructions to replace it. |
| D4 | Commercial applications for customers are built on the MIT libraries. |

## 2. Own code (MIT)

- The license binds others, not the copyright holder: cscosine can use its own code in any product.
- Customer contracts: the libraries **stay cscosine's**, the customer gets a license to use them; only the code written
  for that customer is assigned, if the contract asks for it. Avoid "all code developed belongs to the customer".
- Warranty: MIT disclaims it for the libraries; any warranty for an application is a matter of the contract.
- Relicensing (e.g. to Apache-2.0) is possible for new versions as long as cscosine is the only author; published
  releases stay MIT for whoever has them.

## 3. Third-party libraries

| Library | License | In a delivery |
|---|---|---|
| fmt, cpptrace, libassert, magic_enum, NamedType, tclap, pipes | MIT | Include the notices |
| tl-expected, tl-optional | CC0 | Nothing required |
| Catch2 | BSL-1.0 | Tests only, normally not shipped |
| Eigen | MPL-2.0 | Fine as used; changes to Eigen's own files must be published |
| OpenCV 5 (+ contrib) | Apache-2.0 | License + its `NOTICE`; `OPENCV_ENABLE_NONFREE` off (patented algorithms); check the FFmpeg used by videoio (open point L3) |
| CUDA, cuDNN (csopencvcuda) | NVIDIA licenses | Only the runtime files NVIDIA lists as redistributable |
| Qt 6 | LGPLv3 (most modules); some modules GPLv3 only | See §5 |
| csCMake | MIT (own) | Build tool; nothing shipped |

The forks keep their upstream licenses; cscosine's changes in a fork follow the fork's license.

## 4. Qt under LGPLv3

Plan (D3): dynamic linking; the sources of the Qt built, the pipeline (csqt6) and the instructions to replace Qt
given to users. To be complete:

1. **GPL-only modules**: csqt6 builds the whole `qt5` superrepo minus `qtwebengine` (`-skip qtwebengine`), so
   GPL-only modules (e.g. Qt Charts, Qt Data Visualization / Qt Graphs, Qt Virtual Keyboard, Qt Quick 3D, Qt Wayland
   Compositor, Qt HTTP Server: to verify module by module) are probably in the bundles. Skip them, or at least check
   that no application links them; then a csqt6 check that fails if one is installed.
2. **Sources**: the exact Qt source archive attached to each csqt6 release (not only a link upstream), with the
   configure options (the csqt6 scripts); changes to Qt, if any, published under the LGPL.
3. **Pipeline access**: csqt6 (and every repository involved) public, or its scripts shipped with the sources.
4. **The application's license** (EULA) must not forbid modifying it and reverse engineering it to debug a replaced
   Qt (LGPLv3 §4).
5. **Notices**: the LGPL text and the licenses of the libraries inside Qt (zlib, libpng, freetype, harfbuzz, pcre2,
   …) in the About box / documentation and in the deployment folder.
6. **Replacement**: dynamic linking (`$ORIGIN` on Linux, `@loader_path` on macOS, DLLs next to the executable on
   Windows); no static linking (it would require shipping object files for relinking).
7. **macOS**: replacing a library breaks the signature; the user re-signs (say it in the instructions).

### Devices (LGPLv3 §4(e), GPLv3 §6 "Installation Information")

Applies to "User Products" (consumer devices) whose software can be updated. Any mechanism is fine (e.g. a USB stick
opening a service terminal that copies the user's Qt) when:

| Requirement | Compliant when | Not compliant when |
|---|---|---|
| The user installs **their own modified** Qt | any Qt build of the user is accepted | only Qt builds signed / approved by cscosine are accepted |
| Everything needed is given | the procedure is documented; any password, key, service code is given to the user | a secret key, a service password or a private tool is needed |
| The device **keeps working** | the application runs on the user's Qt | the device refuses to start, disables features or flags tampering *only because* Qt was replaced |
| A compatible Qt can be built | exact source, configure options, compiler, sysroot, ABI given (csqt6) | the user cannot build libraries the application loads |

Allowed: void warranty and support for a modified device; show a "modified software" notice; refuse network access
when the modification harms the network or breaks its rules; no updates for modified software.

Not applicable: devices that are not consumer products (professional / industrial, sold to businesses: the other LGPL
obligations remain); devices nobody can update (true ROM).

Secure boot: an unlock / developer mode, or user-enrolled keys; signature checks with cscosine's keys only are not
enough.

Embedded Linux image: every component has its own obligations (kernel GPLv2, glibc LGPL-2.1, BusyBox GPLv2, …):
a full license inventory is needed, not only Qt.
