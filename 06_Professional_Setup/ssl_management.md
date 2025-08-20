# 06_Professional_Setup/ssl_management.md
# Adaptive Mind Framework - SSL/TLS Certificate Management

## Overview

All web-facing assets for the Adaptive Mind Framework are secured with industry-standard SSL/TLS encryption (`https`), ensuring secure communication for all demonstrations and interactions.

## Certificate Provider & Management

- **Provider:** Let's Encrypt
- **Management:** Fully automated via the Render.com hosting platform.

## Key Features

- **Automated Issuance:** Render automatically provisions SSL certificates for the primary domain (`adaptive-mind.com`) and all configured subdomains (`www`, `demo`).
- **Automated Renewal:** Certificates are automatically renewed by Render before expiration, ensuring zero downtime or manual intervention is required.
- **Security Level:** Provides robust encryption, satisfying enterprise requirements for secure data transmission during demonstrations.
- **Cost:** This enterprise-grade feature is provided at **no additional cost** by the hosting platform.

## Current Status

- **`adaptive-mind.com`:** Certificate is active, issued, and valid.
- **`www.adaptive-mind.com`:** Certificate is active, issued, and valid.
- **`demo.adaptive-mind.com`:** Certificate is active, issued, and valid.
- **Grade:** A+ (via standard SSL Labs tests).