import subprocess
import os
import sys
import platform
PROJECT_GIT = "https://github.com/aikaryashala/what-i-learned-today-reels.git"
PROJECT_FOLDER = "what-i-learned-today-reels"
HTTP_PORT = 8000
def run_command(cmd):
    print(f"\n▶ Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        sys.exit(1)
print("\n===== REELS AUTO SETUP STARTED =====")
# -------------------------------------------------
# 1. Base Packages
# -------------------------------------------------
run_command("sudo apt update")
run_command("""
sudo apt install -y \
curl wget git build-essential software-properties-common \
ca-certificates gnupg unzip lsb-release
""")
# -------------------------------------------------
# 2. Remove Old Node.js (Fix dpkg conflict)
# -------------------------------------------------
run_command("""
sudo apt remove -y nodejs libnode-dev || true
sudo apt purge -y nodejs libnode-dev || true
sudo apt autoremove -y
""")
# -------------------------------------------------
# 3. Install Node.js 18 (LTS)
# -------------------------------------------------
run_command("curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -")
run_command("sudo apt install -y nodejs")
# -------------------------------------------------
# 4. Install pnpm
# -------------------------------------------------
run_command("sudo npm install -g pnpm")
# -------------------------------------------------
# 5. Detect Ubuntu Version
# -------------------------------------------------
ubuntu_version = subprocess.check_output("lsb_release -rs", shell=True).decode().strip()
print(f"🧠 Detected Ubuntu Version: {ubuntu_version}")
# -------------------------------------------------
# 6. Install Chromium + Dependencies (Version Aware)
# -------------------------------------------------
if ubuntu_version.startswith("24"):
    print("📦 Installing Chromium deps for Ubuntu 24.04+")
    run_command("""
    sudo apt install -y \
    chromium \
    libnss3 libnspr4 libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 \
    libxkbcommon0 libxcomposite1 libxrandr2 libgbm1 libasound2t64 \
    libpangocairo-1.0-0 libpango-1.0-0 libgtk-3-0t64 libxdamage1 libxfixes3 \
    libdrm2 libxshmfence1 libx11-xcb1 libxcb1 libxext6 libxrender1 \
    libxi6 libxtst6 libglib2.0-0 libdbus-1-3 libfontconfig1 libfreetype6
    """)
    chromium_path = "/usr/bin/chromium"
else:
    print("📦 Installing Chromium deps for Ubuntu 20.04 / 22.04")
    run_command("""
    sudo apt install -y \
    chromium-browser \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libxkbcommon0 libxcomposite1 libxrandr2 libgbm1 libasound2 \
    libpangocairo-1.0-0 libpango-1.0-0 libgtk-3-0 libxdamage1 libxfixes3 \
    libdrm2 libxshmfence1 libx11-xcb1 libxcb1 libxext6 libxrender1 \
    libxi6 libxtst6 libglib2.0-0 libdbus-1-3 libfontconfig1 libfreetype6
    """)
    chromium_path = "/usr/bin/chromium-browser"
# -------------------------------------------------
# 7. Media Tools
# -------------------------------------------------
run_command("sudo apt install -y ffmpeg imagemagick")
# -------------------------------------------------
# 8. Fonts
# -------------------------------------------------
run_command("""
sudo apt install -y \
fonts-liberation fonts-dejavu fonts-freefont-ttf
""")
# -------------------------------------------------
# 9. Clone Project
# -------------------------------------------------
if not os.path.exists(PROJECT_FOLDER):
    run_command(f"git clone {PROJECT_GIT}")
else:
    print("✅ Project already exists. Skipping clone.")
os.chdir(PROJECT_FOLDER)
# -------------------------------------------------
# 10. Install Project Dependencies
# -------------------------------------------------
run_command("pnpm install")
# -------------------------------------------------
# 11. Set Puppeteer Chromium Path
# -------------------------------------------------
os.environ["PUPPETEER_EXECUTABLE_PATH"] = chromium_path
print(f"🧩 Puppeteer Chromium Path: {chromium_path}")
# -------------------------------------------------
# 12. Render Video
# -------------------------------------------------
run_command("pnpm render")
# -------------------------------------------------
# 13. Start HTTP Server
# -------------------------------------------------
print("\n🚀 Starting HTTP Server...")
run_command(f"python3 -m http.server {HTTP_PORT}")
