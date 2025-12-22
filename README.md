# ⚡ **FlashromGUI**  
*A modern, user‑friendly graphical interface for Flashrom — designed for clarity, safety, and speed.*

<p align="center">
  <img src="assets/banner.png" width="80%" alt="FlashromGUI Banner">
</p>

<p align="center">
  <strong>Cross‑platform</strong> • <strong>Beginner‑friendly</strong> • <strong>Power‑user ready</strong>
</p>

---

## 🎯 **Overview**

FlashromGUI brings the power of the Flashrom command‑line utility into a clean, intuitive graphical interface.  
Whether you're a hardware enthusiast, firmware engineer, or technician, FlashromGUI streamlines reading, writing, verifying, and backing up firmware chips — without sacrificing control or transparency.

---

## ✨ **Features**

### 🖥️ **Modern, Responsive Interface**
- Clean layout built with wxPython  
- Dynamic status updates and progress indicators  
- Clear separation of critical actions (read/write/erase)

### 🔌 **Hardware‑Aware**
- Automatic chip detection  
- Real‑time logging panel  
- Supports common programmers and SPI devices

### 🛡️ **Safety‑Focused**
- Pre‑flash validation  
- Backup prompts  
- Error‑resistant workflow with detailed warnings

### 📦 **Portable Distribution**
- Fully packaged PyInstaller EXE  
- Optional Inno Setup installer with VC++ runtime  
- No Python installation required

---

## 📸 **Screenshots**

> *(Replace these with your actual images once ready)*

<p align="center">
  <img src="assets/screenshot_main.png" width="70%">
  <br>
  <em>Main interface</em>
</p>

<p align="center">
  <img src="assets/screenshot_log.png" width="70%">
  <br>
  <em>Live logging and chip detection</em>
</p>

---

## 🚀 **Installation**

### **Option 1 — Inno Setup Installer (Recommended)**
- Includes VC++ runtime  
- Creates Start Menu and Desktop shortcuts  
- Clean uninstall support  

Download the latest installer from the **Releases** page.

### **Option 2 — Portable EXE**
- No installation required  
- Just extract and run `FlashromGUI.exe`

---

## 🧩 **Usage**

### **Basic Workflow**
1. Launch FlashromGUI  
2. Select your programmer  
3. Detect the chip  
4. Choose an action:  
   - **Read** → Save a backup  
   - **Write** → Flash new firmware  
   - **Verify** → Confirm integrity
