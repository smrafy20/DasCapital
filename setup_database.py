#!/usr/bin/env python3
"""
Database setup script for DashCapital
Run this script to create the database and tables
"""

import pymysql
from app import app, db, User
from werkzeug.security import generate_password_hash
from decimal import Decimal

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to MySQL server (without specifying database)
        # Update these credentials to match your MySQL installation
        connection = pymysql.connect(
            host='localhost',
            user='root',  # Your MySQL username (usually 'root')
            password='1234'  # Your MySQL root password
        )
        
        with connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS dashcapital")
            # Database created successfully
        
        connection.close()
        
    except Exception as e:
    # Error creating database
        return False
    
    return True

def create_tables():
    """Create all tables"""
    try:
        with app.app_context():
            db.create_all()
            # All tables created successfully
        return True
    except Exception as e:
    # Error creating tables
        return False

# def create_sample_users():
#     """No sample users - users will register themselves"""
#     print("ℹ️  No sample users created - users can register through the application")
#     return True

def main():
    # Setting up DashCapital Database
    
    # Step 1: Create database
    if not create_database():
        return
    
    # Step 2: Create tables
    if not create_tables():
        return
    
    # Step 3: Ready for user registration
    # No sample users created - users can register through the application

    # Database setup completed successfully
    # Next steps:
    # 1. Run the application: python app.py
    # 2. Open http://localhost:5000 in your browser
    # 3. Register your first user account
    # 4. Start using the money request features

if __name__ == '__main__':
    main()
