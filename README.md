# DNS & System Service Manager

> Ferramenta em Python para gerenciar configurações de rede, serviços systemd e conexão à internet.

Este projeto foi desenvolvido para facilitar a **configuração de DNS**, **monitoramento da conexão com a internet**, além de **gerenciar serviços systemd** no Linux. É útil tanto para automação quanto para uso manual via terminal.

---

## 🧩 Funcionalidades

- ✅ Configuração automática de servidores DNS no `/etc/resolv.conf`
- 🔒 Bloqueia o arquivo contra alterações indesejadas (`chattr +i`)
- 🌐 Verifica conectividade com 80% de sucesso mínimo (ping em tempo real)
- ⚙️ Cria, instala e remove serviços systemd automaticamente
- 🕒 Suporte a timers systemd para execução periódica
- 🗑️ Remove processos travados do `apt` e arquivos de lock
- 📋 Menu interativo para fácil uso

---

## 📁 Estrutura do Projeto

```
dns_and_date/
├── main.py                  # Script principal com interface de menu
├── tools.py                 # Funções utilitárias e classes reutilizáveis
├── settings.yaml            # Arquivo de configuração (opcional)
└── README.md                # Este arquivo
```

---

## 🛠️ Requisitos

- **Sistema operacional**: Linux (Ubuntu/Debian recomendado)
- **Python**: 3.6+
- **Permissões**: Precisa ser executado com privilégios elevados (`sudo`)

### Instale as dependências (se necessário):

```bash
pip install pyyaml
```

---

## ⚙️ Como Usar

### 1. Clone ou copie o projeto:

```bash
git clone https://gitlab.com/seu-projeto/dns_and_date.git
cd dns_and_date
```

### 2. (Opcional) Configure os servidores DNS e outros parâmetros no `settings.yaml`:

```yaml
dns_servers:
  - 8.8.8.8
  - 8.8.4.4
  - 1.1.1.1
ping_host: www.google.com
resolv_conf: /etc/resolv.conf
```

### 3. Execute o script com permissões elevadas:

```bash
sudo python3 main.py
```

---

## 🎮 Menu Interativo

Após executar, você verá um menu com as seguintes opções:

| Opção | Ação |
|-------|------|
| `0`   | Sair do programa |
| `1`   | Instalar todos os serviços e configurar DNS |
| `2`   | Desinstalar todos os serviços |
| `3`   | Configurar DNS manualmente |
| `4`   | Verificar conexão com a internet |
| `5`   | Limpar processos travados do apt |

---

## 🔄 Serviço e Timer Systemd

O projeto cria automaticamente:

- Um serviço systemd: `system-date-sync.service`
- Um timer systemd: `system-date-sync.timer`  
  → Executa o serviço a cada 5 minutos

Você pode verificar com:

```bash
systemctl list-units --type=service | grep system
systemctl list-units --type=timer | grep system
```

---

## 💡 Dicas

- Sempre execute com `sudo`, pois ele manipula arquivos do sistema.
- Use o modo "Uninstall" antes de reinstalar para evitar conflitos.
- Para depuração, use `journalctl -u system-date-sync` para ver logs do serviço.

---

## 📝 Licença

MIT License – veja o arquivo [LICENSE](LICENSE) para mais detalhes.
```