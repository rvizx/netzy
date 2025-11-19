#!/bin/bash

echo "netzy-proxy-https setup"
echo ""

# Detect package manager
if command -v pacman &> /dev/null; then
    PKG="pacman"
elif command -v apt &> /dev/null; then
    PKG="apt"
else
    echo "ERROR: Need pacman or apt"
    exit 1
fi

# Install python3
if ! command -v python3 &> /dev/null; then
    echo "Installing python3..."
    if [ "$PKG" = "pacman" ]; then
        sudo pacman -S --noconfirm python
    else
        sudo apt update && sudo apt install -y python3
    fi
fi

# Install lsof
if ! command -v lsof &> /dev/null; then
    echo "Installing lsof..."
    if [ "$PKG" = "pacman" ]; then
        sudo pacman -S --noconfirm lsof
    else
        sudo apt install -y lsof
    fi
fi

# Install iproute2
if ! command -v ip &> /dev/null; then
    echo "Installing iproute2..."
    if [ "$PKG" = "pacman" ]; then
        sudo pacman -S --noconfirm iproute2
    else
        sudo apt install -y iproute2
    fi
fi

# Make executable
chmod +x netzy-proxy-https.py

# Create launch script
cat > launch.sh << 'EOF'
#!/bin/bash
sudo python3 "$(dirname "$0")/netzy-proxy-https.py"
EOF
chmod +x launch.sh

# Get IP
LOCAL_IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}')
[ -z "$LOCAL_IP" ] && LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -z "$LOCAL_IP" ] && LOCAL_IP="<your-ip>"

echo ""
echo "Setup complete!"
echo ""
echo "Run:    ./launch.sh"
echo "        or"
echo "        sudo python3 netzy-proxy-https.py"
echo ""
echo "Proxy:  ${LOCAL_IP}:9999"
echo ""
echo "Controls: s=toggle  f=forward  d=drop"
echo ""
