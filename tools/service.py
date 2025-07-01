#!/usr/bin/env python3
import os
import subprocess
import sys

# Force Python not to create .pyc files
sys.dont_write_bytecode = True

class ModelService():
    def __init__(self, prefix: str, name: str, function, depende=None, auto_init=True, destination_path="~/", sufix="service"):
        self.name = f"{prefix}-{name}.{sufix}"
        self.__create = function
        self.depende = depende
        self.auto_init = auto_init
        self.destination_path = os.path.join(destination_path, self.name)
        self.is_timer = True if sufix == "timer" else False


    def create(self):
        def _save(_content):
            """
            Salva o arquivo de serviço.
            """
            try:
                file_path_service = os.path.join(self.file_path, self.name)
                with open(file_path_service, 'w') as file:
                    file.write(_content)
                print(f"[INFO] Serviço salvo: {file_path_service}")
                return True
            except Exception as e:
                print(f"[ERROR] Falha ao salvar o {self.name}: {e}")
                return False
        
        if self.depende:
            _content, self.file_path = self.__create(self.depende)
        else:
            _content, self.file_path = self.__create()
            
        if _save(_content):
            return True
        return False


    def install(self):
        """
        Ativa e inicia o serviço systemd.
        """
        print(f"\n[INSTALL] {self.name}")
        self.systemctl_stop()
        
        def copy_to_destiny():
            """
            Cria ou substitui o serviço no diretório systemd.
            """
            file_path_service = os.path.join(self.file_path, self.name)
            if not os.path.exists(file_path_service):
                print(f"[ERROR] Arquivo não encontrado em: {file_path_service}")
                return False
            try:
                subprocess.run(["sudo", "cp", file_path_service, self.destination_path], check=True)
                print(f"[INFO] Serviço copiado para {self.destination_path}")
                return True
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Falha ao copiar {self.name}: {e}")
                return False
            
        if copy_to_destiny():
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True) 
            if self.auto_init:
                self.systemctl_enable()
                self.systemctl_start()
            return True
        else:
            return False


    def uninstall(self, _reload=True):
        """
        Ativa e inicia o serviço systemd.
        """
        print(f"\n[UNINSTALL] {self.name}")
        if os.path.exists(self.destination_path):
            try:
                if self.systemctl_stop() and self.systemctl_disable():
                    subprocess.run(["sudo", "rm", self.destination_path], check=True)
                    print(f"[INFO] {self.name} desistalado")
                    if _reload:
                        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
                    return True
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Falha ao copiar {self.name}: {e}")
                return False
        return False
                
                
    
    def __systemctl(self, action):
        if os.path.exists(self.destination_path):
            try:
                subprocess.run(["sudo", "systemctl", action, self.name], check=True)
                return True
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Falha ao executar  'systemctl {action} {self.name}': {e}")
        return False
        

 
    def systemctl_enable(self):
        return self.__systemctl("enable")


    def systemctl_disable(self):
        return self.__systemctl("disable")


    def systemctl_start(self):
        return self.__systemctl("start")


    def systemctl_stop(self):
        return self.__systemctl("stop")
    

class MyService:
    def __init__(self, prefix: str, destination_path: str):
        self.prefix = prefix
        self.destination_path = destination_path
    
    def create_service(self, name: str, function, depende=None, auto_init=False):
        return ModelService(self.prefix, name, function, depende, auto_init, self.destination_path, "service")
    
    def create_timer(self, name: str, function, depende=None, auto_init=True):
        return ModelService(self.prefix, name, function, depende, auto_init, self.destination_path, "timer")