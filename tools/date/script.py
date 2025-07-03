import os
import sys
import yaml
import subprocess
from datetime import datetime

# Force Python not to create .pyc files
sys.dont_write_bytecode = True

import subprocess

def ensure_ntp_port_is_open():
    """
    Garante que a porta UDP 123 (usada pelo NTP) esteja liberada.
    
    - Verifica se o ufw está ativo
    - Se estiver, verifica se a regra de saída para 123/udp existe
    - Se não existir, adiciona a regra
    
    Retorna True se a porta está liberada ou não há bloqueio.
    """

    def is_ufw_active():
        """Verifica se o ufw está ativo."""
        try:
            result = subprocess.run(
                ["sudo", "ufw", "status", "verbose"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return "Status: active" in result.stdout
        except Exception:
            return False

    def is_ntp_rule_present():
        """Verifica se a regra de saída para 123/udp já existe."""
        try:
            result = subprocess.run(
                ["sudo", "ufw", "status", "numbered"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return "allow out 123/udp" in result.stdout
        except Exception:
            return False

    def add_ntp_rule():
        """Adiciona a regra de saída para porta 123/udp."""
        print("[INFO] Liberando saída na porta 123/UDP...")
        try:
            subprocess.run(["sudo", "ufw", "allow", "out", "123/udp"], check=True)
            print("[SUCCESS] Regra adicionada com sucesso.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Falha ao adicionar regra: {e}")
            return False

    # Etapa 1: Verifica se o ufw está ativo
    if not is_ufw_active():
        print("[INFO] O firewall 'ufw' está desativado. Não é necessário liberar a porta.")
        return True  # Se ufw estiver desligado, não há bloqueios

    # Etapa 2: Verifica se a regra já existe
    if is_ntp_rule_present():
        print("[INFO] Porta UDP 123 já está liberada.")
        return True

    # Etapa 3: Se não tiver regra, tenta adicionar
    return add_ntp_rule()

def format_system_datetime(dt):
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_last_modification_time(file_path):
    if os.path.exists(file_path):
        ts = os.path.getmtime(file_path)
        return datetime.fromtimestamp(ts)
    else:
        return None


def set_system_date(dt: str):
    """
    Set the system date using the date -s command.
    """
    try:
        date_str = format_system_datetime(dt)
        subprocess.run(["sudo", "date", "-s", date_str], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=True)
        print(f"[INFO] System date sync: {date_str}")
    except subprocess.CalledProcessERRORr as e:
        print(f"[ERROR] Failed system date sync: {e}")


def check_internet(host):
    """
    Check the internet connection by pinging.
    """
    try:
        subprocess.run(["ping", "-c", "1", host], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        print("[INFO] Internet connection OK.")
        return True
    except Exception:
        print("[ERROR] No internet connection.")
        return False


def sync_with_ntp(servers):
    """
    Tries to synchronize time with the list of NTP servers.
    """
    for server in servers:
        try:
            subprocess.run(["sudo", "ntpdate", "-u", server], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"[INFO] Synchronized with server {server}")
            return True
        except subprocess.CalledProcessError:
            print(f"[WARN] Error when syncing with {server}")
    return False

class AjustDate:
    def __init__(self, config_name_file):
        self.load_config(config_name_file)
        success = ensure_ntp_port_is_open()
        if success:
            print("[INFO] Porta UDP 123 está liberada ou não há bloqueio.")
        else:
            print("[ERROR] Falha ao liberar a porta UDP 123.")
        
    
    def load_config(self, config_name_file):
        config = {}
        self._local_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file=os.path.join(self._local_dir, config_name_file)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = yaml.safe_load(f)
            except:
                print(f"[WARN] Failed to read {self.config_file}")
        else:
            print(f"[WARN] The file {self.config_file} does not exist")
        self.timezone=config.get("timezone", "America/Sao_Paulo")
        self.ping_host=config.get("ping_host", '8.8.8.8')
        self.ntp_servers=config.get("ntp_servers", ['pool.ntp.org'])
        self.last_sync_file=os.path.join(self._local_dir, config.get("last_sync_file", os.path.join('.cache', 'last_sync_file.log')))
        
    
    def ensure_timezone(self):
        """
        Check if the timezone is correct. If it is not, try to correct it.
        """
        try:
            result = subprocess.run(["timedatectl"], capture_output=True, text=True)
            if self.timezone in result.stdout:
                print(f"[INFO] ✅ Timezone is already correct: {self.timezone}")
                return True
            subprocess.run(["sudo", "timedatectl", "set-timezone", self.timezone], check=True)
            print(f"[INFO] Timezone set to: {self.timezone}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to check/set timezone: {e}")
        return False
        
        
    def get_min_date(self):
        """
        Sets the minimum date: if there is a log file, use it, otherwise use the last_date from the config.
        """
        try:
            if os.path.exists(self.last_sync_file):
                with open(self.last_sync_file, "r") as file:
                    date_str = file.read().strip()
                    return format_system_datetime(date_str)
        except Exception as e:
            print(f"[ERROR] Failed to get minimum date: {e}")
        last_edit_date = get_last_modification_time(self.config_file)
        return format_system_datetime(last_edit_date or datetime.now())


    def save_date_log(self, dt):
        """
        Saves the last valid synchronized date to the log file.
        """
        try:
            dt = format_system_datetime(dt)
            os.makedirs(os.path.dirname(self.last_sync_file), exist_ok=True)
            with open(self.last_sync_file, "w") as f:
                f.write(dt)
            print(f"[INFO] Date {dt} save in {self.last_sync_file}.")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save date in log: {e}")
        return False


def main(config_file: str):
    ad = AjustDate(config_file)
    
    if not ad.ensure_timezone():
        sys.exit(1)

    min_date = ad.get_min_date()
    set_system_date(min_date)

    if not check_internet(ad.ping_host):
        sys.exit(1)

    if sync_with_ntp(ad.ntp_servers):
        now = datetime.now()        
        print(f"[INFO] ✅ Synchronized date and time: {format_system_datetime(now)}")
        if not ad.save_date_log(now):
            sys.exit(1)
    else:
        print("[FAIL] ❌ Unable to synchronize with any NTP server.")
        sys.exit(1)


if __name__ == "__main__":    
    main(config_file="settings.yaml")
