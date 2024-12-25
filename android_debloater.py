import re
import threading
import subprocess
import tkinter as tk
from pathlib import Path
from gui import GUI, DefaultPackageManager
from tkinter import ttk, filedialog, messagebox


class AndroidDebloater(GUI, DefaultPackageManager):
    """A GUI application to debloat Android devices using ADB."""

    def __init__(self, root: tk.Tk, title: str):
        """
        Initialize the AndroidDebloater application.

        Args:
            root (tk.Tk): The root Tkinter window.
            title (str): The title of the application window.
        """
        self.adb_active: bool = False
        self.selected_apps: set = set()
        self.devices: list = []
        self.device_info: dict = {}

        super().__init__(root, title)
        self.adb_path: Path = Path("assets/adb/adb.exe")
        self.package_command = lambda: self.debloat_selected(self.package_tree_holder)

    def execute(self, command: str, print_log: bool = True) -> subprocess.CompletedProcess | None:
        """
        Execute the given adb command.

        Args:
            command (str): The adb command to execute.
            print_log (bool): Whether to print the command log. Defaults to True.

        Returns:
            subprocess.CompletedProcess | None: The result of the command execution.
        """
        command_list = [self.adb_path] + command.split()
        try:
            return subprocess.run(
                command_list,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except subprocess.CalledProcessError as e:
            if print_log:
                self.log_message(f"Error: {e.stderr}")
            return None

    def start_adb(self) -> None:
        """Start the adb server."""
        threading.Thread(target=self._start_adb_thread).start()

    def _start_adb_thread(self) -> None:
        """Start the adb server in a separate thread."""
        try:
            self.log_message("ADB server is starting...")
            self.execute("start-server")
            self.adb_active = True
            self.log_message("ADB server started.")
            self.get_device_name()
        except Exception as e:
            self.log_message(f"Failed to start ADB: {e}")

    def stop_adb(self) -> None:
        """Stop the adb server."""
        try:
            if self.adb_active:
                self.execute("kill-server")
                self.adb_active = False
                self.log_message("ADB server stopped.")
        except Exception as e:
            self.log_message(f"Failed to stop ADB: {e}")

    def get_device_model(self, device: str) -> str:
        """
        Get the model name of the connected device.

        Args:
            device (str): The device ID.

        Returns:
            str: The model name of the device.
        """
        try:
            result = self.execute(f"-s {device} shell getprop ro.product.model")
            if result and result.returncode == 0:
                return result.stdout.strip()
            return "unknown"
        except Exception as e:
            self.log_message(f"Failed to get model for device {device}: {e}")
            return "unknown"

    def get_device_name(self) -> None:
        """Fetch the list of connected devices."""
        if not self.adb_active:
            self.log_message("ADB is not active. Start ADB first.")
            return

        threading.Thread(target=self._get_device_name_thread).start()

    def _get_device_name_thread(self) -> None:
        """Fetch the list of connected devices in a separate thread."""
        try:
            result = self.execute("devices")
            if not result:
                return

            devices_output = result.stdout.strip()
            device_lines = devices_output.splitlines()[1:]
            device_names = []

            for line in device_lines:
                device_id, status = line.split()
                if status == "unauthorized":
                    self.show_permission_warning(device_id)
                    return
                model = self.get_device_model(device_id)
                device_names.append(f"{model} - {device_id}")

            self.device_dropdown["values"] = device_names
            if device_names:
                self.device_var.set(device_names[0])
        except Exception as e:
            self.log_message(f"Failed to get device names: {e}")

    def get_selected_device_id(self) -> tuple[str, str] | None:
        """
        Get the ID of the selected device.

        Returns:
            tuple[str, str] | None: The device ID and model name.
        """
        selected_device = self.device_var.get()
        if selected_device:
            model, device_id = selected_device.rsplit(" - ", 1)
            return device_id, model
        self.log_message("No Device Selected")
        return None

    def fetch_apps(self) -> None:
        """Fetch the list of installed applications on the selected device."""
        threading.Thread(target=self._fetch_apps_thread).start()

    def _fetch_apps_thread(self) -> None:
        """Fetch the list of installed applications in a separate thread."""
        try:
            device_info = self.get_selected_device_id()
            if not device_info:
                return
            device, model = device_info
            self.log_message(f"Fetching installed applications from {model} - {device}...")

            result_all = self.execute(f"-s {device} shell pm list packages")
            result_disabled = self.execute(f"-s {device} shell pm list packages -d")
            result_system = self.execute(f"-s {device} shell pm list packages -s")

            if not result_all or not result_disabled or not result_system:
                raise Exception("Error fetching package lists.")

            all_apps = [line.replace("package:", "").strip() for line in result_all.stdout.splitlines() if line.strip()]
            disabled_apps = {line.replace("package:", "").strip() for line in result_disabled.stdout.splitlines() if line.strip()}
            system_apps = {line.replace("package:", "").strip() for line in result_system.stdout.splitlines() if line.strip()}

            self.app_list = [
                {"package": app, "status": "Disabled" if app in disabled_apps else "Active",
                 "type": "System" if app in system_apps else "User"}
                for app in all_apps
            ]
            self.log_message(f"Loaded {len(self.app_list)} applications for {model} - {device}.")
            self.update_app_tree()
        except Exception as e:
            self.log_message(f"Error fetching applications: {e}")

    def load_applications(self) -> None:
        """Load the list of applications from the device."""
        if not self.adb_active:
            self.log_message("ADB is not active. Start ADB first.")
            return
        self.fetch_apps()

    def debloat(self, apps: list[str]) -> None:
        """
        Uninstall the selected applications from the device.

        Args:
            apps (list[str]): The list of application package names to uninstall.
        """
        threading.Thread(target=self._debloat_thread, args=(apps,)).start()

    def _debloat_thread(self, apps: list[str]) -> None:
        """Uninstall the selected applications in a separate thread."""
        for app in apps:
            try:
                device_info = self.get_selected_device_id()
                if not device_info:
                    return
                device, _ = device_info
                self.log_message(f"Debloating {app}...")
                result = self.execute(f"-s {device} shell pm uninstall -k --user 0 {app}")
                if result and result.returncode == 0:
                    self.log_message(f"Successfully debloated: {app}")
                    self.app_list = [
                        item for item in self.app_list if item["package"] != app
                    ]
                else:
                    raise Exception(result.stderr if result else "Unknown error")
            except Exception as e:
                self.log_message(f"Failed to debloat {app}: {e}\nDid you connect the device?")
        self.update_app_tree()

    def debloat_selected(self, package_tree: ttk.Treeview = None) -> None:
        """
        Uninstall the selected applications from the tree view.

        Args:
            package_tree (ttk.Treeview, optional): The tree view containing the application packages.
        """
        selected_items = package_tree.selection() if package_tree else self.app_tree.selection()
        if not selected_items:
            self.log_message("No application selected for debloating.")
            return

        selected_apps = [
            package_tree.item(item, "values")[1] if package_tree else self.app_tree.item(item, "values")[0]
            for item in selected_items
        ]
        self.debloat(selected_apps)

    def remove_apps_from_path(self) -> None:
        """Remove applications from paths listed in a text file."""
        if not self.adb_active:
            self.log_message("ADB is not active. Start ADB first.")
            return

        if not self._check_root_access():
            self.log_message("Root Access Required")
            return

        # Run the file dialog in a separate thread to avoid freezing the GUI
        threading.Thread(target=self._select_and_process_file).start()

    def _select_and_process_file(self) -> None:
        """Open a file dialog to select a text file and process it in a separate thread."""
        exe_directory = Path(__file__).parent.resolve()
        initial_directory = exe_directory / 'assets'
        txt_file_path = filedialog.askopenfilename(
            title="Select Txt File",
            initialdir=initial_directory,
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
        )

        if not txt_file_path:
            self.log_message("No file selected!")
            return
        
        confirm = messagebox.askyesno(
            "Confirm Removal",
            "Removing files can damage your device. Do you want to proceed?"
        )

        if not confirm:
            self.log_message("File removal canceled by user.")
            return

        threading.Thread(target=self._remove_apps_in_thread, args=(txt_file_path,)).start()

    def _remove_apps_in_thread(self, txt_file_path: str) -> None:
        """Remove applications from paths listed in a text file in a separate thread."""
        try:
            serial_number, device_model = self.get_selected_device_id()

            with open(txt_file_path, "r") as file:
                lines = file.readlines()
            
            if not lines:
                self.log_message("The selected file is empty.")
                return                

            if any("/system" in line for line in lines):
                self.execute(f"-s {serial_number} shell su -c mount -o rw,remount /system")
                self.log_message("System mounted as READ/WRITE")

            pattern = re.compile(r"/[^ ]+")

            for line in lines:
                matches = pattern.findall(line)
                for match in matches:
                    app_path = match
                    rm_command = f"-s {serial_number} shell rm -r {app_path}"
                    result = self.execute(rm_command, print_log=False)
                    try:
                        if result.returncode == 0:
                            self.log_message(f"Successfully removed: {app_path}")
                        else:
                            self.log_message(f"Failed to remove: {app_path}. Error: {result.stderr}")
                    except AttributeError:
                        self.log_message(f"{app_path} already does not exist on {device_model} ({serial_number}).")
            self.log_message("DONE!")
        except Exception as e:
            self.log_message(f"An error occurred: {e}")

    def _check_root_access(self) -> bool:
        """Check if the device has root access."""
        serial_number, _ = self.get_selected_device_id()
        command = f"-s {serial_number} shell su -c echo rooted"
        result = self.execute(command)
        try:
            if result and "rooted" in result.stdout:
                return True
        except AttributeError:
            return False
        return False


if __name__ == '__main__':
    root = tk.Tk()
    app = AndroidDebloater(root, "Android Debloater")
    app.set_icon(root, Path("assets/android_debloater.ico"))
    root.mainloop()