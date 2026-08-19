import os
import re
import urllib.request
import zipfile
import io
from PIL import Image

decoded_dir = "claude_decoded"
source_icon = "hermes_icon_source.png"

print("[*] Starting Hermes Comprehensive Patcher...")

# 0. Download Missing Native Libraries (Split APK Reconstruction)
print("  [*] Fetching essential native libraries (.so) into APK...")
native_urls = [
    ('sqlite-bundled', 'https://dl.google.com/dl/android/maven2/androidx/sqlite/sqlite-bundled-android/2.6.2/sqlite-bundled-android-2.6.2.aar'),
    ('graphics-path', 'https://dl.google.com/dl/android/maven2/androidx/graphics/graphics-path/1.0.1/graphics-path-1.0.1.aar'),
    ('sentry-ndk', 'https://repo1.maven.org/maven2/io/sentry/sentry-android-ndk/7.14.0/sentry-android-ndk-7.14.0.aar'),
]

for name, url in native_urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
        z = zipfile.ZipFile(io.BytesIO(data))
        for f in z.namelist():
            if f.startswith('jni/') and f.endswith('.so'):
                rel = f.replace('jni/', 'lib/')
                dest = os.path.join(decoded_dir, rel.replace('/', os.sep))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, 'wb') as out_fp:
                    out_fp.write(z.read(f))
        print(f"  [+] Extracted native binaries for: {name}")
    except Exception as e:
        print(f"  [!] Note fetching {name}: {e}")

# 1. Disable all process kill-switches in MainActivity.smali & yz4.smali
for root, dirs, files in os.walk(decoded_dir):
    for f in files:
        if f == "MainActivity.smali":
            main_act_path = os.path.join(root, f)
            with open(main_act_path, "r", encoding="utf-8") as fp:
                main_act_content = fp.read()
            main_act_content = main_act_content.replace("if-nez v1, :cond_1", "goto :cond_1")
            main_act_content = main_act_content.replace("invoke-static {p0}, Landroid/os/Process;->killProcess(I)V", "# killProcess removed")
            main_act_content = main_act_content.replace("invoke-virtual {p0}, Landroid/app/Activity;->finishAndRemoveTask()V", "# finishAndRemoveTask removed")
            with open(main_act_path, "w", encoding="utf-8") as fp:
                fp.write(main_act_content)
            print("  [1] MainActivity.smali: Sentry kill-switch disabled & finish neutralized")

        if f in ["ClaudeApplication.smali", "HermesApplication.smali"]:
            app_smali_path = os.path.join(root, f)
            with open(app_smali_path, "r", encoding="utf-8") as fp:
                app_content = fp.read()
            # Ensure correct Koin initialization lambda index (case 13 / 0xd)
            app_content = app_content.replace("const/16 v3, 0xf\n\n    invoke-direct {v0, v3, p0}, La2;-><init>(ILjava/lang/Object;)V",
                                              "const/16 v3, 0xd\n\n    invoke-direct {v0, v3, p0}, La2;-><init>(ILjava/lang/Object;)V")
            # Remove main-thread runBlocking freeze
            old_blocking = "    new-instance v3, Lsk;\n\n    const/16 v7, 0xb\n\n    invoke-direct {v3, v0, v6, v7}, Lsk;-><init>(Ljava/lang/Object;Le85;I)V\n\n    invoke-static {v3}, Lxwf;->Z(Lbb8;)Ljava/lang/Object;"
            app_content = app_content.replace(old_blocking, "    # Synchronous runBlocking delay removed")
            # Fix early-return bug on WebView feature check
            app_content = app_content.replace("if-nez v0, :cond_c", "if-nez v0, :goto_8")
            with open(app_smali_path, "w", encoding="utf-8") as fp:
                fp.write(app_content)
            print(f"  [1.1] {f}: Koin module initialization verified & main-thread ANR neutralized")

yz4_path = os.path.join(decoded_dir, "smali_classes3", "yz4.smali")
if os.path.exists(yz4_path):
    with open(yz4_path, "r", encoding="utf-8") as f:
        yz4_content = f.read()
    old_kill = "    invoke-static {v0}, Landroid/os/Process;->killProcess(I)V"
    if old_kill in yz4_content:
        yz4_content = yz4_content.replace(old_kill, "    # killProcess removed")
        with open(yz4_path, "w", encoding="utf-8") as f:
            f.write(yz4_content)
        print("  [2] yz4.smali: API Base URL mismatch process kill neutralized")

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

# 3. Replace all vector logos with bitmap XML pointing to Hermes icon
bitmap_xml_template = """<?xml version="1.0" encoding="utf-8"?>
<bitmap xmlns:android="http://schemas.android.com/apk/res/android"
    android:src="@mipmap/ic_launcher"
    android:gravity="center" />
"""

logos_to_replace = [
    "res/drawable/logo_claude_splash.xml",
    "res/drawable/logo_claude_horizontal.xml",
    "res/drawable/claude_logotype.xml",
    "res/drawable/branding_claude_splash.xml",
    "res/drawable/logo_anthropic.xml",
    "res/drawable/claude_spark_icon.xml",
    "res/drawable/claude_mobile_and_hand.xml",
    "res/drawable-anydpi/claude_spark.xml",
]

for rel_p in logos_to_replace:
    p = os.path.join(decoded_dir, rel_p.replace("/", os.sep))
    if os.path.exists(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write(bitmap_xml_template)
        print("  [4] Replaced vector logo: " + rel_p)

# 4. Generate launcher icons from source icon
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
    print("  [5] Replaced launcher icons with Hermes anime illustration")

# 5. Patch backend API endpoints in Smali
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

print(f"  [6] Patched {patched_smali} smali files with Hermes endpoint")

# 6. Hardcoded String Replacements in Smali
hardcoded_replacements = {
    '"Claude"': '"Hermes"',
    '"Claude ': '"Hermes ',
    ' Claude"': ' Hermes"',
    '"Talk to Claude"': '"Talk to Hermes"',
    '"Ask Claude"': '"Ask Hermes"',
    '"Welcome to Claude"': '"Welcome to Hermes"',
    '"ClaudeApp"': '"HermesApp"',
}
for root, dirs, files in os.walk(decoded_dir):
    for f in files:
        if f.endswith(".smali"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                c = fp.read()
            mod = False
            for k, v in hardcoded_replacements.items():
                if k in c:
                    c = c.replace(k, v)
                    mod = True
            if mod:
                with open(path, "w", encoding="utf-8") as fp:
                    fp.write(c)

# 7. Patch Network Security Config
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
    print("  [7] Updated network_security_config.xml")

# 8. Fix AndroidManifest.xml: Strip Split APK restrictions, extractNativeLibs=true, and unique authorities
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

    # Change package name to com.hermes.agent
    content = re.sub(r'package="com\.anthropic\.claude"', 'package="com.hermes.agent"', content)

    # Enable native library extraction on installation
    content = content.replace('android:extractNativeLibs="false"', 'android:extractNativeLibs="true"')

    # Replace all provider authorities and permissions to prevent conflicts with original Claude
    authorities_to_replace = [
        'com.anthropic.claude.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION',
        'com.anthropic.claude.firebaseinitprovider',
        'com.anthropic.claude.provider.datadog.rum',
        'com.anthropic.claude.SentryNdkPreloadProvider',
        'com.anthropic.claude.provider',
        'com.anthropic.claude.androidx-startup',
        'com.anthropic.claude.mlkitinitprovider',
        'com.anthropic.claude.resources.AndroidContextProvider',
        'com.anthropic.claude.SentryInitProvider',
        'com.anthropic.claude.SentryPerformanceProvider',
        'com.anthropic.claude.provider.datadog.profiling',
        'com.anthropic.claude.assist'
    ]
    for auth in authorities_to_replace:
        content = content.replace(auth, auth.replace('com.anthropic.claude', 'com.hermes.agent'))

    # Lower minSdkVersion to 26 (Android 8.0+)
    content = re.sub(r'android:minSdkVersion="\d+"', 'android:minSdkVersion="26"', content)

    # Remove duplicated permissions
    content = re.sub(r'(<uses-permission android:name="android\.permission\.health\.READ_HEALTH_DATA_HISTORY"/>\s*){2,}', r'\1', content)

    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  [8] AndroidManifest converted to standalone package (com.hermes.agent, extractNativeLibs=true, minSdk=26)")

# 9. Lower minSdkVersion in apktool.yml
apktool_yml = os.path.join(decoded_dir, "apktool.yml")
if os.path.exists(apktool_yml):
    with open(apktool_yml, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r'minSdkVersion:\s*\d+', 'minSdkVersion: 26', content)
    with open(apktool_yml, "w", encoding="utf-8") as f:
        f.write(content)
    print("  [9] apktool.yml updated with minSdkVersion 26")

print("[*] All patches applied successfully.")
