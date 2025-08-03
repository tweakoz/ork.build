#!/usr/bin/env python3

import sys
import re
import argparse
from obt.command import capture
from obt.deco import Deco

deco = Deco()

# Column width constants
COL_COMMAND = 20
COL_PID = 8
COL_USER = 12
COL_IPV = 6
COL_PORT = 8
COL_NAME = 40

def get_listening_ports(use_sudo=False):
    """Get all listening TCP ports using lsof"""
    try:
        if use_sudo:
            # User explicitly requested system-wide view
            cmd = ["sudo", "lsof", "-iTCP", "-sTCP:LISTEN", "-n", "-P"]
            try:
                output = capture(cmd)
                if output:
                    print(deco.cyan("Note: Showing system-wide ports (sudo)"))
                    print()
            except:
                print(deco.err("Error: Could not run with sudo (check password/permissions)"))
                return []
        else:
            # Default: only show current user's processes
            cmd = ["lsof", "-iTCP", "-sTCP:LISTEN", "-n", "-P"]
            try:
                output = capture(cmd)
            except:
                print(deco.err("Error: Could not run lsof"))
                return []
        
        lines = output.strip().split('\n')
        
        # Skip header line
        if lines and lines[0].startswith("COMMAND"):
            lines = lines[1:]
            
        ports_info = []
        for line in lines:
            if "LISTEN" in line:
                # Parse lsof output
                parts = line.split()
                if len(parts) >= 9:
                    command = parts[0]
                    pid = parts[1]
                    user = parts[2]
                    fd = parts[3]
                    type_ = parts[4]
                    device = parts[5]
                    node = parts[7]
                    name = parts[8]
                    
                    # Extract port from name (format: *:PORT or IP:PORT or [IPv6]:PORT)
                    # For IPv6, port comes after ]:
                    # For IPv4 and wildcards, port comes after last :
                    if ']' in name:
                        # IPv6 format like [::1]:7002
                        port_match = re.search(r'\]:(\d+)', name)
                        ipv = "IPv6"
                    else:
                        # IPv4 format like 127.0.0.1:8080 or *:8080
                        port_match = re.search(r':(\d+)$', name)
                        ipv = "IPv4"
                    port = port_match.group(1) if port_match else "unknown"
                    
                    # Check the TYPE field as well for confirmation
                    if 'IPv6' in type_:
                        ipv = "IPv6"
                    elif 'IPv4' in type_:
                        ipv = "IPv4"
                    
                    ports_info.append({
                        'command': command,
                        'pid': pid,
                        'user': user,
                        'fd': fd,
                        'type': type_,
                        'device': device,
                        'node': node,
                        'name': name,
                        'port': port,
                        'ipv': ipv
                    })
                    
        # Sort by port number
        ports_info.sort(key=lambda x: int(x['port']) if x['port'].isdigit() else 99999)
        
        # Check for services listening on both IPv4 and IPv6
        port_command_map = {}
        for info in ports_info:
            key = (info['command'], info['port'])
            if key not in port_command_map:
                port_command_map[key] = []
            port_command_map[key].append(info['ipv'])
        
        # Update entries that have both IPv4 and IPv6
        for info in ports_info:
            key = (info['command'], info['port'])
            versions = port_command_map[key]
            if 'IPv4' in versions and 'IPv6' in versions:
                info['ipv'] = 'IPv*'
        
        return ports_info
        
    except Exception as e:
        print(deco.err(f"Error running lsof: {e}"))
        return []

def truncate_with_ellipsis(text, max_width):
    """Truncate text to fit within max_width, adding ellipsis if needed"""
    if len(text) > max_width:
        return text[:max_width-3] + "..."
    return text

def print_header():
    """Print the header row"""
    header = (
        f"{deco.yellow('COMMAND'.ljust(COL_COMMAND))}"
        f"{deco.yellow('PID'.ljust(COL_PID))}"
        f"{deco.yellow('USER'.ljust(COL_USER))}"
        f"{deco.yellow('IPV'.ljust(COL_IPV))}"
        f"{deco.yellow('PORT'.ljust(COL_PORT))}"
        f"{deco.yellow('ADDRESS')}"
    )
    print(header)
    print("=" * 85)

def print_port_info(info):
    """Print a single port info row"""
    # Clean up command name (handle escaped characters)
    command = info['command'].replace('\\x20', ' ')
    command = truncate_with_ellipsis(command, COL_COMMAND)
    pid = truncate_with_ellipsis(info['pid'], COL_PID)
    user = truncate_with_ellipsis(info['user'], COL_USER)
    port = info['port'].ljust(COL_PORT)
    
    # Color code the IPV
    if info['ipv'] == 'IPv6':
        ipv_colored = deco.yellow(info['ipv'].ljust(COL_IPV))
    elif info['ipv'] == 'IPv4':
        ipv_colored = deco.cyan(info['ipv'].ljust(COL_IPV))
    else:  # IPv*
        ipv_colored = deco.magenta(info['ipv'].ljust(COL_IPV))
    
    # Color code the port number based on range
    port_num = int(info['port']) if info['port'].isdigit() else 0
    if port_num < 1024:
        port_colored = deco.red(port)  # System ports
    elif port_num < 49152:
        port_colored = deco.cyan(port)  # User ports
    else:
        port_colored = deco.magenta(port)  # Dynamic/ephemeral ports
    
    row = (
        f"{deco.key(command.ljust(COL_COMMAND))}"
        f"{deco.val(pid.ljust(COL_PID))}"
        f"{deco.orange(user.ljust(COL_USER))}"
        f"{ipv_colored}"
        f"{port_colored}"
        f"{deco.path(info['name'])}"
    )
    print(row)

def main():
    parser = argparse.ArgumentParser(
        description='List TCP listening ports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ork.net.list.open.tcp.ports.py          # Show current user's ports only
  ork.net.list.open.tcp.ports.py -s       # Show all system ports (requires sudo)
        """
    )
    parser.add_argument('-s', '--system', action='store_true',
                        help='Show system-wide ports (requires sudo)')
    
    args = parser.parse_args()
    
    print("=" * 85)
    print(deco.orange("TCP Listening Ports"))
    print("=" * 85)
    print()
    
    ports_info = get_listening_ports(use_sudo=args.system)
    
    if not ports_info:
        print(deco.warn("No listening TCP ports found (or insufficient permissions)"))
        return 1
    
    print_header()
    
    for info in ports_info:
        print_port_info(info)
    
    print()
    print("=" * 85)
    print(f"Total: {deco.val(str(len(ports_info)))} listening ports")
    print()
    print("Port ranges:")
    print(f"  {deco.red('0-1023')}: System/Well-known ports")
    print(f"  {deco.cyan('1024-49151')}: User/Registered ports")
    print(f"  {deco.magenta('49152-65535')}: Dynamic/Ephemeral ports")
    print()
    print("IP versions:")
    print(f"  {deco.cyan('IPv4')}: Internet Protocol version 4")
    print(f"  {deco.yellow('IPv6')}: Internet Protocol version 6")
    print(f"  {deco.magenta('IPv*')}: Listening on both IPv4 and IPv6")
    print("=" * 85)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())