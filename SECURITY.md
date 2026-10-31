# Security Policy

## Supported Versions
Currently, only the main branch (latest release) is supported with security updates.

## Reporting a Vulnerability
If you discover a security vulnerability within ImageSentinel, please do not open a public issue.
Instead, responsibly disclose it by sending an email to the repository maintainer. 

We will acknowledge receipt of your vulnerability report and strive to send you regular updates about our progress. If you report a vulnerability, we will credit you in our security advisories.

## Safe Usage
- ImageSentinel processes files locally. However, if processing untrusted files from unknown sources, consider running the tool in a sandboxed environment (like a VM or Docker container) to prevent potential exploitation of vulnerabilities in underlying image parsing libraries (`Pillow`, `exifread`).
- Do not expose the Web Dashboard (`app.py`) to the public internet, as it is designed for local analysis only and lacks authentication mechanisms.
