"""
data_gen.py - Forensic Log Data Generator
==========================================
Generates a synthetic forensic_logs.csv with 50 rows of realistic
DFIR (Digital Forensics & Incident Response) log data.

Each row simulates a security event with:
- timestamp: When the event occurred
- source_ip: The originating IP address
- event_type: Category of security event
- status: Whether the event succeeded or failed
- description: Human-readable forensic detail
"""

import pandas as pd
import random
from datetime import datetime, timedelta

# --- Seed for reproducibility ---
random.seed(42)

# --- Configuration ---
NUM_ROWS = 50
START_TIME = datetime(2024, 6, 1, 8, 0, 0)

# Simulated attacker and internal IP pools
ATTACKER_IPS = ["192.168.1.105", "10.0.0.47", "203.0.113.22", "198.51.100.9"]
INTERNAL_IPS = ["192.168.1.10", "192.168.1.20", "10.0.0.5", "172.16.0.3"]
ALL_IPS = ATTACKER_IPS + INTERNAL_IPS

# DFIR-relevant event types
EVENT_TYPES = [
    "Login",
    "Failed Login",
    "File Access",
    "Port Scan",
    "Privilege Escalation",
    "Lateral Movement",
    "Data Exfiltration",
    "Malware Execution",
    "Brute Force",
    "USB Insertion",
]

# Status mapping: some event types lean toward failure
STATUS_WEIGHTS = {
    "Login": ["Success", "Fail"],
    "Failed Login": ["Fail"],          # Always fail
    "File Access": ["Success", "Fail"],
    "Port Scan": ["Success"],          # Scan itself succeeds as detection
    "Privilege Escalation": ["Success", "Fail"],
    "Lateral Movement": ["Success"],
    "Data Exfiltration": ["Success"],
    "Malware Execution": ["Success"],
    "Brute Force": ["Fail", "Fail", "Fail", "Success"],  # Mostly fail, rarely success
    "USB Insertion": ["Success"],
}

# Descriptions per event type
DESCRIPTIONS = {
    "Login": [
        "User authenticated via SSH on port 22.",
        "RDP login from internal workstation.",
        "Web portal login via HTTPS.",
    ],
    "Failed Login": [
        "Authentication failed: invalid credentials on SSH.",
        "Multiple failed attempts to access admin panel.",
        "Kerberos pre-authentication failure detected.",
    ],
    "File Access": [
        "Accessed /etc/shadow — sensitive credential file.",
        "Read operation on C:\\Users\\Admin\\Documents\\budget.xlsx",
        "Unauthorized read on /var/log/auth.log.",
    ],
    "Port Scan": [
        "TCP SYN scan detected across subnet 192.168.1.0/24.",
        "NMAP stealth scan (-sS) on ports 1-1024.",
        "UDP scan on high-numbered ports detected by IDS.",
    ],
    "Privilege Escalation": [
        "sudo -l executed by non-root user.",
        "Token impersonation via SeImpersonatePrivilege.",
        "Exploited SUID binary to gain root access.",
    ],
    "Lateral Movement": [
        "PsExec used to execute commands on remote host.",
        "WMI query launched remote process on 192.168.1.20.",
        "Scheduled task created on remote machine via SMB.",
    ],
    "Data Exfiltration": [
        "Large DNS TXT record transfer detected (possible tunneling).",
        "FTP upload of 2.3GB archive to external IP.",
        "HTTPS POST with unusually large payload to unknown endpoint.",
    ],
    "Malware Execution": [
        "Suspicious PowerShell encoded command executed.",
        "Unknown process 'svchost32.exe' spawned from cmd.exe.",
        "Ransomware signature detected: file encryption started.",
    ],
    "Brute Force": [
        "150 failed login attempts in 2 minutes from single IP.",
        "Credential stuffing attack on /api/login endpoint.",
        "Dictionary attack on SMB share detected.",
    ],
    "USB Insertion": [
        "Unregistered USB device inserted on endpoint.",
        "Autorun triggered from USB on workstation.",
        "USB mass storage device enumerated: potential data theft risk.",
    ],
}


def generate_logs(num_rows: int = NUM_ROWS) -> pd.DataFrame:
    """
    Generate a DataFrame of synthetic forensic log entries.
    
    Returns:
        pd.DataFrame: Forensic logs with columns:
            timestamp, source_ip, event_type, status, description
    """
    rows = []
    current_time = START_TIME

    # Simulate an attack campaign: start with recon, escalate to exfiltration
    # This creates realistic correlated patterns for FP-Growth mining
    attack_sequence = [
        "Port Scan", "Failed Login", "Failed Login", "Brute Force",
        "Login", "File Access", "Privilege Escalation",
        "Lateral Movement", "Data Exfiltration",
    ]

    for i in range(num_rows):
        # Time progression: random gap between events (30 seconds to 5 minutes)
        current_time += timedelta(seconds=random.randint(30, 300))

        # Bias toward attack IPs for first 20 events (simulating attacker activity)
        if i < 20:
            ip = random.choice(ATTACKER_IPS)
            # Follow attack sequence for first 9 events
            if i < len(attack_sequence):
                event_type = attack_sequence[i]
            else:
                event_type = random.choice(EVENT_TYPES)
        else:
            ip = random.choice(ALL_IPS)
            event_type = random.choice(EVENT_TYPES)

        # Determine status based on event type
        status = random.choice(STATUS_WEIGHTS.get(event_type, ["Success", "Fail"]))

        # Pick a description matching the event type
        description = random.choice(DESCRIPTIONS.get(event_type, ["Unknown event."]))

        rows.append({
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_ip": ip,
            "event_type": event_type,
            "status": status,
            "description": description,
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    print("[CyberGaze] Generating forensic log dataset...")
    df = generate_logs()
    output_path = "./forensic_logs.csv"
    df.to_csv(output_path, index=False)
    print(f"[CyberGaze] Generated {len(df)} log entries -> {output_path}")
    print(df.head(10).to_string())
    print(f"\n[CyberGaze] Event type distribution:\n{df['event_type'].value_counts().to_string()}")
