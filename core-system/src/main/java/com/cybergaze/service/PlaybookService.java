package com.cybergaze.service;

import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * PlaybookService — NIST SP 800-61 Incident Response Playbook Engine
 * ===================================================================
 * Generates contextual incident response steps based on threat level.
 *
 * NIST SP 800-61r2 defines four phases of incident response:
 *  1. Preparation
 *  2. Detection & Analysis  ← Threat arrives here
 *  3. Containment, Eradication & Recovery  ← This service handles this
 *  4. Post-Incident Activity
 *
 * Threat Levels:
 *  LOW    (1-3)  — Monitoring & logging enhancements
 *  MEDIUM (4-6)  — Active containment measures
 *  HIGH   (7-9)  — Aggressive isolation and forensic preservation
 *  CRITICAL (10) — Full emergency response protocol
 */
@Service
public class PlaybookService {

    /**
     * Generates a prioritized list of NIST-aligned response steps
     * based on the incoming threat level (1–10 scale).
     *
     * @param threatLevel Integer from 1 (benign) to 10 (critical)
     * @return List of ordered response action strings
     */
    public List<String> generatePlaybook(int threatLevel) {
        List<String> steps = new ArrayList<>();

        // ── Phase 0: Always-on baseline steps ──────────────────────────
        steps.add("📋 [NIST Phase 2] Log all incident details with timestamps into SIEM.");
        steps.add("📋 [NIST Phase 2] Assign incident ticket and notify on-call security team.");

        if (threatLevel >= 1) {
            // LOW threat — Enhanced monitoring
            steps.add("🔍 [LOW] Enable verbose logging on all affected endpoints.");
            steps.add("🔍 [LOW] Run integrity check on critical system files (sha256sum).");
            steps.add("🔍 [LOW] Review firewall logs for the past 24 hours.");
        }

        if (threatLevel >= 4) {
            // MEDIUM threat — Active containment begins
            steps.add("⚠️  [MEDIUM] Block Port 445 (SMB) on perimeter firewall — prevent Lateral Movement.");
            steps.add("⚠️  [MEDIUM] Reset credentials for all accounts accessed from attacker IPs.");
            steps.add("⚠️  [MEDIUM] Disable USB auto-run policy via Group Policy (GPO).");
            steps.add("⚠️  [MEDIUM] Apply rate limiting on SSH and RDP endpoints (max 5 attempts/min).");
            steps.add("⚠️  [MEDIUM] Capture memory dump of suspected compromised host(s) before shutdown.");
        }

        if (threatLevel >= 7) {
            // HIGH threat — Isolation and forensic preservation
            steps.add("🚨 [HIGH] Isolate Subnet 192.168.1.0/24 — sever from main network immediately.");
            steps.add("🚨 [HIGH] Revoke all active OAuth tokens and force re-authentication enterprise-wide.");
            steps.add("🚨 [HIGH] Snapshot all VM disk images for forensic preservation (evidence chain-of-custody).");
            steps.add("🚨 [HIGH] Redirect DNS to sinkhole server to prevent C2 (Command & Control) communication.");
            steps.add("🚨 [HIGH] Engage Threat Hunting team — conduct IOC sweep across all endpoints.");
            steps.add("🚨 [HIGH] Notify Legal and Compliance teams of possible data breach.");
        }

        if (threatLevel >= 10) {
            // CRITICAL — Full emergency response
            steps.add("🔴 [CRITICAL] ACTIVATE FULL EMERGENCY RESPONSE PROTOCOL.");
            steps.add("🔴 [CRITICAL] Notify CISO and Executive Leadership immediately.");
            steps.add("🔴 [CRITICAL] Initiate Business Continuity Plan (BCP) procedures.");
            steps.add("🔴 [CRITICAL] Contact law enforcement (FBI IC3 / local CERT) if nation-state actor suspected.");
            steps.add("🔴 [CRITICAL] Prepare breach notification for regulatory bodies (GDPR 72-hour rule, HIPAA, etc.).");
            steps.add("🔴 [CRITICAL] Preserve all logs under legal hold — do NOT power off compromised systems.");
        }

        // ── Phase 4: Post-incident (always appended) ──────────────────
        steps.add("📝 [NIST Phase 4] Schedule post-incident review (within 72 hours).");
        steps.add("📝 [NIST Phase 4] Update threat intelligence feeds with discovered IOCs.");
        steps.add("📝 [NIST Phase 4] Patch vulnerabilities exploited in this incident.");

        return steps;
    }

    /**
     * Maps a raw threat level integer to a human-readable severity label.
     *
     * @param threatLevel Integer 1–10
     * @return Severity string: LOW, MEDIUM, HIGH, or CRITICAL
     */
    public String getThreatSeverity(int threatLevel) {
        if (threatLevel >= 10) return "CRITICAL";
        if (threatLevel >= 7)  return "HIGH";
        if (threatLevel >= 4)  return "MEDIUM";
        return "LOW";
    }

    /**
     * Returns a brief description of the expected threat behavior
     * for the given severity level.
     *
     * @param severity Severity string from getThreatSeverity()
     * @return Map of threat context fields
     */
    public Map<String, String> getThreatContext(String severity) {
        return switch (severity) {
            case "CRITICAL" -> Map.of(
                "mitre_tactic", "Exfiltration / Impact",
                "likely_actor", "Advanced Persistent Threat (APT) or Insider",
                "estimated_dwell_time", "> 30 days",
                "recommended_ir_team", "Full CSIRT + External Forensics Firm"
            );
            case "HIGH" -> Map.of(
                "mitre_tactic", "Lateral Movement / Privilege Escalation",
                "likely_actor", "Targeted Attacker or Malicious Insider",
                "estimated_dwell_time", "7-30 days",
                "recommended_ir_team", "Internal CSIRT + Legal"
            );
            case "MEDIUM" -> Map.of(
                "mitre_tactic", "Initial Access / Credential Access",
                "likely_actor", "Opportunistic Attacker",
                "estimated_dwell_time", "< 7 days",
                "recommended_ir_team", "Security Operations Center (SOC)"
            );
            default -> Map.of(
                "mitre_tactic", "Reconnaissance",
                "likely_actor", "Script Kiddie / Automated Scanner",
                "estimated_dwell_time", "< 24 hours",
                "recommended_ir_team", "Tier-1 SOC Analyst"
            );
        };
    }
}
