import os
import cv2
import hashlib
from PIL import Image

THUMBNAIL_CACHE_DIR = ".thumbnail_cache"
THUMBNAIL_SIZE = (128, 72)

def get_human_readable_size(size_in_bytes):
    """Converts a size in bytes to a human-readable format."""
    if size_in_bytes is None:
        return "0 B"
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size_in_bytes >= power and n < len(power_labels):
        size_in_bytes /= power
        n += 1
    return f"{size_in_bytes:.2f} {power_labels[n]}B"

def get_video_info(filepath):
    """
    Extracts metadata (filesize, duration) and gets the thumbnail path for a video.
    """
    if not os.path.exists(filepath):
        return None

    try:
        filesize = os.path.getsize(filepath)

        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            return {"filesize": get_human_readable_size(filesize), "duration": "00:00:00", "thumbnail_path": None}

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        duration_seconds = frame_count / fps if fps > 0 else 0

        hours = int(duration_seconds / 3600)
        minutes = int((duration_seconds % 3600) / 60)
        seconds = int(duration_seconds % 60)
        duration_str = f"{hours:02}:{minutes:02}:{seconds:02}"

        cap.release()

        thumbnail_path = create_thumbnail(filepath)

        return {
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "filesize_str": get_human_readable_size(filesize),
            "duration_str": duration_str,
            "filesize_bytes": filesize,
            "duration_seconds": duration_seconds,
            "thumbnail_path": thumbnail_path
        }
    except Exception as e:
        print(f"Error processing video {filepath}: {e}")
        return None

def create_thumbnail(filepath):
    """
    Creates a thumbnail for a video file and saves it to the cache.
    Returns the path to the thumbnail.
    """
    if not os.path.exists(THUMBNAIL_CACHE_DIR):
        os.makedirs(THUMBNAIL_CACHE_DIR)

    # Create a unique filename based on the filepath hash
    h = hashlib.md5(filepath.encode()).hexdigest()
    thumbnail_filename = f"{h}.jpg"
    thumbnail_path = os.path.join(THUMBNAIL_CACHE_DIR, thumbnail_filename)

    if os.path.exists(thumbnail_path):
        return thumbnail_path

    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        return None

    try:
        # Get a frame from the middle of the video
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)

        ret, frame = cap.read()
        if not ret:
            return None

        # Convert from BGR (OpenCV) to RGB (Pillow)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)

        img.thumbnail(THUMBNAIL_SIZE)
        img.save(thumbnail_path, "JPEG")

        return thumbnail_path
    except Exception as e:
        print(f"Failed to create thumbnail for {filepath}: {e}")
        return None
    finally:
        cap.release()
