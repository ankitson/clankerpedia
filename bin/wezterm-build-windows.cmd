@echo off
REM ============================================================================
REM wezterm-build-windows.cmd - build the custom wezterm on Windows and assemble
REM the portable bundle. Encodes the toolchain recipe worked out in the June 2026
REM build session (agentsview codex:019ef140) so it is not lost.
REM
REM Usage (run from cmd.exe, NOT powershell - quoting differs):
REM   wezterm-build-windows.cmd <source-dir> <tag>
REM     <source-dir>  extracted wezterm source tree containing a .tag file
REM                   e.g. C:\Users\ankit\wezterm-builds\wezterm-win-src-607fa84f
REM     <tag>         version string, e.g. 20260619-232330-607fa84f
REM
REM Output: C:\Users\ankit\wezterm-builds\WezTerm-windows-<tag>\  (portable dir)
REM         Launch wezterm-gui.exe from there.
REM
REM Prerequisites on the host (install once):
REM   - Visual Studio 2022 Build Tools (C/C++), provides VsDevCmd.bat
REM   - Strawberry Perl at C:\Strawberry (needed to build vendored OpenSSL)
REM   - rustup nightly-x86_64-pc-windows-msvc toolchain
REM Notes:
REM   - rustup SHIMS (cargo.exe/rustc.exe in ~/.cargo/bin) fail under OpenSSH due
REM     to the Windows symlink policy, so we call the REAL toolchain binaries and
REM     pin RUSTC. Strawberry Perl must precede Git's perl; MSVC link.exe must
REM     precede Git's link.exe (VsDevCmd handles the latter).
REM ============================================================================
setlocal EnableDelayedExpansion

if "%~2"=="" (
  echo ERROR: usage: %~nx0 ^<source-dir^> ^<tag^>
  exit /b 2
)
set "SRC=%~1"
set "TAG=%~2"
set "BUILDS=%USERPROFILE%\wezterm-builds"
set "OUT=%BUILDS%\WezTerm-windows-%TAG%"
REM Build into a target dir OUTSIDE the source tree so re-extracting the source
REM (which the sync tool does each run) doesn't wipe the incremental build cache.
set "CARGO_TARGET_DIR=%BUILDS%\target"

if not exist "%SRC%\Cargo.toml" (
  echo ERROR: no Cargo.toml under "%SRC%"
  exit /b 2
)

REM --- seed/refresh .tag so the build reports the exact version --------------
> "%SRC%\.tag" echo %TAG%

REM --- MSVC environment (cl.exe / link.exe) ---------------------------------
set "VSDEV=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"
if not exist "%VSDEV%" (
  echo ERROR: VsDevCmd.bat not found at "%VSDEV%" - install VS 2022 Build Tools
  exit /b 3
)
call "%VSDEV%" -arch=amd64 -host_arch=amd64 >nul

REM --- Strawberry Perl ahead of Git's MSYS perl (for OpenSSL) ----------------
if exist "C:\Strawberry\perl\bin\perl.exe" (
  set "PATH=C:\Strawberry\perl\bin;%PATH%"
) else (
  echo WARNING: Strawberry Perl not found at C:\Strawberry - OpenSSL build may fail
)

REM --- locate the real rustup toolchain bin (bypass the broken shims) --------
set "RUST_BIN="
for /d %%d in ("%USERPROFILE%\.rustup\toolchains\nightly-*windows-msvc") do set "RUST_BIN=%%d\bin"
if not defined RUST_BIN (
  for /d %%d in ("%USERPROFILE%\.rustup\toolchains\*windows-msvc") do set "RUST_BIN=%%d\bin"
)
if not defined RUST_BIN (
  echo ERROR: no *-windows-msvc rustup toolchain under %USERPROFILE%\.rustup\toolchains
  exit /b 3
)
set "CARGO=!RUST_BIN!\cargo.exe"
set "RUSTC=!RUST_BIN!\rustc.exe"
set "PATH=!RUST_BIN!;%PATH%"
echo Using toolchain: !RUST_BIN!

REM --- build the four binaries ----------------------------------------------
pushd "%SRC%"
echo Building (this takes ~10-15 min cold)...
"!CARGO!" build --release -p wezterm -p wezterm-gui -p wezterm-mux-server -p strip-ansi-escapes
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" (
  echo ERROR: cargo build failed (exit %RC%)
  exit /b %RC%
)

REM --- assemble the portable bundle (mirrors ci/deploy.sh msys branch) -------
set "REL=%CARGO_TARGET_DIR%\release"
if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%"
mkdir "%OUT%\mesa"
for %%f in (wezterm.exe wezterm-gui.exe wezterm-mux-server.exe strip-ansi-escapes.exe wezterm.pdb) do (
  copy /Y "%REL%\%%f" "%OUT%\" >nul || echo WARNING: missing %%f
)
copy /Y "%SRC%\assets\windows\conhost\conpty.dll"      "%OUT%\" >nul
copy /Y "%SRC%\assets\windows\conhost\OpenConsole.exe" "%OUT%\" >nul
copy /Y "%SRC%\assets\windows\angle\libEGL.dll"        "%OUT%\" >nul
copy /Y "%SRC%\assets\windows\angle\libGLESv2.dll"     "%OUT%\" >nul
copy /Y "%REL%\mesa\opengl32.dll"                      "%OUT%\mesa\" >nul

REM --- fail loudly if packaging didn't land the key binaries -----------------
for %%f in (wezterm.exe wezterm-gui.exe wezterm-mux-server.exe) do (
  if not exist "%OUT%\%%f" (
    echo ERROR: packaging failed - %%f missing from "%OUT%" ^(check REL="%REL%"^)
    exit /b 5
  )
)

echo.
echo BUILD OK
echo Portable bundle: %OUT%
"%OUT%\wezterm.exe" --version
endlocal
exit /b 0
