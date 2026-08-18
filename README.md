# Hermes Android APK Builder & Patcher

This repository maintains the automated patcher and cloud-build pipeline for the **Hermes** Android app.

---

## 🎯 What This Does
- Takes the native **Claude.apk** (preserving 100% of the exact UI/UX, animations, motion, and styling).
- Patches the backend API endpoints to point directly to your **Hermes Agent** server: `https://jishnupg-opencode-cli.hf.space/hermes/v1`.
- Replaces the application name to **Hermes**.
- Replaces all launcher and adaptive icons with the custom monochrome anime girl illustration.
- Builds, zipaligns, and signs the resulting **`Hermes.apk`** via GitHub Actions Cloud Build.
