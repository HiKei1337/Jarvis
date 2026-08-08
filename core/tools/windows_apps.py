"""JARVIS Windows Application Tools

Provides tools for managing Windows applications and windows:
- list_windows
- find_window
- activate_window
- minimize_window
- maximize_window
- close_window
- launch_app
- verify_app
- get_active_window
"""

from typing import Dict, Any, Optional


class WindowsAppTools:
    """Windows application management tools for JARVIS.
    
    These tools provide comprehensive window and application control:
    - List all open windows
    - Find and activate specific windows
    - Minimize/maximize/restore windows
    - Launch applications with wait capability
    - Verify if applications are running
    - Get process information
    """
    
    def __init__(self, log_fn=None, timeout: int = 10):
        """Initialize Windows application tools.
        
        Args:
            log_fn: Optional logging function
            timeout: Default timeout for wait operations
        """
        from automation.windows import ApplicationController
        
        self.controller = ApplicationController(timeout=timeout)
        self.log_fn = log_fn
    
    def _log(self, message: str):
        """Log a message if logging is enabled."""
        if self.log_fn:
            self.log_fn(message)
    
    # ==================== WINDOW LISTING ====================
    
    def list_windows(self) -> str:
        """Get list of all open windows.
        
        Returns:
            Formatted string with window information
        """
        windows = self.controller.list_windows()
        
        if not windows:
            return "нет открытых окон"
        
        result = []
        for w in windows:
            status = []
            if w.get("active"):
                status.append("активное")
            if w.get("minimized"):
                status.append("свёрнуто")
            if w.get("maximized"):
                status.append("развёрнуто")
            
            status_str = f" ({', '.join(status)})" if status else ""
            result.append(f"{w['title']} ({w['app']}){status_str}")
        
        self._log(f"list_windows: found {len(windows)} windows")
        return "открытые окна: " + "; ".join(result)
    
    def get_active_window(self) -> str:
        """Get information about the currently active window.
        
        Returns:
            Window information or message if no active window
        """
        window = self.controller.get_active_window()
        
        if not window:
            return "не удалось определить активное окно"
        
        self._log(f"get_active_window: {window['title']}")
        return f"активное окно: {window['title']} ({window['app']})"
    
    # ==================== FIND & ACTIVATE ====================
    
    def find_window(self, title: str) -> str:
        """Find window by title.
        
        Args:
            title: Window title or application name
            
        Returns:
            Window information or not found message
        """
        window = self.controller.find_window(title)
        
        if not window:
            return f"окно '{title}' не найдено"
        
        status = []
        if window.get("active"):
            status.append("активное")
        if window.get("minimized"):
            status.append("свёрнуто")
        if window.get("maximized"):
            status.append("развёрнуто")
        
        status_str = f", {', '.join(status)}" if status else ""
        self._log(f"find_window: found '{title}'")
        return f"найдено окно: {window['title']} (PID: {window['pid']}{status_str})"
    
    def activate_window(self, title: str) -> str:
        """Activate window by title.
        
        Args:
            title: Window title or application name
            
        Returns:
            Success or failure message
        """
        if self.controller.activate(title):
            self._log(f"activate_window: activated '{title}'")
            return f"активировал окно '{title}'"
        else:
            self._log(f"activate_window: failed to activate '{title}'")
            return f"не удалось активировать '{title}'"
    
    def minimize_window(self, title: str) -> str:
        """Minimize window by title.
        
        Args:
            title: Window title or application name
            
        Returns:
            Success or failure message
        """
        if self.controller.minimize(title):
            self._log(f"minimize_window: minimized '{title}'")
            return f"свернул окно '{title}'"
        else:
            self._log(f"minimize_window: failed to minimize '{title}'")
            return f"не удалось свернуть '{title}'"
    
    def maximize_window(self, title: str) -> str:
        """Maximize/restore window by title.
        
        Args:
            title: Window title or application name
            
        Returns:
            Success or failure message
        """
        if self.controller.maximize(title):
            self._log(f"maximize_window: maximized '{title}'")
            return f"развернул окно '{title}'"
        else:
            self._log(f"maximize_window: failed to maximize '{title}'")
            return f"не удалось развернуть '{title}'"
    
    def close_window(self, title: str, force: bool = False) -> str:
        """Close window by title.
        
        Args:
            title: Window title or application name
            force: If True, forcefully terminate the process
            
        Returns:
            Success or failure message
        """
        if self.controller.close(title, force=force):
            action = "принудительно закрыл" if force else "закрыл"
            self._log(f"close_window: closed '{title}' (force={force})")
            return f"{action} окно '{title}'"
        else:
            self._log(f"close_window: failed to close '{title}'")
            return f"не удалось закрыть '{title}'"
    
    # ==================== APPLICATION LAUNCH ====================
    
    def launch_app(self, command: str, wait: bool = False) -> str:
        """Launch an application.
        
        Args:
            command: Command to execute (e.g., "notepad", "chrome.exe")
            wait: If True, wait for window to appear
            
        Returns:
            Success or failure message
        """
        if self.controller.launch(command, wait=wait):
            wait_msg = " и дождался появления окна" if wait else ""
            self._log(f"launch_app: launched '{command}'{wait_msg}")
            return f"запустил {command}{wait_msg}"
        else:
            self._log(f"launch_app: failed to launch '{command}'")
            return f"не удалось запустить {command}"
    
    def verify_app(self, process_name: str) -> str:
        """Verify if an application is running.
        
        Args:
            process_name: Process name (e.g., "chrome.exe")
            
        Returns:
            Status message
        """
        if self.controller.verify_app_running(process_name):
            self._log(f"verify_app: '{process_name}' is running")
            return f"{process_name} запущен"
        else:
            self._log(f"verify_app: '{process_name}' is not running")
            return f"{process_name} не запущен"
    
    # ==================== PROCESS INFORMATION ====================
    
    def get_pid(self, title: str) -> str:
        """Get process ID for a window.
        
        Args:
            title: Window title or application name
            
        Returns:
            PID information or not found message
        """
        pid = self.controller.get_pid(title)
        
        if pid is None:
            return f"не удалось найти PID для '{title}'"
        
        self._log(f"get_pid: '{title}' has PID {pid}")
        return f"PID для '{title}': {pid}"
    
    def get_app_name(self, title: str) -> str:
        """Get application name for a window.
        
        Args:
            title: Window title or application name
            
        Returns:
            Application name or not found message
        """
        app_name = self.controller.get_app_name(title)
        
        if app_name is None:
            return f"не удалось определить приложение для '{title}'"
        
        self._log(f"get_app_name: '{title}' is {app_name}")
        return f"приложение для '{title}': {app_name}"


def create_windows_app_tools(log_fn=None) -> Dict[str, Any]:
    """Create and return Windows application tools for registry registration.
    
    Args:
        log_fn: Optional logging function
        
    Returns:
        Dictionary mapping tool names to Tool instances
    """
    from core.tool_registry import Tool
    
    tools_instance = WindowsAppTools(log_fn=log_fn)
    
    tools = {}
    
    # List windows tool
    tools["list_windows"] = Tool(
        name="list_windows",
        description="Get list of all open windows with their titles, PIDs, and states",
        schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        risk_level=0,
        execute=tools_instance.list_windows,
    )
    
    # Get active window tool
    tools["get_active_window"] = Tool(
        name="get_active_window",
        description="Get information about the currently active window",
        schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        risk_level=0,
        execute=tools_instance.get_active_window,
    )
    
    # Find window tool
    tools["find_window"] = Tool(
        name="find_window",
        description="Find a window by its title or application name",
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Window title or application name"},
            },
            "required": ["title"],
        },
        risk_level=0,
        execute=tools_instance.find_window,
    )
    
    # Activate window tool
    tools["activate_window"] = Tool(
        name="activate_window",
        description="Activate (bring to foreground) a window by its title",
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Window title or application name"},
            },
            "required": ["title"],
        },
        risk_level=1,
        execute=tools_instance.activate_window,
    )
    
    # Minimize window tool
    tools["minimize_window"] = Tool(
        name="minimize_window",
        description="Minimize a window by its title",
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Window title or application name"},
            },
            "required": ["title"],
        },
        risk_level=1,
        execute=tools_instance.minimize_window,
    )
    
    # Maximize window tool
    tools["maximize_window"] = Tool(
        name="maximize_window",
        description="Maximize or restore a window by its title",
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Window title or application name"},
            },
            "required": ["title"],
        },
        risk_level=1,
        execute=tools_instance.maximize_window,
    )
    
    # Close window tool
    tools["close_window"] = Tool(
        name="close_window",
        description="Close a window by its title (gracefully or forcefully)",
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Window title or application name"},
                "force": {"type": "boolean", "description": "Force close (terminate process)"},
            },
            "required": ["title"],
        },
        risk_level=4,
        execute=tools_instance.close_window,
    )
    
    # Launch app tool (enhanced version with wait)
    tools["launch_app_wait"] = Tool(
        name="launch_app_wait",
        description="Launch an application and optionally wait for its window to appear",
        schema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to execute"},
                "wait": {"type": "boolean", "description": "Wait for window to appear"},
            },
            "required": ["command"],
        },
        risk_level=3,
        execute=tools_instance.launch_app,
    )
    
    # Verify app tool
    tools["verify_app"] = Tool(
        name="verify_app",
        description="Verify if an application process is running",
        schema={
            "type": "object",
            "properties": {
                "process_name": {"type": "string", "description": "Process name (e.g., 'chrome.exe')"},
            },
            "required": ["process_name"],
        },
        risk_level=0,
        execute=tools_instance.verify_app,
    )
    
    # Get PID tool
    tools["get_pid"] = Tool(
        name="get_pid",
        description="Get process ID for a window",
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Window title or application name"},
            },
            "required": ["title"],
        },
        risk_level=0,
        execute=tools_instance.get_pid,
    )
    
    # Get app name tool
    tools["get_app_name"] = Tool(
        name="get_app_name",
        description="Get application executable name for a window",
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Window title or application name"},
            },
            "required": ["title"],
        },
        risk_level=0,
        execute=tools_instance.get_app_name,
    )
    
    return tools
