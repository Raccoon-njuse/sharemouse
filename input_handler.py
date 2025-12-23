from utils import logger
from pynput import mouse, keyboard
import threading
import time

class InputHandler:
    def __init__(self, on_event=None, on_toggle=None, invert_scroll_x=False, invert_scroll_y=False):
        self.on_event = on_event
        self.on_toggle = on_toggle
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        self.screen_size = self._get_screen_size()
        
        self.capturing = False
        self.hotkey_listener = None
        self.capture_mouse_listener = None
        self.capture_key_listener = None
        
        # Scroll inversion configuration
        self.invert_scroll_x = invert_scroll_x
        self.invert_scroll_y = invert_scroll_y
        
        # Mouse move throttling
        self.last_mouse_move_time = 0
        self.throttle_interval = 0.016  # ~60 FPS
        self.pending_mouse_move = None
        
        # Shortcuts state
        self.pressed_keys = set()
        
    def _get_screen_size(self):
        # A simple way to get screen size using pynput or tkinter? 
        # pynput doesn't give screen size directly nicely.
        # Let's use Quartz on Mac or just assume user config? 
        # Or better, use a dummy move and check position? No.
        # Let's try to use root window info if possible, or just default to common, 
        # but normalization requires it.
        # On macOS `AppKit.NSScreen.mainScreen().frame().size` but that requires AppKit.
        # Let's use `pyautogui.size()` if available? No, not installed.
        # Workaround: Use simple assumption or maybe strict platform specific code?
        # For now, let's try to rely on absolute coords or add a method.
        # Actually, pynput doesn't easily give screen dimensions. 
        # For MVP, let's assume 1920x1080 if we can't get it, OR:
        # We handle "relative" movement for mouse move? 
        # But if we want to map screen A to B, we need normalization.
        # Let's try importing AppKit if on Mac.
        try:
            if 'darwin' in __import__('sys').platform:
                from AppKit import NSScreen
                frame = NSScreen.mainScreen().frame()
                return (frame.size.width, frame.size.height)
            else:
                # Windows
                import ctypes
                user32 = ctypes.windll.user32
                return (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
        except:
            logger.warning("Could not determine screen size, defaulting to 1920x1080")
            return (1920, 1080)

    def start_hotkey_listener(self):
        """Starts the listener that waits for the toggle hotkey (Ctrl+Alt+S)"""
        logger.info("Starting hotkey listener...")
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            
        self.hotkey_listener = keyboard.Listener(on_press=self._on_hotkey_press, on_release=self._on_hotkey_release)
        self.hotkey_listener.start()

    def stop_hotkey_listener(self):
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None

    def start_capture(self):
        """Starts capturing all input and suppressing it locally."""
        if self.capturing: return
        self.capturing = True
        logger.info("Starting input capture (suppressed)...")
        
        # Stop hotkey listener to avoid double handling, 
        # but we need to detect toggle combo inside capture listener too to exit!
        self.stop_hotkey_listener()
        
        self.capture_mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
            suppress=True
        )
        self.capture_mouse_listener.start()
        
        self.capture_key_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
            suppress=True
        )
        self.capture_key_listener.start()

    def stop_capture(self):
        """Stops capturing input."""
        if not self.capturing: return
        self.capturing = False
        logger.info("Stopping input capture...")
        
        if self.capture_mouse_listener:
            self.capture_mouse_listener.stop()
            self.capture_mouse_listener = None
            
        if self.capture_key_listener:
            self.capture_key_listener.stop()
            self.capture_key_listener = None
            
        # Clear state
        self.pressed_keys.clear()
        
        # Restart hotkey listener
        self.start_hotkey_listener()

    def release_all_modifiers(self):
        """Force release of all modifier keys."""
        logger.info("Releasing all modifier keys...")
        
        # Windows-specific low-level release
        if 'win32' in __import__('sys').platform:
            try:
                import ctypes
                user32 = ctypes.windll.user32
                # VK Codes: Shift=0x10, Ctrl=0x11, Alt=0x12, Win=0x5B
                keys = [0x10, 0x11, 0x12, 0x5B] 
                for vk in keys:
                    # KEYEVENTF_KEYUP = 0x0002
                    user32.keybd_event(vk, 0, 0x0002, 0)
                logger.info("Windows modifiers reset via ctypes")
                return
            except Exception as e:
                logger.error(f"Windows ctypes reset failed: {e}")

        # Fallback for other OS or if ctypes fails
        modifiers = [
            keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
            keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
            keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r,
            keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r
        ]
        for key in modifiers:
            try:
                self.keyboard_controller.release(key)
            except:
                pass

    def _check_toggle(self, key, is_press):
        # Check for Ctrl+Alt+S
        # pynput keys: Key.ctrl, Key.alt, 's'
        # We track pressed keys set
        
        key_str = self._get_key_str(key)
        
        if is_press:
            self.pressed_keys.add(key_str)
        else:
            if key_str in self.pressed_keys:
                self.pressed_keys.remove(key_str)
                
        # Logic: need Ctrl (any) + Alt (any) + S
        has_ctrl = 'Key.ctrl' in self.pressed_keys or 'Key.ctrl_l' in self.pressed_keys or 'Key.ctrl_r' in self.pressed_keys
        has_alt = 'Key.alt' in self.pressed_keys or 'Key.alt_l' in self.pressed_keys or 'Key.alt_r' in self.pressed_keys
        has_s = "'s'" in self.pressed_keys or 's' in self.pressed_keys # char keys format varies
        
        # logger.debug(f"Keys: {self.pressed_keys}")
        
        if has_ctrl and has_alt and has_s:
            logger.info("Toggle sequence detected!")
            if self.on_toggle:
                self.on_toggle()
            # Clear keys to prevent rapid re-trigger
            self.pressed_keys.clear()
            return True
        return False

    def _on_hotkey_press(self, key):
        self._check_toggle(key, True)

    def _on_hotkey_release(self, key):
        self._check_toggle(key, False)

    # Capture Listeners
    def _on_mouse_move(self, x, y):
        # Normalize coordinates
        nx = x / self.screen_size[0]
        ny = y / self.screen_size[1]
        current_time = time.time()
        
        if self.on_event:
            # Check if we should send immediately
            if current_time - self.last_mouse_move_time >= self.throttle_interval:
                # Send immediately
                self.on_event({'type': 'mm', 'x': nx, 'y': ny})
                self.last_mouse_move_time = current_time
                self.pending_mouse_move = None
            else:
                # Save as pending if there's no pending move
                if not self.pending_mouse_move:
                    self.pending_mouse_move = {'x': nx, 'y': ny}
                    # Schedule sending the pending move after throttle interval
                    threading.Timer(self.throttle_interval, self._send_pending_mouse_move).start()

    def _on_mouse_click(self, x, y, button, pressed):
        nx = x / self.screen_size[0]
        ny = y / self.screen_size[1]
        btn = str(button).replace('Button.', '')
        if self.on_event:
            self.on_event({'type': 'mc', 'x': nx, 'y': ny, 'button': btn, 'pressed': pressed})

    def _on_mouse_scroll(self, x, y, dx, dy):
        # Apply scroll inversion
        processed_dx = -dx if self.invert_scroll_x else dx
        processed_dy = -dy if self.invert_scroll_y else dy
        
        if self.on_event:
            self.on_event({'type': 'ms', 'dx': processed_dx, 'dy': processed_dy})
    
    def _send_pending_mouse_move(self):
        """Send the pending mouse move event if there is one."""
        if self.pending_mouse_move and self.on_event:
            current_time = time.time()
            if current_time - self.last_mouse_move_time >= self.throttle_interval:
                self.on_event({'type': 'mm', 'x': self.pending_mouse_move['x'], 'y': self.pending_mouse_move['y']})
                self.last_mouse_move_time = current_time
                self.pending_mouse_move = None

    def _on_key_press(self, key):
        if self._check_toggle(key, True):
            return # Don't send the toggle keys themselves if possible, or send them? 
                   # If we suppress, we don't send to OS. Protocol consumer shouldn't act on them locally?
                   # Actually, if we toggle OFF, we shouldn't send 's' to remote.
            pass
        
        key_str = self._get_key_str(key)
        if self.on_event:
            self.on_event({'type': 'kp', 'key': key_str, 'pressed': True})

    def _on_key_release(self, key):
        if self._check_toggle(key, False):
            return 
            
        key_str = self._get_key_str(key)
        if self.on_event:
            self.on_event({'type': 'kp', 'key': key_str, 'pressed': False})

    def _get_key_str(self, key):
        if hasattr(key, 'char'):
            return f"'{key.char}'" if key.char else 'None'
        else:
            return str(key)

    # Injection
    def inject_event(self, data):
        try:
            etype = data.get('type')
            if etype == 'mm':
                x = int(data['x'] * self.screen_size[0])
                y = int(data['y'] * self.screen_size[1])
                self.mouse_controller.position = (x, y)
                
            elif etype == 'mc':
                x = int(data['x'] * self.screen_size[0])
                y = int(data['y'] * self.screen_size[1])
                self.mouse_controller.position = (x, y)
                
                btn_name = data['button']
                btn = getattr(mouse.Button, btn_name, mouse.Button.left)
                if data['pressed']:
                    self.mouse_controller.press(btn)
                else:
                    self.mouse_controller.release(btn)
                    
            elif etype == 'ms':
                # Apply scroll inversion for incoming events
                dx = data['dx']
                dy = data['dy']
                processed_dx = -dx if self.invert_scroll_x else dx
                processed_dy = -dy if self.invert_scroll_y else dy
                self.mouse_controller.scroll(processed_dx, processed_dy)
                
            elif etype == 'kp':
                key_str = data['key']
                pressed = data['pressed']
                
                # Parse key
                key = None
                if key_str.startswith('Key.'):
                    key_attr = key_str.replace('Key.', '')
                    key = getattr(keyboard.Key, key_attr, None)
                elif key_str.startswith("'") and key_str.endswith("'"):
                     key = key_str[1:-1]
                
                if key:
                    if pressed:
                        self.keyboard_controller.press(key)
                    else:
                        self.keyboard_controller.release(key)
        except Exception as e:
            logger.error(f"Injection error: {e}")

