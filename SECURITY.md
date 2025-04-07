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

### GitHub Dependabot Integration

This project has Dependabot configured to scan for vulnerabilities and create pull requests for security updates. If you see a Dependabot alert in GitHub:

1. Visit the Security tab in the GitHub repository
2. Check the "Dependabot alerts" section
3. Review the vulnerability details
4. Either:
   - Accept the suggested dependency update via the pull request
   - Or manually update the dependency in requirements.txt and document the change

Note: Sometimes GitHub may continue to show an alert even after updating dependencies. This can happen if:
- The vulnerability is in a transitive dependency
- There's a delay in GitHub's scanning system
- The specific vulnerability can only be fixed through a code change rather than a dependency update

### Recent Security Updates

#### April 2025
- Updated eventlet from 0.33.3 to 0.39.1 to address vulnerability PVE-2024-73179 related to HTTP header processing in the WSGI implementation.
- Updated pip from 21.2.4 to 25.0.1 to address vulnerability PYSEC-2023-228.
- Updated all dependencies to their latest versions for improved security.

### Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it by opening an issue in the repository or contacting the maintainers directly.

### Keeping Dependencies Secure

It's recommended to periodically run security scans on the dependencies and update them as needed. We've set up automated scanning using GitHub Actions that runs weekly. 