"""JARVIS Skills Tools

Provides skill-based tools for the Tool Registry:
- url (open website)
- music_play, music_search
- youtube, kinopoisk
- media (media keys)
- volume
"""

from typing import Dict, Any, Optional
import webbrowser
import time


class SkillsTools:
    """Skills tools for JARVIS.
    
    These tools provide higher-level capabilities:
    - Opening websites
    - Music playback (Yandex Music)
    - Video playback (YouTube, Kinopoisk)
    - Media control
    - Volume control
    """
    
    def __init__(self, log_fn=None):
        """Initialize skills tools.
        
        Args:
            log_fn: Optional logging function
        """
        self.log_fn = log_fn
        
        # Import skills lazily to avoid circular imports
        self._music = None
        self._video = None
        self._volume = None
    
    @property
    def music(self):
        """Lazy load music skill."""
        if self._music is None:
            from core.skills.music import MusicSkill
            self._music = MusicSkill()
        return self._music
    
    @property
    def video(self):
        """Lazy load video skill."""
        if self._video is None:
            from core.skills.video import VideoSkill
            self._video = VideoSkill()
        return self._video
    
    @property
    def volume(self):
        """Lazy load volume skill."""
        if self._volume is None:
            from core.skills.volume import VolumeSkill
            self._volume = VolumeSkill()
        return self._volume
    
    def _log(self, message: str):
        """Log a message if logging is enabled."""
        if self.log_fn:
            self.log_fn(message)
    
    def url(self, address: str) -> str:
        """Open a website in the browser.
        
        Args:
            address: URL to open
            
        Returns:
            Status message
        """
        from core.checker import Checker
        
        before = Checker().titles()
        webbrowser.open(address)
        win = Checker().wait_change(before, timeout=8)
        
        if win:
            self._log(f"url: opened {address} (window: {win})")
            return f"открыл {address}"
        
        self._log(f"url: opened {address} (no window change)")
        return f"открыл {address} (окно не изменилось — проверь)"
    
    def music_play(self) -> str:
        """Open Yandex Music application.
        
        Returns:
            Status message
        """
        result = self.music.open_app()
        self._log(f"music_play: {result}")
        return result
    
    def music_search(self, query: str, vision=None, mouse=None) -> str:
        """Search and play music on Yandex Music.
        
        Args:
            query: Search query
            vision: Optional vision module for visual search
            mouse: Optional mouse module for visual clicks
            
        Returns:
            Status message
        """
        result = self.music.play_search(query, vision, mouse, self._log)
        self._log(f"music_search: {result}")
        return result
    
    def youtube(self, query: str) -> str:
        """Play a video on YouTube.
        
        Args:
            query: Search query or empty for random video
            
        Returns:
            Status message
        """
        result = self.video.youtube(query, self._log)
        self._log(f"youtube: {result}")
        return result
    
    def kinopoisk(self, query: str) -> str:
        """Play a movie/series on Kinopoisk.
        
        Args:
            query: Title to search for
            
        Returns:
            Status message
        """
        result = self.video.kinopoisk(query, self._log)
        self._log(f"kinopoisk: {result}")
        return result
    
    def media(self, key: str) -> str:
        """Send a media key command.
        
        Args:
            key: Media key name (playpause, next, prev, volup, voldown, mute)
            
        Returns:
            Status message
        """
        if self.music.media(key):
            self._log(f"media: {key}")
            return f"медиа-команда: {key}"
        self._log(f"media: unknown key {key}")
        return f"не знаю медиа-команду {key}"
    
    def volume(self, level: Any) -> str:
        """Set system volume level.
        
        Args:
            level: Volume level (0-10 scale or 0-100 percentage)
            
        Returns:
            Status message
        """
        result = self.volume.set_level(level)
        self._log(f"volume: {result}")
        return result


def create_skills_tools(log_fn=None, vision=None, mouse=None) -> Dict[str, Any]:
    """Create and return skills tools for registry registration.
    
    Args:
        log_fn: Optional logging function
        vision: Optional vision module for music search
        mouse: Optional mouse module for music search
        
    Returns:
        Dictionary mapping tool names to Tool instances
    """
    from core.tool_registry import Tool
    
    tools_instance = SkillsTools(log_fn=log_fn)
    tools = {}
    
    # URL tool
    tools["url"] = Tool(
        name="url",
        description="Open a website in the browser",
        schema={
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "URL to open"},
            },
            "required": ["address"],
        },
        risk_level=1,
        execute=tools_instance.url,
    )
    
    # Music play tool
    tools["music_play"] = Tool(
        name="music_play",
        description="Open Yandex Music application",
        schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        risk_level=1,
        execute=tools_instance.music_play,
    )
    
    # Music search tool
    tools["music_search"] = Tool(
        name="music_search",
        description="Search and play music on Yandex Music",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
        risk_level=1,
        execute=lambda query: tools_instance.music_search(query, vision, mouse),
    )
    
    # YouTube tool
    tools["youtube"] = Tool(
        name="youtube",
        description="Play a video on YouTube",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (empty for random)"},
            },
            "required": [],
        },
        risk_level=1,
        execute=lambda query="": tools_instance.youtube(query),
    )
    
    # Kinopoisk tool
    tools["kinopoisk"] = Tool(
        name="kinopoisk",
        description="Play a movie/series on Kinopoisk",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Title to search for"},
            },
            "required": ["query"],
        },
        risk_level=1,
        execute=tools_instance.kinopoisk,
    )
    
    # Media tool
    tools["media"] = Tool(
        name="media",
        description="Send a media key command",
        schema={
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Media key (playpause, next, prev, volup, voldown, mute)",
                    "enum": ["playpause", "next", "prev", "volup", "voldown", "mute"],
                },
            },
            "required": ["key"],
        },
        risk_level=2,
        execute=tools_instance.media,
    )
    
    # Volume tool
    tools["volume"] = Tool(
        name="volume",
        description="Set system volume level (0-10 scale)",
        schema={
            "type": "object",
            "properties": {
                "value": {"type": "number", "description": "Volume level (0-10 or 0-100)"},
            },
            "required": ["value"],
        },
        risk_level=2,
        execute=tools_instance.volume,
    )
    
    return tools
