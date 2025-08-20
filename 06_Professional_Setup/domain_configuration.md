# 06_Professional_Setup/domain_configuration.md
# Adaptive Mind Framework - Professional Domain Configuration

## Overview

This document outlines the domain and DNS configuration for the Adaptive Mind Framework IP package. The setup was designed for professionalism, security, and cost-effectiveness.

## Domain Details

- **Primary Domain:** `adaptive-mind.com`
- **Registrar:** Namecheap, Inc.
- **Registration Date:** August 21, 2025
- **Status:** Active

## Key Configuration Choices

- **`.com` TLD:** The `.com` top-level domain was strategically chosen over `.ai` for its universal trust, superior email deliverability, and lower long-term registration costs, making it a more stable and professional asset for an enterprise acquirer.
- **Domain Privacy:** WhoisGuard privacy protection is enabled and active, protecting ownership details from public scraping.

## DNS Configuration (Managed via Namecheap)

The DNS is configured to point to the live demonstration environment hosted on Render.com.

| Type         | Host  | Value                                    | TTL       |
| :----------- | :---- | :--------------------------------------- | :-------- |
| CNAME Record | `@`   | `adaptive-mind-framework.onrender.com`   | Automatic |
| CNAME Record | `www` | `adaptive-mind.com`                      | Automatic |
| CNAME Record | `demo`| `adaptive-mind-framework.onrender.com`   | Automatic |
| TXT Record   | `_domainkey` | `v=DKIM1; k=rsa; p=...` (Managed by Namecheap Email) | 30 min    |

**Note:** No premium DNS service is required, as the combination of Namecheap's standard DNS and Render's global CDN provides sufficient performance and reliability for demonstration and initial production phases.