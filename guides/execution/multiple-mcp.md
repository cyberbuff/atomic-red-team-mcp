# Running Multiple MCP Servers for Cross-Platform Atomic Test Execution

This guide explains how to run multiple Atomic Red Team MCP servers across Windows, Linux, and macOS machines using HTTP servers, allowing you to execute atomic tests on all platforms from a single client interface.

## Overview

By running MCP servers on multiple machines, you can:
- Execute platform-specific atomic tests remotely
- Test security controls across different operating systems
- Simulate multi-platform attack scenarios
- Centrally manage atomic test execution across your infrastructure

## Architecture

```
        ┌─────────────────────────┐
        │  Client (Cursor,        │
        │  Claude Desktop, etc.)  │
        └───────────┬─────────────┘
                    │
    ┌───────────────┴─────────────┐
    │               │             │
    ▼               ▼             ▼
┌────────┐      ┌────────┐   ┌────────┐
│Windows │      │ Linux  │   │ macOS  │
│  MCP   │      │  MCP   │   │  MCP   │
│ Server │      │ Server │   │ Server │
│ (HTTP) │      │ (HTTP) │   │ (HTTP) │
└────────┘      └────────┘   └────────┘
```

---

## Part 1: Setting Up MCP Servers on Each Platform

### Prerequisites

For each target machine, you'll need:
- Python 3.10+ or `uv` installed
- Network connectivity (default port 8000, or custom port)
- Appropriate security permissions for executing atomic tests
- Firewall rules allowing inbound connections on your chosen port

---

## Installing uv on Each Platform

`uv` is a fast Python package installer and runner. Install it on each machine:

### Windows (PowerShell)
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Linux/macOS
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, verify:
```bash
uv --version
uv python install 3.12
uv python pin 3.12
```

---

## Part 2: Running MCP HTTP Servers

### Windows Server Setup (PowerShell)

**Option A: Basic Setup (No Authentication)**

```powershell
# Set environment variables
$env:ART_MCP_TRANSPORT = "streamable-http"
$env:ART_EXECUTION_ENABLED = "true"
$env:ART_MCP_PORT = "8000"
$env:ART_MCP_HOST = "0.0.0.0"

# Run the MCP server
uvx atomic-red-team-mcp
```

**Option B: Secure Setup (With Authentication - Recommended)**

```powershell
# Generate a secure authentication token
$TOKEN = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Host "Your authentication token: $TOKEN" -ForegroundColor Green
Write-Host "Save this token for client configuration!" -ForegroundColor Yellow

# Set environment variables with authentication
$env:ART_MCP_TRANSPORT = "streamable-http"
$env:ART_EXECUTION_ENABLED = "true"
$env:ART_MCP_PORT = "8000"
$env:ART_MCP_HOST = "0.0.0.0"
$env:ART_AUTH_TOKEN = $TOKEN

# Run the MCP server
uvx atomic-red-team-mcp
```

**Option C: Run as Background Process**

```powershell
# Create a PowerShell script to run the server
$scriptContent = @"
`$env:ART_MCP_TRANSPORT = 'streamable-http'
`$env:ART_EXECUTION_ENABLED = 'true'
`$env:ART_MCP_PORT = '8000'
`$env:ART_MCP_HOST = '0.0.0.0'
`$env:ART_AUTH_TOKEN = 'YOUR_TOKEN_HERE'
uvx atomic-red-team-mcp
"@

# Save script
$scriptContent | Out-File -FilePath "$env:USERPROFILE\start-mcp-server.ps1"

# Run in background (option 1 - new window)
Start-Process powershell -ArgumentList "-NoExit", "-File", "$env:USERPROFILE\start-mcp-server.ps1"

# Or run as a scheduled task (option 2 - persistent)
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File $env:USERPROFILE\start-mcp-server.ps1"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "AtomicMCPServer" -Description "Atomic Red Team MCP Server"
```

**Verify Windows Server is Running:**
```powershell
# Check if port is listening
netstat -an | findstr :8000

# Test connection
Invoke-WebRequest -Uri http://localhost:8000/health
```

---

### Linux Server Setup (Terminal)

**Option A: Basic Setup (No Authentication)**

```bash
# Set environment variables
export ART_MCP_TRANSPORT="streamable-http"
export ART_EXECUTION_ENABLED="true"
export ART_MCP_PORT="8000"
export ART_MCP_HOST="0.0.0.0"

# Run the MCP server
uvx atomic-red-team-mcp
```

**Option B: Secure Setup (With Authentication - Recommended)**

```bash
# Generate a secure authentication token
TOKEN=$(openssl rand -hex 32)
echo "Your authentication token: $TOKEN"
echo "Save this token for client configuration!"

# Set environment variables with authentication
export ART_MCP_TRANSPORT="streamable-http"
export ART_EXECUTION_ENABLED="true"
export ART_MCP_PORT="8000"
export ART_MCP_HOST="0.0.0.0"
export ART_AUTH_TOKEN="$TOKEN"

# Run the MCP server
uvx atomic-red-team-mcp
```

**Option C: Run as Background Service (systemd)**

```bash
# Create a systemd service file
sudo tee /etc/systemd/system/atomic-mcp.service > /dev/null <<EOF
[Unit]
Description=Atomic Red Team MCP Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME
Environment="ART_MCP_TRANSPORT=streamable-http"
Environment="ART_EXECUTION_ENABLED=true"
Environment="ART_MCP_PORT=8000"
Environment="ART_MCP_HOST=0.0.0.0"
Environment="ART_AUTH_TOKEN=YOUR_TOKEN_HERE"
ExecStart=$(which uvx) atomic-red-team-mcp
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable atomic-mcp.service
sudo systemctl start atomic-mcp.service

# Check status
sudo systemctl status atomic-mcp.service

# View logs
sudo journalctl -u atomic-mcp.service -f
```

**Verify Linux Server is Running:**
```bash
# Check if port is listening
ss -tulpn | grep :8000
# Or
netstat -tulpn | grep :8000

# Test connection
curl http://localhost:8000/health
```

---

### macOS Server Setup (Terminal)

**Option A: Basic Setup (No Authentication)**

```bash
# Set environment variables
export ART_MCP_TRANSPORT="streamable-http"
export ART_EXECUTION_ENABLED="true"
export ART_MCP_PORT="8000"
export ART_MCP_HOST="0.0.0.0"

# Run the MCP server
uvx atomic-red-team-mcp
```

**Option B: Secure Setup (With Authentication - Recommended)**

```bash
# Generate a secure authentication token
TOKEN=$(openssl rand -hex 32)
echo "Your authentication token: $TOKEN"
echo "Save this token for client configuration!"

# Set environment variables with authentication
export ART_MCP_TRANSPORT="streamable-http"
export ART_EXECUTION_ENABLED="true"
export ART_MCP_PORT="8000"
export ART_MCP_HOST="0.0.0.0"
export ART_AUTH_TOKEN="$TOKEN"

# Run the MCP server
uvx atomic-red-team-mcp
```

**Option C: Run as LaunchDaemon (Background Service)**

```bash
# Create a launch daemon plist
cat > ~/Library/LaunchAgents/com.atomic-red-team.mcp.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.atomic-red-team.mcp</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which uvx)</string>
        <string>atomic-red-team-mcp</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>ART_MCP_TRANSPORT</key>
        <string>streamable-http</string>
        <key>ART_EXECUTION_ENABLED</key>
        <string>true</string>
        <key>ART_MCP_PORT</key>
        <string>8000</string>
        <key>ART_MCP_HOST</key>
        <string>0.0.0.0</string>
        <key>ART_AUTH_TOKEN</key>
        <string>YOUR_TOKEN_HERE</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/atomic-mcp.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/atomic-mcp-error.log</string>
</dict>
</plist>
EOF

# Load the launch daemon
launchctl load ~/Library/LaunchAgents/com.atomic-red-team.mcp.plist

# Check status
launchctl list | grep atomic-red-team

# View logs
tail -f /tmp/atomic-mcp.log

# Unload if needed
# launchctl unload ~/Library/LaunchAgents/com.atomic-red-team.mcp.plist
```


**Verify macOS Server is Running:**
```bash
# Check if port is listening
lsof -i :8000
# Or
netstat -an | grep 8000

# Test connection
curl http://localhost:8000/health
```

---

## Part 3: Finding Server IP Addresses

Before configuring your client, get the IP addresses of each server.

Example:
- Windows server: `192.168.1.10`
- Linux server: `192.168.1.11`
- macOS server: `192.168.1.12`

---

## Part 4: Configuring Firewall Rules

Allow inbound connections on port 8000 (or your custom port).

### Windows Firewall (PowerShell - Run as Administrator)

```powershell
# Allow from any IP (use with caution)
New-NetFirewallRule -DisplayName "Atomic MCP Server" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

# Or allow from specific IP/subnet only (recommended)
New-NetFirewallRule -DisplayName "Atomic MCP Server" -Direction Inbound -LocalPort 8000 -Protocol TCP -RemoteAddress 192.168.1.0/24 -Action Allow

# Check the rule
Get-NetFirewallRule -DisplayName "Atomic MCP Server"
```

### Linux Firewall (ufw)

```bash
# Allow from any IP
sudo ufw allow 8000/tcp

# Or allow from specific IP/subnet only (recommended)
sudo ufw allow from 192.168.1.0/24 to any port 8000

# Enable firewall if not enabled
sudo ufw enable

# Check status
sudo ufw status
```

### Linux Firewall (firewalld - RHEL/CentOS/Fedora)

```bash
# Allow from any IP
sudo firewall-cmd --permanent --add-port=8000/tcp

# Or allow from specific IP only
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port port="8000" protocol="tcp" accept'

# Reload firewall
sudo firewall-cmd --reload

# Check rules
sudo firewall-cmd --list-all
```

### macOS Firewall

```bash
# macOS built-in firewall works at application level
# If you need port-level control, use pf (packet filter)

# Allow specific IP to port 8000
sudo pfctl -e  # Enable pf
echo "pass in proto tcp from 192.168.1.0/24 to any port 8000" | sudo tee -a /etc/pf.conf
sudo pfctl -f /etc/pf.conf  # Reload rules
```

---

## Part 5: Client Configuration

Configure your MCP client to connect to all three servers.

### Example Server Details

Save your authentication tokens:
- **Windows Server:** `192.168.1.10:8000`
- **Linux Server:** `192.168.1.11:8000`
- **macOS Server:** `192.168.1.12:8000`

### Cursor Configuration

Edit `~/.cursor/mcp.json` (macOS/Linux) or `%USERPROFILE%\.cursor\mcp.json` (Windows):

**With Authentication (Recommended):**
```json
{
  "mcpServers": {
    "atomic-windows": {
      "url": "http://192.168.1.10:8000/mcp",
      "headers": {
        "Authorization": "Bearer abc123...789xyz"
      }
    },
    "atomic-linux": {
      "url": "http://192.168.1.11:8000/mcp",
      "headers": {
        "Authorization": "Bearer abc123...789xyz"
      }
    },
    "atomic-macos": {
      "url": "http://192.168.1.12:8000/mcp",
      "headers": {
        "Authorization": "Bearer abc123...789xyz"
      }
    }
  }
}
```

**Without Authentication:**
```json
{
  "mcpServers": {
    "atomic-windows": {
      "url": "http://192.168.1.10:8000/mcp"
    },
    "atomic-linux": {
      "url": "http://192.168.1.11:8000/mcp"
    },
    "atomic-macos": {
      "url": "http://192.168.1.12:8000/mcp"
    }
  }
}
```

**Restart Cursor** to apply the configuration.

---

### Claude Desktop Configuration

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "atomic-windows": {
      "url": "http://192.168.1.10:8000/mcp",
      "headers": {
        "Authorization": "Bearer abc123...windows"
      }
    },
    "atomic-linux": {
      "url": "http://192.168.1.11:8000/mcp",
      "headers": {
        "Authorization": "Bearer def456...linux"
      }
    },
    "atomic-macos": {
      "url": "http://192.168.1.12:8000/mcp",
      "headers": {
        "Authorization": "Bearer ghi789...macos"
      }
    }
  }
}
```

**Restart Claude Desktop** to apply the configuration.

---

### Windsurf Configuration

Similar to Cursor, edit your Windsurf MCP settings file with the same JSON structure.

---

## Part 6: Executing Atomic Tests Across All Platforms

Now you can interact with all three servers from your client!

### Step 1: Verify Server Connections

In your AI assistant interface, ask:
```
Check the server information for all three Atomic Red Team MCP servers
```

The assistant will use `server_info` on each server:
- `atomic-windows:server_info()`
- `atomic-linux:server_info()`
- `atomic-macos:server_info()`

**Expected Response:**
```
Windows Server:
- OS: Windows
- Version: 1.2.0
- Transport: streamable-http

Linux Server:
- OS: Linux
- Version: 1.2.0
- Transport: streamable-http

macOS Server:
- OS: Darwin
- Version: 1.2.0
- Transport: streamable-http
```

---

### Step 2: Search for Platform-Specific Atomics

**Example 1: Find Windows Registry Persistence Tests**
```
Search for registry persistence atomics on the `atomic-windows` MCP server
```

The assistant will execute:
```
atomic-windows:query_atomics(query="registry persistence", supported_platforms="windows")
```

**Example 2: Find Linux Cron Job Persistence Tests**
```
Search for cron persistence atomics on the `atomic-linux` server
```

**Example 3: Find macOS LaunchAgent Tests**
```
Search for LaunchAgent atomics on the `atomic-macos` server
```

---

### Step 3: Execute Atomic Tests on Specific Platforms

**Example: Execute T1547.001 (Registry Run Key) on Windows**

```
Execute the atomic test for Registry Run Keys on the `atomic-windows` server
```

**Workflow:**
1. Assistant queries for T1547.001 on Windows server
2. You select the specific atomic test
3. Assistant prompts for input arguments (if any)
4. Test executes on Windows server
5. Results are returned

**Example: Cross-Platform Command Execution Test**

```
Run the atomic test c141bbdb-7fca-4254-9fd6-f47e79447e17 using `atomic-linux` and `atomic-macos` MCP servers and provide a consolidated output
```

The assistant will:
1. Query `atomic-linux` for c141bbdb-7fca-4254-9fd6-f47e79447e17 tests
2. Query `atomic-macos` for c141bbdb-7fca-4254-9fd6-f47e79447e17 tests
3. Execute selected tests on each platform
4. Provide consolidated results

---


## Part 7: Troubleshooting

### Server Not Responding

**Check if server is running:**
```bash
# Windows
netstat -an | findstr :8000

# Linux/macOS
netstat -an | grep 8000
# Or
ss -tulpn | grep 8000
```

**Check firewall:**
```bash
# Windows
Get-NetFirewallRule -DisplayName "Atomic MCP Server"

# Linux (ufw)
sudo ufw status

# Linux (firewalld)
sudo firewall-cmd --list-all
```

**Test local connection:**
```bash
curl http://localhost:8000/health
```

### Network Connectivity Issues

**Test from client machine:**
```bash
# Test connectivity
ping 192.168.1.10
telnet 192.168.1.10 8000

# Or using nc
nc -zv 192.168.1.10 8000

# Or using curl
curl -v http://192.168.1.10:8000/health
```

### Server Logs

**View logs to diagnose issues:**

**Linux (systemd):**
```bash
sudo journalctl -u atomic-mcp.service -f
```

**macOS (LaunchDaemon):**
```bash
tail -f /tmp/atomic-mcp.log
tail -f /tmp/atomic-mcp-error.log
```

---

## Part 8: Security Best Practices

### 1. Always Use Authentication
- Generate strong, random tokens (32+ characters)
- Use different tokens for each server
- Store tokens securely (password manager, secrets vault)

### 2. Network Isolation
- Use VPN or private network for server communication
- Restrict firewall rules to specific IP ranges
- Consider using SSH tunnels for additional security

### 3. SSH Tunneling (Recommended for Remote Access)

Set `ART_MCP_HOST=127.0.0.1` on all the machines(windows, linux, and macOS) and enable SSH tunneling to access the MCP servers.

**Setup SSH tunnels from client to each server:**

```bash
# Forward Windows server port 8000 to local 8001
ssh -L 8001:localhost:8000 user@192.168.1.10

# Forward Linux server port 8000 to local 8002
ssh -L 8002:localhost:8000 user@192.168.1.11

# Forward macOS server port 8000 to local 8003
ssh -L 8003:localhost:8000 user@192.168.1.12
```

**Then configure client to use localhost:**
```json
{
  "mcpServers": {
    "atomic-windows": {
      "url": "http://localhost:8001/mcp",
      "headers": {
        "Authorization": "Bearer abc123...windows"
      }
    },
    "atomic-linux": {
      "url": "http://localhost:8002/mcp",
      "headers": {
        "Authorization": "Bearer def456...linux"
      }
    },
    "atomic-macos": {
      "url": "http://localhost:8003/mcp",
      "headers": {
        "Authorization": "Bearer ghi789...macos"
      }
    }
  }
}
```

### 4. Run in Isolated Environments
- Use VMs or sandboxes for test execution
- Don't run on production systems
- Create snapshots before testing

### 5. Monitor and Audit
- Review server logs regularly
- Monitor for unauthorized access attempts
- Track which tests are executed

---

## Part 9: Stopping/Restarting Servers

### Windows
```powershell
# If running in foreground, press Ctrl+C

# If running as scheduled task
Stop-ScheduledTask -TaskName "AtomicMCPServer"
Start-ScheduledTask -TaskName "AtomicMCPServer"

# Or unregister the task
Unregister-ScheduledTask -TaskName "AtomicMCPServer" -Confirm:$false
```

### Linux
```bash
# If running as systemd service
sudo systemctl stop atomic-mcp.service
sudo systemctl start atomic-mcp.service
sudo systemctl restart atomic-mcp.service

# Or kill by port
sudo lsof -ti:8000 | xargs kill -9
```

### macOS
```bash
# If running as LaunchDaemon
launchctl unload ~/Library/LaunchAgents/com.atomic-red-team.mcp.plist
launchctl load ~/Library/LaunchAgents/com.atomic-red-team.mcp.plist

# Or kill by port
sudo lsof -ti:8000 | xargs kill -9
```

---

## Summary

You now have:
1. ✅ MCP servers running on Windows, Linux, and macOS
2. ✅ HTTP-based communication between client and servers
3. ✅ Authentication configured for security
4. ✅ Ability to execute atomic tests across all platforms
5. ✅ Centralized management from your AI assistant
