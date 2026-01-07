#!/usr/bin/env python3
"""
Check for TODO/FIXME comments in production code.
This script is used by pre-commit hooks to ensure code quality.
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple


def find_todos_fixmes(file_path: Path) -> List[Tuple[int, str, str]]:
    """Find TODO and FIXME comments in a Python file.
    
    Returns:
        List of tuples: (line_number, comment_type, comment_text)
    """
    results = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        # Skip binary files
        return results
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return results
    
    # Patterns to match TODO and FIXME comments
    patterns = [
        (r'#\s*(TODO|FIXME|XXX|HACK)\b', 'comment'),
        (r'"""\s*(TODO|FIXME|XXX|HACK)\b', 'docstring'),
        (r"'''\s*(TODO|FIXME|XXX|HACK)\b", 'docstring'),
    ]
    
    for line_num, line in enumerate(lines, 1):
        line_stripped = line.strip()
        
        # Skip empty lines and pure comment lines in test files
        if not line_stripped or line_stripped.startswith('#'):
            continue
            
        for pattern, comment_type in patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                keyword = match.group(1).upper()
                # Extract the rest of the comment
                comment_start = match.end()
                comment_text = line[comment_start:].strip(' :')
                
                results.append((line_num, keyword, comment_text))
    
    return results


def is_allowed_todo(file_path: Path, line_num: int, keyword: str, comment: str) -> bool:
    """Check if a TODO/FIXME is allowed based on project rules."""
    
    # Allow TODOs in specific contexts
    allowed_contexts = [
        # Development and documentation
        'README', 'CHANGELOG', 'CONTRIBUTING',
        # Configuration files
        '.pre-commit', 'pyproject.toml', '.github',
        # Example and template files
        'example', 'template', 'sample',
    ]
    
    file_str = str(file_path).lower()
    if any(context in file_str for context in allowed_contexts):
        return True
    
    # Allow TODOs with issue references
    if re.search(r'#\d+|issue|ticket|jira', comment, re.IGNORECASE):
        return True
    
    # Allow TODOs with specific dates or versions
    if re.search(r'\d{4}-\d{2}-\d{2}|v\d+\.\d+|version', comment, re.IGNORECASE):
        return True
    
    # Allow specific documented TODOs
    allowed_todos = [
        'optimization',
        'performance',
        'caching',
        'monitoring',
        'logging',
        'documentation',
        'testing',
        'error handling',
        'validation',
        'security',
    ]
    
    comment_lower = comment.lower()
    if any(allowed in comment_lower for allowed in allowed_todos):
        return True
    
    # Strict mode for production code
    return False


def main():
    """Main function to check files passed as arguments."""
    if len(sys.argv) < 2:
        print("Usage: check_todos.py <file1> [file2] ...", file=sys.stderr)
        sys.exit(1)
    
    exit_code = 0
    total_issues = 0
    
    for file_arg in sys.argv[1:]:
        file_path = Path(file_arg)
        
        # Skip non-Python files
        if file_path.suffix != '.py':
            continue
            
        # Skip test files, migration files, and other excluded patterns
        excluded_patterns = [
            'test_', '_test.py', '/tests/', '/migrations/',
            'conftest.py', 'setup.py', '__init__.py'
        ]
        
        if any(pattern in str(file_path) for pattern in excluded_patterns):
            continue
        
        todos_fixmes = find_todos_fixmes(file_path)
        
        if not todos_fixmes:
            continue
        
        print(f"\n📝 Found TODO/FIXME comments in {file_path}:")
        
        for line_num, keyword, comment in todos_fixmes:
            total_issues += 1
            
            if is_allowed_todo(file_path, line_num, keyword, comment):
                status = "✅ ALLOWED"
                print(f"  Line {line_num}: {keyword}: {comment} ({status})")
            else:
                status = "❌ NOT ALLOWED"
                print(f"  Line {line_num}: {keyword}: {comment} ({status})")
                exit_code = 1
    
    if total_issues > 0:
        print(f"\n📊 Summary: Found {total_issues} TODO/FIXME comments")
        
        if exit_code != 0:
            print("\n⚠️  Some TODO/FIXME comments are not allowed in production code.")
            print("Please either:")
            print("1. Remove the TODO/FIXME and implement the functionality")
            print("2. Create an issue and reference it in the comment")
            print("3. Add a specific deadline or version number")
            print("4. Move the code to a development branch")
        else:
            print("✅ All TODO/FIXME comments are properly documented.")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()