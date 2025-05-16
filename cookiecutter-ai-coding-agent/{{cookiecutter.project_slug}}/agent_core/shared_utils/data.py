from collections import Counter

def count_video_views(events):
    """Count video views by video ID."""
    return Counter(event['videoid'] for event in events if 'videoid' in event)

def validate_file_format(uploaded_file):
    """Validate CSV has required columns."""
    try:
        df = pd.read_csv(uploaded_file)
        return all(col in df.columns for col in ['videoid', 'videotitle', 'authorid'])
    except Exception:
        return False

def process_events(uploaded_file, config):
    """Process uploaded file and return results."""
    df = pd.read_csv(uploaded_file)
    return count_video_views(df.to_dict('records'))

