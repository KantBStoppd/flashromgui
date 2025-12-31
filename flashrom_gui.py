import wx
import os
import platform
import shutil
import sys
import wx.adv
import subprocess
import re
import threading
from flashrom_controller import FlashromController
from PIL import Image

def get_flashrom_path(): 
    system = platform.system() 
    
    if system == "Windows":
        # Your bundled EXE 
        return os.path.join(os.getcwd(), "flashrom", "flashrom.exe")

        if system == "Darwin": # macOS
            # 1. Try MacPorts 
            macports_path = "/opt/local/bin/flashrom"
            if os.path.exists(macports_path):
                return macports_path

            # 2. Try Homebrew (Intel)
            brew_path_intel = "/usr/local/bin/flashrom"
            if os.path.exists(brew_path_intel):
                return brew_path_intel

            # 3. Try Homebrew (Apple Silicon) 
            brew_path_arm = "/opt/homebrew/bin/flashrom"
            if os.path.exists(brew_path_arm):
                return brew_path_arm

            # 4. Try PATH
            path = shutil.which("flashrom")
            if path:
                return path

            raise FileNotFoundError("flashrom not found on macOS")

        if system == "Linux":
            path = shutil.which("flashrom")
            if path:
                return path
            raise FileNotFoundError("flashrom not found on Linux")
            
        raise RuntimeError("Unsupported OS")

class MyApp(wx.App):
    def OnInit(self):
        splash_path = resource_path("assets/splashscreen.png")
        bitmap = wx.Bitmap(splash_path, wx.BITMAP_TYPE_PNG)
        splash = wx.adv.SplashScreen(
            bitmap,
            wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT,
            5000,
            None,
            -1,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.BORDER_SIMPLE | wx.STAY_ON_TOP
        )
        wx.Yield()
        self.frame = FlashromGUI(None, "Flashrom GUI")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

class ZoomableBitmap(wx.StaticBitmap):
    def __init__(self, parent, normal_path, zoomed_path, callback, grey_path=None, zoomed_grey_path=None):
        super().__init__(
            parent,
            bitmap=wx.BitmapBundle.FromBitmap(
                wx.Bitmap(normal_path, wx.BITMAP_TYPE_PNG)
            )
        )
        self.normal_path = normal_path
        self.zoomed_path = zoomed_path
        self.grey_path = grey_path
        self.zoomed_grey_path = zoomed_grey_path
        self.callback = callback
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_mouse_leave)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_click)
        
    def Enable(self, enable=True):
        super().Enable(enable)
        if enable:
            self.SetBitmap(
                wx.BitmapBundle.FromBitmap(
                    wx.Bitmap(self.normal_path, wx.BITMAP_TYPE_PNG)
                )
            )
        else:
             if self.grey_path:
                 self.SetBitmap(
                     wx.BitmapBundle.FromBitmap(
                         wx.Bitmap(self.grey_path, wx.BITMAP_TYPE_PNG)
                     )
                 )
        
    def on_mouse_enter(self, event):
        bmp = wx.Bitmap(self.zoomed_path)
        self.SetBitmap(wx.BitmapBundle.FromBitmap(bmp))
        self.SetSize(bmp.GetSize())
        self.GetParent().Layout()
        self.Refresh()
        event.Skip()

    def on_mouse_leave(self, event):
        bmp = wx.Bitmap(self.normal_path)
        self.SetBitmap(wx.BitmapBundle.FromBitmap(bmp))
        self.SetSize(bmp.GetSize())
        self.GetParent().Layout()
        self.Refresh()
        event.Skip()

    def on_click(self, event):
        if self.callback:
            self.callback(event)
        event.Skip()

def resource_path(relative_path):
    """
    Get absolute path to a resource.
    Works for:
      - PyInstaller one-file (_MEIPASS)
      - PyInstaller one-folder
      - macOS .app bundles (Contents/Resources)
      - Running from source
    """
    # 1. PyInstaller one-file or one-folder
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    # 2. macOS .app bundle support
    # If frozen and running inside MyApp.app/Contents/MacOS/
    if getattr(sys, 'frozen', False) and sys.platform == "darwin":
        macos_app_resources = os.path.abspath(
            os.path.join(os.path.dirname(sys.executable), "..", "Resources")
        )
        if os.path.exists(macos_app_resources):
            return os.path.join(macos_app_resources, relative_path)

    # 3. Normal case (source or PyInstaller fallback)
    return os.path.join(base_path, relative_path)

class FlashromGUI(wx.Frame):
    def load_chip_list(self):
        chips = []
        try:
            exe_path = get_flashrom_path()

            # Optional: helpful for debugging
            if hasattr(self, "log_ctrl"):
                self.log_output(f"Running: {exe_path} -L")

            output = subprocess.check_output(
                [exe_path, "-L"],
                encoding="utf-8",
                stderr=subprocess.STDOUT
            )

            if not output.strip():
                self.log_output("Flashrom returned no chip list output.")

            for line in output.splitlines():
                line = line.strip()
                if line and not line.startswith("Supported"):
                    chips.append(line)

        except Exception as e:
            message = f"Failed to load chip list:\n{e}"
            if hasattr(self, "log_ctrl"):
                self.log_output(message)
            else:
                print(message)

        return chips


        
    def populate_chip_list(self):
        chip_list = self.load_chip_list()
        self.chip_combo.Set(chip_list)

            
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=wx.Size(800, 600))
        app_icon = resource_path("assets/icons/icon.ico")
        self.SetIcon(wx.Icon(app_icon, wx.BITMAP_TYPE_ANY))
        self.statusbar = self.CreateStatusBar()
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(106, 201, 255))

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer_tick, self.timer)
        self.progress_value = 0

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(frame_sizer)

        icon_panel = wx.Panel(self.panel)
        icon_panel.SetMinSize(wx.Size(800, 150))
        icon_sizer = wx.BoxSizer(wx.HORIZONTAL)
        icon_panel.SetSizer(icon_sizer)
        
        self.icon_widgets = {}

        icon_map = {
            "probe": self.on_probe,
            "detect": self.on_detect,
            "read": self.on_read,
            "write": self.on_write,
            "verify": self.on_verify
        }

        icon_dir = resource_path("assets/icons/zoombar")
        
        icon_sizer.InsertStretchSpacer(0)
        for name, callback in icon_map.items():
            normal_path = os.path.join(icon_dir, f"{name}.png")
            zoomed_path = os.path.join(icon_dir, f"zoomed_{name}.png")
            grey_path = os.path.join(icon_dir, f"{name}_grey.png")
            zoomed_grey_path = os.path.join(icon_dir, f"zoomed_{name}_grey.png")
            icon = ZoomableBitmap(icon_panel, normal_path, zoomed_path, callback, grey_path, zoomed_grey_path)
            icon_sizer.Add(icon, 0, wx.EXPAND | wx.ALL, 0)
            self.icon_widgets[name] = icon
        icon_sizer.AddStretchSpacer()

        chip_zoom_sizer = wx.BoxSizer(wx.VERTICAL)
        chip_zoom_sizer.Add(icon_panel, 0, wx.ALIGN_CENTER | wx.TOP, 10)
        chip_zoom_sizer.AddSpacer(10)
        self.chip_combo = wx.ComboBox(self.panel, choices=[], style=wx.CB_DROPDOWN)
        wx.CallAfter(self.populate_chip_list)
        label = wx.StaticText(self.panel, wx.ID_ANY, "Select Chip")
        label.SetFont(wx.Font(9, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        label.SetForegroundColour(wx.Colour(255, 255, 255))  # white text
        label.SetBackgroundColour(wx.Colour(35, 38, 37))
        chip_zoom_sizer.Add(label, 0, wx.LEFT | wx.BOTTOM, 5)
        chip_zoom_sizer.Add(self.chip_combo, 0, wx.EXPAND | wx.BOTTOM, 10)

        file_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.file_path_ctrl = wx.TextCtrl(self.panel)
        self.browse_button = wx.Button(self.panel, label="Browse")
        file_sizer.Add(self.file_path_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        file_sizer.Add(self.browse_button, 0, wx.ALL, 5)

        log_sizer = wx.BoxSizer(wx.HORIZONTAL)
        log_sizer.AddSpacer(5)
        self.log_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.HSCROLL | wx.TE_READONLY)
        log_sizer.Add(self.log_ctrl, 1, wx.EXPAND)
        log_sizer.AddSpacer(5)

        programmer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        programmer_sizer.AddStretchSpacer()
        combo_sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.panel, wx.ID_ANY, "Select Programmer")
        label.SetFont(wx.Font(9, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        label.SetForegroundColour(wx.Colour(255, 255, 255))  # white text
        label.SetBackgroundColour(wx.Colour(35, 38, 37))
        combo_sizer.Add(label, 0, wx.LEFT | wx.BOTTOM, 5)
        self.programmer_combo = wx.ComboBox(self.panel, choices=[
            "ch341a_spi", "internal", "dummy", "nic3com", "nicrealtek", "nicnatsemi", "gfxnvidia",
            "raiden_debug_spi", "drkaiser", "satasii", "atahpt", "atavia", "atapromise", "it8212",
            "ft2232_spi", "serprog", "buspirate_spi", "dediprog", "developerbox", "rayer_spi",
            "pony_spi", "nicintel", "nicintel_spi", "nicintel_eeprom", "ogp_spi", "satamv",
            "linux_mtd", "linux_spi", "parade_lspcon", "mediatek_i2c_spi", "realtek_mst_i2c_spi",
            "usbblaster_spi", "mstarddc_spi", "pickit2_spi", "ch347_spi", "digilent_spi",
            "jlink_spi", "ni845x_spi", "stlinkv3_spi", "dirtyjtag_spi", "spidriver"
        ], style=wx.CB_DROPDOWN)
        combo_sizer.Add(self.programmer_combo, 0, wx.ALIGN_RIGHT | wx.BOTTOM, 10)
        programmer_sizer.Add(combo_sizer, 0, wx.RIGHT | wx.BOTTOM, 10)

        self.progress_bar = wx.Gauge(self.panel, range=100, style=wx.GA_HORIZONTAL)
        self.progress_bar.Hide()

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(file_sizer, 0, wx.EXPAND)
        self.main_sizer.Add(chip_zoom_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        self.main_sizer.Add(log_sizer, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)
        self.main_sizer.Add(programmer_sizer, 0, wx.EXPAND)
        self.main_sizer.Add(self.progress_bar, flag=wx.EXPAND | wx.ALL, border=10)
        
        self.copy_log_button = wx.Button(self.panel, label="Copy Log")
        self.main_sizer.Add(self.copy_log_button, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)

        self.panel.SetSizer(self.main_sizer)
        self.panel.Layout()
        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.on_browse, self.browse_button)
        self.Bind(wx.EVT_COMBOBOX, self.on_chip_selected, self.chip_combo)
        self.Bind(wx.EVT_COMBOBOX, self.on_programmer_selected, self.programmer_combo)
        self.Bind(wx.EVT_BUTTON, self.on_copy_log, self.copy_log_button)
        self.controller = FlashromController(on_output=self.log_output)
    
    def detect_chip(self):
        try:
            result = subprocess.run(
                ["flashrom", "-p", "internal"],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
            self.log_ctrl.AppendText(output + "\n")
            
           # Try to extract
            match = re.search(r"Found\s+([^\n]+?)\s+flash\s+chip", output)
            if match:
                detected_chip = match.group(1).strip()
                self.log_ctrl.AppendText(f"Detected chip: {detected_chip}\n")
                self.sync_chip_selection(detected_chip)
            else:
                self.log_ctrl.AppendText("No chip detected.\n")
                
        except subprocess.CalledProcessError as e:
            self.log_ctrl.AppendText(f"Detection failed:\n{e.stderr}\n")
            
    def sync_chip_selection(self, detected_chip):
        choices = [choice.lower() for choice in self.chip_combo.GetItems()]
        if detected_chip.lower() in choices:
            self.chip_combo.SetValue(detected_chip)
            self.log_ctrl.AppendText(f"Chip auto-selected: {detected_chip}\n")
        else:
            self.log_ctrl.AppendText(f"Detected chip not in list. Please select manually.\n")
            
    def set_icons_enabled(self, enabled):
        for icon in self.icon_widgets.values():
            icon.Enable(enabled)

    def on_timer_tick(self, event):
        self.progress_value += 2
        if self.progress_value >= 100:
            self.timer.Stop()
            self.progress_bar.Hide()
        else:
            self.progress_bar.SetValue(self.progress_value)

    def log_output(self, message):
        self.log_ctrl.AppendText(message + "\n")
        self.statusbar.SetStatusText(message)

    def on_browse(self, event):
        with wx.FileDialog(self, "Open file", wildcard="*.*",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.file_path_ctrl.SetValue(dlg.GetPath())

    def on_chip_selected(self, event):
        chip = self.chip_combo.GetValue()
        self.log_ctrl.AppendText(f"Chip selected: {chip}\n")

    def get_filepath(self):
        return self.file_path_ctrl.GetValue()

    def get_programmer(self):
        return self.programmer_combo.GetValue()
        
    def on_programmer_selected(self, event):
        programmer = self.programmer_combo.GetValue()
        self.log_ctrl.AppendText(f"Programmer selected: {programmer}\n")

    def run_flashrom(self, args, action_label):
        self.statusbar.SetStatusText(action_label)
        self.log_ctrl.SetValue(f"{action_label}\nRunning: flashrom {' '.join(args)}\n")

        self.set_icons_enabled(False)

        def task():
            try:
                # Cross‑platform flashrom path
                flashrom_path = get_flashrom_path()
                full_cmd = [flashrom_path] + args

                result = subprocess.run(
                    full_cmd,
                    capture_output=True,
                    text=True
                )

                wx.CallAfter(
                    self.log_ctrl.AppendText,
                    result.stdout + "\n" + result.stderr
                )
                wx.CallAfter(
                    self.statusbar.SetStatusText,
                    "Done" if result.returncode == 0 else "Failed"
                )

            except Exception as e:
                wx.CallAfter(self.log_output, f"Error: {e}")
                wx.CallAfter(self.statusbar.SetStatusText, "Error")

            finally:
                wx.CallAfter(self.timer.Stop)
                wx.CallAfter(self.progress_bar.Hide)
                wx.CallAfter(self.set_icons_enabled, True)

        threading.Thread(target=task).start()


    def on_detect(self, event=None):
        if not hasattr(self, 'controller'):
            self.log_output("Flashrom controller not initialized.")
            return

        try:
            exe_path = get_flashrom_path()

            result = subprocess.run(
                [exe_path, "-p", "internal"],
                capture_output=True,
                text=True
            )

            output = result.stdout
            self.log_output(output)

            # Corrected regex (your original had args reversed)
            match = re.search(r"Found\s+([^\n]+?\s+flash\s+chip)", output)
            if match:
                detected_chip = match.group(1).strip()
                self.log_output(f"Detected chip: {detected_chip}")

                # Sync with dropdown
                choices = [c.lower() for c in self.chip_combo.GetItems()]
                if detected_chip.lower() in choices:
                    self.chip_combo.SetValue(detected_chip)
                    self.log_output(f"Chip auto-selected: {detected_chip}")
                else:
                    self.log_output("Detected chip not in list. Please select manually.")
            else:
                self.log_output("No chip detected.")

        except Exception as e:
            self.log_output(f"Detection failed:\n{e}")

        # Controller fallback
        programmer = self.get_programmer()
        chip_name = self.controller.on_detect_chip(programmer)
        self.chip_combo.SetValue(chip_name if chip_name else "Unknown")


    def on_read(self, event=None):
        with wx.FileDialog(
            self,
            message="Save ROM dump as...",
            wildcard="ROM files (*.bin)|*.bin|All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as save_dialog:
            if save_dialog.ShowModal() == wx.ID_CANCEL:
                return

            save_path = save_dialog.GetPath()

        self.progress_value = 0
        self.progress_bar.SetValue(0)
        self.progress_bar.Show()
        self.timer.Start(100)

        args = ["-p", self.get_programmer(), "-r", save_path]
        self.run_flashrom(args, "Reading chip...")


    def on_write(self, event=None):
        if not self.get_filepath():
            wx.MessageBox("Please select a ROM file.", "Error", wx.OK | wx.ICON_ERROR)
            return

        self.progress_value = 0
        self.progress_bar.SetValue(0)
        self.progress_bar.Show()
        self.timer.Start(100)

        args = ["-p", self.get_programmer(), "-w", self.get_filepath()]
        self.run_flashrom(args, "Writing chip...")


    def on_verify(self, event=None):
        if not self.get_filepath():
            wx.MessageBox("Please select a ROM file.", "Error", wx.OK | wx.ICON_ERROR)
            return

        self.progress_value = 0
        self.progress_bar.SetValue(0)
        self.progress_bar.Show()
        self.timer.Start(100)

        args = ["-p", self.get_programmer(), "-v", self.get_filepath()]
        self.run_flashrom(args, "Verifying chip...")

        
    def on_probe(self, event):
        output = self.controller.on_probe_chip()
        self.log_output(output)
        
    def on_copy_log(self, event):
        log_text = self.log_ctrl.GetValue()
        if not log_text.strip():
            wx.MessageBox("Log is empty.", "Save Log", wx.ICON_INFORMATION)
            return
            
        log_path = os.path.join(os.getcwd(), "log_file.txt")
        try:
            with open(log_path, 'w', encoding='utf-8') as file:
                file.write(log_text)
            wx.MessageBox(f"Log saved to:\n{log_path}", "Save Log", wx.ICON_INFORMATION)
        except IOError as e:
            wx.MessageBox(f"Failed to save log:\n{e}", "Error", wx.ICON_ERROR)

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()