#!/usr/bin/env python3
"""Siemens BACnet Field Panel XML scraper.

Fetches *FieldPanel.xml* from a target BACnet controller and dumps key
configuration details.

Usage:
    python siemens_bacnet_fp_scan.py <device_ip>
"""
from __future__ import annotations

import argparse
import socket
import struct
import sys
import xml.etree.ElementTree as ET
from typing import List, Tuple

import requests  # Third-party

# ---------------------------------------------------------------------------
# Field mappings (XML index -> label). Order matters.
# ---------------------------------------------------------------------------
XML_FIELDS: List[Tuple[int, str]] = [
    (18, "Remote Site ID"),
    (26, "Building Level Network Name"),
    (27, "Site Name"),
    (28, "Hostname"),
    (30, "IP Address"),
    (32, "Gateway IP Address"),
    (57, "Maximum Transmission Size"),
    (60, "BACnet Device Name"),
    (62, "BACnet UDP Port"),
    (63, "Device Location"),
    (64, "Device Description"),
    (88, "Device Barcode"),
    (104, "Device Revision String"),
    (105, "Device Firmware"),
    (109, "Panel Key Name"),
    (148, "SNMP Username"),
    (149, "SNMP Private Password"),
    (150, "SNMP Authorization Password"),
]

# Service flag mapping (XML index -> value that means "enabled").
SERVICE_FLAGS = {
    "Telnet": (48, 1),
    "Wireless": (84, 1),
    "Webserver": (103, 3),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hex_to_ip(hex_str: str) -> str:
    """Convert hex-encoded IP to dotted-quad."""
    return socket.inet_ntoa(struct.pack(">L", int(hex_str, 16)))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape FieldPanel.xml")
    parser.add_argument("device_ip", help="Target controller IP address")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def main() -> None:  # noqa: D401
    args = _parse_args()
    url = f"http://{args.device_ip}/FieldPanel.xml"

    try:
        resp = requests.get(url, timeout=10, verify=False)  # nosec B310
        resp.raise_for_status()
    except requests.RequestException as exc:
        sys.exit(f"[!] Failed to fetch XML: {exc}")

    root = ET.fromstring(resp.content)

    # Fixed port block (49-56) ---------------------------------------------
    ports = " ".join(root[i].text for i in range(49, 57))
    print(f"Ports: {ports}")

    # Standard fields -------------------------------------------------------
    for idx, label in XML_FIELDS:
        value = root[idx].text
        if idx in (30, 32):  # IP addresses are hex-encoded
            value = _hex_to_ip(value)
        print(f"{label}: {value}")

    # Service flags ---------------------------------------------------------
    for service, (idx, enabled_val) in SERVICE_FLAGS.items():
        status = "Enabled" if int(root[idx].text) == enabled_val else "Disabled"
        print(f"{service} {status}")


if __name__ == "__main__":
    main()
