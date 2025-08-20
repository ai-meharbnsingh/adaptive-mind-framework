# 06_Professional_Setup/subdomain_configuration.md
# Adaptive Mind Framework - Subdomain Configuration

## Overview

A clear subdomain strategy has been implemented to provide logical access points to the demonstration platform.

## Configured Subdomains

1.  **`www.adaptive-mind.com`**
    -   **Purpose:** Standard alias for the primary domain.
    -   **Configuration:** A CNAME record pointing to `adaptive-mind.com`. It is set to redirect to the root domain at the hosting level.

2.  **`demo.adaptive-mind.com`**
    -   **Purpose:** The primary, memorable URL for accessing the live interactive demonstration.
    -   **Configuration:** A CNAME record pointing directly to the Render.com service (`adaptive-mind-framework.onrender.com`).

## Deferred Subdomains

- **`eval.adaptive-mind.com`:** Originally planned in the enterprise specification, this subdomain was strategically deferred. The `demo.` subdomain effectively serves both quick demonstrations and in-depth buyer evaluations, simplifying the infrastructure and reducing complexity for the initial sales phase. An acquirer can easily implement this if their internal policies require a separate evaluation environment.