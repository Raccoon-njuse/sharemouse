from utils import logger
import pyperclip
import threading
import time

class ClipboardManager:
    def __init__(self, on_update=None):
        self.on_update = on_update
        self.last_content = ""
        self.running = False
        self.polling_thread = None
        self._is_updating_local = False # Flag to prevent feedback loop

    def start(self):
        logger.info("Starting clipboard manager...")
        self.running = True
        self.polling_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.polling_thread.start()

    def stop(self):
        logger.info("Stopping clipboard manager...")
        self.running = False

    def update_local(self, content):
        """Updates local clipboard without triggering a network send."""
        if content == self.last_content:
            return
            
        logger.info(f"Received clipboard update (len={len(content)})")
        self._is_updating_local = True
        try:
            pyperclip.copy(content)
            self.last_content = content
        except Exception as e:
            logger.error(f"Clipboard update failed: {e}")
        finally:
            # Give a small grace period for the poll loop to see the change and ignore it?
            # Or just rely on self.last_content check in poll loop?
            # If we update logic: poll loop reads 'current', sees it matches 'last_content', does nothing.
            # But here we SET last_content. So poll loop will read 'current' == 'last_content', so no change detected.
            # So _is_updating_local might not be needed if we update last_content first!
            # But let's keep it for safety.
            time.sleep(0.1) 
            self._is_updating_local = False

    def _poll_loop(self):
        while self.running:
            try:
                if not self._is_updating_local:
                    current = pyperclip.paste()
                    if current != self.last_content:
                        self.last_content = current
                        if self.on_update:
                            logger.info(f"Local clipboard changed (len={len(current)})")
                            self.on_update(current)
            except Exception as e:
                logger.debug(f"Clipboard polling error: {e}")
            
            time.sleep(0.5)
