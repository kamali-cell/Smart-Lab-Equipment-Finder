from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import check_password_hash
import sqlite3
import os

app = Flask(__name__)

# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE = os.path.join(BASE_DIR, "labfind.db")

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required"
        }), 400

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    conn.close()

    if user and check_password_hash(user["password"], password):

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"]
            }
        })

    return jsonify({
        "success": False,
        "message": "Invalid username or password"
    }), 401


# =========================================================
# EQUIPMENT
# =========================================================

@app.route("/api/equipment", methods=["GET"])
def get_equipment():

    conn = get_db_connection()

    equipment = conn.execute(
        "SELECT * FROM equipment ORDER BY id"
    ).fetchall()

    conn.close()

    return jsonify([
        dict(item)
        for item in equipment
    ])


# =========================================================
# EQUIPMENT DETAILS
# =========================================================

@app.route("/api/equipment/<int:equipment_id>", methods=["GET"])
def get_equipment_details(equipment_id):

    conn = get_db_connection()

    equipment = conn.execute(
        "SELECT * FROM equipment WHERE id = ?",
        (equipment_id,)
    ).fetchone()

    conn.close()

    if equipment is None:

        return jsonify({
            "success": False,
            "message": "Equipment not found"
        }), 404

    return jsonify(dict(equipment))


# =========================================================
# SEARCH EQUIPMENT
# =========================================================

@app.route("/api/search", methods=["GET"])
def search_equipment():

    keyword = request.args.get("q", "")

    conn = get_db_connection()

    results = conn.execute("""
        SELECT *
        FROM equipment
        WHERE name LIKE ?
           OR category LIKE ?
           OR room LIKE ?
           OR status LIKE ?
    """, (
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%"
    )).fetchall()

    conn.close()

    return jsonify([
        dict(item)
        for item in results
    ])


# =========================================================
# ROOMS
# =========================================================

@app.route("/api/rooms", methods=["GET"])
def get_rooms():

    conn = get_db_connection()

    rooms = conn.execute(
        "SELECT * FROM rooms ORDER BY id"
    ).fetchall()

    conn.close()

    return jsonify([
        dict(room)
        for room in rooms
    ])


# =========================================================
# CREATE BOOKING
# =========================================================

@app.route("/api/bookings", methods=["POST"])
def create_booking():

    data = request.get_json()

    user_id = data.get("user_id")
    equipment_id = data.get("equipment_id")
    booking_date = data.get("booking_date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    purpose = data.get(
        "purpose",
        "Laboratory equipment usage"
    )

    if not all([
        user_id,
        equipment_id,
        booking_date,
        start_time,
        end_time
    ]):

        return jsonify({
            "success": False,
            "message": "Please fill all required booking fields"
        }), 400

    conn = get_db_connection()

    equipment = conn.execute(
        "SELECT status FROM equipment WHERE id = ?",
        (equipment_id,)
    ).fetchone()

    if equipment is None:

        conn.close()

        return jsonify({
            "success": False,
            "message": "Equipment not found"
        }), 404

    if equipment["status"] != "Available":

        conn.close()

        return jsonify({
            "success": False,
            "message": "Equipment is currently not available"
        }), 400

    conn.execute("""
        INSERT INTO bookings
        (
            user_id,
            equipment_id,
            booking_date,
            start_time,
            end_time,
            purpose,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        equipment_id,
        booking_date,
        start_time,
        end_time,
        purpose,
        "Pending"
    ))

    conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "message": "Booking created successfully"
    })


# =========================================================
# GET USER BOOKINGS
# =========================================================

@app.route("/api/bookings/<int:user_id>", methods=["GET"])
def get_user_bookings(user_id):

    conn = get_db_connection()

    bookings = conn.execute("""
        SELECT
            bookings.id,
            equipment.name AS equipment_name,
            equipment.room,
            bookings.booking_date,
            bookings.start_time,
            bookings.end_time,
            bookings.purpose,
            bookings.status
        FROM bookings
        JOIN equipment
        ON bookings.equipment_id = equipment.id
        WHERE bookings.user_id = ?
        ORDER BY bookings.id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return jsonify([
        dict(booking)
        for booking in bookings
    ])


# =========================================================
# FAVORITES - ADD
# =========================================================

@app.route("/api/favorites", methods=["POST"])
def add_favorite():

    data = request.get_json()

    user_id = data.get("user_id")
    equipment_id = data.get("equipment_id")

    if not user_id or not equipment_id:

        return jsonify({
            "success": False,
            "message": "User and equipment are required"
        }), 400

    conn = get_db_connection()

    try:

        conn.execute("""
            INSERT INTO favorites
            (
                user_id,
                equipment_id
            )
            VALUES (?, ?)
        """, (
            user_id,
            equipment_id
        ))

        conn.commit()

    except sqlite3.IntegrityError:

        conn.close()

        return jsonify({
            "success": False,
            "message": "Equipment already in favorites"
        }), 400

    conn.close()

    return jsonify({
        "success": True,
        "message": "Added to favorites"
    })


# =========================================================
# FAVORITES - REMOVE
# =========================================================

@app.route(
    "/api/favorites/<int:user_id>/<int:equipment_id>",
    methods=["DELETE"]
)
def delete_favorite(user_id, equipment_id):

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM favorites
        WHERE user_id = ?
        AND equipment_id = ?
    """, (
        user_id,
        equipment_id
    ))

    conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "message": "Removed from favorites"
    })


# =========================================================
# FAVORITES - GET
# =========================================================

@app.route(
    "/api/favorites/<int:user_id>",
    methods=["GET"]
)
def get_favorites(user_id):

    conn = get_db_connection()

    favorites = conn.execute("""
        SELECT
            equipment.id,
            equipment.name,
            equipment.category,
            equipment.room,
            equipment.status,
            equipment.description
        FROM favorites
        JOIN equipment
        ON favorites.equipment_id = equipment.id
        WHERE favorites.user_id = ?
    """, (user_id,)).fetchall()

    conn.close()

    return jsonify([
        dict(item)
        for item in favorites
    ])


# =========================================================
# ADMIN - ADD EQUIPMENT
# =========================================================

@app.route(
    "/api/admin/equipment",
    methods=["POST"]
)
def add_equipment():

    data = request.get_json()

    name = data.get("name")
    category = data.get("category")
    room = data.get("room")
    status = data.get(
        "status",
        "Available"
    )
    description = data.get(
        "description",
        ""
    )

    if not name or not category or not room:

        return jsonify({
            "success": False,
            "message": "Name, category and room are required"
        }), 400

    conn = get_db_connection()

    cursor = conn.execute("""
        INSERT INTO equipment
        (
            name,
            category,
            room,
            status,
            description
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        category,
        room,
        status,
        description
    ))

    conn.commit()

    new_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "success": True,
        "message": "Equipment added successfully",
        "equipment_id": new_id
    })


# =========================================================
# ADMIN - UPDATE EQUIPMENT
# =========================================================

@app.route(
    "/api/admin/equipment/<int:equipment_id>",
    methods=["PUT"]
)
def update_equipment(equipment_id):

    data = request.get_json()

    name = data.get("name")
    category = data.get("category")
    room = data.get("room")
    status = data.get("status")
    description = data.get("description")

    conn = get_db_connection()

    equipment = conn.execute(
        "SELECT * FROM equipment WHERE id = ?",
        (equipment_id,)
    ).fetchone()

    if equipment is None:

        conn.close()

        return jsonify({
            "success": False,
            "message": "Equipment not found"
        }), 404

    conn.execute("""
        UPDATE equipment
        SET
            name = ?,
            category = ?,
            room = ?,
            status = ?,
            description = ?
        WHERE id = ?
    """, (
        name,
        category,
        room,
        status,
        description,
        equipment_id
    ))

    conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "message": "Equipment updated successfully"
    })


# =========================================================
# ADMIN - DELETE EQUIPMENT
# =========================================================

@app.route(
    "/api/admin/equipment/<int:equipment_id>",
    methods=["DELETE"]
)
def delete_equipment(equipment_id):

    conn = get_db_connection()

    equipment = conn.execute(
        "SELECT * FROM equipment WHERE id = ?",
        (equipment_id,)
    ).fetchone()

    if equipment is None:

        conn.close()

        return jsonify({
            "success": False,
            "message": "Equipment not found"
        }), 404

    conn.execute(
        "DELETE FROM equipment WHERE id = ?",
        (equipment_id,)
    )

    conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "message": "Equipment deleted successfully"
    })


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    print("LabFind backend starting...")
    print("Open: http://127.0.0.1:5000")

    app.run(debug=True)