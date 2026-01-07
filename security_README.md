# Security Configuration Guide

This document provides comprehensive security guidelines for the Context Engineering MCP Platform.

## Overview

The platform implements multiple layers of security:
- **API Authentication & Authorization**
- **Rate Limiting & Request Validation**
- **Data Encryption & Secure Storage**
- **CORS & Security Headers**
- **Input Validation & Sanitization**
- **Logging & Monitoring**

## Security Features

### 1. Authentication & Authorization

#### API Key Management
```bash
# Generate secure API keys
python -c "from security_config import SecurityConfig; print(SecurityConfig().generate_jwt_secret())"

# Encrypt API keys for storage
from security_config import security_config
encrypted_key = security_config.encrypt_api_key("your-api-key")
```

#### JWT Token Authentication
```python
# Generate JWT token
token = security_config.generate_jwt_token("user123", {"role": "admin"})

# Verify JWT token
payload = security_config.verify_jwt_token(token)
```

### 2. Rate Limiting

Default configuration:
- **60 requests per minute** per client
- Configurable via `RATE_LIMIT_RPM` environment variable
- Automatic cleanup of expired rate limit entries

### 3. Request Validation

- **Maximum request size**: 50MB (configurable via `MAX_REQUEST_SIZE`)
- **File upload limit**: 10MB (configurable via `MAX_FILE_UPLOAD_SIZE`)
- **Path traversal protection**: Validates file paths
- **Input sanitization**: Filename and content sanitization

### 4. CORS Configuration

```bash
# Configure allowed origins (development)
CORS_ORIGINS=http://localhost:3000,http://localhost:9003,http://localhost:8888,http://localhost:9002

# Production example
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

### 5. Security Headers

Automatically applied to all responses:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'`
- `Referrer-Policy: strict-origin-when-cross-origin`

## Environment Configuration

### Required Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Security (recommended for production)
JWT_SECRET=your_jwt_secret_here_min_32_chars
ENCRYPTION_SALT=your_encryption_salt_here
```

### Optional Security Variables

```bash
# HTTPS Configuration
ENABLE_HTTPS=true
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem

# Request Limits
MAX_REQUEST_SIZE=50  # MB
MAX_FILE_UPLOAD_SIZE=10  # MB
RATE_LIMIT_RPM=60

# Session Configuration
SESSION_TIMEOUT=3600  # seconds

# Database Encryption
DB_ENCRYPTION_KEY=your_db_encryption_key_here
```

## Production Deployment

### 1. HTTPS Configuration

```bash
# Enable HTTPS
ENABLE_HTTPS=true
SSL_CERT_PATH=/etc/ssl/certs/your-cert.pem
SSL_KEY_PATH=/etc/ssl/private/your-key.pem
```

### 2. Reverse Proxy Setup (Nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    location / {
        proxy_pass http://127.0.0.1:8888;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Container Security

```dockerfile
# Use non-root user
RUN addgroup --system --gid 1001 appgroup
RUN adduser --system --uid 1001 --gid 1001 appuser
USER appuser

# Set secure permissions
COPY --chown=appuser:appgroup . /app
RUN chmod 755 /app
```

## Security Monitoring

### 1. Event Logging

Security events are automatically logged:
- Rate limit violations
- Invalid API key attempts
- Request size violations
- Authentication failures
- Suspicious activity patterns

### 2. Log Analysis

```python
# Example log entry
{
    "event_type": "rate_limit_exceeded",
    "timestamp": "2024-01-01T12:00:00Z",
    "severity": "WARNING",
    "details": {
        "client_id": "abc123",
        "path": "/api/contexts",
        "service": "context_api"
    }
}
```

### 3. Alerting Setup

Configure alerts for:
- High rate of authentication failures
- Unusual traffic patterns
- API errors above threshold
- Security event patterns

## Best Practices

### 1. API Key Management

- **Never hardcode API keys** in source code
- **Use environment variables** for all secrets
- **Rotate API keys regularly** (recommended: every 90 days)
- **Use different keys** for different environments

### 2. Password Security

```python
# Hash passwords securely
hashed = security_config.hash_password("user_password")

# Verify passwords
is_valid = security_config.verify_password("user_password", hashed)
```

### 3. File Upload Security

```python
# Validate file types
allowed_types = ['.pdf', '.txt', '.md', '.json']
if not any(filename.endswith(ext) for ext in allowed_types):
    raise HTTPException(status_code=400, detail="File type not allowed")

# Sanitize filenames
safe_filename = security_config.sanitize_filename(original_filename)
```

### 4. Input Validation

```python
# Validate paths
if not security_config.is_safe_path(user_provided_path):
    raise HTTPException(status_code=400, detail="Invalid path")

# Validate API key format
if not security_config.validate_api_key_format(api_key):
    raise HTTPException(status_code=401, detail="Invalid API key")
```

## Incident Response

### 1. Security Incident Detection

Monitor for:
- Multiple failed authentication attempts
- Unusual API usage patterns
- High error rates
- Suspicious file upload attempts

### 2. Response Procedures

1. **Identify the threat** - Analyze logs and patterns
2. **Contain the incident** - Rate limit or block suspicious IPs
3. **Assess the impact** - Check for data compromise
4. **Remediate** - Update security configurations
5. **Document** - Record incident details for future prevention

### 3. Emergency Actions

```bash
# Emergency API key rotation
export NEW_GEMINI_API_KEY="new_secure_key"
# Restart services

# Block suspicious IP
# Add to CORS_ORIGINS exclusion or firewall rules

# Increase rate limiting
export RATE_LIMIT_RPM=10  # Reduce from default 60
```

## Security Testing

### 1. Automated Security Scans

```bash
# Install security scanning tools
pip install bandit safety

# Run security analysis
bandit -r . -f json -o security-report.json
safety check --json > safety-report.json

# Run tests with security focus
pytest tests/security/ -v
```

### 2. Manual Security Testing

- **API endpoint testing** with invalid inputs
- **Rate limiting verification**
- **CORS policy testing**
- **Authentication bypass attempts**
- **File upload vulnerability testing**

### 3. Penetration Testing

Recommended annual penetration testing focusing on:
- API security vulnerabilities
- Authentication mechanisms
- Data encryption implementation
- Network security configuration

## Compliance Considerations

### Data Protection
- **Encryption at rest** for sensitive data
- **Encryption in transit** via HTTPS
- **Data minimization** principles
- **Access logging** for audit trails

### Privacy
- **API key anonymization** in logs
- **User data protection** measures
- **Data retention policies**
- **Right to data deletion** support

## Security Updates

### 1. Dependency Management

```bash
# Check for security vulnerabilities
pip audit

# Update dependencies
pip install --upgrade -r requirements-security.txt
```

### 2. Security Patches

- Monitor security advisories for FastAPI, Uvicorn, and dependencies
- Test security updates in staging environment
- Apply patches promptly to production

### 3. Configuration Reviews

- **Monthly**: Review security configurations
- **Quarterly**: Update API keys and secrets
- **Annually**: Comprehensive security audit

## Contact & Support

For security issues:
- **Security vulnerabilities**: Report via private channels
- **Configuration questions**: Check documentation first
- **Incident reporting**: Use structured incident report format

---

**Note**: This security guide should be reviewed and updated regularly to address new threats and maintain security best practices.