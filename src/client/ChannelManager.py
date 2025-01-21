from PyQt5 import Qt
from PyQt5.QtWidgets import QMessageBox
from enum import Enum, auto
from src.utility.Settings import ENCODING


class ChannelType(Enum):
    CREATE = auto()
    DELETE = auto()
    JOIN = auto()
    LEAVE = auto()
    UPDATE = auto()
    LIST = auto()
    GET_HISTORY = auto()


class ChannelManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.channels = []
        self.current_channel = None

    def handle_action(self, action: ChannelType, channel_name: str = None, data: dict = None):

        if action == ChannelType.CREATE:
            self._handle_create(channel_name)
        elif action == ChannelType.DELETE:
            self._handle_delete(channel_name)
        elif action == ChannelType.JOIN:
            self._handle_join(channel_name)
        elif action == ChannelType.LEAVE:
            self._handle_leave(channel_name)
        elif action == ChannelType.UPDATE:
            self._handle_update(channel_name, data)
        elif action == ChannelType.LIST:
            self._handle_list(data)
        elif action == ChannelType.GET_HISTORY:
            self._handle_get_history(channel_name)

    def _handle_create(self, channel_name: str):
        if channel_name not in self.channels:
            self.channels.append(channel_name)
            self.main_window.channel_list.addItem(channel_name)

    def _handle_delete(self, channel_name: str):
        if channel_name in self.channels:
            self.channels.remove(channel_name)
            # Remove from QListWidget
            items = self.main_window.channel_list.findItems(channel_name, Qt.MatchExactly)
            for item in items:
                row = self.main_window.channel_list.row(item)
                self.main_window.channel_list.takeItem(row)

            # Clear chat if we were in this channel
            if self.current_channel == channel_name:
                self.current_channel = None
                self.main_window.chat_display.clear()
                QMessageBox.information(self.main_window, 'Channel Deleted',
                    f'The channel "{channel_name}" has been deleted.')

    def _handle_join(self, channel_name: str):
        """Handle joining a channel"""
        if self.current_channel == channel_name:
            return  # Already in this channel

        self.current_channel = channel_name
        self.main_window.chat_display.clear()
        # Send join command to server
        command = f"join {channel_name}"
        self.main_window.socket.sendall(command.encode(ENCODING))

    def _handle_leave(self, channel_name: str):
        """Handle leaving a channel"""
        if self.current_channel == channel_name:
            self.current_channel = None
            self.main_window.chat_display.clear()
            # Send leave command to server if needed
            command = f"leave {channel_name}"
            self.main_window.socket.sendall(command.encode(ENCODING))

    def _handle_update(self, channel_name: str, data: dict):
        """Handle channel updates (e.g., user list changes)"""
        if data and self.current_channel == channel_name:
            # Handle any channel updates like user list changes
            # Implementation depends on your specific needs
            pass

    def _handle_list(self, data: dict):
        """Handle receiving channel list from server"""
        if data and 'channels' in data:
            self.channels = data['channels']
            self.main_window.channel_list.clear()
            for channel in self.channels:
                self.main_window.channel_list.addItem(channel)

    def _handle_get_history(self, channel_name: str):
        """Handle retrieving channel history"""
        if self.current_channel == channel_name:
            command = f"get_history {channel_name}"
            self.main_window.socket.sendall(command.encode(ENCODING))