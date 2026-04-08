import uuid
import platform
import hashlib

def get_hwid() -> str:
    """
    Generate a unique Hardware ID for the current machine.
    Combines MAC address and hostname to create a stable hash.
    """
    # uuid.getnode() provides a unique identifier based on network interface (fallback to random)
    node = str(uuid.getnode())
    # platform.node() provides the hostname
    hostname = platform.node()
    # platform.processor() and machine() for additional entropy
    entropy = f"{node}-{hostname}-{platform.machine()}"
    
    # Hash it to create a fixed-length string
    return hashlib.sha256(entropy.encode()).hexdigest()[:16]
