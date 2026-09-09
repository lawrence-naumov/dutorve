#!/bin/bash
set -e

PROJECT_PATH="$HOME/.system-setup/"
INVENTORY_FILE="inventory.yml"
VAULT_PASS_FILE=".vault_pass"
GAME_MODE="false"

cd "$PROJECT_PATH"
command_list=("update" "install" "recreate-inventory", "help")
command_found=0
for item in "${command_list[@]}"; do
  if [[ "$item" == "$1" ]]; then
    command_found=1
    break
  fi
done

print_default_help() {
  echo "Usage: system-setup COMMAND"
  echo "Commands:"
  echo "  update                update installation"
  echo "  install               run configuring system"
  echo "  recreate-inventory    recreate inventory file"
}

print_help_for_command() {
  command = $1
  case "$command" in
  "update")
    echo "Pull new version from github and hard reset to it."
    echo "Usage: system-setup update"
    ;;
  "install")
    echo "Run installation and software configuration"
    echo "Usage: system-setup install [--game-mode]"
    echo -e "\nParams:"
    echo "  --game-mode: Configure network drivers for less ping value"
    ;;
  "recreate-inventory")
    echo "Recreate ansible inventory file"
    echo "Use when you chanched password or forgot the inventory file password"
    echo "Usage: recreate-inventory"
    ;;
  *)
    echo "Unknown command. Use 'system-setup help' for command list"
    ;;
  esac
}

if ((!command_found)) || [[ "$1" == "help" ]] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
  print_default_help
  exit 0
fi

if [[ "$1" == "update" ]]; then
  git pull
  git reset --hard main
fi

if [[ "$1" == "install" ]] && [ ! -f "$INVENTORY_FILE" ] || [[ "$1" == "recreate-inventory" ]]; then
  echo "Creating a new secured inventory file..."

  read -sp "Enter the password for your local machine: " SERVER_PASS
  echo ""
  GAME_MODE="false"
  read -sp "Enter a NEW password to secure your Ansible Vault: " VAULT_PASS
  echo ""

  echo -n "$VAULT_PASS" >"$VAULT_PASS_FILE"
  chmod 600 "$VAULT_PASS_FILE"

  echo -n "Encrypting your local machine password..."
  ENCRYPTED_PASS=$(echo -n "$SERVER_PASS" | ansible-vault encrypt_string --vault-password-file="$VAULT_PASS_FILE" --stdin-name 'ansible_sudo_pass')
  echo " Done."

  cat <<EOF >"$INVENTORY_FILE"
all:
  hosts:
    localhost:
      ansible_connection: local
      ansible_python_interpreter: /usr/bin/python3
      $ENCRYPTED_PASS
EOF

  rm -f "$VAULT_PASS_FILE"

  echo "Success! Secured '$INVENTORY_FILE' has been created."
fi

if [[ "$1" == "install" ]]; then
  ansible-playbook -i "$INVENTORY_FILE" setup-playbook.yml --ask-vault-pass
fi
