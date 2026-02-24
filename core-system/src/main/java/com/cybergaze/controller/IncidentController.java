package com.cybergaze.controller;

import com.cybergaze.service.PlaybookService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * IncidentController — DFIR Panic Button REST API
 * =================================================
 * Handles incoming incident trigger requests from the React dashboard.
 *
 * When an analyst clicks the "PANIC" button in the UI, this controller:
 * 1. Receives the threat level (1–10)
 * 2. Invokes PlaybookService to generate NIST-aligned response steps
 * 3. Returns a structured JSON response with all actions to take
 *
 * CORS is configured to allow requests from:
 * - http://localhost:3000 (Create React App)
 * - http://localhost:5173 (Vite dev server)
 */
@RestController
@RequestMapping("/api/commander")
@CrossOrigin(origins = { "http://localhost:3000", "http://localhost:5173" })
@RequiredArgsConstructor
@Slf4j
public class IncidentController {

    private final PlaybookService playbookService;

    /**
     * POST /api/commander/trigger-response
     * ======================================
     * The main "Panic Button" endpoint.
     *
     * Request Body:
     * {
     * "threatLevel": 8,
     * "description": "Ransomware detected on FINANCE-PC-001"
     * }
     *
     * Response Body:
     * {
     * "incidentId": "CG-20240601-001",
     * "severity": "HIGH",
     * "threatLevel": 8,
     * "triggeredAt": "2024-06-01T08:30:00",
     * "playbookSteps": [...],
     * "threatContext": {...}
     * }
     *
     * @param requestBody Map containing "threatLevel" (int) and optional
     *                    "description"
     * @return ResponseEntity with incident response playbook
     */
    @PostMapping("/trigger-response")
    public ResponseEntity<Map<String, Object>> triggerResponse(
            @RequestBody Map<String, Object> requestBody) {
        // ── Extract and validate threat level ─────────────────────────
        int threatLevel;
        try {
            threatLevel = Integer.parseInt(requestBody.getOrDefault("threatLevel", 5).toString());
            threatLevel = Math.max(1, Math.min(10, threatLevel)); // Clamp to [1, 10]
        } catch (NumberFormatException e) {
            return ResponseEntity.badRequest().body(Map.of(
                    "error", "Invalid threatLevel. Provide an integer between 1 and 10."));
        }

        String description = requestBody.getOrDefault("description", "No description provided.").toString();
        log.warn("[CyberGaze] 🚨 PANIC BUTTON TRIGGERED — Threat Level: {}/10 — {}", threatLevel, description);

        // ── Generate NIST playbook ────────────────────────────────────
        List<String> playbookSteps = playbookService.generatePlaybook(threatLevel);
        String severity = playbookService.getThreatSeverity(threatLevel);
        Map<String, String> threatContext = playbookService.getThreatContext(severity);

        // ── Build response ────────────────────────────────────────────
        String incidentId = "CG-" + LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss"));
        String triggeredAt = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);

        Map<String, Object> response = new HashMap<>();
        response.put("incidentId", incidentId);
        response.put("severity", severity);
        response.put("threatLevel", threatLevel);
        response.put("description", description);
        response.put("triggeredAt", triggeredAt);
        response.put("playbookStepCount", playbookSteps.size());
        response.put("playbookSteps", playbookSteps);
        response.put("threatContext", threatContext);
        response.put("status", "RESPONSE_INITIATED");
        response.put("message",
                String.format("Incident %s acknowledged. %d response steps activated for %s threat.",
                        incidentId, playbookSteps.size(), severity));

        log.info("[CyberGaze] Incident {} created with {} playbook steps (Severity: {})",
                incidentId, playbookSteps.size(), severity);

        return ResponseEntity.ok(response);
    }

    /**
     * GET /api/commander/health
     * ==========================
     * Health check for the Core Commander service.
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of(
                "status", "online",
                "service", "CyberGaze Core Commander",
                "version", "1.0.0",
                "timestamp", LocalDateTime.now().toString()));
    }

    /**
     * GET /api/commander/threat-levels
     * ==================================
     * Returns the threat level scale and severity descriptions.
     * Useful for the React dashboard to render a severity legend.
     */
    @GetMapping("/threat-levels")
    public ResponseEntity<Map<String, Object>> getThreatLevels() {
        return ResponseEntity.ok(Map.of(
                "scale", List.of(
                        Map.of("range", "1–3", "severity", "LOW", "color", "#22c55e", "description",
                                "Reconnaissance / Anomalous activity"),
                        Map.of("range", "4–6", "severity", "MEDIUM", "color", "#f59e0b", "description",
                                "Active credential attacks / Initial access"),
                        Map.of("range", "7–9", "severity", "HIGH", "color", "#ef4444", "description",
                                "Lateral movement / Privilege escalation"),
                        Map.of("range", "10", "severity", "CRITICAL", "color", "#7c3aed", "description",
                                "Full breach / Data exfiltration / Ransomware"))));
    }
}
