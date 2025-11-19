#!/bin/bash

echo -e "\n\033[1;97mnetzy-proxy-https setup\033[0m\n"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "\033[38;5;203m✗\033[0m Don't run setup as root"
    exit 1
fi

# Detect Python
if ! command -v python3 &> /dev/null; then
    echo -e "\033[38;5;203m✗\033[0m python3 not found"
    exit 1
fi

echo -e "\033[38;5;150m✓\033[0m python3 found: $(python3 --version)"

# Make executable
chmod +x netzy-proxy-https.py

echo -e "\033[38;5;150m✓\033[0m made netzy-proxy-https.py executable"

# Get local IP
LOCAL_IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}')
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="<your-ip>"
fi

echo -e "\n\033[38;5;150m✓\033[0m Setup complete!\n"
echo -e "\033[1mUsage:\033[0m"
echo -e "  \033[38;5;222m1.\033[0m Run the proxy:"
echo -e "     \033[2m$\033[0m sudo python3 netzy-proxy-https.py"
echo -e ""
echo -e "  \033[38;5;222m2.\033[0m Configure your mobile device:"
echo -e "     Proxy: \033[1m${LOCAL_IP}:8080\033[0m"
echo -e ""
echo -e "  \033[38;5;222m3.\033[0m Controls:"
echo -e "     \033[38;5;111ms\033[0m = toggle manual/auto mode"
echo -e "     \033[38;5;111mf\033[0m = forward queued request"
echo -e "     \033[38;5;111md\033[0m = drop queued request"
echo -e ""

