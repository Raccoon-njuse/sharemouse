import socket
import struct
import json
import threading
import time
from utils import logger

class NetworkManager:
    def __init__(self, mode, host, port, on_message_received=None):
        self.mode = mode
        self.host = host
        self.port = port
        self.running = False
        self.sock = None
        self.conn = None
        self.on_message_received = on_message_received
        self._send_lock = threading.Lock()

    def start(self):
        self.running = True
        thread_target = self._run_server if self.mode == 'server' else self._run_client
        threading.Thread(target=thread_target, daemon=True).start()
        logger.info(f"NetworkManager started in {self.mode} mode")

    def _run_server(self):
        logger.info(f"Server listening on {self.host}:{self.port}")
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server_sock.bind((self.host, self.port))
            server_sock.listen(1)
            self.sock = server_sock
            while self.running:
                logger.info("Waiting for connection...")
                try:
                    conn, addr = server_sock.accept()
                    logger.info(f"Connected by {addr}")
                    self.conn = conn
                    self._handle_connection(conn)
                except OSError:
                    if self.running:
                        logger.warning("Socket accept failed (probably closed)")
                    break
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self._close_socket()

    def _run_client(self):
        while self.running:
            try:
                logger.info(f"Connecting to {self.host}:{self.port}...")
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                self.conn = self.sock
                logger.info("Connected to server")
                self._handle_connection(self.sock)
            except Exception as e:
                logger.error(f"Connection failed: {e}. Retrying in 2s...")
                time.sleep(2)
            
            # If connection lost or failed, cleanup before retry
            if self.running:
                self.conn = None
                try: self.sock.close() 
                except: pass

    def _handle_connection(self, conn):
        try:
            while self.running:
                # Read 4 bytes length
                length_bytes = self._recv_all(conn, 4)
                if not length_bytes:
                    break
                length = struct.unpack('!I', length_bytes)[0]
                
                # Check for sanity to avoid OOM on garbage data
                if length > 10 * 1024 * 1024: # 10MB limit
                    logger.error(f"Packet too large: {length} bytes")
                    break

                # Read payload
                payload = self._recv_all(conn, length)
                if not payload:
                    break
                
                try:
                    data = json.loads(payload.decode('utf-8'))
                    if self.on_message_received:
                        self.on_message_received(data)
                except json.JSONDecodeError:
                    logger.error("Failed to decode JSON")
                    
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            logger.info("Connection lost/closed")
            self.conn = None
            # Server keeps listening, client loop handles reconnection

    def _recv_all(self, sock, count):
        buf = b''
        while count > 0:
            try:
                newbuf = sock.recv(count)
                if not newbuf: return None
                buf += newbuf
                count -= len(newbuf)
            except OSError:
                return None
        return buf

    def send_data(self, data):
        if not self.conn:
            return False
        try:
            payload = json.dumps(data).encode('utf-8')
            packet = struct.pack('!I', len(payload)) + payload
            with self._send_lock:
                self.conn.sendall(packet)
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False

    def stop(self):
        logger.info("Stopping NetworkManager...")
        self.running = False
        self._close_socket()

    def _close_socket(self):
        if self.conn:
            try: self.conn.close()
            except: pass
        if self.sock:
            try: self.sock.close()
            except: pass
        self.conn = None
        self.sock = None
