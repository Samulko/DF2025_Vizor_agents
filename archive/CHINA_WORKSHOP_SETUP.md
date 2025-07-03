# Workshop Setup Guide for China 🇨🇳

## What You Need to Do

Just run these two commands after setup:
```bash
git pull origin master
uv sync
```

That's it! The project is already configured to work in China.

---

## Step 1: Install UV (Python Package Manager)

### On Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

or 

pip install -i https://pypi.tuna.tsinghua.edu.cn/simple uv

```

### On macOS:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

or

pip install -i https://pypi.tuna.tsinghua.edu.cn/simple uv
```


After installation, restart your terminal.

Then run:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

After, restart thr terminal.

---

## Step 2: Switch to Ubuntu (If Using Docker/WSL) - if the text in the terminal appears green and blue you should be good. If its white, follow this step.

If you're using Docker Desktop or WSL with a different Linux distribution, switch to Ubuntu:

### For WSL Users:
```bash
# Install Ubuntu (if not already installed)
wsl --install -d Ubuntu

# Set Ubuntu as default
wsl --set-default Ubuntu

# Switch to Ubuntu
wsl -d Ubuntu
```

---

## Step 3: Update Ubuntu (Recommended)

```bash
# Update package list
sudo apt update

# Upgrade all packages
sudo apt upgrade -y

# Check Ubuntu version
lsb_release -a
```

---

## Step 4: Run the Workshop Project

```bash
# Navigate to your project folder
cd path/to/your/project

# Get latest changes
git pull origin master

# Install all dependencies (works in China!)
uv sync
```

---

## If Something Goes Wrong

### UV command not found?
Restart your terminal and try again.

### Internet connection issues?
The project is pre-configured to use Chinese mirrors, so `uv sync` should work automatically.

### Still having problems?
Ask a workshop facilitator for help!

---

**You're ready for the workshop! 🚀**