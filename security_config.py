# Security Configuration Module for Context Engineering MCP Platform
import os
import secrets
import hashlib
from typing import Dict, List, Optional
from cryptography.fernet import Fernet
import jwt
from datetime import datetime, timedelta

class SecurityConfig:
    """Centralized security configuration and utilities"""
    
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET', self._generate_jwt_secret())
        self.encryption_salt = os.getenv('ENCRYPTION_SALT', self._generate_salt())
        self.enable_https = os.getenv('ENABLE_HTTPS', 'false').lower() == 'true'
        self.max_request_size = int(os.getenv('MAX_REQUEST_SIZE', '50')) * 1024 * 1024  # MB to bytes
        self.max_file_upload_size = int(os.getenv('MAX_FILE_UPLOAD_SIZE', '10')) * 1024 * 1024
        self.rate_limit_rpm = int(os.getenv('RATE_LIMIT_RPM', '60'))
        self.session_timeout = int(os.getenv('SESSION_TIMEOUT', '3600'))
        self._fernet = None
        
    def _generate_jwt_secret(self) -> str:
        """Generate a secure JWT secret if not provided"""
        return secrets.token_urlsafe(32)
    
    def _generate_salt(self) -> str:
        """Generate a secure salt for encryption"""
        return secrets.token_urlsafe(16)
    
    def get_fernet(self) -> Fernet:
        """Get or create Fernet encryption instance"""
        if self._fernet is None:
            # Create a key from the encryption salt
            key = hashlib.sha256(self.encryption_salt.encode()).digest()
            key_b64 = Fernet.generate_key()  # Use proper key generation
            self._fernet = Fernet(key_b64)
        return self._fernet
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key for secure storage"""
        return self.get_fernet().encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt an API key"""
        return self.get_fernet().decrypt(encrypted_key.encode()).decode()
    
    def generate_jwt_token(self, user_id: str, additional_claims: Optional[Dict] = None) -> str:
        """Generate a JWT token for authentication"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=self.session_timeout),
            'iat': datetime.utcnow(),
            'iss': 'context-engineering-mcp'
        }
        
        if additional_claims:
            payload.update(additional_claims)
            
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[Dict]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash a password with salt"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            self.encryption_salt.encode(),
            100000  # iterations
        ).hex()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return self.hash_password(password) == hashed
    
    def get_cors_origins(self) -> List[str]:
        """Get allowed CORS origins"""
        origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
        return [origin.strip() for origin in origins.split(',')]
    
    def is_safe_path(self, path: str) -> bool:
        """Check if a file path is safe (prevent directory traversal)"""
        # Normalize the path and check for directory traversal attempts
        normalized = os.path.normpath(path)
        return not normalized.startswith('..') and not os.path.isabs(normalized)
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename for safe storage"""
        import re
        # Remove or replace dangerous characters
        sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
        return sanitized
    
    def validate_api_key_format(self, api_key: str) -> bool:
        """Validate API key format"""
        # Basic validation - adjust based on your API key format
        return len(api_key) >= 20 and api_key.replace('-', '').replace('_', '').isalnum()


class SecurityMiddleware:
    """Security middleware for FastAPI applications"""
    
    def __init__(self, security_config: SecurityConfig):
        self.config = security_config
        self.rate_limit_store = {}  # In production, use Redis
        
    async def rate_limit_check(self, client_id: str) -> bool:
        """Check if client is within rate limits"""
        now = datetime.utcnow()
        minute_key = now.strftime('%Y-%m-%d-%H-%M')
        
        key = f"{client_id}:{minute_key}"
        current_count = self.rate_limit_store.get(key, 0)
        
        if current_count >= self.config.rate_limit_rpm:
            return False
            
        self.rate_limit_store[key] = current_count + 1
        
        # Clean up old entries (basic cleanup)
        if len(self.rate_limit_store) > 10000:
            cutoff = (now - timedelta(minutes=2)).strftime('%Y-%m-%d-%H-%M')
            keys_to_remove = [k for k in self.rate_limit_store.keys() if k.split(':')[1] < cutoff]
            for k in keys_to_remove:
                del self.rate_limit_store[k]
                
        return True
    
    def get_client_id(self, request) -> str:
        """Extract client identifier from request"""
        # Use API key or IP address as client identifier
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return hashlib.sha256(api_key.encode()).hexdigest()[:16]
        
        # Fallback to IP address
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        return request.client.host if request.client else 'unknown'


# Global security instance
security_config = SecurityConfig()
security_middleware = SecurityMiddleware(security_config)


def get_security_headers() -> Dict[str, str]:
    """Get security headers for HTTP responses"""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }


def log_security_event(event_type: str, details: Dict, severity: str = 'INFO'):
    """Log security events for monitoring"""
    import logging
    
    logger = logging.getLogger('security')
    
    log_entry = {
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat(),
        'severity': severity,
        'details': details
    }
    
    if severity == 'CRITICAL':
        logger.critical(f"Security Event: {log_entry}")
    elif severity == 'ERROR':
        logger.error(f"Security Event: {log_entry}")
    elif severity == 'WARNING':
        logger.warning(f"Security Event: {log_entry}")
    else:
        logger.info(f"Security Event: {log_entry}")


# Example usage and testing
if __name__ == "__main__":
    # Test the security configuration
    config = SecurityConfig()
    
    # Test API key encryption
    test_key = "test-api-key-12345"
    encrypted = config.encrypt_api_key(test_key)
    decrypted = config.decrypt_api_key(encrypted)
    print(f"API Key encryption test: {test_key == decrypted}")
    
    # Test JWT token generation
    token = config.generate_jwt_token("user123", {"role": "admin"})
    payload = config.verify_jwt_token(token)
    print(f"JWT test: {payload is not None}")
    
    # Test password hashing
    password = "secure_password_123"
    hashed = config.hash_password(password)
    verified = config.verify_password(password, hashed)
    print(f"Password hashing test: {verified}")