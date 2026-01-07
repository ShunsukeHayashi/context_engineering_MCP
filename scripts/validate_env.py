#!/usr/bin/env python3
"""
Validate environment configuration files.
This script checks .env files for security issues and completeness.
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple


class EnvValidator:
    """Validator for environment configuration files."""
    
    def __init__(self):
        # Sensitive keys that should not have default values
        self.sensitive_keys = {
            'GEMINI_API_KEY', 'JWT_SECRET', 'ENCRYPTION_SALT',
            'DB_ENCRYPTION_KEY', 'API_KEY', 'SECRET_KEY',
            'PASSWORD', 'TOKEN', 'PRIVATE_KEY'
        }
        
        # Required keys for different environments
        self.required_keys = {
            'development': {
                'GEMINI_API_KEY',
            },
            'production': {
                'GEMINI_API_KEY', 'JWT_SECRET', 'ENCRYPTION_SALT',
                'ENABLE_HTTPS', 'CORS_ORIGINS'
            }
        }
        
        # Default values that should be changed in production
        self.insecure_defaults = {
            'your_gemini_api_key_here',
            'your_jwt_secret_here_min_32_chars',
            'your_encryption_salt_here',
            'your_db_encryption_key_here',
            'localhost',
            'debug',
            'development',
            'false',  # for HTTPS in production
        }
    
    def parse_env_file(self, file_path: Path) -> Dict[str, str]:
        """Parse environment file and return key-value pairs."""
        env_vars = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            return env_vars
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE format
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                env_vars[key] = value
            else:
                print(f"Warning: Invalid format at line {line_num}: {line}")
        
        return env_vars
    
    def check_sensitive_keys(self, env_vars: Dict[str, str], file_path: Path) -> List[str]:
        """Check for insecure sensitive key values."""
        issues = []
        
        for key, value in env_vars.items():
            # Check if key contains sensitive information
            is_sensitive = any(
                sensitive in key.upper() 
                for sensitive in self.sensitive_keys
            )
            
            if is_sensitive:
                # Check for common insecure patterns
                if not value or value.lower() in self.insecure_defaults:
                    issues.append(
                        f"🔑 Sensitive key '{key}' has default/empty value"
                    )
                elif len(value) < 16 and 'KEY' in key.upper():
                    issues.append(
                        f"🔑 Key '{key}' appears too short (< 16 characters)"
                    )
                elif value == 'changeme' or 'example' in value.lower():
                    issues.append(
                        f"🔑 Key '{key}' has placeholder value"
                    )
        
        return issues
    
    def check_required_keys(self, env_vars: Dict[str, str], file_path: Path) -> List[str]:
        """Check for missing required keys."""
        issues = []
        
        # Determine environment type from filename
        file_name = file_path.name.lower()
        
        if 'prod' in file_name or 'production' in file_name:
            env_type = 'production'
        else:
            env_type = 'development'
        
        required = self.required_keys.get(env_type, set())
        missing_keys = required - set(env_vars.keys())
        
        for key in missing_keys:
            issues.append(f"❌ Missing required key for {env_type}: '{key}'")
        
        return issues
    
    def check_security_patterns(self, env_vars: Dict[str, str], file_path: Path) -> List[str]:
        """Check for common security issues."""
        issues = []
        
        for key, value in env_vars.items():
            # Check for URLs with credentials
            if re.search(r'https?://[^:]+:[^@]+@', value):
                issues.append(f"🌐 URL with embedded credentials in '{key}'")
            
            # Check for absolute paths that might be system-specific
            if key.endswith('_PATH') and value.startswith('/') and 'localhost' not in key.lower():
                if not value.startswith(('/app', '/opt', '/usr/local')):
                    issues.append(f"📁 Hardcoded absolute path in '{key}': {value}")
            
            # Check for debug flags in production-like files
            if 'prod' in file_path.name.lower():
                if key.upper() in ('DEBUG', 'DEVELOPMENT_MODE') and value.lower() == 'true':
                    issues.append(f"🐛 Debug mode enabled in production file: '{key}'")
            
            # Check for weak CORS settings
            if key == 'CORS_ORIGINS' and '*' in value:
                issues.append("🌍 CORS allows all origins (*) - security risk")
            
            # Check for insecure protocols in production
            if 'prod' in file_path.name.lower() and 'http://' in value and 'https://' not in value:
                issues.append(f"🔒 Insecure HTTP protocol in production: '{key}'")
        
        return issues
    
    def check_format_and_style(self, file_path: Path) -> List[str]:
        """Check file format and style issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            return [f"Error reading file: {e}"]
        
        # Check for common formatting issues
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
                
            # Check for spaces around equals sign
            if '=' in line and not line.startswith('#'):
                if ' = ' in line:
                    issues.append(f"📝 Line {line_num}: Remove spaces around '='")
                
                # Check for unquoted values with spaces
                if '=' in line:
                    key, value = line.split('=', 1)
                    if ' ' in value and not (value.startswith('"') or value.startswith("'")):
                        issues.append(f"📝 Line {line_num}: Quote value with spaces")
        
        # Check file ending
        if not content.endswith('\n'):
            issues.append("📝 File should end with newline")
        
        return issues
    
    def validate_file(self, file_path: Path) -> Tuple[List[str], List[str], List[str]]:
        """Validate a single environment file."""
        env_vars = self.parse_env_file(file_path)
        
        # Collect all issues
        security_issues = []
        security_issues.extend(self.check_sensitive_keys(env_vars, file_path))
        security_issues.extend(self.check_required_keys(env_vars, file_path))
        security_issues.extend(self.check_security_patterns(env_vars, file_path))
        
        format_issues = self.check_format_and_style(file_path)
        
        # Warnings (non-blocking)
        warnings = []
        
        # Check for too many variables (might indicate config bloat)
        if len(env_vars) > 50:
            warnings.append(f"📊 Large number of variables ({len(env_vars)})")
        
        # Check for duplicate-looking keys
        keys = list(env_vars.keys())
        for i, key1 in enumerate(keys):
            for key2 in keys[i+1:]:
                if key1.lower().replace('_', '') == key2.lower().replace('_', ''):
                    warnings.append(f"🔄 Similar keys found: '{key1}' and '{key2}'")
        
        return security_issues, format_issues, warnings


def main():
    """Main function to validate environment files."""
    if len(sys.argv) < 2:
        print("Usage: validate_env.py <env_file1> [env_file2] ...", file=sys.stderr)
        sys.exit(1)
    
    validator = EnvValidator()
    exit_code = 0
    total_files = 0
    total_issues = 0
    
    for file_arg in sys.argv[1:]:
        file_path = Path(file_arg)
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            exit_code = 1
            continue
        
        total_files += 1
        print(f"\n🔍 Validating {file_path}:")
        
        security_issues, format_issues, warnings = validator.validate_file(file_path)
        
        # Report security issues (blocking)
        if security_issues:
            print("  🚨 Security Issues:")
            for issue in security_issues:
                print(f"    {issue}")
                total_issues += 1
            exit_code = 1
        
        # Report format issues (blocking)
        if format_issues:
            print("  📝 Format Issues:")
            for issue in format_issues:
                print(f"    {issue}")
                total_issues += 1
            exit_code = 1
        
        # Report warnings (non-blocking)
        if warnings:
            print("  ⚠️  Warnings:")
            for warning in warnings:
                print(f"    {warning}")
        
        if not security_issues and not format_issues and not warnings:
            print("  ✅ File is valid")
    
    # Summary
    print(f"\n📊 Validation Summary:")
    print(f"  Files checked: {total_files}")
    print(f"  Issues found: {total_issues}")
    
    if exit_code == 0:
        print("✅ All environment files are valid")
    else:
        print("❌ Some environment files have issues that need to be fixed")
        print("\n💡 Tips:")
        print("  - Use strong, unique values for sensitive keys")
        print("  - Quote values that contain spaces")
        print("  - Avoid hardcoded paths and credentials")
        print("  - Enable HTTPS and secure settings for production")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()