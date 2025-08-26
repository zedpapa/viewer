import unittest
import os
import sys

# Add the parent directory to the path so we can import the 'src' module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import Database

class TestDatabase(unittest.TestCase):

    def setUp(self):
        """ Set up a new in-memory database for each test. """
        self.db = Database(':memory:')

    def tearDown(self):
        """ Close the database connection after each test. """
        self.db.close()

    def test_initialization(self):
        """ Test that tables are created on initialization. """
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
        self.assertIsNotNone(cursor.fetchone())
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='labels'")
        self.assertIsNotNone(cursor.fetchone())
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_labels'")
        self.assertIsNotNone(cursor.fetchone())

    def test_get_or_create_video(self):
        """ Test getting and creating videos. """
        video_path1 = '/videos/movie1.mp4'
        video_id1 = self.db.get_or_create_video(video_path1)
        self.assertEqual(video_id1, 1)

        # Test getting the same video again
        video_id2 = self.db.get_or_create_video(video_path1)
        self.assertEqual(video_id2, 1)

        # Test creating a new video
        video_path2 = '/videos/movie2.mp4'
        video_id3 = self.db.get_or_create_video(video_path2)
        self.assertEqual(video_id3, 2)

    def test_get_or_create_label(self):
        """ Test getting and creating labels. """
        label_id1 = self.db.get_or_create_label('Genre')
        self.assertEqual(label_id1, 1)
        label_id2 = self.db.get_or_create_label('Genre')
        self.assertEqual(label_id2, 1)
        label_id3 = self.db.get_or_create_label('Rating')
        self.assertEqual(label_id3, 2)

    def test_add_and_get_video_labels(self):
        """ Test adding and retrieving labels for a video. """
        video_id = self.db.get_or_create_video('/vids/test.mkv')
        label_id_genre = self.db.get_or_create_label('Genre')
        label_id_rating = self.db.get_or_create_label('Rating')

        self.db.add_video_label(video_id, label_id_genre, 'Action')
        self.db.add_video_label(video_id, label_id_rating, '5 Stars')

        labels = self.db.get_labels_for_video(video_id)
        self.assertEqual(len(labels), 2)
        # Note: The order depends on the ORDER BY clause in the SQL query
        self.assertEqual(labels[0][1], 'Genre')
        self.assertEqual(labels[0][2], 'Action')
        self.assertEqual(labels[1][1], 'Rating')
        self.assertEqual(labels[1][2], '5 Stars')

    def test_remove_video_label(self):
        """ Test removing a label from a video. """
        video_id = self.db.get_or_create_video('a.mp4')
        label_id = self.db.get_or_create_label('Status')
        self.db.add_video_label(video_id, label_id, 'Watched')

        labels = self.db.get_labels_for_video(video_id)
        self.assertEqual(len(labels), 1)
        video_label_id = labels[0][0]

        self.db.remove_video_label(video_label_id)
        labels_after_remove = self.db.get_labels_for_video(video_id)
        self.assertEqual(len(labels_after_remove), 0)

    def test_get_all_unique_labels(self):
        """ Test retrieving all unique label names. """
        self.db.get_or_create_label('Apple')
        self.db.get_or_create_label('Banana')
        self.db.get_or_create_label('Cherry')

        unique_labels = self.db.get_all_unique_labels()
        self.assertEqual(unique_labels, ['Apple', 'Banana', 'Cherry'])

    def test_get_videos_for_label_name(self):
        """ Test retrieving videos associated with a label name. """
        vid1 = self.db.get_or_create_video('vid1.mp4')
        vid2 = self.db.get_or_create_video('vid2.mp4')
        vid3 = self.db.get_or_create_video('vid3.mkv')

        label_id_action = self.db.get_or_create_label('Action')
        label_id_comedy = self.db.get_or_create_label('Comedy')

        self.db.add_video_label(vid1, label_id_action, 'Yes')
        self.db.add_video_label(vid2, label_id_comedy, 'Yes')
        self.db.add_video_label(vid3, label_id_action, 'Yes')

        action_videos = self.db.get_videos_for_label_name('Action')
        self.assertIn('vid1.mp4', action_videos)
        self.assertIn('vid3.mkv', action_videos)
        self.assertEqual(len(action_videos), 2)

        comedy_videos = self.db.get_videos_for_label_name('Comedy')
        self.assertEqual(comedy_videos, ['vid2.mp4'])

    def test_update_video_filepath(self):
        """ Test updating a video's filepath. """
        old_path = '/movies/old_name.avi'
        new_path = '/movies/new_name.avi'

        # Create the initial record
        video_id1 = self.db.get_or_create_video(old_path)
        self.assertEqual(video_id1, 1)

        # Update the filepath
        self.db.update_video_filepath(old_path, new_path)

        # The old path should not resolve to the same ID anymore (it's gone)
        # and a new video with the old path would get a new ID
        video_id_old_after_update = self.db.get_or_create_video(old_path)
        self.assertNotEqual(video_id_old_after_update, video_id1)
        self.assertEqual(video_id_old_after_update, 2)

        # The new path should now resolve to the original ID
        video_id_new = self.db.get_or_create_video(new_path)
        self.assertEqual(video_id_new, 1)


if __name__ == '__main__':
    unittest.main()
