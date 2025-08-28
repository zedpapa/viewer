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
    Extracts metadata for a video.
    Returns a tuple: (info_dict, error_string).
    On success, error_string is None. On failure, info_dict is None.
    """
    if not os.path.exists(filepath):
        return None, f"File does not exist: {filepath}"

    info = {"filepath": filepath, "filename": os.path.basename(filepath)}

    try:
        info["filesize_bytes"] = os.path.getsize(filepath)
        info["filesize_str"] = get_human_readable_size(info["filesize_bytes"])
    except OSError as e:
        return None, f"Could not get filesize for {info['filename']}: {e}"

    cap = None
    try:
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            return None, f"Could not open video file: {info['filename']}"

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps > 0 and frame_count > 0:
            duration_seconds = frame_count / fps
            hours = int(duration_seconds / 3600)
            minutes = int((duration_seconds % 3600) / 60)
            seconds = int(duration_seconds % 60)
            info["duration_str"] = f"{hours:02}:{minutes:02}:{seconds:02}"
            info["duration_seconds"] = duration_seconds
        else:
            info["duration_str"] = "N/A"
            info["duration_seconds"] = 0
    except Exception as e:
        return None, f"Error reading duration from {info['filename']}: {e}"
    finally:
        if cap:
            cap.release()

    thumbnail_path, error = create_thumbnail(filepath)
    if error:
        # We might still want to display the video even if thumbnail fails
        print(f"Thumbnail generation warning for {info['filename']}: {error}")
        info["thumbnail_path"] = None
    else:
        info["thumbnail_path"] = thumbnail_path

    return info, None

def create_thumbnail(filepath):
    """
    Creates a thumbnail for a video file and saves it to the cache.
    Returns a tuple: (thumbnail_path, error_string).
    """
    if not os.path.exists(THUMBNAIL_CACHE_DIR):
        try:
            os.makedirs(THUMBNAIL_CACHE_DIR)
        except OSError as e:
            return None, f"Could not create cache directory: {e}"

    h = hashlib.md5(filepath.encode()).hexdigest()
    thumbnail_filename = f"{h}.jpg"
    thumbnail_path = os.path.join(THUMBNAIL_CACHE_DIR, thumbnail_filename)

    if os.path.exists(thumbnail_path):
        return thumbnail_path, None

    cap = None
    try:
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            return None, "OpenCV could not open the video file."

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count <= 0:
            return None, "Video has no frames."

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)
        ret, frame = cap.read()
        if not ret:
            return None, "Failed to read frame from video."

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img.thumbnail(THUMBNAIL_SIZE)
        img.save(thumbnail_path, "JPEG")

        return thumbnail_path, None
    except Exception as e:
        return None, f"An unexpected error occurred: {e}"
    finally:
        if cap:
            cap.release()
