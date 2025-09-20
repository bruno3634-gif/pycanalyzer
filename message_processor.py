# message_processor.py
class MessageProcessor:
    def __init__(self, dbc_manager):
        self.dbc_manager = dbc_manager

    def decode_message(self, msg):
        if not self.dbc_manager.db:
            return {}
        try:
            return self.dbc_manager.db.decode_message(msg["id"], msg["data"])
        except Exception:
            return {}
