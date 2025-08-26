import sqlite3

class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.create_tables()
        except sqlite3.Error as e:
            print(e)

    def create_tables(self):
        """ Create the necessary tables if they don't exist. """
        try:
            cursor = self.conn.cursor()
            # Table for videos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY,
                    filepath TEXT NOT NULL UNIQUE
                )
            """)

            # Table for labels (e.g., Genre, Rating)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS labels (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE
                )
            """)

            # Linking table for videos, labels, and their values
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_labels (
                    id INTEGER PRIMARY KEY,
                    video_id INTEGER,
                    label_id INTEGER,
                    value TEXT NOT NULL,
                    FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE,
                    FOREIGN KEY (label_id) REFERENCES labels (id) ON DELETE CASCADE
                )
            """)
            self.conn.commit()
            print("Database tables created or already exist.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def close(self):
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    def get_or_create_video(self, filepath):
        """ Get the ID of a video, creating a new record if it doesn't exist. """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM videos WHERE filepath = ?", (filepath,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            cursor.execute("INSERT INTO videos (filepath) VALUES (?)", (filepath,))
            self.conn.commit()
            return cursor.lastrowid

    def get_or_create_label(self, label_name):
        """ Get the ID of a label, creating a new record if it doesn't exist. """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM labels WHERE name = ?", (label_name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            cursor.execute("INSERT INTO labels (name) VALUES (?)", (label_name,))
            self.conn.commit()
            return cursor.lastrowid

    def add_video_label(self, video_id, label_id, value):
        """ Add a label and value to a video. """
        cursor = self.conn.cursor()
        # Check if this exact label-value pair already exists for this video
        cursor.execute("""
            SELECT id FROM video_labels
            WHERE video_id = ? AND label_id = ? AND value = ?
        """, (video_id, label_id, value))
        if cursor.fetchone():
            print("This label-value pair already exists for the video.")
            return

        cursor.execute(
            "INSERT INTO video_labels (video_id, label_id, value) VALUES (?, ?, ?)",
            (video_id, label_id, value)
        )
        self.conn.commit()
        print(f"Added label to video_id {video_id} with value '{value}'")

    def get_labels_for_video(self, video_id):
        """ Get all labels and their values for a given video. """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT vl.id, l.name, vl.value
            FROM video_labels vl
            JOIN labels l ON vl.label_id = l.id
            WHERE vl.video_id = ?
            ORDER BY l.name, vl.value
        """, (video_id,))
        return cursor.fetchall()

    def remove_video_label(self, video_label_id):
        """ Remove a specific label instance from a video. """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM video_labels WHERE id = ?", (video_label_id,))
        self.conn.commit()
        print(f"Removed video_label with id {video_label_id}")

    def get_all_unique_labels(self):
        """ Get all unique label names from the database. """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM labels ORDER BY name")
        return [row[0] for row in cursor.fetchall()]

    def get_videos_for_label_name(self, label_name):
        """ Get all video filepaths that have a specific label name. """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT v.filepath
            FROM videos v
            JOIN video_labels vl ON v.id = vl.video_id
            JOIN labels l ON vl.label_id = l.id
            WHERE l.name = ?
        """, (label_name,))
        return [row[0] for row in cursor.fetchall()]

    def update_video_filepath(self, old_filepath, new_filepath):
        """ Update the filepath of a video record. """
        cursor = self.conn.cursor()
        cursor.execute("UPDATE videos SET filepath = ? WHERE filepath = ?", (new_filepath, old_filepath))
        self.conn.commit()
        print(f"Updated filepath from {old_filepath} to {new_filepath}")
