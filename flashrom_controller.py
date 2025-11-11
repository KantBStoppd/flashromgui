# flashrom_controller.py
import subprocess
import wx

class FlashromController:
    def __init__(self, on_output=None):
        self.on_output = on_output or print

    def run_flashrom(self, mode, file_path, programmer="your_programmer"):
        if mode == "read":
            cmd = ["flashrom", "-p", programmer, "-r", file_path]
        elif mode == "write":
            cmd = ["flashrom", "-p", programmer, "-w", file_path]
        elif mode == "verify":
            cmd = ["flashrom", "-p", programmer, "-v", file_path]
        else:
            raise ValueError("Invalid mode")

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout, result.stderr

    def on_read_chip(self, event):
        filename = self.text_ctrl.GetValue()
        chip = self.chip_combo.GetValue()
        programmer = self.programmer_combo.GetValue()

        if not filename or not chip:
            wx.MessageBox("Please select a ROM file and chip.", "Missing Info", wx.ICON_WARNING)
            return

        stdout, stderr = self.run_flashrom("read", filename, programmer)
        self.output_text_ctrl.SetValue(stdout)
        if stderr:
            self.output_text_ctrl.AppendText("\nErrors:\n" + stderr)
        self.status_bar.SetStatusText("Read complete.")

    def on_write_chip(self, event):
        filename = self.text_ctrl.GetValue()
        chip = self.chip_combo.GetValue()
        programmer = self.programmer_combo.GetValue()

        if not filename or not chip:
            wx.MessageBox("Please select a ROM file and chip.", "Missing Info", wx.ICON_WARNING)
            return

        stdout, stderr = self.run_flashrom("write", filename, programmer)
        self.output_text_ctrl.SetValue(stdout)
        if stderr:
            self.output_text_ctrl.AppendText("\nErrors:\n" + stderr)
        self.status_bar.SetStatusText("Write complete.")

    def on_verify_chip(self, event):
        filename = self.text_ctrl.GetValue()
        chip = self.chip_combo.GetValue()
        programmer = self.programmer_combo.GetValue()

        if not filename or not chip:
            wx.MessageBox("Please select a ROM file and chip.", "Missing Info", wx.ICON_WARNING)
            return

        stdout, stderr = self.run_flashrom("verify", filename, programmer)
        self.output_text_ctrl.SetValue(stdout)
        if stderr:
            self.output_text_ctrl.AppendText("\nErrors:\n" + stderr)
        self.status_bar.SetStatusText("Verify complete.")


    def on_detect_chip(self, programmer="internal"):
        try:
            result = subprocess.run(
                ["flashrom", "-p", programmer],
                capture_output=True,
                text=True
            )
            output = result.stdout
            if self.on_output:
                self.on_output(f"Detecting chip with programmer '{programmer}'...\n{output}")

            for line in output.splitlines():
                if "Found chip" in line:
                    chip_name = line.split("\"")[1] if "\"" in line else line
                    return chip_name

            return None
        except Exception as e:
            if self.on_output:
                self.on_output(f"Detection error: {e}")
            return None
            
    def on_probe_chip(self):
        try:
            result = subprocess.run(
                ["flashrom"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Probe failed: {e.stderr}"
