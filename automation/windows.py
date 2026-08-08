import ctypes
import time
import subprocess
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

import pygetwindow as gw
import psutil

logger = logging.getLogger(__name__)

# модель может сказать "Блокнот" или "Notepad" — ищем оба
SYNONYMS = {
    "блокнот": ["notepad", "блокнот"],
    "notepad": ["notepad", "блокнот"],
    "калькулятор": ["calculator", "калькулятор"],
    "calculator": ["calculator", "калькулятор"],
    "chrome": ["chrome"],
    "cmd": ["cmd", "командная"],
    "проводник": ["проводник", "explorer"],
    "telegram": ["telegram"],
    "steam": ["steam"],
    "браузер": ["chrome", "firefox", "edge", "opera", "browser"],
}


@dataclass
class WindowInfo:
    """Information about a window."""
    title: str
    pid: int
    app: str
    hwnd: int
    active: bool = False
    minimized: bool = False
    maximized: bool = False


class WindowManager:
    """Basic window management functionality (legacy compatibility)."""
    
    def activate(self, title):
        variants = SYNONYMS.get(title.lower(), [title.lower()])
        try:
            windows = gw.getAllWindows()
        except Exception:
            return False

        for w in windows:
            if not w.title.strip():
                continue
            low = w.title.lower()
            if any(v in low for v in variants):
                try:
                    if w.isMinimized:
                        w.restore()
                    self._force_foreground(w._hWnd)
                    time.sleep(0.3)
                    return True
                except Exception:
                    return False
        return False

    @staticmethod
    def _force_foreground(hwnd):
        user32 = ctypes.windll.user32
        # трюк: имитируем нажатие ALT — это разрешает красть фокус
        user32.keybd_event(0x12, 0, 0, 0)
        user32.keybd_event(0x12, 0, 2, 0)
        user32.SetForegroundWindow(hwnd)


class ApplicationController:
    """Comprehensive application and window controller for JARVIS.
    
    Provides full control over Windows applications:
    - List all open windows
    - Get active window
    - Find window by title
    - Activate/minimize/maximize/close windows
    - Launch applications with wait capability
    - Terminate applications
    - Get process information
    - Wait for window appearance
    
    Architecture:
        User Request → ApplicationController → Windows API → Result
    """
    
    def __init__(self, timeout: int = 10):
        """Initialize application controller.
        
        Args:
            timeout: Default timeout in seconds for wait operations
        """
        self.timeout = timeout
        self.wm = WindowManager()
        
    # ==================== WINDOW LISTING ====================
    
    def list_windows(self) -> List[Dict[str, Any]]:
        """Get list of all open windows.
        
        Returns:
            List of dictionaries with window information:
            [{"title": "...", "pid": 1234, "app": "chrome.exe", "active": True}, ...]
        """
        try:
            windows = gw.getAllWindows()
        except Exception as e:
            logger.error(f"Failed to get windows list: {e}")
            return []
        
        result = []
        active_hwnd = self._get_active_hwnd()
        
        for w in windows:
            if not w.title.strip():
                continue
            
            try:
                window_info = self._get_window_info(w, active_hwnd)
                if window_info:
                    result.append(window_info)
            except Exception as e:
                logger.warning(f"Failed to get info for window '{w.title}': {e}")
                continue
        
        return result
    
    def _get_window_info(self, window, active_hwnd: Optional[int]) -> Optional[Dict[str, Any]]:
        """Extract window information.
        
        Args:
            window: PyGetWindow window object
            active_hwnd: Handle of currently active window
            
        Returns:
            Dictionary with window info or None if extraction failed
        """
        try:
            hwnd = window._hWnd
            pid = window.pid
            
            # Get process name
            app_name = "unknown"
            try:
                process = psutil.Process(pid)
                app_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            return {
                "title": window.title,
                "pid": pid,
                "app": app_name,
                "hwnd": hwnd,
                "active": hwnd == active_hwnd,
                "minimized": window.isMinimized,
                "maximized": window.isMaximized,
            }
        except Exception:
            return None
    
    def _get_active_hwnd(self) -> Optional[int]:
        """Get handle of currently active window.
        
        Returns:
            Handle of active window or None
        """
        try:
            user32 = ctypes.windll.user32
            return user32.GetForegroundWindow()
        except Exception:
            return None
    
    # ==================== FIND & ACTIVATE ====================
    
    def find_window(self, title: str) -> Optional[Dict[str, Any]]:
        """Find window by title (supports synonyms).
        
        Args:
            title: Window title or application name
            
        Returns:
            Window info dict or None if not found
        """
        variants = self._get_variants(title)
        
        try:
            windows = gw.getAllWindows()
        except Exception:
            return None
        
        for w in windows:
            if not w.title.strip():
                continue
            
            low_title = w.title.lower()
            if any(v in low_title for v in variants):
                return self._get_window_info(w, self._get_active_hwnd())
        
        return None
    
    def _get_variants(self, title: str) -> List[str]:
        """Get search variants for a title including synonyms.
        
        Args:
            title: Original title
            
        Returns:
            List of search terms
        """
        lower_title = title.lower()
        if lower_title in SYNONYMS:
            return SYNONYMS[lower_title]
        return [lower_title]
    
    def activate(self, title: str) -> bool:
        """Activate window by title.
        
        Args:
            title: Window title or application name
            
        Returns:
            True if activated successfully
        """
        return self.wm.activate(title)
    
    def minimize(self, title: str) -> bool:
        """Minimize window by title.
        
        Args:
            title: Window title or application name
            
        Returns:
            True if minimized successfully
        """
        window_info = self.find_window(title)
        if not window_info:
            return False
        
        try:
            hwnd = window_info["hwnd"]
            user32 = ctypes.windll.user32
            user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
            return True
        except Exception as e:
            logger.error(f"Failed to minimize window: {e}")
            return False
    
    def maximize(self, title: str) -> bool:
        """Maximize/restore window by title.
        
        Args:
            title: Window title or application name
            
        Returns:
            True if maximized successfully
        """
        window_info = self.find_window(title)
        if not window_info:
            return False
        
        try:
            hwnd = window_info["hwnd"]
            user32 = ctypes.windll.user32
            user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
            return True
        except Exception as e:
            logger.error(f"Failed to maximize window: {e}")
            return False
    
    def close(self, title: str, force: bool = False) -> bool:
        """Close window by title.
        
        Args:
            title: Window title or application name
            force: If True, forcefully terminate the process
            
        Returns:
            True if closed successfully
        """
        window_info = self.find_window(title)
        if not window_info:
            return False
        
        pid = window_info["pid"]
        
        if force:
            return self._kill_process(pid)
        else:
            try:
                # Try graceful close first
                import pyautogui
                hwnd = window_info["hwnd"]
                
                # Activate window first
                self.activate(title)
                time.sleep(0.3)
                
                # Send Alt+F4
                pyautogui.hotkey('alt', 'f4')
                time.sleep(0.5)
                
                return True
            except Exception as e:
                logger.warning(f"Graceful close failed, trying force: {e}")
                return self._kill_process(pid)
    
    def _kill_process(self, pid: int) -> bool:
        """Forcefully terminate a process.
        
        Args:
            pid: Process ID
            
        Returns:
            True if terminated successfully
        """
        try:
            process = psutil.Process(pid)
            process.terminate()
            logger.info(f"Terminated process {pid}")
            return True
        except psutil.NoSuchProcess:
            logger.warning(f"Process {pid} already terminated")
            return True
        except psutil.AccessDenied as e:
            logger.error(f"Access denied to terminate process {pid}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to terminate process {pid}: {e}")
            return False
    
    # ==================== APPLICATION LAUNCH ====================
    
    def launch(self, command: str, wait: bool = False, timeout: Optional[int] = None) -> bool:
        """Launch an application.
        
        Args:
            command: Command to execute (e.g., "notepad", "chrome.exe")
            wait: If True, wait for window to appear
            timeout: Timeout in seconds (uses default if None)
            
        Returns:
            True if launched successfully (and appeared if wait=True)
        """
        if timeout is None:
            timeout = self.timeout
        
        try:
            # Get window titles before launch
            before_titles = set(w.title for w in gw.getAllWindows() if w.title.strip())
            
            # Launch application
            subprocess.Popen(command, shell=True)
            logger.info(f"Launched: {command}")
            
            if not wait:
                return True
            
            # Wait for new window to appear
            return self.wait_window_appear(command, timeout=timeout, exclude_titles=before_titles)
            
        except Exception as e:
            logger.error(f"Failed to launch application '{command}': {e}")
            return False
    
    def wait_window_appear(self, title: str, timeout: Optional[int] = None, 
                          exclude_titles: Optional[set] = None) -> bool:
        """Wait for a window to appear.
        
        Args:
            title: Window title or application name to wait for
            timeout: Timeout in seconds
            exclude_titles: Set of titles that existed before launch
            
        Returns:
            True if window appeared within timeout
        """
        if timeout is None:
            timeout = self.timeout
        
        variants = self._get_variants(title)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                windows = gw.getAllWindows()
                for w in windows:
                    if not w.title.strip():
                        continue
                    
                    # Skip pre-existing windows
                    if exclude_titles and w.title in exclude_titles:
                        continue
                    
                    low_title = w.title.lower()
                    if any(v in low_title for v in variants):
                        logger.info(f"Window appeared: {w.title}")
                        return True
                        
            except Exception:
                pass
            
            time.sleep(0.5)
        
        logger.warning(f"Timeout waiting for window: {title}")
        return False
    
    def verify_app_running(self, process_name: str) -> bool:
        """Verify if an application is running.
        
        Args:
            process_name: Process name (e.g., "chrome.exe")
            
        Returns:
            True if process is running
        """
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() == process_name.lower():
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            logger.error(f"Failed to check process '{process_name}': {e}")
            return False
    
    # ==================== PROCESS INFORMATION ====================
    
    def get_pid(self, title: str) -> Optional[int]:
        """Get process ID for a window.
        
        Args:
            title: Window title or application name
            
        Returns:
            Process ID or None if not found
        """
        window_info = self.find_window(title)
        return window_info["pid"] if window_info else None
    
    def get_app_name(self, title: str) -> Optional[str]:
        """Get application name for a window.
        
        Args:
            title: Window title or application name
            
        Returns:
            Application name (e.g., "chrome.exe") or None
        """
        window_info = self.find_window(title)
        return window_info["app"] if window_info else None
    
    def get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get detailed process information.
        
        Args:
            pid: Process ID
            
        Returns:
            Dictionary with process info or None
        """
        try:
            process = psutil.Process(pid)
            return {
                "name": process.name(),
                "exe": process.exe(),
                "cwd": process.cwd(),
                "status": process.status(),
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Cannot get info for process {pid}: {e}")
            return None
    
    # ==================== UTILITY METHODS ====================
    
    def get_active_window(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently active window.
        
        Returns:
            Window info dict or None
        """
        active_hwnd = self._get_active_hwnd()
        if not active_hwnd:
            return None
        
        try:
            windows = gw.getAllWindows()
            for w in windows:
                if w._hWnd == active_hwnd:
                    return self._get_window_info(w, active_hwnd)
        except Exception:
            pass
        
        return None
    
    def close_all_minimized(self) -> int:
        """Close all minimized windows.
        
        Returns:
            Number of windows closed
        """
        count = 0
        try:
            windows = gw.getAllWindows()
            for w in windows:
                if w.isMinimized:
                    try:
                        self.close(w.title)
                        count += 1
                    except Exception:
                        pass
        except Exception:
            pass
        return count
    
    def restore_all_windows(self) -> int:
        """Restore all minimized windows.
        
        Returns:
            Number of windows restored
        """
        count = 0
        try:
            windows = gw.getAllWindows()
            for w in windows:
                if w.isMinimized:
                    try:
                        w.restore()
                        count += 1
                    except Exception:
                        pass
        except Exception:
            pass
        return count