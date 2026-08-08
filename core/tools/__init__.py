"""JARVIS Tools Package

Provides tool categories for the Tool Registry:
- computer_use: Mouse, keyboard, scroll, launch_app
- skills: URL, music, video, volume, media
- communication: press, type, type_think, click_see, chat
- windows_apps: Window management and application control
- vision_control: Vision-based computer control (SEE→ACT→VERIFY)
"""

from core.tools.computer_use import create_computer_use_tools
from core.tools.skills import create_skills_tools
from core.tools.communication import create_communication_tools
from core.tools.windows_apps import create_windows_app_tools
from core.tools.vision_control import create_vision_control_tools

__all__ = [
    "create_computer_use_tools",
    "create_skills_tools",
    "create_communication_tools",
    "create_windows_app_tools",
    "create_vision_control_tools",
]
