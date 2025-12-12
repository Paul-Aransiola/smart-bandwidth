"""Test script to demonstrate network scanning capabilities."""

import asyncio
from src.services.network_scanner import NetworkScanner


async def main():
    """Test network scanner functionality."""
    scanner = NetworkScanner()

    print("=" * 80)
    print("NETWORK SCANNER TEST")
    print("=" * 80)

    # 1. Detect local network ranges
    print("\n1. Detecting local network ranges...")
    ranges = scanner.get_local_network_ranges()
    for r in ranges:
        print(f"   - {r}")

    # 2. Quick ARP scan
    print("\n2. Scanning ARP table (quick)...")
    arp_devices = scanner.scan_arp_table()
    print(f"   Found {len(arp_devices)} devices in ARP cache")
    for ip, info in list(arp_devices.items())[:5]:  # Show first 5
        print(f"   - {ip}: {info.get('mac_address')} ({info.get('hostname', 'unknown')})")

    # 3. Active connections
    print("\n3. Scanning active connections...")
    conn_devices = scanner.scan_active_connections()
    print(f"   Found {len(conn_devices)} active connections")
    for ip, info in list(conn_devices.items())[:5]:  # Show first 5
        print(f"   - {ip} (port {info.get('remote_port')})")

    # 4. Full scan (with ping - this is slow!)
    print("\n4. Performing comprehensive scan...")
    print("   This will take a while (scanning all IPs in range)...")
    all_devices = await scanner.scan_all_networks(
        use_ping=True,  # Try pinging all IPs
        include_connections=True,
    )

    print(f"\n   Total devices discovered: {len(all_devices)}")
    print("\n   Device Details:")
    print("   " + "-" * 76)

    for ip, info in all_devices.items():
        mac = info.get("mac_address", "N/A")
        hostname = info.get("hostname", "Unknown")
        method = info.get("discovery_method", "unknown")
        device_type = scanner.classify_device_type(info)

        print(f"   IP: {ip:15} | MAC: {mac:17} | Type: {device_type:10} | {hostname}")
        print(f"   {'':15}   Discovered via: {method}")
        print("   " + "-" * 76)

    print("\n✅ Network scan completed!")
    print("\nSummary:")
    print(f"   - Network ranges scanned: {len(ranges)}")
    print(f"   - Total devices found: {len(all_devices)}")
    print(f"   - Devices with MAC: {sum(1 for d in all_devices.values() if d.get('mac_address'))}")
    print(
        f"   - Devices with hostname: {sum(1 for d in all_devices.values() if d.get('hostname'))}"
    )


if __name__ == "__main__":
    asyncio.run(main())
