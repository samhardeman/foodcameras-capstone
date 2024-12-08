import sqlite3
import os

DB_FILE = './database/people_data.db'

def initialize_database():
    """Initialize the SQLite database with the required tables."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            longitude REAL NOT NULL,
            latitude REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            level TEXT,
            people_count INTEGER,
            image TEXT,
            FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def clear_database():
    """Clear all tables in the database."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print("Database cleared successfully.")
    else:
        print("No database file found to clear.")
    initialize_database()

def add_location(friendly_name, latitude, longitude, group_id=None):
    """Add a new location to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO locations (friendly_name, latitude, longitude, group_id) 
        VALUES (?, ?, ?, ?)
    ''', (friendly_name, latitude, longitude, group_id))
    conn.commit()
    conn.close()
    print(f"Location '{friendly_name}' added successfully.")

def add_location_group(friendly_name):
    """Add a new location group to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO location_groups (friendly_name) 
        VALUES (?)
    ''', (friendly_name,))
    conn.commit()
    conn.close()
    print(f"Location group '{friendly_name}' added successfully.")

def group_cameras(group_id, location_ids):
    """Group cameras from multiple locations under a single group."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for location_id in location_ids:
        cursor.execute('UPDATE locations SET group_id = ? WHERE id = ?', (group_id, location_id))
    conn.commit()
    conn.close()
    print(f"Cameras grouped under group ID {group_id}.")

def modify_location_name(location_id, new_name):
    """Update the friendly name of a location."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE locations SET friendly_name = ? WHERE id = ?', (new_name, location_id))
    conn.commit()
    conn.close()
    print(f"Location ID {location_id} name updated to '{new_name}'.")

def modify_location_coordinates(location_id, latitude, longitude):
    """Update the latitude and longitude of a location."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE locations SET latitude = ?, longitude = ? WHERE id = ?', (latitude, longitude, location_id))
    conn.commit()
    conn.close()
    print(f"Location ID {location_id} coordinates updated to ({latitude}, {longitude}).")

def view_database_entries():
    """View all database entries: locations, groups, and cameras."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # View location groups
    print("\nLocation Groups:")
    cursor.execute('SELECT * FROM location_groups')
    groups = cursor.fetchall()
    for group in groups:
        print(f"Group ID: {group[0]}, Friendly Name: {group[1]}")

    # View locations
    print("\nLocations:")
    cursor.execute('SELECT * FROM locations')
    locations = cursor.fetchall()
    for location in locations:
        print(f"Location ID: {location[0]}, Friendly Name: {location[1]}, Coordinates: ({location[2]}, {location[3]}), Group ID: {location[4]}")

    # View cameras
    print("\nCameras:")
    cursor.execute('SELECT * FROM cameras')
    cameras = cursor.fetchall()
    for camera in cameras:
        print(f"Camera ID: {camera[0]}, Location ID: {camera[1]}, Description: {camera[2]}, URL: {camera[3]}")

    conn.close()

def main():
    """CLI for managing the database."""
    initialize_database()
    print("Welcome to the Database Manager CLI.")
    
    while True:
        print("\nCommands:")
        print("1. Clear database (dangerous)")
        print("2. Add new location")
        print("3. Add new location group")
        print("4. Group cameras")
        print("5. Modify location name")
        print("6. Modify location coordinates")
        print("7. View database entries")
        print("8. Exit")
        
        choice = input("Enter command number: ").strip()
        
        if choice == "1":
            confirm = input("Are you sure you want to clear the database? (yes/no): ").strip().lower()
            if confirm == "yes":
                clear_database()
            else:
                print("Operation cancelled.")
        
        elif choice == "2":
            friendly_name = input("Enter friendly name: ").strip()
            latitude = float(input("Enter latitude: ").strip())
            longitude = float(input("Enter longitude: ").strip())
            add_location(friendly_name, latitude, longitude)
        
        elif choice == "3":
            friendly_name = input("Enter group friendly name: ").strip()
            add_location_group(friendly_name)
        
        elif choice == "4":
            group_id = int(input("Enter group ID: ").strip())
            location_ids = input("Enter location IDs to group (comma-separated): ").strip()
            location_ids = [int(loc_id) for loc_id in location_ids.split(",")]
            group_cameras(group_id, location_ids)
        
        elif choice == "5":
            location_id = int(input("Enter location ID: ").strip())
            new_name = input("Enter new friendly name: ").strip()
            modify_location_name(location_id, new_name)
        
        elif choice == "6":
            location_id = int(input("Enter location ID: ").strip())
            latitude = float(input("Enter new latitude: ").strip())
            longitude = float(input("Enter new longitude: ").strip())
            modify_location_coordinates(location_id, latitude, longitude)
        
        elif choice == "7":
            view_database_entries()
        
        elif choice == "8":
            print("Exiting Database Manager CLI. Goodbye!")
            break
        
        else:
            print("Invalid command. Please try again.")

if __name__ == "__main__":
    main()
