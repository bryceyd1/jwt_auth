#!/usr/bin/env python3
"""
JWT Auth Diagnostic Script
Run this to identify potential issues with the JWT Auth app configuration
"""

import sys
import os
import json

def check_file_structure():
    """Check if all required files exist"""
    required_files = [
        'jwt_auth/__init__.py',
        'jwt_auth/hooks.py',
        'jwt_auth/auth.py',
        'jwt_auth/providers.py',
        'jwt_auth/install.py',
        'jwt_auth/boot.py',
        'jwt_auth/modules.txt',
        'jwt_auth/patches.txt',
        'jwt_auth/jwt_auth/__init__.py',
        'jwt_auth/jwt_auth/doctype/__init__.py',
        'jwt_auth/jwt_auth/doctype/jwt_auth_settings/__init__.py',
        'jwt_auth/jwt_auth/doctype/jwt_auth_settings/jwt_auth_settings.json',
        'jwt_auth/jwt_auth/doctype/jwt_auth_settings/jwt_auth_settings.py',
        'jwt_auth/jwt_auth/doctype/jwt_auth_settings/jwt_auth_settings.js',
        'jwt_auth/public/js/app.bundle.js',
        'jwt_auth/patches/__init__.py',
        'jwt_auth/patches/set_default_provider.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    else:
        print("✅ All required files present")
        return True

def check_doctype_definition():
    """Check the JWT Auth Settings DocType definition"""
    try:
        with open('jwt_auth/jwt_auth/doctype/jwt_auth_settings/jwt_auth_settings.json', 'r') as f:
            doctype_def = json.load(f)
        
        # Check required properties
        required_props = ['doctype', 'module', 'issingle', 'fields']
        missing_props = [prop for prop in required_props if prop not in doctype_def]
        
        if missing_props:
            print(f"❌ DocType definition missing properties: {missing_props}")
            return False
        
        # Check if provider field exists
        fields = doctype_def.get('fields', [])
        provider_field = next((f for f in fields if f.get('fieldname') == 'provider'), None)
        
        if not provider_field:
            print("❌ Provider field missing from DocType definition")
            return False
        
        print("✅ DocType definition looks correct")
        return True
        
    except Exception as e:
        print(f"❌ Error checking DocType definition: {e}")
        return False

def check_hooks_configuration():
    """Check hooks.py configuration"""
    try:
        hooks_content = open('jwt_auth/hooks.py', 'r').read()
        
        required_vars = ['app_name', 'app_title', 'app_version']
        missing_vars = []
        
        for var in required_vars:
            if var not in hooks_content:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ hooks.py missing variables: {missing_vars}")
            return False
        
        print("✅ hooks.py configuration looks correct")
        return True
        
    except Exception as e:
        print(f"❌ Error checking hooks configuration: {e}")
        return False

def main():
    print("JWT Auth Diagnostic Report")
    print("=" * 40)
    
    checks = [
        check_file_structure,
        check_doctype_definition,
        check_hooks_configuration
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All checks passed! The app structure looks correct.")
        print("\nIf you're still experiencing the sidebar error, try:")
        print("1. Restart your bench (bench restart)")
        print("2. Clear cache (bench --site [site-name] clear-cache)")
        print("3. Migrate (bench --site [site-name] migrate)")
    else:
        print("❌ Some issues found. Please fix the above problems and try again.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
