import socket
import logging
from contextlib import closing

def find_available_port(start_port=8501, max_port=8600):
    """Find an available port starting from start_port up to max_port.
    
    Args:
        start_port (int): Starting port number
        max_port (int): Maximum port number to try
    
    Returns:
        int: Available port number
    
    Raises:
        RuntimeError: If no ports are available in the range
        ValueError: If port numbers are invalid
    """
    # Ensure ports are integers
    try:
        start_port = int(start_port)
        max_port = int(max_port)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Port numbers must be integers: {e}")
        
    if not (1024 <= start_port <= 65535) or not (1024 <= max_port <= 65535):
        raise ValueError(f"Port numbers must be between 1024 and 65535")
        
    for port in range(start_port, max_port + 1):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            try:
                sock.bind(('', port))
                logging.info(f"Found available port: {port}")
                return port
            except socket.error:
                logging.debug(f"Port {port} is in use, trying next port")
                continue
    raise RuntimeError(f"No available ports in range {start_port}-{max_port}")
