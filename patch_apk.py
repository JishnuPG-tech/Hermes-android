import os
import re
from PIL import Image

decoded_dir = "claude_decoded"
source_icon = "hermes_icon_source.png"

print("[*] Starting Hermes APK Patcher...")

# 1. Patch app_name in strings.xml
strings_path = os.path.join(decoded_dir, "res", "values", "strings.xml")
if os.path.exists(strings_path):
    with open(strings_path, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(r'<string name="app_name">[^<]+</string>', '<string name="app_name">Hermes</string>', content)
    with open(strings_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("  [1] Updated app_name in strings.xml to 'Hermes'")

# 2. Generate launcher icons from source icon
if os.path.exists(source_icon):
    img = Image.open(source_icon).convert("RGBA")
    SIZES = {
        "mipmap-mdpi":    48,
        "mipmap-hdpi":    72,
        "mipmap-xhdpi":   96,
        "mipmap-xxhdpi":  144,
        "mipmap-xxxhdpi": 192,
    }
    for folder, size in SIZES.items():
        dest_dir = os.path.join(decoded_dir, "res", folder)
        os.makedirs(dest_dir, exist_ok=True)
        bg = Image.new("RGBA", (size, size), (15, 23, 42, 255))
        resized = img.resize((size, size), Image.LANCZOS)
        bg.paste(resized, (0, 0), resized)
        bg.convert("RGB").save(os.path.join(dest_dir, "ic_launcher.png"), "PNG")
        bg.convert("RGB").save(os.path.join(dest_dir, "ic_launcher_round.png"), "PNG")
        resized.save(os.path.join(dest_dir, "ic_launcher_foreground.png"), "PNG")
    
    # Adaptive icon XMLs
    anydpi_dir = os.path.join(decoded_dir, "res", "mipmap-anydpi")
    os.makedirs(anydpi_dir, exist_ok=True)
    with open(os.path.join(anydpi_dir, "ic_launcher.xml"), "w", encoding="utf-8") as f:
        f.write("""<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
""")
    with open(os.path.join(anydpi_dir, "ic_launcher_round.xml"), "w", encoding="utf-8") as f:
        f.write("""<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
""")
    print("  [2] Replaced launcher icons with Hermes anime illustration")

# 3. Patch backend API endpoints in Smali
old_endpoints = [
    "https://api.claude.ai",
    "https://api.claude-ai.staging.ant.dev",
    "https://claude.ai",
    "https://claude-ai.staging.ant.dev"
]
new_endpoint = "https://jishnupg-opencode-cli.hf.space/hermes/v1"

patched_smali = 0
for root, dirs, files in os.walk(decoded_dir):
    for f in files:
        if f.endswith(".smali"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
            modified = False
            for old_ep in old_endpoints:
                if old_ep in content:
                    content = content.replace(old_ep, new_endpoint)
                    modified = True
            if modified:
                with open(path, "w", encoding="utf-8") as fp:
                    fp.write(content)
                patched_smali += 1

print(f"  [3] Patched {patched_smali} smali files with Hermes endpoint: {new_endpoint}")

# 4. Patch Network Security Config
net_sec_path = os.path.join(decoded_dir, "res", "xml", "network_security_config.xml")
if os.path.exists(net_sec_path):
    with open(net_sec_path, "w", encoding="utf-8") as f:
        f.write("""<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="true">
        <trust-anchors>
            <certificates src="system" />
            <certificates src="user" />
        </trust-anchors>
    </base-config>
</network-security-config>""")
    print("  [4] Updated network_security_config.xml")

print("[*] All patches successfully applied.")
