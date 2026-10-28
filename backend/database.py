import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = "labfind.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    """)

    # Equipment table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            room TEXT NOT NULL,
            status TEXT DEFAULT 'Available',
            description TEXT
        )
    """)

    # Bookings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            equipment_id INTEGER NOT NULL,
            booking_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            purpose TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (equipment_id) REFERENCES equipment(id)
        )
    """)

    # Favorites table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            equipment_id INTEGER NOT NULL,
            UNIQUE(user_id, equipment_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (equipment_id) REFERENCES equipment(id)
        )
    """)

    # Rooms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name TEXT NOT NULL,
            lab_name TEXT NOT NULL,
            description TEXT
        )
    """)

    # Create default users
    admin_password = generate_password_hash("admin123")
    user_password = generate_password_hash("user123")

    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, role)
        VALUES (?, ?, ?)
    """, ("admin", admin_password, "admin"))

    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, role)
        VALUES (?, ?, ?)
    """, ("student", user_password, "user"))

    # Add sample equipment
    equipment_data = [
        (
            "Digital Microscope",
            "Microscope",
            "Lab 101",
            "Available",
            "High-resolution digital microscope for laboratory observation."
        ),
        (
            "Oscilloscope",
            "Electronics",
            "Lab 102",
            "Available",
            "Digital oscilloscope for measuring electrical signals."
        ),
        (
            "Centrifuge Machine",
            "Biotechnology",
            "Lab 103",
            "In Use",
            "Laboratory centrifuge for separating samples."
        ),
        (
            "Digital Multimeter",
            "Electronics",
            "Lab 102",
            "Available",
            "Digital multimeter for electrical measurements."
        ),
        (
            "Spectrophotometer",
            "Chemistry",
            "Lab 104",
            "Maintenance",
            "Instrument used for measuring light absorption."
        )
    ]

    cursor.executemany("""
        INSERT INTO equipment
        (name, category, room, status, description)
        SELECT ?, ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM equipment WHERE name = ?
        )
    """, [
        item + (item[0],)
        for item in equipment_data
    ])

    # Add sample rooms
    rooms_data = [
        (
            "Lab 101",
            "Physics Laboratory",
            "Laboratory for physics experiments and measurements."
        ),
        (
            "Lab 102",
            "Electronics Laboratory",
            "Laboratory containing electronic testing equipment."
        ),
        (
            "Lab 103",
            "Biotechnology Laboratory",
            "Laboratory for biotechnology and biological experiments."
        ),
        (
            "Lab 104",
            "Chemistry Laboratory",
            "Laboratory for chemistry experiments and analysis."
        )
    ]

    cursor.executemany("""
        INSERT INTO rooms (room_name, lab_name, description)
        SELECT ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM rooms WHERE room_name = ?
        )
    """, [
        item + (item[0],)
        for item in rooms_data
    ])

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")