# netzy

Simple HTTP/HTTPS intercepting proxy.

### Setup

```bash
./setup.sh
```

### Usage

```bash
sudo python3 netzy-proxy-https.py
```

### Configuration

Configure proxy settings on any device/browser:
- **Proxy Host**: Your computer's IP address (run `./setup.sh` to see it)
- **Proxy Port**: `9999`

Works with: phones, browsers (Firefox/Chrome), curl, wget, any HTTP client

### Controls

- **s** - Toggle between auto-forward and manual mode
- **f** - Forward the next queued request
- **d** - Drop the next queued request

### Features

-  HTTP and HTTPS support
-  CONNECT tunnel for HTTPS
-  Request interception and inspection
-  Queue-based forward/drop system
-  Shows full request details (method, host, path, headers)
-  Works with any device that supports HTTP proxy

### Requirements

- Python 3.x (built-in libraries only - **NO pip installs needed**)
- Root/sudo access (for binding to port)

#### What setup.sh installs:
- `python3` - the Python interpreter itself
- `lsof` - system tool (for killing port processes)
- `iproute2` - system tool (for getting your IP)
