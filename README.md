# netzy-proxy-https

Simple HTTP/HTTPS intercepting proxy for mobile device testing.

## Setup

```bash
./setup.sh
```

## Usage

```bash
sudo python3 netzy-proxy-https.py
```

## Mobile Configuration

Configure your mobile device's WiFi proxy settings:
- **Proxy Host**: Your computer's IP address
- **Proxy Port**: `8080`

## Controls

- **s** - Toggle between auto-forward and manual mode
- **f** - Forward the next queued request
- **d** - Drop the next queued request

## Features

- ✅ HTTP and HTTPS support
- ✅ CONNECT tunnel for HTTPS
- ✅ Request interception and inspection
- ✅ Queue-based forward/drop system
- ✅ Shows full request details (method, host, path, headers)
- ✅ Works with mobile devices

## Requirements

- Python 3.x (built-in libraries only)
- Root/sudo access (for binding to port)

