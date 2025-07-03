import socket
import fcntl
import struct
import os
import getpass
import subprocess
import sys
from typing import List, Optional

# Prevent Python from generating .pyc files
sys.dont_write_bytecode = True


def _exec(command: List[str]) -> bool:
    """
    Executes the given command.
    Returns True if successful, False otherwise.
    """
    try:
        subprocess.run(command, check=True)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to execute command: {e}")
        return False


def _save(content: str, file_path: str) -> bool:
    """
    Saves content to a file.
    Returns True if successful, False otherwise.
    """
    try:
        with open(file_path, "w") as file:
            file.write(content)
        print(f"[INFO] Saved: {file_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save file: {e}")
        return False


def _del_if_exists(file_path: str) -> bool:
    """
    Deletes the file if it exists.
    Returns True if deleted or not present, False on error.
    """
    if os.path.exists(file_path):
        return _exec(["sudo", "rm", "-rf", file_path])
    return True


def _cat_file(file_path: str) -> str:
    """
    Reads and returns the contents of a file.
    """
    command = ["cat", file_path]
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    return result.stdout


def check_internet_connection_2(attempts: int = 5, host: str = "1.1.1.1") -> bool:
    """
    Checks internet connectivity by pinging the specified host.
    Returns True if packets are received, False otherwise.
    """
    try:
        command = ["ping", "-c", str(attempts), host]
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        print("\n================== Internet Connection Check ==================\n")
        print(result.stdout)

        if f"{attempts} packets transmitted, 0 received," in result.stdout:
            print("[ERROR] No response from server. No internet connection.")
            return False
        if f"{attempts} packets transmitted, {attempts} received," in result.stdout:
            print("[INFO] Internet connection established successfully.")
            return True

        print("[INFO] Internet connection is partially working.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to ping host: {e}")
        return False


def check_internet_connection(host: str = "1.1.1.1", attempts: int = 5) -> bool:
    """
    Checks internet connectivity by pinging the specified host.
    Prints output in real time and returns True if at least 80% of packets are received.
    """
    print(f"[INFO] Testing connection to {host} ({attempts} attempts)...")
    
    # Platfrom: Linux/macOS or  Windows
    arg = "-c" if sys.platform != "win32" else "-n"
    try:
        process = subprocess.Popen(
            ["ping", host, arg, str(attempts)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        received = 0
        transmitted = 0

        if process.stdout:
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

                print(line)

                if "bytes from" in line or "64 bytes from" in line:
                    received += 1
                elif "packets transmitted" in line or "Packets: Sent" in line:
                    parts = line.split(",")
                    for part in parts:
                        if "received" in part:
                            received = int(part.split()[0])
                        elif "transmitted" in part or "Received" in part:
                            transmitted = int(part.split()[0])

        process.wait()

        if transmitted == 0:
            transmitted = attempts

        success_rate = (received / transmitted) * 100
        print(f"\n[RESULT] Received {received}/{transmitted} packets ({success_rate:.1f}%)\n")

        return (success_rate >= 80.0, success_rate)

    except Exception as e:
        print(f"[ERROR] Connection check failed: {e}")
        return False


def block_file(file_path: str) -> bool:
    """
    Makes the file immutable to prevent modifications.
    Returns True if successful, False otherwise.
    """
    if os.path.exists(file_path):
        result = _exec(["sudo", "chattr", "+i", file_path])
        if result:
            print(f"[INFO] File {file_path} has been locked.")
        return result
    return False


def unblock_file(file_path: str) -> bool:
    """
    Removes immutability from a file.
    Returns True if successful, False otherwise.
    """
    if os.path.exists(file_path):
        result = _exec(["sudo", "chattr", "-i", file_path])
        if result:
            print(f"[INFO] File {file_path} has been unlocked.")
        return result
    return False


def del_file(file_path: str) -> bool:
    """
    Deletes the file after removing immutability if necessary.
    Returns True if file was deleted or didn't exist, False otherwise.
    """
    if _del_if_exists(file_path):
        return True
    if unblock_file(file_path):
        return _del_if_exists(file_path)
    return False


def _check_content_matches(expected_dns: List[str], content: str) -> bool:
    """
    Verifies that all expected DNS entries are present in the content.
    Returns True if all are found, False otherwise.
    """
    for dns in expected_dns:
        if f"nameserver {dns}" not in content:
            return False
    return True

def is_apt_process(line: str) -> bool:
    return any(keyword in line for keyword in ["apt-get", "apt-cache", "apt install", "/usr/lib/apt"])


def get_default_interface_and_ip():
    """
    Retorna informações sobre a interface de saída padrão:
    - Interface (ex: eth0)
    - IP local atribuído
    - Gateway padrão
    """
    def list_network_interfaces():
        """
        Lista todas as interfaces de rede disponíveis no sistema.
        """
        try:
            return os.listdir("/sys/class/net")
        except FileNotFoundError:
            return []
    
    def get_all_ips():
        """
        Retorna um dicionário com interfaces e seus IPs.
        """
        cmd = ["ip", "-br", "addr", "show"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        data = {}

        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            intf = parts[0]
            ip = parts[2].split("/")[0] if '/' in parts[2] else None
            data[intf] = ip

        return data

    def get_gateway():
        """Retorna o gateway padrão."""
        data = {}
        try:
            result = subprocess.run(["ip", "route"],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
            result = [line.strip() for line in result.stdout.splitlines() if line.startswith("default")]
            result = result[0] if result else None
        except:
            return {}
        if result:
            try: 
                iface = [part.strip() for part in result.split() if part in list_network_interfaces()]
                iface = iface[0] if iface else None
                if iface:
                    data["interface"]=iface
                    try:
                        ip = [ip for ifcon, ip in get_all_ips().items() if iface == ifcon]
                        ip = ip[0] if ip else None
                    except:
                        ip = get_ip_address(iface)
                    if ip:
                        data["ip"]=ip
                        try:
                            class_ip = ip.split('.')[-1] if '.' in ip else ip
                            class_ip = ip.rstrip(class_ip) if class_ip != ip else class_ip
                            gw = [part for part in result.split() if class_ip in part]
                            if gw: data["gateway"]=gw[0]
                        except:
                            pass
            except Exception:
                pass            
        return data

    def get_ip_address(ifname):
        """Retorna o IP da interface."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ip = socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', ifname[:15].encode('utf-8'))
            )[20:24])
            return ip
        except Exception:
            return None

    # Busca gateway e interface
    gw_info = get_gateway()
    if not gw_info:
        return {"error": "No default route found"}

    return gw_info
    
class NetworkManager:
    def __init__(
        self,
        dns_servers: List[str] = None,
        ping_host: str = "www.google.com",
        resolv_conf: str = "/etc/resolv.conf",
    ):
        self.dns_servers = dns_servers or ["8.8.8.8", "8.8.4.4", "1.1.1.1"]
        self.ping_host = ping_host
        self.resolv_conf_path = resolv_conf

    def configure_dns(self) -> Optional[bool]:
        """
        Configures DNS servers in /etc/resolv.conf.
        Returns:
            - True if configuration succeeded
            - False if failed
            - None if already configured
        """
        if os.path.exists(self.resolv_conf_path):
            print(f"[INFO] Current content of {self.resolv_conf_path}:")
            current_content = _cat_file(self.resolv_conf_path)
            print(current_content)

            if current_content and _check_content_matches(self.dns_servers, current_content):
                return None  # Already configured

        unblock_file(self.resolv_conf_path)
        if not del_file(self.resolv_conf_path):
            print(f"[ERROR] Failed to remove {self.resolv_conf_path}.")
            return False

        print(f"\n[INFO] Setting up {self.resolv_conf_path}.\n")
        content = "\n".join([f"nameserver {dns}" for dns in self.dns_servers]) + "\n"

        if _save(content, "temp.conf"):
            if _exec(["sudo", "mv", "temp.conf", self.resolv_conf_path]):
                print(f"[INFO] Successfully configured {self.resolv_conf_path}.")
                block_file(self.resolv_conf_path)

                new_content = _cat_file(self.resolv_conf_path)
                print(f"[INFO] New content of {self.resolv_conf_path}:\n{new_content}")
                return True
            _del_if_exists("temp.conf")

        print(f"[ERROR] Failed to save {self.resolv_conf_path}.")
        return False

    def check_connection(self, percentage_of_correct: float = 60.0) -> bool:
        """
        Checks internet connection and handles common issues.
        """
        info = get_default_interface_and_ip()
        print("[INFO] Default Network Interface Info:")
        for k, v in info.items():
            print(f" - {k}: {v}")
            
        print("\n[INFO] Checking initial internet connection.")
        hosts=[self.ping_host] + self.dns_servers        
        print("[INFO] Testing DNS servers...\n")
        results = []
        rates = 0.0
        for host in hosts:
            result, rate = check_internet_connection(host=host)
            results.append(result)
            rates += rate
            print(f"[INFO] {str(f'{rate:.1f}').zfill(3)}% rate of success in test host='{host}'\n")
        rates=float(rates/len(hosts))
        if all(results):
            print("[SUCCESS] Successfully connected to DNS servers.")
        elif rates >= percentage_of_correct:
            print("[SUCCESS] Successfully connected to DNS servers on most attempts.")
        else:
            print("[ERROR] Failed to connect to DNS servers.")
        print(f"[INFO] Full test {str(f'{rates:.1f}').zfill(3)}% rate of success")
        return rates >= percentage_of_correct

    def check_proccess_lock(self):
        print("[INFO] Checking for stuck apt processes.")
        result = subprocess.run(["ps", "aux"], stdout=subprocess.PIPE, text=True)
        lines = result.stdout.split("\n")
        current_user = getpass.getuser()

        for line in lines:
            if is_apt_process(line):
                parts = line.split()
                try:
                    pid = parts[1]
                    user = parts[0]

                    # Pula se for processo do usuário atual e do próprio script ou editor
                    if user == current_user and ("python" in line or "code" in line or "debugpy" in line):
                        print(f"[SKIP] Skipping own/editor process: {line}")
                        continue

                    print(f"[INFO] Killing stuck apt process (PID: {pid})")
                    _exec(["sudo", "kill", "-9", pid])
                except Exception as e:
                    print(f"[ERROR] Could not parse line: {e}")

        lock_file="/var/lib/apt/lists/lock"
        if os.path.exists(lock_file):
            print("[INFO] Removing apt lock files.")
            _del_if_exists()

        return True


if __name__ == "__main__":
    manager = NetworkManager()
    config_result = manager.configure_dns()
    if config_result is None:
        print("[INFO] Configuration already applied.")
    else:
        print(f"[RESULT] Configuration completed: {'Yes' if config_result else 'No'}")
    if not manager.check_connection():
        manager.check_proccess_lock()
        manager.check_connection()