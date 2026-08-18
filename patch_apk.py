import os
import re
from PIL import Image

decoded_dir = "claude_decoded"
source_icon = "hermes_icon_source.png"

print("[*] Starting Hermes Standalone & Bypass Patcher...")

# 1. Smali Auth Bypass: default to MainAppScreens$LoggedIn (hermes_user)
o49_path = os.path.join(decoded_dir, "smali", "o49.smali")
if os.path.exists(o49_path):
    with open(o49_path, "r", encoding="utf-8") as f:
        o49 = f.read()
    target_logged_out = """    new-instance v0, Lcom/anthropic/claude/app/main/MainAppScreens$LoggedOut;

    invoke-direct {v0, v5, v6, v5}, Lcom/anthropic/claude/app/main/MainAppScreens$LoggedOut;-><init>(Lcom/anthropic/claude/login/WelcomeNotice;ILxz5;)V"""
    replacement_logged_in = """    const-string v1, "hermes_user"

    new-instance v0, Lcom/anthropic/claude/app/main/MainAppScreens$LoggedIn;

    sget-object v2, Lxk;->M:Lxk;

    invoke-direct {v0, v1, v5, v2, v5}, Lcom/anthropic/claude/app/main/MainAppScreens$LoggedIn;-><init>(Ljava/lang/String;Ljava/lang/String;Lxk;Lxz5;)V"""
    if target_logged_out in o49:
        o49 = o49.replace(target_logged_out, replacement_logged_in)
        with open(o49_path, "w", encoding="utf-8") as f:
            f.write(o49)
        print("  [1] Patched o49.smali: Default initial screen set to MainAppScreens$LoggedIn")

il0_path = os.path.join(decoded_dir, "smali", "il0.smali")
if os.path.exists(il0_path):
    with open(il0_path, "r", encoding="utf-8") as f:
        il0 = f.read()
    d_target = """.method public final d()Ljava/lang/String;
    .locals 2"""
    d_repl = """.method public final d()Ljava/lang/String;
    .locals 1

    const-string v0, "hermes_user"

    return-object v0"""
    if d_target in il0:
        il0 = il0.replace(d_target, d_repl)
        with open(il0_path, "w", encoding="utf-8") as f:
            f.write(il0)
        print("  [2] Patched il0.smali: Persistent authenticated session enabled")

# 2. Patch strings.xml (Global Claude -> Hermes renaming)
strings_path = os.path.join(decoded_dir, "res", "values", "strings.xml")
if os.path.exists(strings_path):
    with open(strings_path, "r", encoding="utf-8") as f:
        s = f.read()
    s_new = re.sub(r'>([^<]*)Claude([^<]*)<', r'>\1Hermes\2<', s)
    s_new = re.sub(r'>([^<]*)Claude([^<]*)<', r'>\1Hermes\2<', s_new)
    s_new = s_new.replace("Anthropic", "Hermes AI")
    with open(strings_path, "w", encoding="utf-8") as f:
        f.write(s_new)
    print("  [3] Updated strings.xml with Hermes branding")

# 3. Generate launcher icons from source icon
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
    print("  [4] Replaced launcher icons with Hermes anime illustration")

# 4. Patch backend API endpoints in Smali
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

print(f"  [5] Patched {patched_smali} smali files with Hermes endpoint")

# 5. Patch Network Security Config
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
    print("  [6] Updated network_security_config.xml")

# 6. Fix AndroidManifest.xml: Strip Split APK restrictions & Lower minSdkVersion
manifest_path = os.path.join(decoded_dir, "AndroidManifest.xml")
if os.path.exists(manifest_path):
    with open(manifest_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove split attributes
    content = re.sub(r'\s*android:requiredSplitTypes="[^"]*"', '', content)
    content = re.sub(r'\s*android:splitTypes="[^"]*"', '', content)
    content = re.sub(r'\s*android:isSplitRequired="[^"]*"', '', content)

    # Remove Split APK meta-data
    split_metadata_patterns = [
        r'<meta-data\s+android:name="com\.android\.vending\.splits\.required"[^>]*/>\s*',
        r'<meta-data\s+android:name="com\.android\.vending\.splits"[^>]*/>\s*',
        r'<meta-data\s+android:name="com\.android\.vending\.derived\.apk\.id"[^>]*/>\s*',
        r'<meta-data\s+android:name="com\.android\.stamp\.source"[^>]*/>\s*',
        r'<meta-data\s+android:name="com\.android\.stamp\.type"[^>]*/>\s*'
    ]
    for p in split_metadata_patterns:
        content = re.sub(p, '', content)

    # Change package name to com.hermes.agent so it never conflicts with Play Store Claude
    content = re.sub(r'package="com\.anthropic\.claude"', 'package="com.hermes.agent"', content)
    content = content.replace('com.anthropic.claude.firebaseinitprovider', 'com.hermes.agent.firebaseinitprovider')
    content = content.replace('com.anthropic.claude.provider.datadog.rum', 'com.hermes.agent.provider.datadog.rum')
    content = content.replace('com.anthropic.claude.SentryNdkPreloadProvider', 'com.hermes.agent.SentryNdkPreloadProvider')

    # Lower minSdkVersion to 26 (Android 8.0+)
    content = re.sub(r'android:minSdkVersion="\d+"', 'android:minSdkVersion="26"', content)

    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  [7] AndroidManifest converted to standalone package (com.hermes.agent, minSdk=26)")

# 7. Lower minSdkVersion in apktool.yml
apktool_yml = os.path.join(decoded_dir, "apktool.yml")
if os.path.exists(apktool_yml):
    with open(apktool_yml, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r'minSdkVersion:\s*\d+', 'minSdkVersion: 26', content)
    with open(apktool_yml, "w", encoding="utf-8") as f:
        f.write(content)
    print("  [8] apktool.yml updated with minSdkVersion 26")

print("[*] All patches applied successfully.")
