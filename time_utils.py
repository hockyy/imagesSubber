"""
Time utility functions for video timeline processing.
Handles conversion between different time formats.
"""


def time_to_seconds(time_str: str) -> float:
    """
    Convert HH:MM:SS,mmm or HH:MM:SS.mmm to seconds.
    
    Args:
        time_str: Time string in HH:MM:SS,mmm or HH:MM:SS.mmm format
        
    Returns:
        Time in seconds as float
    """
    time_str = time_str.replace(',', '.')
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds_parts = parts[2].split('.')
    seconds = int(seconds_parts[0])
    milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
    
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
    return total_seconds


def seconds_to_fcpxml_time(seconds: float) -> str:
    """
    Convert seconds to FCPXML time format (rational number).
    
    Args:
        seconds: Time in seconds
        
    Returns:
        FCPXML time format string
    """
    # FCPXML uses rational time: numerator/denominator
    # Common timebase is 1001/30000s for 29.97fps or 1/25s for 25fps
    # We'll use 1/1000s for millisecond precision
    numerator = int(seconds * 1000)
    return f"{numerator}/1000s"


def seconds_to_frames(seconds: float, fps: int = 24) -> int:
    """
    Convert seconds to frames.
    
    Args:
        seconds: Time in seconds
        fps: Frames per second (default: 24)
        
    Returns:
        Number of frames
    """
    return int(seconds * fps)


def time_range_to_offset_duration(start_seconds: float, end_seconds: float, fps: int = 24) -> tuple:
    """
    Convert [start, end] time range to (offset_frames, duration_frames).
    
    Args:
        start_seconds: Start time in seconds
        end_seconds: End time in seconds
        fps: Frames per second (default: 24)
        
    Returns:
        Tuple of (offset_frames, duration_frames)
    """
    start_frames = seconds_to_frames(start_seconds, fps)
    end_frames = seconds_to_frames(end_seconds, fps)
    duration_frames = end_frames - start_frames
    return start_frames, duration_frames
