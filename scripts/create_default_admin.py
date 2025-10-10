"""
Script to create default admin user
"""
import sys
sys.path.append('..')

from auth.auth import create_default_admin

if __name__ == "__main__":
    create_default_admin()
    print("Default admin user setup complete!")
