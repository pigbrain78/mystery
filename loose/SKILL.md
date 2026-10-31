---
name: aegis-sovereign-core
description: Provides the core functionalities of the Aegis Trace Core system, including Sovereign Axiom integration for financial and compliance operations. Use this skill when interacting with the Aegis Trace Core, managing sovereign passports, executing FX settlements, or generating SAT proofs.
---

# Aegis Sovereign Core Skill

## Overview

This skill encapsulates the `AegisTraceCore` system, which now includes the `SovereignAxiom` framework. It provides a robust set of tools for managing digital identities, financial transactions, and compliance within a sovereign system architecture.

## Core Capabilities

This skill offers the following key functionalities:

### 1. Aegis Trace Core System Management

*   **System Heartbeat Logging**: Access the `log_status` method to monitor the system's operational and financial health, including details on the architect, active skills, security mode, and Sovereign Axiom financial pools.

### 2. Sovereign Passport Protocol

*   **Issue Sovereign Passport**: Utilize the `issue_passport` method to create ZKP-backed credentials for agents. This process registers agents, assigns a `passport_id`, sets their tier to "GOLD", and ensures `sat_compliance`.

### 3. FX Rail & Escrow

*   **Execute FX Settlement**: Employ the `perform_fx_settlement` method to facilitate instant foreign exchange settlements. This includes capturing a 0.1% spread as a fee, converting amounts to target currencies, and updating financial pools. Settlements are restricted to "GOLD" tier agents.

### 4. SAT Module (Zero-Knowledge Compliance Proof)

*   **Generate SAT Proof**: Use the `get_sat_proof` method to generate Zero-Knowledge Compliance Proofs for registered agents, confirming compliance status without exposing sensitive data.

## Usage

To interact with the Aegis Sovereign Core, instantiate the `AegisTraceCore` class and call its methods. The `SovereignAxiom` functionalities are exposed directly through the `AegisTraceCore` instance.

### Example:

```python
from scripts.aegis_trace_core import AegisTraceCore

aegis = AegisTraceCore()
aegis.log_status()

# Issue a passport
passport_id = aegis.issue_passport("NEW_AGENT_ID", "NEW_FIRM_ID")
print(f"Issued Passport ID: {passport_id[:16]}...")

# Perform an FX settlement
settlement_result = aegis.perform_fx_settlement("NEW_AGENT_ID", "RECEIVER_AGENT_ID", 5000.0, "USD")
print(f"FX Settlement Status: {settlement_result["status"]}")

# Get a SAT proof
sat_proof = aegis.get_sat_proof("NEW_AGENT_ID")
print(f"SAT Proof: {sat_proof}")

aegis.log_status()
```

## Resources

This skill includes the following resources:

### scripts/
*   `aegis_trace_core.py`: The main Python script containing the `AegisTraceCore` and `SovereignAxiom` class implementations.

### references/
*   `aegis_sovereign_core_documentation.md`: Detailed documentation outlining the integration and usage of the Aegis Trace Core with Sovereign Axiom.
