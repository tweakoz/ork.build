# Windows builds through a WSL obt.net node

Use this guide for native Windows work controlled from another machine through obt.net. The worker
runs in a WSL OBT environment; jobs explicitly enter PowerShell, CMD, or MSYS2 to run Windows tools.
WSL is the orchestration layer, not the target ABI. Do not launch a second native Windows node merely
to reach native compilers.

## Execution boundaries

```text
controller CLI → obt.net → WSL node / Linux process environment
                              ├─ powershell.exe → native Windows commands
                              ├─ cmd.exe → vcvars64.bat → MSVC or clang-cl
                              └─ MSYS2 bash.exe → CLANG64/UCRT64 tools → native Windows output
```

Use a literal node name, such as `WINBUILD`, for Windows-specific work. A WSL worker reports Linux;
`@linux` does not distinguish native Linux workers from WSL hosts.

| Consumer | Example path | Python/tool identity |
|---|---|---|
| Controller | `/tmp/native-build-inputs/build.ps1` | Controller's OBT venv |
| WSL node, remote cwd, sync destination | `/mnt/c/Users/dev/projects/build-area` | Linux OBT venv |
| PowerShell / CMD / native CMake | `C:/Users/dev/projects/build-area` | Windows executable |
| MSYS2 Bash | `/c/Users/dev/projects/build-area` | Selected MSYS2 environment |

`/mnt/c/...` and `/c/...` are different POSIX mount conventions. Do not pass them interchangeably.
Use `wslpath -w` in WSL and `cygpath -w` in MSYS2 when conversion is needed. Native tools generally
accept `C:/...`; CMD built-ins and batch files may need backslashes. Quote paths containing spaces.
Do not replace Windows paths mechanically inside scripts that contain escapes or regexes.

## Establish the node and route

Before starting anything, inspect the registered fleet, existing jobs, and managed tunnel:

```bash
obt.net.py list
obt.net.py connection-status WINBUILD
obt.net.py jobs WINBUILD
```

The controller listens on port 7461 by default. `localhost` in WSL is not the controller on another
machine. Supply a controller address reachable from WSL, and check the actual current interface/IP.
A remembered wired bind address can disappear after unplugging a cable or changing networks.

A registered node may still be unreachable if it advertises its WSL NAT address. For a WSL node using
the managed SSH route, configure fixed ports and advertise loopback for the local forwards:

```bash
# Run in WSL, inside the intended OBT environment.
obt.net.node.py --name WINBUILD --controller tcp://CONTROLLER_IP:7461 \
  --root /mnt/c/Users/dev/projects/build-area --advertise-ip 127.0.0.1 \
  --control-port 63101 --pub-port 63102 --fetch-port 63103
```

The loopback advertisement is specific to the managed-tunnel topology, not a universal node setting.
On the controller, the SSH host alias must reach the WSL SSH server:

```bash
obt.net.py connect WINBUILD --ssh-target windows-wsl
obt.net.py connection-status WINBUILD
obt.net.py run WINBUILD -- /usr/bin/uname -s
```

`connect` owns the SSH forwards and their health record. Use it instead of manually accumulating
three tunnels. Specify `--bind-address` only when that local address currently exists. For multiple
WSL nodes on one controller, allocate distinct port triplets and pass matching values to node and
`connect`; defaults cannot all bind the same local ports.

Nodes must run inside `obt.env.launch.py` with the intended staging directory. For an authorized
headless worker, screen/tmux can keep the process and logs independent of an SSH session. Example
launched from a WSL shell, with a complete OBT installation in `~/.venv`:

```bash
screen -L -Logfile "$HOME/obt-node-WINBUILD.log" -dmS obt-node-WINBUILD \
  "$HOME/.venv/bin/obt.env.launch.py" \
  --stagedir /mnt/c/Users/dev/projects/build-area \
  --command 'obt.net.node.py --name WINBUILD --controller tcp://CONTROLLER_IP:7461 --root /mnt/c/Users/dev/projects/build-area --advertise-ip 127.0.0.1 --control-port 63101 --pub-port 63102 --fetch-port 63103'
```

Follow node ownership rules; do not start a duplicate worker or restart someone else's lane. Check
`screen -ls`/`tmux ls`, logs, and port ownership first. After an OBT upgrade, restart the owned node
so it imports the updated implementation. Prefer one complete matching venv for launcher and node.
If diagnosing mixed versions, inspect the actual Python executable, imported `obt` location, CLI flags,
`VIRTUAL_ENV`, PATH and PYTHONPATH. A launcher can inject an older PYTHONPATH even when a newer Python
is selected. Clear that inherited path only when deliberately selecting a verified complete install;
an arbitrary interpreter swap does not supply missing OBT launcher data or staging tools.

After a Windows reboot, WSL and its SSH service may need starting again. A systemd service inside WSL
does not, by itself, establish Windows-side VM startup/keepalive. Screen also does not survive shutdown.
Read the host's existing startup configuration before changing it.

## Short native probes versus tracked jobs

The client offers two SSH-backed convenience verbs:

```bash
obt.net.py wslPS WINBUILD -- '$PSVersionTable.PSVersion.ToString()'
obt.net.py wslCMD WINBUILD -- ver
```

These require a matching entry in OBT's `sshhosts` mapping; an OpenSSH alias alone is not that entry.
`connect --ssh-target` selects the tunnel target, not necessarily this separate wrapper mapping.
`wslPS` invokes Windows PowerShell with `-NoProfile -NonInteractive -Command`.
`wslCMD` invokes native `cmd.exe /d /s /c`. Both use SSH internally and can operate without worker
callback connectivity. This is expected routing, not a reason to bypass OBT with ad hoc SSH commands.
Their `--cwd` is a **WSL path** (default `/mnt/c`, avoiding a Windows UNC working directory).
Their timeout defaults to unlimited; `--out` is unsupported. They are synchronous, not job submission.

For long work use `submit` with the actual Windows executable and an honest timeout. Do not put a
synchronous `wslPS` invocation inside `submit`. The job should own the foreground compiler process:

```bash
obt.net.py submit WINBUILD --timeout 21600 \
  --cwd /mnt/c/Users/dev/projects/build-area -- \
  /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe \
  -NoProfile -NonInteractive -Command \
  '& "C:/Users/dev/projects/build-area/inputs/build.ps1"'
```

Use a signed/approved script when required by host policy. Where local policy permits interactive
script blocks but rejects `-File`, an explicitly reviewed helper can be evaluated with normal
`-Command` semantics:

```bash
obt.net.py submit WINBUILD --timeout 21600 \
  --cwd /mnt/c/Users/dev/projects/build-area -- \
  /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe \
  -NoProfile -NonInteractive -Command \
  '& ([scriptblock]::Create([IO.File]::ReadAllText("C:/Users/dev/projects/build-area/inputs/build.ps1")))'
```

This form does not provide file-backed `$PSScriptRoot`; pass paths explicitly or put them in the
helper. Do not change execution policy, use `-ExecutionPolicy Bypass`, or weaken organizational
controls to make a build run. If policy disallows the operation, report the actual policy boundary.

Poll the returned job ID, not an old PID:

```bash
obt.net.py status WINBUILD j-XXXX
obt.net.py log WINBUILD j-XXXX --stderr --tail 40
obt.net.py log WINBUILD j-XXXX --tail 40 --grep FAILED
```

Keep success output to the verdict; fetch bounded diagnostics on failure. `--grep` is a substring
filter, not a regular expression. One compiler/generator line can be huge even with `--tail 1`.
A successful submission means accepted work, not successful compilation; require terminal rc and
expected artifacts. Preserve configure/build logs and a small manifest with source revision/delta,
tool versions, configuration, output paths and hashes.

Use `cancel` only on your job. WSL process-group termination is not proof that every interop-launched
Windows descendant exited. Verify the native process tree before relaunching, replacing artifacts,
or removing a lock. Never kill every `ninja.exe`, `python.exe`, or compiler on a shared machine.

## Quote once per boundary; stage complex commands

A controller shell, remote WSL shell, PowerShell/CMD, and MSYS2 can each interpret a command. Minimize
that chain: keep remote logic in a staged `.ps1`, `.cmd`, or `.sh` and invoke it with explicit paths.

- In Bash, single-quote the PowerShell command so `$env:PATH`, `$LASTEXITCODE`, and `$variables` reach
  PowerShell unchanged. Double quotes, backticks and `$()` can execute or expand on the controller.
- `JSON.stringify()` is not shell escaping. Do not interpolate serialized text into shell code.
- Do not pipe native output through a second shell unless the pipeline's exit status is handled.
- `--env` on a WSL command sets the Linux process environment. Set native PATH/SDK variables inside
  the native helper, or deliberately configure WSLENV; do not assume arbitrary Linux variables or
  POSIX PATH entries become a correct Windows build environment.
- PowerShell 5.1 does not turn every native nonzero exit into an exception. Check `$LASTEXITCODE`
  immediately after each external tool and `exit` with that code. `$ErrorActionPreference = 'Stop'`
  handles PowerShell errors, not that native-code rule.
- Read plain file strings with `[IO.File]::ReadAllText` when serializing diagnostics. PowerShell
  provider-decorated `Get-Content` objects can balloon nested JSON with irrelevant metadata.

A remote program may intentionally return 255. Treat it as an SSH failure only with transport/error
context; the WSL wrapper distinguishes recognized SSH diagnostics from a native program's exit code.

## Select one native toolchain per build tree

### MSVC or clang-cl: initialize the Windows SDK environment

Discover Build Tools with the installed `vswhere.exe` and verify `vcvars64.bat`, compiler, CMake and
Ninja paths. Do not assume a bootstrap installer finishing means its elevated child has finished.
MSVC and clang-cl target the Microsoft ABI, but they are distinct compiler choices. Supply the one
required by the project and use a separate build directory when changing compiler/ABI/configuration.

A staged `build-msvc.cmd` can contain the following, with the verified tool locations substituted:

```bat
@echo off
setlocal
call "C:\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
set "PATH=C:\Tools\CMake\bin;C:\Tools\Ninja;%PATH%"
cd /d "C:\Users\dev\projects\build-area"
if errorlevel 1 exit /b %errorlevel%
cmake.exe -S source -B build-msvc -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=cl.exe -DCMAKE_CXX_COMPILER=cl.exe
if errorlevel 1 exit /b %errorlevel%
cmake.exe --build build-msvc --parallel 8
exit /b %errorlevel%
```

For clang-cl, select its verified executable for both compiler variables. A PowerShell helper can run
the batch file without trying to import the batch environment back into PowerShell:

```powershell
$ErrorActionPreference = 'Stop'
& $env:ComSpec /d /c 'C:\Users\dev\projects\build-area\inputs\build-msvc.cmd'
exit $LASTEXITCODE
```

`vcvars64.bat` and the compiler must run in the same CMD environment. Calling the batch file in one
child and compiling in another loses the environment. Avoid `%PATH%` expansion in a compound
`cmd /c` line before `vcvars` executes; a batch file with separate lines avoids this. If compound CMD
logic is unavoidable, use delayed expansion correctly and account for literal `!` in paths.

### MSYS2: choose CLANG64 or UCRT64 explicitly

MSYS2 Bash is a shell; it does not make `/usr/bin/gcc`, Linux GCC, CLANG64 and UCRT64 interchangeable.
CLANG64 uses LLVM/libc++; UCRT64 normally uses GCC/libstdc++. Even when both use UCRT, their C++ ABIs
and library choices are not interchangeable with MSVC. Verify the selected executables and target.
Do not configure a native project with WSL `/usr/bin/cmake` and then expect a native Windows build.

For example, stage `build-clang64.sh` with LF endings:

```bash
set -euo pipefail
export PATH=/clang64/bin:/usr/bin
cd /c/Users/dev/projects/build-area
/clang64/bin/cmake.exe -S source -B build-clang64 -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=/clang64/bin/clang.exe \
  -DCMAKE_CXX_COMPILER=/clang64/bin/clang++.exe
/clang64/bin/cmake.exe --build build-clang64 --parallel 8
```

Invoke through the native PowerShell helper; MSYS2's shell receives its own path syntax:

```powershell
$ErrorActionPreference = 'Stop'
$env:MSYSTEM = 'CLANG64'
& 'C:/msys64/usr/bin/bash.exe' --noprofile --norc '/c/Users/dev/projects/build-area/inputs/build-clang64.sh'
exit $LASTEXITCODE
```

Set UCRT64 and `/ucrt64/bin` instead only for a UCRT64 project/build tree. A project may additionally
need selected staging tools on PATH; add verified directories explicitly. MSYS2 translates some
POSIX-looking arguments when launching native executables. If a Windows switch or literal string is
mangled, examine actual argv and use narrowly scoped `MSYS2_ARG_CONV_EXCL` only for the affected
invocation. Do not globally disable conversion as a first response.

For Windows APIs use native Windows Python (for example `C:/msys64/clang64/bin/python.exe`, after
checking its installed name/version). Linux Python cannot load a Windows DLL via ctypes. The OBT
node and controller still use their own Linux/controller venvs; do not replace their interpreters.

### CLANG64 startup rejected by Windows Code Integrity

Observed September 2026: MSYS2 Clang 22.1.8 failed before compiling, including on `--version`.
MSYS2 Bash surfaced exit 127 with little diagnostic output. Direct native execution returned
`0xC0E90002` (signed decimal `-1058471934`), and CodeIntegrity/Operational events 3077/3033
identified `C:/msys64/clang64/bin/libclang-cpp.dll`. The DLL matched its cached MSYS2 package
byte-for-byte. Reproducing with the earlier launch environment and an interactive normal-user
token ruled out those particular launch differences; another native compiler compiled and ran code.

Establish that evidence before diagnosing a policy problem. Exit 127 alone also means a missing
command or dependency. Capture the native exit status, check DLL dependencies and package hashes,
and correlate the actual process/path/time with Code Integrity events. A compiler that worked
previously can still encounter a changed policy or reputation decision; that history does not
identify what changed.

Read-only `citool.exe -lp` identifies active policies. In the observed case,
`VerifiedAndReputableDesktop` was enforced (Smart App Control), with policy GUID
`{0283AC0F-FFF1-49AE-ADA1-8A933130CAD6}`. Earlier activation records already contained that policy,
and Microsoft's `MpCmdRun.exe -ValidateMapsConnection` diagnostic passed. Neither observation
explained why the verdict changed. Do not claim that all Windows compilation is broken or that
reinstalling identical package bytes will repair a reputation rejection.

A validated recovery used the **official LLVM 22.1.8 Windows distribution in an isolated directory**
while retaining the installed CLANG64 MinGW target, headers, UCRT, libraries and compiler runtime.
Download from the official LLVM release, verify the published archive hash or release attestation,
and retain provenance. Preserve the MSYS2 installation. An official release is not a guarantee that
local policy will allow it: verify startup before proceeding. This is a replacement compiler route,
not a repair of the rejected DLL or proof of the cause.

For a matching LLVM 22 / CLANG64 installation, a native compiler invocation from MSYS2 Bash is:

```bash
toolchain=/c/Users/dev/projects/build-area/toolchains/llvm-22.1.8
"$toolchain/bin/clang.exe" --driver-mode=g++ \
  --target=x86_64-w64-windows-gnu --sysroot=C:/msys64/clang64 \
  -resource-dir C:/msys64/clang64/lib/clang/22 \
  -stdlib=libc++ -fuse-ld=lld --rtlib=compiler-rt --unwindlib=libunwind \
  -std=c++23 probe.cpp -o probe.exe
PATH="$toolchain/bin:/clang64/bin:/usr/bin" ./probe.exe
```

Use the matching official linker beside the compiler. For C, omit `--driver-mode=g++`,
`-stdlib=libc++` and the C++ language flag. Verify paths and versions instead of copying the
example blindly. The compiler's default `--version` target may say MSVC; the explicit target
selects MinGW for compilation. Do not invoke clang-cl or switch to MSVC ABI while reusing
CLANG64 C++ libraries.

Test C++ features and runtime behavior required by the consumer, not merely `--version`.
The observed recovery passed C++23 compilation/linking, libc++ containers/formatting, exception
unwinding, a Windows API call, and execution. PE imports confirmed `libc++.dll` and UCRT
`api-ms-win-crt-*` DLLs. An installed Clang 19 also ran but was below libc++22's supported
compiler baseline and was rejected as the production recovery.

Then rebuild the real targets with the explicit compiler/target flags and run their native loader
checks. For recursive make, command-line `CC`/`CXX` overrides survive ordinary makefile assignments;
environment overrides may not. Preserve the consumer's existing flags, including any intentional
`-nostdlib++` policy; a diagnostic using libc++ does not authorize adding it to a runtime-free target.
Use an isolated build tree to avoid mixing objects or PCH files from different compilers.

No security settings, exclusions, trusted certificates, or binary identities were changed for this
recovery. Record separately whether the replacement build works and whether the original compiler
still fails. Do not report the original policy issue as fixed merely because a replacement works.

### Dependencies and ABI boundaries

Do not expose the entire MSYS2 include prefix to clang-cl: MinGW `windows.h`, CRT, varargs, or STL
headers can shadow the Windows SDK/MSVC headers. Stage only required public dependency headers and
narrow imported CMake target include directories. Avoid static MinGW archives in MSVC-ABI components;
a C-compatible DLL import library may work with the selected linker, but validate exports, calling
conventions and ownership, and stage its transitive DLL dependencies.

Across compiler/runtime boundaries, use a defined C ABI and opaque handles or fixed-width data.
Allocate and free memory in the same owning module; do not pass STL containers, exceptions, CRT FILE
objects, or allocator ownership across incompatible runtimes. Test with a host built using the other
intended compiler, not just a same-toolchain smoke test.

## Source transfer, filesystem behavior, and artifacts

Align a node checkout with `gitsync` before modifying/building it; preserve tracked dirt and divergence.
Use `gitbootstrap` for a new clean named-branch source. If these cannot handle a large NTFS checkout,
first establish the actual repository/base/delta, then use an explicitly verified bundle/patch or
manifest transfer. Never reset or silently force through local changes merely to satisfy tooling.

Keep small helpers in a dedicated transfer directory:

```bash
obt.net.py push WINBUILD /tmp/native-build-inputs/build.ps1 \
  /mnt/c/Users/dev/projects/build-area/inputs/build.ps1
```

Current node-routed `push` uses tree sync against the destination's **parent directory**; `pull` also
manifests the parent. Putting a helper directly beside a giant source tree can make a tiny transfer
scan that whole tree. Use `inputs/` and a separate small `results/`. For directory sync, inspect
`--dry` first and keep deletion opt-in. Use job artifacts/content hashes for selected outputs; do not
transfer build directories blindly. `--cwd`, `--out` and artifact collection are interpreted on the
WSL worker, so describe files with WSL paths/globs even when a Windows tool created them.

Large Git operations on NTFS can be much faster with native Windows Git than WSL Git. Discover its
path explicitly; being absent from PowerShell PATH does not prove it is uninstalled. Configure
`core.longpaths` when needed. Treat autocrlf, filemode and symlink settings as repository contracts;
compare bytes rather than DrvFS executable-bit noise. Do not normalize arbitrary binary files.
Check that LFS content is materialized, not pointer text, and that a partial-clone bundle contains
needed objects. A shared clone's alternates retain a dependency on its source object store.

Windows symlink creation may be unavailable. Prefer project-supported forwarding headers or explicit
copies with correct generated-file dependencies; do not change Developer Mode/security policy merely
to make symlinks succeed. Preserve canonical header identity when `#pragma once` matters.

Windows command-length limits differ by launcher: CMD is substantially tighter than direct process
creation (roughly 8 KiB versus 32K UTF-16 characters). Use response files where supported, with the
**callee's** documented quoting/encoding grammar. Test paths with spaces/Unicode and long argument
lists. A response file is not universally shell syntax and does not automatically fix every launcher.

## Build installers and hand the UI to the user

Packaging is a separate build target. Read the project's packaging contract and use its existing
entry point. Discover the installed packaging tool explicitly (for example, Inno Setup's ISCC.exe);
it may live under an earlier build's tools directory rather than Program Files or PATH. Record its
version and actual path. Keep project-specific commands, package names and install options in the
project's own documentation.

1. Verify which source delta, configuration, application binaries and dependency SDK the package
   will contain. An installer script may use a different default SDK directory than the compiler.
   Pass explicit paths; if a temporary helper needs adapting, retain its original hash and exact
   adaptations. Do not silently relabel stale binaries as a new build.
2. Stage into a new output directory using the project's dependency, architecture, asset and
   provenance checks. Keep test profiles, captures, logs and source inventories outside the payload.
   Include required subprocesses, plugins, resources, redistributables and license notices. Check
   recursive DLL imports and run the staged application with a controlled native PATH when possible.
   Sparse source checkouts may omit tracked license files: restore matching notices from the verified
   source revision instead of disabling notice checks. Verify transferred bytes; preserve existing
   files when the only difference is confirmed CRLF/LF text representation.
3. Submit the packaging command as a tracked obt.net job through native PowerShell/CMD/MSYS2, with
   an appropriate timeout. Preserve native exit status. Require terminal success, the expected
   installer file, its size and SHA-256; a successful submission is not a completed installer.
4. With user authorization, launch that exact artifact in the logged-in user's interactive Windows
   session. A WSL/SSH-launched process need not appear on the desktop. An explicitly owned scheduled
   task can bridge this boundary without elevating a per-user installer.

For a per-user installer, stage a helper like this after substituting verified paths and identity:

```powershell
$ErrorActionPreference = 'Stop'
$taskName = 'InstallerReview-UNIQUE-RUN'
$installer = 'C:/Users/dev/projects/build-area/package/setup.exe'
if (!(Test-Path -LiteralPath $installer -PathType Leaf)) { throw 'Installer missing' }
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    throw 'Task name already exists; inspect it before choosing another run'
}
$action = New-ScheduledTaskAction -Execute $installer `
    -WorkingDirectory (Split-Path -Parent $installer)
$principal = New-ScheduledTaskPrincipal -UserId 'dev' -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $taskName -Action $action `
    -Principal $principal -Settings $settings | Out-Null
Start-ScheduledTask -TaskName $taskName
```

Verify the intended user is logged in before launching. Inspect the resulting process path, session,
and window title/handle; task submission alone does not prove a visible installer. Some installers
spawn a child setup process, so inspect the owned process family. Do not change to Highest privilege
as a generic launch fix. Machine-wide installation and UAC require the appropriate user interaction.

When the user says they will drive the mouse, leave the installer open without silent switches,
automated clicks, or a short task timeout that kills it. Do not infer installation success from
launch success. Let the user choose the destination and finish options. Afterwards, verify the
installed version/path and selected runtime files when requested or within the agreed validation
scope. Preserve existing profiles, runtime registrations and unrelated installations. Remove only
this run's task registration after its installer processes have finished; retain the package and
build evidence. Do not stop an installer merely because the controlling obt.net command has ended.

## Runtime checks and troubleshooting

A successful compile does not prove deployment. Check architecture, DLL imports/exports, transitive
runtime dependencies and an isolated native run. A development machine's PATH can hide missing DLLs;
validate a controlled runtime PATH. Do not overwrite DLLs/executables held open by a running process.

GUI, audio, input, and GPU tests may need the logged-in user's Windows session. A WSL service/SSH
session can have a different token, desktop or environment. Use an existing authorized interactive
normal-user launcher/task; do not infer that a windowless process crash is a graphics-code defect.
Some loaders ignore environment overrides when elevated. Record actual token/session/runtime paths.
Do not change system runtime registrations or elevate automatically to make a test pass.

| Symptom | First checks |
|---|---|
| Registered node, `run` cannot reach it | Advertised address, managed tunnel, three fixed ports, correct SSH target |
| `wslPS` works, job verbs fail | Separate SSH wrapper versus controller/node transport; test each independently |
| ZMQ timeout only inside an agent sandbox | Retry through the harness's normal network approval path before diagnosing the host |
| Missing OBT modules, staging, or flags | Real venv/import paths, full OBT launcher, inherited PYTHONPATH, stale node process |
| Native command sees UNC cwd | Set worker `--cwd` to a drive-backed `/mnt/c/...` location |
| Build “succeeds” with no artifacts | Native exit propagation, detached child, wrong output directory or configuration |
| Windows SDK/CRT type conflicts | Compiler ABI and broad MSYS2 include directories contaminating clang-cl |
| Tiny transfer stalls | Destination-parent manifest scan, huge tree, blocked Git status; not necessarily the network |
| New source revision behaves like old one | Hash transferred files, chosen build/runtime paths, locked DLLs, cached generated files |
| Clang exits 127 before compiling | Native exit status, DLL imports, package hashes and correlated Code Integrity events; see CLANG64 recovery above |
| Old binary now fails too | Driver/SDK/OS/environment changes before code bisect |

Leave a small durable resume note with the node/root/toolchain, exact source state, job IDs, terminal
results, artifacts, remaining limits, and launch instructions. Treat PIDs, IP addresses, USB routes,
and temporary directories as observations to revalidate, not permanent identities.
