# dbc_manager.py
import cantools
import json

class DBCManager:
    def __init__(self):
        self.db = None

    def load_dbc(self, file_path):
        self.db = cantools.database.load_file(file_path)

    def dbc_to_symb(self, symb_file):
        if not self.db:
            return
        data = {}
        for msg in self.db.messages:
            data[msg.name] = {
                "id": msg.frame_id,
                "signals": [{ "name": s.name, "start": s.start, "length": s.length, "unit": s.unit } for s in msg.signals]
            }
        with open(symb_file, "w") as f:
            json.dump(data, f, indent=4)

    def symb_to_dbc(self, symb_file, dbc_file):
        with open(symb_file, "r") as f:
            data = json.load(f)
        messages = []
        for name, msg_info in data.items():
            messages.append(cantools.database.can.Message(name=name, frame_id=msg_info["id"], signals=[]))
        db = cantools.database.can.Database(messages=messages)
        cantools.database.dump_file(db, dbc_file)
