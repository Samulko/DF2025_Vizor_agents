# China Workshop Setup Guide
# Solving UV/PyPI Firewall Issues

This guide helps workshop participants in China bypass firewall restrictions when installing Python packages with UV.

## Problem
The Great Firewall of China can block or severely slow down access to PyPI (Python Package Index), causing `uv sync` and package installations to fail or timeout.

## Solution
Use Chinese mirror sites that replicate PyPI packages locally within China.

---

## Quick Setup (Recommended)

### Step 1: Create UV Configuration Directory
```bash
# Linux/macOS
mkdir -p ~/.config/uv

# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "$env:APPDATA\uv"
```

### Step 2: Create UV Configuration File

**Linux/macOS:**
```bash
cat > ~/.config/uv/uv.toml << 'EOF'
[[index]]
name = "tsinghua"
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
EOF
```

**Windows (PowerShell):**
```powershell
@"
[[index]]
name = "tsinghua"
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
"@ | Out-File -FilePath "$env:APPDATA\uv\uv.toml" -Encoding UTF8
```

### Step 3: Test Configuration
```bash
cd /path/to/your/project
# IMPORTANT: Delete existing lock file first
rm uv.lock
uv sync
```

## Quick Fix: Environment Variable Method

If you need a quick solution without changing config files:

```bash
# Linux/macOS
export UV_INDEX_URL="https://mirrors.aliyun.com/pypi/simple/"
uv sync

# Windows (PowerShell)
$env:UV_INDEX_URL="https://mirrors.aliyun.com/pypi/simple/"
uv sync
```

---

## Alternative Mirror Sources

If Tsinghua University mirror is slow, try these alternatives:

### Alibaba Cloud (Aliyun)
```toml
[[index]]
name = "aliyun"
url = "https://mirrors.aliyun.com/pypi/simple/"
default = true
```

### University of Science and Technology of China (USTC)
```toml
[[index]]
name = "ustc"
url = "https://mirrors.ustc.edu.cn/pypi/simple"
default = true
```

### Douban
```toml
[[index]]
name = "douban"
url = "http://pypi.douban.com/simple/"
default = true
```

---

## Fallback Method: Using pip

If UV continues to have issues, use pip as a fallback:

### Step 1: Create pip configuration
```bash
# Linux/macOS
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF

# Windows
mkdir %APPDATA%\pip
echo [global] > %APPDATA%\pip\pip.ini
echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple >> %APPDATA%\pip\pip.ini
echo trusted-host = pypi.tuna.tsinghua.edu.cn >> %APPDATA%\pip\pip.ini
```

### Step 2: Install using pip
```bash
# Instead of uv sync, use:
pip install -r requirements.txt

# Or if you have a pyproject.toml:
pip install -e .
```

---

## Troubleshooting

### Issue: Mirror Changes Not Taking Effect
**Solution:** Delete the lock file and resync:
```bash
rm uv.lock
uv sync
```
This is **crucial** - UV caches package sources in the lock file!

### Issue: SSL Certificate Errors
**Solution:** Add `trusted-host` configuration:
```bash
pip install --trusted-host pypi.tuna.tsinghua.edu.cn -i https://pypi.tuna.tsinghua.edu.cn/simple package_name
```

### Issue: UV Not Respecting Mirror Configuration
**Solution:** Use command-line flags:
```bash
uv pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple package_name
```

### Issue: Some Packages Still Download from PyPI
**Explanation:** This is a known UV limitation. Some dependency resolution may still use PyPI.
**Solution:** Use the global configuration method above, which forces ALL requests through the mirror.

### Issue: Mirror is Slow or Unresponsive
**Solution:** Try a different mirror from the alternatives list above.

---

## Project-Specific Configuration

For this workshop project, you can also uncomment the mirror configuration in `pyproject.toml`:

```toml
# Uncomment these lines in pyproject.toml:
[[tool.uv.index]]
name = "tsinghua"
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
```

---

## Verification

To verify your setup is working:

1. Check that your configuration file exists:
   ```bash
   # Linux/macOS
   cat ~/.config/uv/uv.toml
   
   # Windows
   type %APPDATA%\uv\uv.toml
   ```

2. Test with a simple package install:
   ```bash
   uv pip install requests
   ```

3. Check the download URL in the output - it should show your chosen mirror.

---

## Workshop Support

If you encounter issues during the workshop:

1. Try a different mirror from the alternatives list
2. Use the pip fallback method
3. Ask for help from workshop facilitators
4. Check your internet connection

## Mirror Speed Comparison

You can test which mirror is fastest for you:

```bash
# Test Tsinghua
time uv pip install --dry-run --index-url https://pypi.tuna.tsinghua.edu.cn/simple requests

# Test Aliyun  
time uv pip install --dry-run --index-url https://mirrors.aliyun.com/pypi/simple/ requests

# Test USTC
time uv pip install --dry-run --index-url https://mirrors.ustc.edu.cn/pypi/simple requests
```

Use the fastest one for your configuration.

---

**Happy coding! 🐍🚀**