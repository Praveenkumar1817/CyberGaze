package com.cybergaze;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * CyberGazeApplication — Spring Boot Entry Point
 * ================================================
 * Bootstraps the CyberGaze Core Commander service.
 *
 * This service handles:
 *  - The "Panic Button" incident response trigger
 *  - NIST SP 800-61 aligned playbook execution
 *  - Threat level assessment and response coordination
 *
 * Runs on port 8080 (configurable in application.properties).
 */
@SpringBootApplication
public class CyberGazeApplication {

    public static void main(String[] args) {
        SpringApplication.run(CyberGazeApplication.class, args);
        System.out.println("[CyberGaze] Core Commander is online. Listening for incident triggers...");
    }
}
