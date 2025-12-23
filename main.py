import argparse
import time
import sys
import threading
from utils import logger
from network_manager import NetworkManager
from input_handler import InputHandler
from clipboard_manager import ClipboardManager

class ShareMouseApp:
    def __init__(self):
        self.args = self.parse_arguments()
        self.mode = self.args.mode
        
        # Modules
        self.net_mgr = NetworkManager(self.mode, self.args.host, self.args.port, self._on_network_message)
        self.input_handler = InputHandler(
            on_event=self._on_input_event, 
            on_toggle=self._on_toggle_control,
            invert_scroll_x=self.args.invert_scroll_x,
            invert_scroll_y=self.args.invert_scroll_y
        )
        self.clipboard_mgr = ClipboardManager(on_update=self._on_clipboard_update)
        
        self.remote_active = False

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="LAN ShareMouse - Share Keyboard, Mouse and Clipboard")
        parser.add_argument("--mode", choices=["server", "client"], required=True, help="Run as server (host) or client (guest)")
        parser.add_argument("--host", default="0.0.0.0", help="Host IP address to bind (server) or connect to (client)")
        parser.add_argument("--port", type=int, default=5001, help="Port number")
        parser.add_argument("--invert-scroll-x", action="store_true", help="Invert horizontal mouse scroll direction")
        parser.add_argument("--invert-scroll-y", action="store_true", help="Invert vertical mouse scroll direction (natural scrolling)")
        return parser.parse_args()

    def start(self):
        logger.info(f"Starting ShareMouse in {self.mode} mode...")
        
        # Start Network
        self.net_mgr.start()
        
        # Start Clipboard
        self.clipboard_mgr.start()
        
        if self.mode == 'server':
            # Server listens for hotkey to take control
            self.input_handler.start_hotkey_listener()
            logger.info("Press Ctrl+Alt+S to toggle remote control")
        else:
            # Client just waits for commands
            logger.info("Waiting for commands from server...")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        logger.info("Shutting down...")
        self.net_mgr.stop()
        self.clipboard_mgr.stop()
        if self.mode == 'server':
            self.input_handler.stop_capture()
            self.input_handler.stop_hotkey_listener()
            
    # --- Event Callbacks ---

    def _on_toggle_control(self):
        if self.mode != 'server':
            return
            
        if not self.net_mgr.conn:
            logger.warning("Cannot toggle control: No client connected")
            return
            
        self.remote_active = not self.remote_active
        logger.info(f"Remote Control Active: {self.remote_active}")
        
        if self.remote_active:
            self.input_handler.start_capture()
        else:
            # Send signal to client to release modifiers BEFORE stopping capture logic locally
            logger.info("Sending reset_modifiers signal to client")
            self.net_mgr.send_data({'type': 'reset_modifiers'})
            self.input_handler.stop_capture()

    def _on_input_event(self, data):
        # Input received from local capture (Server only)
        if self.mode == 'server' and self.remote_active:
            self.net_mgr.send_data(data)

    def _on_clipboard_update(self, content):
        # Local clipboard changed, send to remote
        self.net_mgr.send_data({'type': 'cb', 'content': content})

    def _on_network_message(self, data):
        # Received data from network
        etype = data.get('type')
        
        if etype == 'reset_modifiers':
            self.input_handler.release_all_modifiers()
            
        elif etype == 'cb':
            # Clipboard update
            self.clipboard_mgr.update_local(data['content'])
            
        elif etype in ['mm', 'mc', 'ms', 'kp']:
            # Input event
            if self.mode == 'client':
                # Client executes commands from Server
                self.input_handler.inject_event(data)
            elif self.mode == 'server':
                # Maybe support bidirectional in future, but for now Server ignores input from Client
                # UNLESS we want Client to control Server? 
                # Current logic: Server controls Client via toggle.
                pass

if __name__ == "__main__":
    app = ShareMouseApp()
    app.start()
