from collections import defaultdict

_sessions = defaultdict(list)

def get_session(session_id):
    return _sessions.get(session_id, [])

def add_message(session_id, messages):
    _sessions[session_id] = messages
