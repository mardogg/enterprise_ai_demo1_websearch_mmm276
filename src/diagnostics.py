"""Consent-based, read-only diagnostics collection for supported OSes."""
from __future__ import annotations
import platform
import subprocess
import re
from typing import List, Dict

REDACT_IP_PATTERN = re.compile(r"(\b\d{1,3}(?:\.\d{1,3}){3}\b)")

WINDOWS_CMDS = [
    ("Network config", "ipconfig"),
    ("Ping DNS 8.8.8.8", "ping 8.8.8.8 -n 3"),
    ("Ping google.com", "ping google.com -n 3"),
    ("Disks", "wmic logicaldisk get size,freespace,caption"),
    ("Free RAM", "wmic OS get FreePhysicalMemory"),
]

MAC_CMDS = [
    ("Network config", "ifconfig"),
    ("Ping DNS 8.8.8.8", "ping -c 3 8.8.8.8"),
    ("Ping google.com", "ping -c 3 google.com"),
    ("Disks", "df -h"),
    ("Top snapshot", "top -l 1"),
]

LINUX_CMDS = [
    ("Network config", "ip a"),
    ("Ping DNS 8.8.8.8", "ping -c 3 8.8.8.8"),
    ("Ping google.com", "ping -c 3 google.com"),
    ("Disks", "df -h"),
    ("Top snapshot", "top -b -n 1"),
]


def run_command(cmd: str) -> str:
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        out = proc.stdout.strip() or proc.stderr.strip()
        return out
    except Exception as e:  # pragma: no cover
        return f"<error running {cmd}: {e}>"


def collect(redact_ips: bool = True) -> Dict[str, str]:
    system = platform.system().lower()
    if system.startswith("win"):
        commands = WINDOWS_CMDS
    elif system.startswith("darwin"):
        commands = MAC_CMDS
    elif system.startswith("linux"):
        commands = LINUX_CMDS
    else:
        return {"unsupported": "Unsupported OS for automatic diagnostics"}

    results: Dict[str, str] = {}
    for label, cmd in commands:
        output = run_command(cmd)
        if redact_ips:
            output = REDACT_IP_PATTERN.sub("<IP>", output)
        results[label] = output
    return results


def summarize(results: Dict[str, str]) -> Dict[str, List[str]]:
    summary = {"Network": [], "Storage": [], "Performance": [], "Connectivity": []}
    # Simple heuristic parsing
    net_cfg = results.get("Network config", "")
    if "<IP>" in net_cfg:
        summary["Network"].append("IP addresses detected (redacted)")
    if "Disks" in results:
        disks = results.get("Disks", "")
        if "FreePhysicalMemory" in disks or "Bytes" in disks:
            summary["Storage"].append("Disk stats collected")
    if "Top snapshot" in results:
        summary["Performance"].append("Top snapshot available")
    if any(k.startswith("Ping") for k in results.keys()):
        summary["Connectivity"].append("Ping tests executed")
    return summary
