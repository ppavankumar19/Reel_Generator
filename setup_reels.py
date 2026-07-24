#!/usr/bin/env python3
"""
What I Learned Today - Reels Generator Universal Setup

✅ Cross-platform setup for the What I Learned Today Reels project.
Automatically detects your OS and installs dependencies accordingly.

Supports:
- Windows 10/11 (via Chocolatey)
- macOS (via Homebrew)
- Linux Ubuntu/Debian (via apt)

USAGE:
  # Fresh setup with repo clone (recommended)
  python3 setup_wilt_reels.py

  # Specify custom directory
  python3 setup_wilt_reels.py --dir ~/my-reels

  # Use existing clone
  python3 setup_wilt_reels.py --dir ~/what-i-learned-today-reels

  # Setup only (skip render)
  python3 setup_wilt_reels.py --no-render

  # Windows PowerShell
  python setup_wilt_reels.py --dir %USERPROFILE%\\what-i-learned-today-reels
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_step(msg):
    """Print a step message with formatting"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}▶ {msg}{Colors.RESET}")


def print_success(msg):
    """Print a success message"""
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")


def print_warning(msg):
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")


def print_error(msg):
    """Print an error message"""
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")


def run(cmd, *, cwd=None, env=None, check=True, shell=False, capture_output=False):
    """Run a command and print it. Raises on failure if check=True."""
    if isinstance(cmd, list):
        printable = " ".join(str(c) for c in cmd)
    else:
        printable = cmd
    
    print_step(printable)
    
    try:
        if capture_output:
            result = subprocess.run(
                cmd, 
                cwd=cwd, 
                env=env, 
                shell=shell, 
                capture_output=True, 
                text=True
            )
        else:
            result = subprocess.run(cmd, cwd=cwd, env=env, shell=shell)
        
        if check and result.returncode != 0:
            # Show captured output so the error is visible before raising
            if capture_output:
                if result.stdout:
                    print(result.stdout, end="")
                if result.stderr:
                    print(result.stderr, end="", file=sys.stderr)
            raise RuntimeError(f"Command failed (exit {result.returncode}): {printable}")
        
        return result
    except FileNotFoundError:
        if check:
            raise RuntimeError(f"Command not found: {cmd[0] if isinstance(cmd, list) else cmd.split()[0]}")
        return None


def which(name: str):
    """Check if a command exists in PATH"""
    return shutil.which(name)


def get_sudo():
    """Return ['sudo'] if not root, else [] — works on Linux/macOS, skips on Windows."""
    if os.name == 'nt':
        return []
    try:
        if os.geteuid() == 0:
            return []
    except AttributeError:
        return []
    return ["sudo"]


def is_wsl():
    """Detect Windows Subsystem for Linux."""
    try:
        with open("/proc/version") as f:
            return "microsoft" in f.read().lower()
    except Exception:
        return False


def get_os():
    """Detect the operating system"""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        raise RuntimeError(f"Unsupported OS: {system}")


def is_admin():
    """Check if running with admin privileges (Windows)"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


# ============================================================================
# WINDOWS SETUP
# ============================================================================

def setup_chocolatey_windows(env):
    """Install Chocolatey package manager on Windows"""
    if which("choco"):
        print_success("Chocolatey already installed")
        return env
    
    print_warning("Chocolatey not found. Installing...")
    print_warning("This requires Administrator privileges!")
    
    if not is_admin():
        print_error("Please run this script as Administrator on Windows")
        print("Right-click PowerShell/CMD and select 'Run as Administrator'")
        sys.exit(1)
    
    # Install Chocolatey
    install_cmd = (
        'Set-ExecutionPolicy Bypass -Scope Process -Force; '
        '[System.Net.ServicePointManager]::SecurityProtocol = '
        '[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; '
        'iex ((New-Object System.Net.WebClient).DownloadString('
        "'https://community.chocolatey.org/install.ps1'))"
    )
    
    run(["powershell", "-Command", install_cmd], env=env, shell=False)
    print_success("Chocolatey installed")
    
    return env


def install_package_windows(env, package):
    """Install a package using Chocolatey on Windows"""
    if which(package):
        print_success(f"{package} already installed")
        return
    
    print_step(f"Installing {package} via Chocolatey...")
    run(["choco", "install", package, "-y"], env=env)
    print_success(f"{package} installed")


def setup_node_windows(env):
    """Install Node.js on Windows"""
    if which("node"):
        print_success("Node.js already installed")
        run(["node", "-v"], env=env)
        run(["npm", "-v"], env=env)
        return env
    
    print_step("Installing Node.js...")
    install_package_windows(env, "nodejs-lts")
    
    # Refresh PATH
    refresh_env_windows()
    
    run(["node", "-v"], env=env)
    run(["npm", "-v"], env=env)
    return env


def refresh_env_windows():
    """Refresh environment variables on Windows"""
    print_step("Refreshing environment variables...")
    run(["refreshenv"], shell=True, check=False)


def setup_windows(env):
    """Complete Windows setup"""
    print("\n" + "="*60)
    print("WINDOWS SETUP")
    print("="*60)
    
    # Install Chocolatey
    env = setup_chocolatey_windows(env)
    
    # Install packages
    install_package_windows(env, "git")
    install_package_windows(env, "ffmpeg")
    
    # Node.js
    env = setup_node_windows(env)
    
    return env


# ============================================================================
# MACOS SETUP
# ============================================================================

def detect_brew_bin():
    """Find Homebrew binary on macOS"""
    for p in ("/opt/homebrew/bin/brew", "/usr/local/bin/brew"):
        if Path(p).exists():
            return p
    return which("brew")


def setup_homebrew_macos(env):
    """Install Homebrew on macOS"""
    brew = detect_brew_bin()
    if brew:
        # Always ensure brew's bin dir is in PATH — critical on Apple Silicon
        # where /opt/homebrew/bin may not be in the inherited env PATH
        brew_dir = str(Path(brew).parent)
        if brew_dir not in env.get("PATH", ""):
            env["PATH"] = brew_dir + os.pathsep + env.get("PATH", "")
        print_success(f"Homebrew found at {brew_dir}")
        return env

    print_warning("Homebrew not found. Installing...")
    install_script = (
        '/bin/bash -c "$(curl -fsSL '
        'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    )
    run(install_script, shell=True, env=env)
    
    brew = detect_brew_bin()
    if not brew:
        raise RuntimeError("Homebrew installation failed")
    
    brew_dir = str(Path(brew).parent)
    env["PATH"] = brew_dir + os.pathsep + env.get("PATH", "")
    print_success(f"Homebrew installed at {brew_dir}")
    
    return env


def brew_install(env, formula):
    """Install a package via Homebrew"""
    rc = run(["brew", "list", "--versions", formula], env=env, check=False, capture_output=True)
    if rc and rc.returncode == 0:
        print_success(f"{formula} already installed")
        return
    
    print_step(f"Installing {formula}...")
    run(["brew", "install", formula], env=env)
    print_success(f"{formula} installed")


def setup_node_macos(env):
    """Install Node.js on macOS"""
    if which("node"):
        print_success("Node.js already installed")
        run(["node", "-v"], env=env)
        run(["npm", "-v"], env=env)
        return env
    
    print_step("Installing Node.js LTS...")
    for formula in ("node@22", "node@20", "node"):
        result = run(["brew", "install", formula], env=env, check=False)
        if result and result.returncode == 0:
            break
    
    # Update PATH for versioned node
    prefix = subprocess.check_output(["brew", "--prefix"], env=env, text=True).strip()
    for formula in ("node@22", "node@20"):
        binpath = Path(prefix) / "opt" / formula / "bin"
        if binpath.exists():
            env["PATH"] = str(binpath) + os.pathsep + env.get("PATH", "")
            break
    
    run(["node", "-v"], env=env)
    run(["npm", "-v"], env=env)
    return env


def setup_macos(env):
    """Complete macOS setup"""
    print("\n" + "="*60)
    print("MACOS SETUP")
    print("="*60)
    
    # Install Homebrew
    env = setup_homebrew_macos(env)
    
    # Update and install packages
    run(["brew", "update"], env=env)
    brew_install(env, "git")
    brew_install(env, "ffmpeg")
    brew_install(env, "mpv")
    
    # Node.js
    env = setup_node_macos(env)
    
    return env


# ============================================================================
# LINUX SETUP
# ============================================================================

def apt_env(env):
    """Return env dict with DEBIAN_FRONTEND=noninteractive set."""
    e = dict(env)
    e["DEBIAN_FRONTEND"] = "noninteractive"
    return e


def update_apt(env):
    """Update apt package lists."""
    print_step("Updating package lists...")
    run(get_sudo() + ["apt-get", "update", "-y"], env=apt_env(env), check=True)


def install_package_linux(package, env, required=True):
    """Install a package using apt-get. Returns True if installed/available."""
    # Use dpkg -s for reliable status check (checks 'Status: install ok installed')
    result = run(["dpkg", "-s", package], check=False, capture_output=True)
    if result and result.returncode == 0 and "Status: install ok installed" in result.stdout:
        print_success(f"{package} already installed")
        return True

    print_step(f"Installing {package}...")
    result = run(
        get_sudo() + ["apt-get", "install", "-y", "--no-install-recommends", package],
        env=apt_env(env),
        check=required,
    )
    if result is None or result.returncode != 0:
        print_warning(f"Optional package '{package}' could not be installed — skipping")
        return False
    print_success(f"{package} installed")
    return True


def setup_node_linux(env):
    """Install Node.js on Linux using NodeSource."""
    if which("node"):
        print_success("Node.js already installed")
        run(["node", "-v"], env=env)
        run(["npm", "-v"], env=env)
        return env

    print_step("Installing Node.js LTS via NodeSource...")

    run([
        "curl", "-fsSL",
        "https://deb.nodesource.com/setup_22.x",
        "-o", "/tmp/nodesource_setup.sh"
    ], env=env)

    run(get_sudo() + ["bash", "/tmp/nodesource_setup.sh"], env=apt_env(env))
    install_package_linux("nodejs", env, required=True)

    # Ensure standard node bin paths are in PATH
    for node_bin_dir in ("/usr/bin", "/usr/local/bin"):
        if Path(node_bin_dir + "/node").exists():
            if node_bin_dir not in env.get("PATH", ""):
                env["PATH"] = node_bin_dir + os.pathsep + env.get("PATH", "")
            break

    run(["node", "-v"], env=env)
    run(["npm", "-v"], env=env)

    return env


def setup_linux(env):
    """Complete Linux/Ubuntu setup (native, WSL, Multipass)."""
    headless = is_wsl()

    print("\n" + "="*60)
    if headless:
        print("LINUX (UBUNTU/DEBIAN) SETUP — WSL detected")
    else:
        print("LINUX (UBUNTU/DEBIAN) SETUP")
    print("="*60)

    update_apt(env)

    install_package_linux("git", env)
    install_package_linux("curl", env)
    install_package_linux("ffmpeg", env)
    # mpv is a display player — optional on headless/WSL/Multipass
    install_package_linux("mpv", env, required=False)

    env = setup_node_linux(env)

    return env


# ============================================================================
# COMMON SETUP (ALL PLATFORMS)
# ============================================================================

def setup_pnpm(env):
    """Install pnpm package manager via sudo npm install -g pnpm."""
    if which("pnpm"):
        print_success("pnpm already installed")
        run(["pnpm", "-v"], env=env)
        return env

    print_step("Installing pnpm globally via npm (sudo)...")
    run(get_sudo() + ["npm", "install", "-g", "pnpm"], env=env)

    # Ensure npm global bin dir is in PATH (needed if it wasn't already)
    try:
        npm_prefix = subprocess.check_output(
            ["npm", "config", "get", "prefix"], env=env, text=True
        ).strip()
        npm_bin = Path(npm_prefix) / "bin"
        if npm_bin.exists() and str(npm_bin) not in env.get("PATH", ""):
            env["PATH"] = str(npm_bin) + os.pathsep + env.get("PATH", "")
            print_step(f"Added {npm_bin} to PATH")
    except Exception:
        pass

    if not which("pnpm"):
        raise RuntimeError("pnpm installation failed. Try manually: sudo npm install -g pnpm")

    run(["pnpm", "-v"], env=env)
    print_success("pnpm installed")
    return env


def clone_or_validate_repo(env, repo_url, project_dir):
    """Clone repository or validate existing directory."""
    package_json = project_dir / "package.json"

    if package_json.exists():
        print_success(f"Project already exists at: {project_dir}")
        return

    # If dir exists but has no package.json, git clone would fail on non-empty dirs
    if project_dir.exists() and any(project_dir.iterdir()):
        raise RuntimeError(
            f"Directory exists but contains no package.json: {project_dir}\n"
            f"Remove it or choose a different --dir path."
        )

    print_step(f"Cloning repository to: {project_dir}")
    project_dir.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "clone", repo_url, str(project_dir)], env=env)

    if not package_json.exists():
        raise RuntimeError(f"Clone succeeded but package.json not found in {project_dir}")

    print_success("Repository cloned successfully")


def _cleanup_prev_run(project_dir):
    """
    Wipe stale artifacts left by any previous failed setup run so that
    pnpm install always starts from a clean state.  Covers all three
    locations our script has ever tried to write onlyBuiltDependencies.
    """
    # 1. package.json — written by early script versions (now triggers WARN)
    pkg_json = project_dir / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text())
            pnpm_cfg = data.get("pnpm", {})
            if "onlyBuiltDependencies" in pnpm_cfg:
                pnpm_cfg.pop("onlyBuiltDependencies")
                if pnpm_cfg:
                    data["pnpm"] = pnpm_cfg
                else:
                    data.pop("pnpm", None)
                pkg_json.write_text(json.dumps(data, indent=2) + "\n")
                print_step("Cleaned stale pnpm.onlyBuiltDependencies from package.json")
        except Exception as e:
            print_warning(f"Could not clean package.json: {e}")

    # 2. .npmrc — written by previous script version
    npmrc = project_dir / ".npmrc"
    if npmrc.exists():
        content = npmrc.read_text()
        marker = "# Allow build scripts (added by setup_reels.py)"
        if marker in content or "onlyBuiltDependencies[]=" in content:
            cleaned = [l for l in content.splitlines()
                       if l.strip() != marker
                       and not l.startswith("onlyBuiltDependencies[]=")]
            npmrc.write_text("\n".join(cleaned).rstrip("\n") + "\n")
            print_step("Cleaned stale .npmrc entries")

    # 3. pnpm-workspace.yaml — if we created it, it only has our block
    ws = project_dir / "pnpm-workspace.yaml"
    if ws.exists():
        lines = [l for l in ws.read_text().splitlines() if l.strip()]
        is_ours = all(
            l.startswith("onlyBuiltDependencies:") or l.strip().startswith("- ")
            for l in lines
        )
        if is_ours:
            ws.unlink()
            print_step("Removed stale pnpm-workspace.yaml")

    # 4. Restore pnpm-lock.yaml from git if we deleted it in a previous run
    #    so pnpm-workspace.yaml changes are the only diff going into re-resolution
    lockfile = project_dir / "pnpm-lock.yaml"
    if not lockfile.exists() and (project_dir / ".git").exists():
        result = subprocess.run(
            ["git", "checkout", "HEAD", "--", "pnpm-lock.yaml"],
            cwd=str(project_dir), capture_output=True
        )
        if result.returncode == 0:
            print_step("Restored pnpm-lock.yaml from git")


def _parse_blocked_pkgs(pnpm_output):
    """Extract package names from ERR_PNPM_IGNORED_BUILDS output."""
    m = re.search(r"Ignored build scripts:\s*([^\n]+)", pnpm_output)
    if not m:
        return []
    pkgs = []
    for token in re.split(r"[,\s]+", m.group(1).strip()):
        token = token.strip()
        if not token:
            continue
        # Strip @version — handle scoped (@scope/name@ver) and plain (name@ver)
        name = ("@" + token[1:].rsplit("@", 1)[0]) if token.startswith("@") else token.split("@")[0]
        if name:
            pkgs.append(name)
    return pkgs


def _allow_pnpm_builds(project_dir, pnpm_output):
    """
    Handle ERR_PNPM_IGNORED_BUILDS across pnpm versions:
      pnpm 10+ → writes onlyBuiltDependencies to pnpm-workspace.yaml
                  (this is what 'pnpm approve-builds' does internally in v10)
      pnpm 9.x  → writes onlyBuiltDependencies[]= entries to .npmrc
      Both      → removes the stale pnpm.onlyBuiltDependencies from package.json
                  (package.json is no longer read by pnpm 10+ for this key)
    """
    pkgs = _parse_blocked_pkgs(pnpm_output)
    if not pkgs:
        print_warning("Could not parse blocked package names — retrying anyway")
        return

    print_step(f"Allowing build scripts for: {', '.join(pkgs)}")

    # --- pnpm 10+: write to pnpm-workspace.yaml ---
    ws_path = project_dir / "pnpm-workspace.yaml"
    if ws_path.exists():
        content = ws_path.read_text()
        if "onlyBuiltDependencies:" not in content:
            block = "\nonlyBuiltDependencies:\n" + "".join(f"  - {p}\n" for p in pkgs)
            ws_path.write_text(content.rstrip("\n") + block)
            print_success(f"pnpm-workspace.yaml updated with onlyBuiltDependencies: {pkgs}")
        else:
            print_success("onlyBuiltDependencies already present in pnpm-workspace.yaml")
    else:
        block = "onlyBuiltDependencies:\n" + "".join(f"  - {p}\n" for p in pkgs)
        ws_path.write_text(block)
        print_success(f"pnpm-workspace.yaml created with onlyBuiltDependencies: {pkgs}")

    # --- pnpm 9.x fallback: write to .npmrc ---
    npmrc_path = project_dir / ".npmrc"
    existing_npmrc = npmrc_path.read_text() if npmrc_path.exists() else ""
    new_lines = [f"onlyBuiltDependencies[]={p}" for p in pkgs
                 if f"onlyBuiltDependencies[]={p}" not in existing_npmrc]
    if new_lines:
        with open(npmrc_path, "a") as f:
            if existing_npmrc and not existing_npmrc.endswith("\n"):
                f.write("\n")
            f.write("# Allow build scripts (added by setup_reels.py)\n")
            for line in new_lines:
                f.write(line + "\n")
        print_success(f".npmrc updated: {new_lines}")

    # --- Remove stale package.json entry (triggers WARN in pnpm 10+) ---
    pkg_json_path = project_dir / "package.json"
    if pkg_json_path.exists():
        data = json.loads(pkg_json_path.read_text())
        pnpm_section = data.get("pnpm", {})
        if "onlyBuiltDependencies" in pnpm_section:
            del pnpm_section["onlyBuiltDependencies"]
            data["pnpm"] = pnpm_section if pnpm_section else data.pop("pnpm", None) or {}
            if not data.get("pnpm"):
                data.pop("pnpm", None)
            pkg_json_path.write_text(json.dumps(data, indent=2) + "\n")
            print_success("Removed stale pnpm.onlyBuiltDependencies from package.json")

    # --- Delete pnpm-lock.yaml so pnpm regenerates it with the new setting ---
    # pnpm caches onlyBuiltDependencies INSIDE the lockfile. Even after updating
    # pnpm-workspace.yaml, if the lockfile is "up to date" pnpm skips re-resolution
    # and still reads the OLD onlyBuiltDependencies from the lockfile — causing
    # ERR_PNPM_IGNORED_BUILDS again. Deleting the lockfile forces pnpm to regenerate
    # it from package.json, picking up the new pnpm-workspace.yaml settings.
    lockfile = project_dir / "pnpm-lock.yaml"
    if lockfile.exists():
        lockfile.unlink()
        print_step("Deleted pnpm-lock.yaml — pnpm will regenerate it with correct settings")


def install_dependencies(env, project_dir):
    """Install project dependencies via pnpm, handling pnpm 9+ build-script approval."""
    print("\n" + "="*60)
    print("INSTALLING PROJECT DEPENDENCIES")
    print("="*60)

    # Always wipe stale artifacts from any previous failed run before starting
    _cleanup_prev_run(project_dir)

    result = run(
        ["pnpm", "install"], env=env, cwd=str(project_dir),
        check=False, capture_output=True
    )

    # Always show pnpm output
    if result:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)

    if result and result.returncode != 0:
        combined = (result.stdout or "") + (result.stderr or "")
        if "ERR_PNPM_IGNORED_BUILDS" in combined or "approve-builds" in combined:
            print_warning("pnpm 9+ blocked build scripts — auto-approving and retrying...")
            _allow_pnpm_builds(project_dir, combined)
            run(["pnpm", "install"], env=env, cwd=str(project_dir))
        else:
            raise RuntimeError("pnpm install failed (see output above)")

    print_success("Dependencies installed")


def render_video(env, project_dir):
    """Render the video using pnpm"""
    print("\n" + "="*60)
    print("RENDERING VIDEO")
    print("="*60)
    
    run(["pnpm", "render"], env=env, cwd=str(project_dir))
    
    out_mp4 = project_dir / "out" / "video.mp4"
    
    if out_mp4.exists():
        print_success("Video rendered successfully!")
        print(f"\n📹 Output: {out_mp4}")
        
        os_type = get_os()
        if os_type == "windows":
            print(f"\nPlay: start \"{out_mp4}\"")
        elif os_type == "macos":
            print(f"\nPlay: mpv '{out_mp4}' OR open '{out_mp4}'")
        else:  # linux
            print(f"\nPlay: mpv '{out_mp4}' OR xdg-open '{out_mp4}'")
    else:
        print_warning("Render completed but output file not found at expected location")
        print(f"Expected: {out_mp4}")


def print_next_steps(project_dir):
    """Print instructions for next steps"""
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    
    print(f"\n📝 Customize your video:")
    print(f"   Edit: {project_dir / 'src' / 'config.ts'}")
    print(f"   Or edit: {project_dir / 'public' / 'data.json'}")
    print(f"\n🎬 Render again:")
    print(f"   cd {project_dir}")
    print(f"   pnpm render")
    print(f"\n🚀 Start development server:")
    print(f"   cd {project_dir}")
    print(f"   pnpm dev")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(
        description="Universal setup for What I Learned Today - Reels Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fresh setup (recommended)
  python3 setup_wilt_reels.py

  # Custom directory
  python3 setup_wilt_reels.py --dir ~/my-reels

  # Setup without rendering
  python3 setup_wilt_reels.py --no-render

  # Windows
  python setup_wilt_reels.py --dir %USERPROFILE%\\what-i-learned-today-reels
        """
    )
    
    # Default repository and directory
    REPO_URL = "https://github.com/aikaryashala/what-i-learned-today-reels.git"
    default_dir = Path.home() / "what-i-learned-today-reels"
    
    parser.add_argument(
        "--repo", 
        default=REPO_URL, 
        help=f"Git repository URL (default: {REPO_URL})"
    )
    parser.add_argument(
        "--dir", 
        default=str(default_dir), 
        help=f"Project directory (default: {default_dir})"
    )
    parser.add_argument(
        "--no-render", 
        action="store_true", 
        help="Skip video rendering (setup only)"
    )
    
    args = parser.parse_args()
    
    # Environment setup
    env = dict(os.environ)
    project_dir = Path(args.dir).expanduser().resolve()
    os_type = get_os()
    
    # Print header
    print("\n" + "="*60)
    print("WHAT I LEARNED TODAY - REELS GENERATOR SETUP")
    print("="*60)
    print(f"OS: {os_type.upper()}")
    print(f"Project directory: {project_dir}")
    print(f"Repository: {args.repo}")
    print("="*60)
    
    # OS-specific setup
    if os_type == "windows":
        env = setup_windows(env)
    elif os_type == "macos":
        env = setup_macos(env)
    elif os_type == "linux":
        env = setup_linux(env)
    
    # Common setup
    env = setup_pnpm(env)
    
    # Repository
    clone_or_validate_repo(env, args.repo, project_dir)
    
    # Install dependencies
    install_dependencies(env, project_dir)
    
    # Render video (unless skipped)
    if not args.no_render:
        render_video(env, project_dir)
    else:
        print_warning("Video rendering skipped (--no-render)")
    
    # Print next steps
    print_next_steps(project_dir)
    
    print("\n" + "="*60)
    print_success("SETUP COMPLETE!")
    print("="*60 + "\n")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
