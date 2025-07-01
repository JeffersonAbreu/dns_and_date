#!/usr/bin/env python3
import os
import sys
from typing import List

import yaml
# Force Python not to create .pyc files
sys.dont_write_bytecode = True

try:
    from .tools import NetworkManager, ModelService, MyService, create_service_date, create_timer_date
except Exception:
    from tools import NetworkManager, ModelService, MyService, create_service_date, create_timer_date

def load_config(name_file):
    local_dir = os.path.dirname(os.path.abspath(__file__))
    file_path=os.path.join(local_dir, name_file)
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return yaml.safe_load(f)
        except:
            print(f"[WARN] Failed to read {file_path}")
    return {}

def menu(menu_options: List[str]):
    print("\n\n==========   Menu   ==========")
    for i, option in enumerate(menu_options):
        print(f" {i} - {option}")
    opcao = None
    try:
        while opcao not in range(len(menu_options)):
            opcao = int(input("Enter the option: "))
    except Exception:
        opcao = 0
    return opcao


def main(args):
    """
    Configura todos os serviços definidos na lista.
    """
    settings = args[0] or {}
    manager = NetworkManager(
        dns_servers=settings.get("dns_servers"),
        ping_host=settings.get("ping_host"),
        resolv_conf=settings.get("resolv_conf")
    )

    my_model = MyService(args[1], args[2])

    DATE_SYNC='date-sync'
    serv_date = my_model.create_service(DATE_SYNC, create_service_date)
    timer_date = my_model.create_timer(DATE_SYNC, create_timer_date, serv_date.name)

    services: List[ModelService]  = [
        serv_date,
    ]

    timers: List[ModelService]  = [
        timer_date,
    ]
    
    services_uinstall = timers + services
    services_install = services + timers
    
    MENU_TEXT = [
        "Exit",
        "Install all",
        "Uninstall all",
        "Configure DNS",
        "Check Connecton",
        "Check apt Lock proccess",
    ]

    while True:
        opcao = menu(MENU_TEXT)
        print()
        if opcao == 0:
          print("Log out of the system...")
          break  
      
        elif opcao == 1:
            print()
            print("### Install and Config ###\n")
            services_success = []
            for service in services_uinstall:
                service.uninstall()
                
            for service in services_install:
                if service.create():
                    services_success.append(service.name)
                                    
            if services_success != []:
                for service in services_install:
                    if service.name in services_success:
                        service.install()
            print()
            
        elif opcao == 2:
            print()
            print("### Uninstalling ###\n")
            for service in services_uinstall:
                if service.uninstall():
                    print(f"Uninstall: {service.name}")
            print()
            
        elif opcao == 3:
            config_result = manager.configure_dns()
            if config_result is None:
                print("[INFO] Configuration already applied.")
            else:
                print(f"[RESULT] Configuration completed: {'Yes' if config_result else 'No'}")
        elif opcao == 4:
           manager.check_connection()
        
        elif opcao == 3:
            manager.check_proccess_lock()

if __name__ == "__main__":
    PREFIX_NAME_SERVICE = "system"
    DESTINATION_PATH = "/etc/systemd/system/"
    
    config="settings.yaml"
    
    main([
        load_config(config),
        PREFIX_NAME_SERVICE,
        DESTINATION_PATH
    ])