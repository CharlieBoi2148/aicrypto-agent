import os
import subprocess
import signal
import shlex
import time
import socket
import threading
import select
import random
import errno
import collections
import atexit

from src.utils.logger import Logger



class ServerManager:
    def __init__(self, config):
        """
        Initialize the ServerManager with a challenge configuration.
        
        Args:
            challenge_config (dict): Dictionary containing challenge information
                                    parsed from a challenge.yaml file.
            logger: Optional logger instance
        """
        self.config = config
        print(self.config)
        self.process = None
        self.server_socket = None
        self.running = False
        self.client_threads = []
        self.max_clients = 20
        self.active_clients = collections.deque()
        self.clients_lock = threading.Lock()
        
        # Keep a set of all child processes we launch so we can ensure they are
        # terminated when the corresponding client disconnects or when the
        # server stops.
        self.child_processes = set()
        
        # Initialize logger
        self._init_logger()
        self.logger.log("ServerManager initialized")
        # Extract server configuration
        if 'server_work_dir' not in self.config:
            raise ValueError("Server configuration not found in challenge config")
        
        self.work_dir = self.config['server_work_dir']
        self.command = "python main.py"
        self.port = 1337  # Ensure port is an integer
        self.actual_port = self.port  # Store the actual port used, which may differ from config
        
        # Validate configuration
        self._validate_config()

    def _init_logger(self):
        """Initialize logger with proper path handling."""
        log_dir = os.path.join(*self.config['write_path'].split('/')[:-1])
        log_path = os.path.join(log_dir, 'server.log')
        log_name = f'server_{self.config["write_path"].split("/")[-1]}'
        self.logger = Logger(log_name, log_path)

    def _validate_config(self):
        """Validate server configuration."""
        if not self.work_dir:
            raise ValueError("Work directory not specified in server configuration")
        if not self.command:
            raise ValueError("Command not specified in server configuration")
        if not self.port:
            raise ValueError("Port not specified in server configuration")

    def log(self, message):
        """Log a message if logger is available"""
        self.logger.log(f"{message}")

    def _kill_process(self, process):
        """Safely kill a process and its children."""
        if not process or process.poll() is not None:
            return
        
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.wait(timeout=1)
        except Exception as e:
            self.log(f"Error killing process: {e}")

        # Remove the process from the tracking set if present
        try:
            self.child_processes.discard(process)
        except Exception:
            pass

    def _disconnect_client(self, client_data):
        """Safely disconnect a client and clean up resources."""
        client_data['active'] = False
        try:
            self._kill_process(client_data.get('process'))
            client_data['socket'].close()
        except Exception as e:
            self.log(f"Error disconnecting client: {e}")

    def handle_client(self, client_socket, client_address):
        """Handle communication between client and process."""
        self.log(f"New connection from {client_address}")
        
        # Manage client connections
        client_data = {
            "socket": client_socket, 
            "address": client_address, 
            "process": None, 
            "active": True
        }
        
        with self.clients_lock:
            # Remove oldest clients if at capacity
            while len(self.active_clients) >= self.max_clients:
                oldest_client = self.active_clients.popleft()
                self.log(f"Maximum clients reached. Disconnecting oldest client from {oldest_client['address']}")
                self._disconnect_client(oldest_client)
            
            self.active_clients.append(client_data)
        
        # Start process for this client
        try:
            process = self._start_client_process()
            client_data['process'] = process
            
            # Handle bidirectional communication
            self._handle_communication(client_socket, process, client_data)
            
        except Exception as e:
            self.log(f"Error handling client: {e}")
        finally:
            self._cleanup_client(client_data)

    def _start_client_process(self):
        """Start a new process for a client."""
        command_parts = shlex.split(self.command)
        proc = subprocess.Popen(
            command_parts,
            cwd=self.work_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            text=False,
            preexec_fn=os.setsid
        )
        # Track the process so we can clean it up later
        self.child_processes.add(proc)
        return proc

    def _handle_communication(self, client_socket, process, client_data):
        """Handle bidirectional communication between client and process."""
        def process_to_client():
            try:
                while self.running and process.poll() is None and client_data['active']:
                    ready_to_read, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)
                    
                    for stream in ready_to_read:
                        chunk = os.read(stream.fileno(), 4096)
                        if chunk:
                            client_socket.sendall(chunk)
            except Exception as e:
                self.log(f"Error in process_to_client: {e}")

        def client_to_process():
            try:
                while self.running and process.poll() is None and client_data['active']:
                    ready_to_read, _, _ = select.select([client_socket], [], [], 0.1)
                    
                    if client_socket in ready_to_read:
                        data = client_socket.recv(4096)
                        if not data:
                            # Client disconnected
                            client_data['active'] = False
                            break
                        os.write(process.stdin.fileno(), data)
            except Exception as e:
                self.log(f"Error in client_to_process: {e}")

        # Start communication threads
        threads = [
            threading.Thread(target=process_to_client, daemon=True),
            threading.Thread(target=client_to_process, daemon=True)
        ]
        
        for thread in threads:
            thread.start()
        
        # Wait for process completion or disconnection
        while process.poll() is None and self.running and client_data['active']:
            time.sleep(0.1)

        # When exiting the loop, ensure the process is terminated if still running
        self._kill_process(process)

    def _cleanup_client(self, client_data):
        """Clean up client resources."""
        self._kill_process(client_data.get('process'))
        
        try:
            client_data['socket'].close()
        except:
            pass
        
        # Remove from active clients
        with self.clients_lock:
            if client_data in self.active_clients:
                self.active_clients.remove(client_data)
        
        self.log(f"Connection from {client_data['address']} closed")

    def _get_random_port(self):
        """Generate a random port number between 10000 and 65535."""
        return random.randint(10000, 65535)
    
    def start(self):
        """Start the server and listen for client connections."""
        if self.running:
            self.log(f"Server already running on port {self.actual_port}")
            return
        
        # Make sure work directory exists
        if not os.path.exists(self.work_dir):
            raise FileNotFoundError(f"Work directory '{self.work_dir}' does not exist")
        
        max_attempts = 5
        attempt = 0
        
        while attempt < max_attempts:
            try:
                self._start_server()
                break
            except socket.error as e:
                if e.errno == errno.EADDRINUSE:
                    self.log(f"Port {self.port} is already in use. Trying another port...")
                    self.port = self._get_random_port()
                    attempt += 1
                else:
                    self.log(f"Failed to start server: {e}")
                    self.stop()
                    raise
            except Exception as e:
                self.log(f"Failed to start server: {e}")
                self.stop()
                raise
                
        if attempt >= max_attempts:
            raise RuntimeError(f"Failed to find an available port after {max_attempts} attempts")
    
    def _start_server(self):
        """Start the server socket and accept connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('127.0.0.1', self.port))
        self.server_socket.listen(5)
        
        self.running = True
        self.actual_port = self.port
        self.log(f"Server started successfully. Listening on port {self.actual_port}")
        
        # Start accepting connections
        self.accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
        self.accept_thread.start()

    def _accept_connections(self):
        """Accept client connections in a loop."""
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                client_socket, client_address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
                self.client_threads.append(client_thread)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.log(f"Error accepting connection: {e}")

    def stop(self):
        """Stop the server and clean up all resources."""
        if not self.running:
            return
            
        self.log("Stopping server...")
        self.running = False
        
        # Stop all active client processes
        with self.clients_lock:
            while self.active_clients:
                client_data = self.active_clients.popleft()
                self._disconnect_client(client_data)
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.log(f"Error closing server socket: {e}")
            finally:
                self.server_socket = None
        
        # Wait for accept thread
        if hasattr(self, 'accept_thread') and self.accept_thread:
            try:
                self.accept_thread.join(timeout=2)
            except Exception:
                pass
        
        # Clear thread list
        self.client_threads.clear()
        
        # As an extra safety net, terminate any child processes that might not be
        # associated with an active client (should be rare, but prevents leaks).
        for proc in list(self.child_processes):
            self._kill_process(proc)
        
        self.log("Server stopped")
        self.logger.close()
    
    def __del__(self):
        """Clean up when the object is garbage collected."""
        self.stop()

        # Ensure that all child processes are cleaned up if the interpreter exits
        atexit.register(lambda: None)  # placeholder to keep atexit available
        
    def get_port(self):
        """Return the actual port the server is running on."""
        return self.actual_port



 
   