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
  python setup_wilt_reels.py --dir %USERPROFILE%\what-i-learned-today-reels
"""

import argparse
import os
import platform
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
            raise RuntimeError(f"Command failed (exit {result.returncode}): {printable}")
        
        return result
    except FileNotFoundError:
        if check:
            raise RuntimeError(f"Command not found: {cmd[0] if isinstance(cmd, list) else cmd.split()[0]}")
        return None


def which(name: str):
    """Check if a command exists in PATH"""
    return shutil.which(name)


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
        print_success("Homebrew found")
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

def update_apt():
    """Update apt package lists"""
    print_step("Updating package lists...")
    run(["sudo", "apt", "update"], check=True)


def install_package_linux(package):
    """Install a package using apt"""
    # Check if installed
    result = run(
        ["dpkg", "-l", package], 
        check=False, 
        capture_output=True
    )
    
    if result and result.returncode == 0 and package in result.stdout:
        print_success(f"{package} already installed")
        return
    
    print_step(f"Installing {package}...")
    run(["sudo", "apt", "install", "-y", package])
    print_success(f"{package} installed")


def setup_node_linux(env):
    """Install Node.js on Linux using NodeSource"""
    if which("node"):
        print_success("Node.js already installed")
        run(["node", "-v"], env=env)
        run(["npm", "-v"], env=env)
        return env
    
    print_step("Installing Node.js LTS via NodeSource...")
    
    # Install Node.js 22.x LTS
    run([
        "curl", "-fsSL", 
        "https://deb.nodesource.com/setup_22.x",
        "-o", "/tmp/nodesource_setup.sh"
    ], env=env)
    
    run(["sudo", "bash", "/tmp/nodesource_setup.sh"], env=env)
    install_package_linux("nodejs")
    
    run(["node", "-v"], env=env)
    run(["npm", "-v"], env=env)
    
    return env


def setup_linux(env):
    """Complete Linux setup"""
    print("\n" + "="*60)
    print("LINUX (UBUNTU/DEBIAN) SETUP")
    print("="*60)
    
    # Update package lists
    update_apt()
    
    # Install packages
    install_package_linux("git")
    install_package_linux("curl")
    install_package_linux("ffmpeg")
    install_package_linux("mpv")
    
    # Node.js
    env = setup_node_linux(env)
    
    return env


# ============================================================================
# COMMON SETUP (ALL PLATFORMS)
# ============================================================================

def setup_pnpm(env):
    """Install pnpm package manager"""
    if which("pnpm"):
        print_success("pnpm already installed")
        run(["pnpm", "-v"], env=env)
        return env
    
    print_step("Installing pnpm...")
    
    # Try corepack first (modern Node.js)
    if which("corepack"):
        print_step("Enabling pnpm via corepack...")
        run(["corepack", "enable"], env=env, check=False)
        run(["corepack", "prepare", "pnpm@latest", "--activate"], env=env, check=False)
    
    # Check if pnpm is now available
    if which("pnpm"):
        print_success("pnpm enabled via corepack")
        run(["pnpm", "-v"], env=env)
        return env
    
    # Fallback to npm global install
    print_step("Installing pnpm globally via npm...")
    run(["npm", "install", "-g", "pnpm"], env=env)
    
    run(["pnpm", "-v"], env=env)
    print_success("pnpm installed")
    
    return env


def clone_or_validate_repo(env, repo_url, project_dir):
    """Clone repository or validate existing directory"""
    package_json = project_dir / "package.json"
    
    if package_json.exists():
        print_success(f"Project already exists at: {project_dir}")
        return
    
    print_step(f"Cloning repository to: {project_dir}")
    project_dir.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "clone", repo_url, str(project_dir)], env=env)
    
    if not package_json.exists():
        raise RuntimeError(f"Clone succeeded but package.json not found in {project_dir}")
    
    print_success("Repository cloned successfully")


def install_dependencies(env, project_dir):
    """Install project dependencies via pnpm"""
    print("\n" + "="*60)
    print("INSTALLING PROJECT DEPENDENCIES")
    print("="*60)
    
    run(["pnpm", "install"], env=env, cwd=str(project_dir))
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
