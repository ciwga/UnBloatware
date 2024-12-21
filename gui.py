import sys
import queue
import threading
import subprocess
import tkinter as tk
from pathlib import Path
from datetime import datetime
from default_packages import get_packages
from tkinter import ttk, filedialog, messagebox, scrolledtext


class GUI:
    """Base class for creating the Android Debloater GUI."""

    def __init__(self, root: tk.Tk, window_title="Android Debloater"):
        """
        Initialize the GUI application.

        Args:
            root (tk.Tk): The root Tkinter window.
            window_title (str): The title of the application window.
        """
        self.root = root
        self.root.title(window_title)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root_mode: bool = False
        self.app_list: list = []
        self.old_stdout = sys.stdout
        sys.stdout = self
        self.package_tree_holder: ttk.Treeview | None = None
        self.package_command: callable | None = None
        self.adb_path: Path | None = None
        self._setup_ui()

    @staticmethod
    def set_icon(root: tk.Tk, icon_path: Path) -> None:
        """
        Set the icon for the window.

        Args:
            root (tk.Tk): The window to set the icon for.
            icon_path (Path): The path to the icon file.
        """
        root.iconbitmap(str(icon_path))

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.root.geometry("1200x600")
        self._create_top_frame()
        self._create_main_frame()
        self._create_button_frame()
        self._create_menu()

    def _create_top_frame(self) -> None:
        """Create the top frame of the UI."""
        top_frame: ttk.Frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, pady=5)
        device_label: ttk.Label = ttk.Label(top_frame, text="Device:")
        device_label.pack(side=tk.LEFT, padx=5)
        self.device_var: tk.StringVar = tk.StringVar()
        self.device_dropdown: ttk.Combobox = ttk.Combobox(
            top_frame, textvariable=self.device_var, state="readonly"
        )
        self.device_dropdown.pack(side=tk.LEFT, padx=5)
        refresh_button: ttk.Button = ttk.Button(
            top_frame, text="Refresh", command=self.get_device_name
        )
        refresh_button.pack(side=tk.LEFT, padx=5)

    def _create_main_frame(self) -> None:
        """Create the main frame of the UI."""
        main_frame: ttk.Frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        self._create_app_list_frame(main_frame)
        self._create_search_frame(main_frame)
        self._create_log_frame(main_frame)

    def _create_app_list_frame(self, parent_frame: ttk.Frame) -> None:
        """Create the application list frame."""
        app_list_frame: ttk.LabelFrame = ttk.LabelFrame(
            parent_frame, text="Applications"
        )
        app_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.app_tree: ttk.Treeview = ttk.Treeview(
            app_list_frame, columns=("package", "status", "type"), show="headings"
        )
        self.app_tree.heading("package", text="Package Name")
        self.app_tree.heading("status", text="Status")
        self.app_tree.heading("type", text="Type")
        self.app_tree.column("package", width=400)
        self.app_tree.column("status", width=100)
        self.app_tree.column("type", width=100)
        self.app_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        app_list_scrollbar: ttk.Scrollbar = ttk.Scrollbar(
            app_list_frame, command=self.app_tree.yview
        )
        app_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.app_tree.config(yscrollcommand=app_list_scrollbar.set)

    def _create_search_frame(self, parent_frame: ttk.Frame) -> None:
        """Create the search frame."""
        search_frame: ttk.LabelFrame = ttk.LabelFrame(parent_frame, text="Search")
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        search_label: ttk.Label = ttk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=5)
        self.search_var: tk.StringVar = tk.StringVar()
        self.search_var.trace("w", self.filter_app_list)
        search_entry: ttk.Entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, padx=5, pady=5)

    def _create_log_frame(self, parent_frame: ttk.Frame) -> None:
        """Create the log frame."""
        log_frame: ttk.LabelFrame = ttk.LabelFrame(parent_frame, text="Logs")
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text: tk.Text = tk.Text(
            log_frame, wrap=tk.WORD, height=20, width=50, relief=tk.FLAT
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        log_scrollbar: ttk.Scrollbar = ttk.Scrollbar(
            log_frame, command=self.log_text.yview
        )
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)

    def _create_button_frame(self) -> None:
        """Create the button frame."""
        button_frame: ttk.LabelFrame = ttk.LabelFrame(self.root, text="Actions")
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        self._create_buttons(button_frame)

    def _create_buttons(self, parent_frame: ttk.LabelFrame) -> None:
        """Create the action buttons."""
        ttk.Button(parent_frame, text="Start ADB", command=self.start_adb).pack(
            side=tk.LEFT, padx=5, pady=5
        )
        ttk.Button(parent_frame, text="Stop ADB", command=self.stop_adb).pack(
            side=tk.LEFT, padx=5, pady=5
        )
        self.load_apps_button: ttk.Button = ttk.Button(
            parent_frame, text="Load Applications", command=self.load_applications
        )
        self.load_apps_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.debloat_button: ttk.Button = ttk.Button(
            parent_frame, text="Uninstall Selected", command=self.debloat_selected
        )
        self.debloat_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.remove_files_button: ttk.Button = ttk.Button(
            parent_frame, text="Remove Files from Txt", command=self.remove_apps_from_path
        )
        self.manage_packages_button: ttk.Button = ttk.Button(
            parent_frame, text="Manage Packages", command=self.open_package_manager
        )
        self.manage_packages_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.open_terminal_button: ttk.Button = ttk.Button(
            parent_frame, text="Open Terminal", command=self.open_terminal
        )
        self.open_terminal_button.pack(side=tk.LEFT, padx=5, pady=5)

    def _create_menu(self) -> None:
        """Create the menu bar."""
        menu: tk.Menu = tk.Menu(self.root, tearoff=0)
        self.root.config(menu=menu)
        root_menu: tk.Menu = tk.Menu(menu, tearoff=0)
        root_menu.add_command(label="Root Mode", command=self.toggle_root_mode)
        menu.add_cascade(label="Option", menu=root_menu)
        self.menu: tk.Menu = menu
        self.root_menu: tk.Menu = root_menu

    def toggle_root_mode(self) -> None:
        """Toggle root mode."""
        self.root_mode = not self.root_mode
        if self.root_mode:
            self.log_message("Root mode is activated")
            self.root_menu.entryconfig("Root Mode", label="Root Mode ✓")
            self._switch_to_root_mode()
        else:
            self.log_message("Root mode is deactivated")
            self.root_menu.entryconfig("Root Mode ✓", label="Root Mode")
            self._switch_to_normal_mode()

    def _switch_to_root_mode(self) -> None:
        """Switch to root mode UI."""
        self.load_apps_button.pack_forget()
        self.debloat_button.pack_forget()
        self.manage_packages_button.pack_forget()
        self.remove_files_button.pack(side=tk.LEFT, padx=5, pady=5)

    def _switch_to_normal_mode(self) -> None:
        """Switch to normal mode UI."""
        self.load_apps_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.debloat_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.manage_packages_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.remove_files_button.pack_forget()

    def show_permission_warning(self, device_id: str) -> None:
        """
        Show a permission warning dialog.

        Args:
            device_id (str): The ID of the unauthorized device.
        """
        messagebox.showwarning(
            "Permission Needed",
            f"The device ({device_id}) is unauthorized. Please allow USB Debugging on the device.",
        )

    def log_message(self, message: str) -> None:
        """
        Log a message to the log text widget.

        Args:
            message (str): The message to log.
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{current_time}] {message}\n"
        self.log_text.insert(tk.END, full_message)
        self.log_text.yview(tk.END)

    def write(self, message: str) -> None:
        """
        Write a message to the log.

        Args:
            message (str): The message to write.
        """
        if message:
            self.log_message(message)

    def flush(self) -> None:
        """Flush the log (no-op)."""
        pass

    def start_adb(self) -> None:
        """Start the ADB server (to be implemented)."""
        pass

    def stop_adb(self) -> None:
        """Stop the ADB server (to be implemented)."""
        pass

    def on_close(self) -> None:
        """Handle the window close event."""
        self.stop_adb()
        self.root.destroy()

    def get_device_name(self) -> None:
        """Get the device name (to be implemented)."""
        pass

    def load_applications(self) -> None:
        """Load applications from the device (to be implemented)."""
        pass

    def debloat_selected(self, package_tree: ttk.Treeview = None) -> None:
        """
        Uninstall the selected applications.

        Args:
            package_tree (ttk.Treeview, optional): The tree view containing the selected packages.
        """
        pass

    def remove_apps_from_path(self) -> None:
        """Remove applications listed in a text file (to be implemented)."""
        pass

    def update_app_tree(self) -> None:
        """Update the application list tree view based on search query."""
        search_query = self.search_var.get().lower()
        filtered_apps = [
            app for app in self.app_list if search_query in app["package"].lower()
        ]
        for row in self.app_tree.get_children():
            self.app_tree.delete(row)
        for app in filtered_apps:
            self.app_tree.insert("", tk.END, values=(app["package"], app["status"], app["type"]))

    def filter_app_list(self, *args) -> None:
        """Filter the application list based on search input."""
        self.update_app_tree()

    def open_package_manager(self) -> None:
        """Open the package manager window."""
        package_manager = DefaultPackageManager(self.root, self.package_command)
        self.package_tree_holder = package_manager.get_package_tree()

    def open_terminal(self) -> None:
        """Open the terminal."""
        try:
            model, device_id = self.device_var.get().rsplit(" - ", 1)
            terminal_window = Terminal(self.root, model, device_id, self.adb_path)
        except (IndexError, ValueError):
            self.log_message("No device selected or invalid device ID.")


class Terminal:
    """Class representing a terminal."""

    def __init__(self, root: tk.Tk, model: str, device_id: str, adb_path: Path):
        """
        Initialize the Terminal.

        Args:
            root (tk.Tk): The root Tkinter window.
            model (str): The device model.
            device_id (str): The selected device ID.
            adb_path (Path): The path to the ADB executable.
        """
        self.terminal_window = tk.Toplevel(root)
        self.terminal_window.title("ADB Shell")
        self.terminal_window.geometry("800x400")
        self.terminal_window.attributes('-alpha', 0.85)
        GUI.set_icon(self.terminal_window, Path("assets/android_debloater.ico"))

        self.model = model
        self.device_id = device_id
        self.adb_path = adb_path
        self.command_history = []
        self.history_index = 0
        self.process = None
        self.output_queue = queue.Queue()
        self.is_root = False

        # Set terminal style
        self.terminal_text = scrolledtext.ScrolledText(
            self.terminal_window, wrap=tk.WORD, height=20, width=50, relief=tk.FLAT,
            bg="#000000", fg="white", insertbackground="white", undo=True
        )
        self.terminal_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._bind_events()

        # Configure tags for prompt and command/output
        self.terminal_text.tag_config("prompt", foreground="#00FF00")
        self.terminal_text.tag_config("command_output", foreground="white")

        self.prompt = f"{self.model}@android$ "
        self._insert_prompt()

        # Start periodic check for process output
        self.terminal_window.after(100, self._process_output)

    def _bind_events(self):
        """Bind events to terminal text widget."""
        self.terminal_text.bind("<Return>", self._on_key_press)
        self.terminal_text.bind("<Up>", self._on_up_key_press)
        self.terminal_text.bind("<Down>", self._on_down_key_press)
        self.terminal_text.bind("<Control-c>", self._on_ctrl_c)
        self.terminal_text.bind("<Control-v>", self._on_ctrl_v)
        self.terminal_text.bind("<BackSpace>", self._on_backspace)
        self.terminal_text.bind("<Escape>", self._on_escape)
        self.terminal_text.bind("<Button-3>", self._on_right_click)
        self.terminal_text.bind("<Button-1>", self._on_left_click)
        self.terminal_text.bind("<<Modified>>", self._on_text_modified)

    def _insert_prompt(self):
        """Insert the prompt into the terminal text widget."""
        self.terminal_text.insert(tk.END, self.prompt, "prompt")
        self.terminal_text.mark_set("input_start", "end-1c")
        self.terminal_text.mark_gravity("input_start", tk.LEFT)
        self.terminal_text.see(tk.END)

    def _on_key_press(self, event: tk.Event) -> str:
        """Handle key press events.

        Args:
            event (tk.Event): The Tkinter event object.

        Returns:
            str: Returns "break" to stop further event processing.
        """
        if self.terminal_text.index(tk.INSERT) < self.terminal_text.index("input_start"):
            return "break"
        if event.keysym == "Return":
            self._execute_command()
            return "break"

    def _on_backspace(self, event: tk.Event) -> str:
        """Handle backspace key press event.

        Args:
            event (tk.Event): The Tkinter event object.

        Returns:
            str: Returns "break" to stop further event processing.
        """
        if self.terminal_text.index(tk.INSERT) <= self.terminal_text.index("input_start"):
            return "break"

    def _on_up_key_press(self, event: tk.Event) -> None:
        """Handle up arrow key press event.

        Args:
            event (tk.Event): The Tkinter event object.
        """
        if self.command_history:
            self.history_index = (self.history_index - 1) % len(self.command_history)
            self._replace_current_line_with_history()

    def _on_down_key_press(self, event: tk.Event) -> None:
        """Handle down arrow key press event.

        Args:
            event (tk.Event): The Tkinter event object.
        """
        if self.command_history:
            self.history_index = (self.history_index + 1) % len(self.command_history)
            self._replace_current_line_with_history()

    def _replace_current_line_with_history(self) -> None:
        """Replace the current line with the command from history."""
        current_line_start = self.terminal_text.index("input_start")
        self.terminal_text.delete(current_line_start, tk.END)
        self.terminal_text.insert(tk.END, self.command_history[self.history_index], "command_output")

    def _on_ctrl_c(self, event: tk.Event) -> str:
        """Handle Ctrl+C key press event to terminate the process.

        Args:
            event (tk.Event): The Tkinter event object.

        Returns:
            str: Returns "break" to stop further event processing.
        """
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process = None
            self.terminal_text.insert(tk.END, "\nProcess terminated by user\n", "command_output")
            self._insert_prompt()
        return "break"

    def _on_ctrl_v(self, event: tk.Event) -> str:
        """Handle Ctrl+V key press event to paste clipboard content.

        Args:
            event (tk.Event): The Tkinter event object.

        Returns:
            str: Returns "break" to stop further event processing.
        """
        self.terminal_text.event_generate("<<Paste>>")
        return "break"

    def _on_escape(self, event: tk.Event) -> str:
        """Handle Escape key press event to clear the current input line.

        Args:
            event (tk.Event): The Tkinter event object.

        Returns:
            str: Returns "break" to stop further event processing.
        """
        self.terminal_text.delete("input_start", tk.END)
        return "break"

    def _on_right_click(self, event: tk.Event) -> str:
        """Handle right-click event to paste clipboard content.

        Args:
            event (tk.Event): The Tkinter event object.

        Returns:
            str: Returns "break" to stop further event processing.
        """
        self.terminal_text.event_generate("<<Paste>>")
        return "break"

    def _on_left_click(self, event: tk.Event) -> str:
        """Handle left-click event to prevent cursor from moving before the prompt.

        Args:
            event (tk.Event): The Tkinter event object.

        Returns:
            str: Returns "break" to stop further event processing.
        """
        if self.terminal_text.index(tk.CURRENT) < self.terminal_text.index("input_start"):
            self.terminal_text.mark_set(tk.INSERT, "input_start")
            return "break"

    def _on_text_modified(self, event: tk.Event) -> None:
        """Handle text modified event to prevent cursor from moving before the prompt.

        Args:
            event (tk.Event): The Tkinter event object.
        """
        self.terminal_text.edit_modified(False)
        if self.terminal_text.index(tk.INSERT) < self.terminal_text.index("input_start"):
            self.terminal_text.mark_set(tk.INSERT, "input_start")

    def _execute_command(self) -> None:
        """Execute the command entered in the terminal."""
        command = self.terminal_text.get("input_start", "end-1c").strip()
        if command:
            self.command_history.append(command)
            self.history_index = len(self.command_history)
            self.terminal_text.insert(tk.END, "\n", "command_output")

            if command == "su":
                if self._check_root_access():
                    self.is_root = True
                    self.prompt = f"{self.model}@root$ "
                    self.terminal_text.insert(tk.END, "Switched to root mode\n", "command_output")
                    self._insert_prompt()
                    return
                self._insert_prompt()
                return

            if command == "exit" or (self.is_root and command == "Ctrl+Z"):
                self.is_root = False
                self.prompt = f"{self.model}@android$ "
                self._insert_prompt()
                return

            full_command = [str(self.adb_path), "-s", self.device_id, "shell"]
            if self.is_root:
                full_command.extend(["su", "-c", command])
            else:
                full_command.append(command)

            self.process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            threading.Thread(target=self._read_process_output, daemon=True).start()
        else:
            self.terminal_text.insert(tk.END, "\n", "command_output")
        self.terminal_text.see(tk.END)

    def _read_process_output(self) -> None:
        """Read the output from the subprocess and insert it into the terminal."""
        try:
            for line in iter(self.process.stdout.readline, ''):
                self.output_queue.put(line)
            for line in iter(self.process.stderr.readline, ''):
                self.output_queue.put(line)
            self.output_queue.put(None)
        except AttributeError:
            pass
        finally:
            self.process = None
            self.output_queue.put(None)

    def _process_output(self) -> None:
        """Process the output queue and insert it into the terminal."""
        while not self.output_queue.empty():
            line = self.output_queue.get()
            if line is None:
                self.terminal_text.insert(tk.END, "\n", "command_output")
                self._insert_prompt()
                break
            self.terminal_text.insert(tk.END, line, "command_output")
            self.terminal_text.see(tk.END)
        self.terminal_window.after(100, self._process_output)

    def _check_root_access(self) -> bool:
        """Check if the device has root access."""
        check_command = [str(self.adb_path), "-s", self.device_id, "shell", "su", "-c", "echo rooted"]
        result = subprocess.run(check_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "rooted" in result.stdout:
            return True
        self.terminal_text.insert(tk.END, "Root access is required for this command\n", "command_output")
        return False
            

class DefaultPackageManager:
    """Class for managing default packages."""

    def __init__(self, root: tk.Tk, debloat_command: callable):
        """
        Initialize the DefaultPackageManager.

        Args:
            root (tk.Tk): The root Tkinter window.
            debloat_command (callable): The command to execute for debloating.
        """
        self.package_window: tk.Toplevel = tk.Toplevel(root)
        self.package_window.geometry("800x600")
        self.package_groups: dict = get_packages()
        GUI.set_icon(self.package_window, Path("assets/android_debloater.ico"))
        self.debloat_button_command: callable = debloat_command
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface for the package manager."""
        self._create_package_list_frame()
        self._create_search_frame()
        self._create_action_frame()

    def _create_package_list_frame(self) -> None:
        """Create the package list frame."""
        package_list_frame: ttk.LabelFrame = ttk.LabelFrame(self.package_window, text="Package Groups")
        package_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.package_tree: ttk.Treeview = ttk.Treeview(package_list_frame, columns=("group", "package"), show="headings")
        self.package_tree.heading("group", text="Group")
        self.package_tree.heading("package", text="Package Name")
        self.package_tree.column("group", width=150)
        self.package_tree.column("package", width=600)
        self.package_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        package_scrollbar: ttk.Scrollbar = ttk.Scrollbar(package_list_frame, command=self.package_tree.yview)
        package_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.package_tree.config(yscrollcommand=package_scrollbar.set)
        self.insert_default_packages()

    def _create_search_frame(self) -> None:
        """Create the search frame."""
        search_frame: ttk.Frame = ttk.Frame(self.package_window)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        search_label: ttk.Label = ttk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=5)
        search_var: tk.StringVar = tk.StringVar()
        search_var.trace("w", lambda *args: self.filter_packages(search_var))
        search_entry: ttk.Entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(fill=tk.X, padx=5)
        self.search_var: tk.StringVar = search_var

    def _create_action_frame(self) -> None:
        """Create the action frame."""
        action_frame: ttk.Frame = ttk.Frame(self.package_window)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        select_all_button: ttk.Button = ttk.Button(action_frame, text="Select All", command=lambda: self.select_all_packages(self.search_var))
        select_all_button.pack(side=tk.LEFT, padx=5)
        debloat_button: ttk.Button = ttk.Button(action_frame, text="Uninstall Selected", command=self.debloat_button_command)
        debloat_button.pack(side=tk.LEFT, padx=5)

    def insert_default_packages(self) -> None:
        """Insert default packages into the tree view."""
        for group, packages in self.package_groups.items():
            for package in packages:
                self.package_tree.insert("", tk.END, values=(group, package))

    def filter_packages(self, search_holder: tk.StringVar) -> None:
        """
        Filter the package list based on search query.

        Args:
            search_holder (tk.StringVar): The variable holding the search query.
        """
        search_query = search_holder.get().lower()
        filtered_packages = [
            (group, package)
            for group, packages in self.package_groups.items()
            for package in packages
            if search_query in package.lower() or search_query in group.lower()
        ]
        for row in self.package_tree.get_children():
            self.package_tree.delete(row)
        for group, package in filtered_packages:
            self.package_tree.insert("", tk.END, values=(group, package))

    def select_all_packages(self, search_holder: tk.StringVar) -> None:
        """
        Select all packages that match the search query.

        Args:
            search_holder (tk.StringVar): The variable holding the search query.
        """
        query = search_holder.get().lower()
        for item in self.package_tree.get_children():
            values = self.package_tree.item(item, "values")
            if query in values[1].lower() or query in values[0].lower():
                self.package_tree.selection_add(item)

    def get_package_tree(self) -> ttk.Treeview:
        """
        Get the package tree view.

        Returns:
            ttk.Treeview: The tree view containing the packages.
        """
        return self.package_tree