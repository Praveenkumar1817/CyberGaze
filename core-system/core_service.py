"""
core_service.py — CyberGaze Core Commander (Python/FastAPI)
============================================================
Replacement for the Java Spring Boot service. Handles:
  - POST /api/commander/trigger-response  (Panic Button)
  - GET  /api/commander/health
  - GET  /api/commander/threat-levels

Runs on port 8080 so the React dashboard requires zero changes.
"""

import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="CyberGaze Core Commander",
    description="NIST SP 800-61 Playbook Engine — Panic Button Service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Threat level → severity mapping ────────────────
def get_severity(level: int) -> str:
    if level >= 10: return "CRITICAL"
    if level >= 7:  return "HIGH"
    if level >= 4:  return "MEDIUM"
    return "LOW"

# ── NIST SP 800-61 Playbook generator ──────────────
def generate_playbook(threat_level: int) -> list[str]:
    """
    Returns an ordered list of NIST-aligned incident response steps
    scaled to the incoming threat level (1–10).
    """
    steps = [
        "📋 [NIST-1] Document incident with precise timestamps in your SIEM/ticketing system.",
        "📋 [NIST-1] Assign incident ID and notify on-call security analyst.",
    ]

    if threat_level >= 1:
        steps += [
            "🔍 [LOW] Enable verbose logging on all endpoints in the affected subnet.",
            "🔍 [LOW] Run file-integrity check (sha256) on critical system binaries.",
            "🔍 [LOW] Review firewall deny-logs for the past 24 hours.",
        ]

    if threat_level >= 4:
        steps += [
            "⚠️  [MEDIUM] Block port 445 (SMB) at perimeter — prevent lateral movement.",
            "⚠️  [MEDIUM] Force reset of all credentials accessed from suspect IPs.",
            "⚠️  [MEDIUM] Apply rate-limiting on SSH/RDP: max 5 attempts per minute.",
            "⚠️  [MEDIUM] Disable USB autorun via Group Policy (GPO).",
            "⚠️  [MEDIUM] Capture memory dump of compromised host before power-off.",
        ]

    if threat_level >= 7:
        steps += [
            "🚨 [HIGH] Isolate affected subnet from main network immediately.",
            "🚨 [HIGH] Revoke all active OAuth/SAML tokens and force re-auth company-wide.",
            "🚨 [HIGH] Snapshot all VM disks for forensic chain-of-custody preservation.",
            "🚨 [HIGH] Sinkhole DNS to cut C&C (Command & Control) communication.",
            "🚨 [HIGH] Deploy Threat Hunting team for full IOC sweep.",
            "🚨 [HIGH] Notify Legal and Compliance of potential breach.",
        ]

    if threat_level >= 10:
        steps += [
            "🔴 [CRITICAL] ACTIVATE FULL EMERGENCY RESPONSE PROTOCOL.",
            "🔴 [CRITICAL] Brief CISO and executive leadership immediately.",
            "🔴 [CRITICAL] Initiate Business Continuity Plan (BCP).",
            "🔴 [CRITICAL] Contact law enforcement (CISA / FBI IC3) if nation-state suspected.",
            "🔴 [CRITICAL] Prepare breach notifications (GDPR 72hr, HIPAA, etc.).",
            "🔴 [CRITICAL] Place all logs under legal hold — do NOT power off systems.",
        ]

    steps += [
        "📝 [POST-IR] Schedule post-incident review within 72 hours.",
        "📝 [POST-IR] Feed discovered IOCs into threat-intel platform.",
        "📝 [POST-IR] Patch and harden exploited vulnerabilities.",
    ]
    return steps


def get_threat_context(severity: str) -> dict:
    mapping = {
        "CRITICAL": {
            "mitre_tactic": "Exfiltration / Impact",
            "likely_actor": "APT or Malicious Insider",
            "dwell_time_est": "> 30 days",
            "ir_team": "Full CSIRT + External Forensics",
        },
        "HIGH": {
            "mitre_tactic": "Lateral Movement / Privilege Escalation",
            "likely_actor": "Targeted Attacker",
            "dwell_time_est": "7–30 days",
            "ir_team": "Internal CSIRT + Legal",
        },
        "MEDIUM": {
            "mitre_tactic": "Initial Access / Credential Access",
            "likely_actor": "Opportunistic Attacker",
            "dwell_time_est": "< 7 days",
            "ir_team": "Security Operations Center (SOC)",
        },
        "LOW": {
            "mitre_tactic": "Reconnaissance",
            "likely_actor": "Automated Scanner / Script Kiddie",
            "dwell_time_est": "< 24 hours",
            "ir_team": "Tier-1 SOC Analyst",
        },
    }
    return mapping.get(severity, mapping["LOW"])


# ── Request / Response models ───────────────────────
class TriggerRequest(BaseModel):
    threatLevel: int = Field(default=5, ge=1, le=10)
    description: Optional[str] = "No description provided."


# ── Endpoints ───────────────────────────────────────
@app.get("/api/commander/health")
def health():
    return {"status": "online", "service": "CyberGaze Core Commander (Python)", "version": "1.0.0"}


@app.get("/api/commander/threat-levels")
def threat_levels():
    return {"scale": [
        {"range": "1–3",  "severity": "LOW",      "color": "#4ade80", "description": "Recon / Anomalous activity"},
        {"range": "4–6",  "severity": "MEDIUM",   "color": "#fbbf24", "description": "Credential attacks / Initial access"},
        {"range": "7–9",  "severity": "HIGH",     "color": "#f87171", "description": "Active intrusion / Lateral movement"},
        {"range": "10",   "severity": "CRITICAL", "color": "#a78bfa", "description": "Full breach / Ransomware / Exfiltration"},
    ]}


@app.post("/api/commander/trigger-response")
def trigger_response(req: TriggerRequest):
    severity = get_severity(req.threatLevel)
    steps = generate_playbook(req.threatLevel)
    context = get_threat_context(severity)
    incident_id = f"CG-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    return {
        "incidentId": incident_id,
        "severity": severity,
        "threatLevel": req.threatLevel,
        "description": req.description,
        "triggeredAt": datetime.now().isoformat(),
        "playbookStepCount": len(steps),
        "playbookSteps": steps,
        "threatContext": context,
        "status": "RESPONSE_INITIATED",
        "message": (
            f"Incident {incident_id} acknowledged. "
            f"{len(steps)} response actions activated for {severity} threat."
        ),
    }


if __name__ == "__main__":
    import uvicorn
    print("[CyberGaze] Core Commander starting on http://0.0.0.0:8080")
    uvicorn.run("core_service:app", host="0.0.0.0", port=8080, reload=True)
