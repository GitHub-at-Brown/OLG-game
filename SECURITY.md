# Security Policy

## Dependency Vulnerability Management

This project uses safety scanning tools to identify and remediate security vulnerabilities in its dependencies.

### Performing Security Scans

#### Using Safety CLI (Recommended)

We have integrated with Safety CLI for security scanning. To perform a scan:

1. Install Safety CLI:
```bash 
pip install safety
```

2. Run a security scan:
```bash
safety scan -r requirements.txt
```

This will use the project configuration stored in `.safety-project.ini`.

#### Using pip-audit

As an alternative, you can use pip-audit:

1. Install pip-audit:
```bash
pip install pip-audit
```

2. Run a security scan:
```bash
pip-audit -r requirements.txt
```

### Recent Security Updates

#### April 2025
- Updated eventlet from 0.33.3 to 0.37.0 to address vulnerability PVE-2024-73179 related to HTTP header processing in the WSGI implementation.

### Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it by opening an issue in the repository or contacting the maintainers directly.

### Keeping Dependencies Secure

It's recommended to periodically run security scans on the dependencies and update them as needed. You can also set up automated scanning using GitHub Actions or other CI/CD tools. 