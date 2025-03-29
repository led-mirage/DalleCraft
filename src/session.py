# DalleCraft
#
# Copyright (c) 2025 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

import json
import os
from datetime import datetime

LOG_DIR = "logs"


class SessionEntry:
    def __init__(self, prompt, revised_prompt, api_type, model_name, image_size, image_quality, success, elapsed_time, image_filename, thumbnail_filename, error_info=None, timestamp=None):
        self.id = 0
        self.timestamp = datetime.now() if timestamp is None else timestamp
        self.prompt = prompt
        self.revised_prompt = revised_prompt
        self.api_type = api_type
        self.model_name = model_name
        self.image_size = image_size
        self.image_quality = image_quality
        self.success = success
        self.elapsed_time = elapsed_time
        self.image_filename = image_filename
        self.thumbnail_filename = thumbnail_filename
        self.error_info = error_info

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "prompt": self.prompt,
            "revised_prompt": self.revised_prompt,
            "api_type": self.api_type,
            "model_name": self.model_name,
            "image_size": self.image_size,
            "image_quality": self.image_quality,
            "success": self.success,
            "elapsed_time": self.elapsed_time,
            "image_filename": self.image_filename,
            "thumbnail_filename": self.thumbnail_filename,
            "error_info": self.error_info
        }

    @classmethod
    def from_dict(cls, data):
        entry = cls(
            prompt=data["prompt"],
            revised_prompt=data["revised_prompt"],
            api_type=data.get("api_type", ""),
            model_name=data.get("model_name", ""),
            image_size=data.get("image_size", ""),
            image_quality=data.get("image_quality", ""),
            success=data["success"],
            elapsed_time=data.get("elapsed_time", 0.0),
            image_filename=data.get("image_filename", ""),
            thumbnail_filename=data.get("thumbnail_filename", ""),
            error_info=data["error_info"],
        )
        entry.id = data.get("id", 0)
        entry.timestamp = datetime.fromisoformat(data["timestamp"])
        return entry


class Session:
    FILE_VERSION = "1.0"

    def __init__(self):
        self.session_name = ""
        self.entries = []
        self.created_at = datetime.now()
        self.saved_at = None
        self.logfile_name = f"Session_{self.created_at.strftime('%Y%m%d_%H%M%S')}.json"
        self.next_entry_id = 1

    def find_entry(self, entry_id):
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None

    def add_entry(self, entry):
        entry.id = self.next_entry_id
        self.next_entry_id += 1
        self.entries.append(entry)

    def remove_entry(self, entry_id):
        entry = self.find_entry(entry_id)
        if entry is not None:
            self.entries.remove(entry)

    def save_to_file(self):
        self.saved_at = datetime.now()
        data = {
            "version": self.FILE_VERSION,
            "session_name": self.session_name,
            "created_at": self.created_at.isoformat(),
            "saved_at": self.saved_at.isoformat(),
            "next_entry_id": self.next_entry_id,
            "entries": [entry.to_dict() for entry in self.entries]
        }

        try:
            if not os.path.isdir(LOG_DIR):
                os.mkdir(LOG_DIR)

            path = os.path.join(LOG_DIR, self.logfile_name)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"ファイル保存エラー: {str(e)}")
            return False

    @classmethod
    def load_from_file(cls, filename):
        try:
            path = os.path.join(LOG_DIR, filename)
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # バージョンチェック
            file_version = data.get("version", "unknown")
            if file_version != cls.FILE_VERSION:
                print(f"警告: ファイルバージョンが異なります (ファイル: {file_version}, 現行: {cls.FILE_VERSION})")
                # ここに必要に応じてバージョン互換性のための変換処理を追加

            session = cls()
            session.logfile_name = filename
            session.session_name = data["session_name"]
            session.created_at = datetime.fromisoformat(data["created_at"])
            session.saved_at = datetime.fromisoformat(data["saved_at"])
            session.next_entry_id = data["next_entry_id"]

            # エントリの読み込み
            for entry_data in data["entries"]:
                entry = SessionEntry.from_dict(entry_data)
                session.entries.append(entry)

            return session

        except json.JSONDecodeError:
            print("JSONデコードエラー: ファイル形式が正しくありません")
            return None
        except Exception as e:
            print(f"ファイル読み込みエラー: {str(e)}")
            return None


class SessionManager:
    def __init__(self):
        self.current_session = None

    def create_new_session(self, name=None):
        self.current_session = Session()
        return self.current_session

    def get_current_session(self):
        return self.current_session

    def next_session(self):
        logfiles = self.get_logfiles()
        if self.current_session.logfile_name in logfiles:
            index = logfiles.index(self.current_session.logfile_name)
            if index < len(logfiles) - 1:
                session = Session.load_from_file(logfiles[index + 1])
                self.current_session = session
                return session
            else:
                return None
        else:
            return None

    def previous_session(self):
        logfiles = self.get_logfiles()
        if self.current_session.logfile_name in logfiles:
            index = logfiles.index(self.current_session.logfile_name)
            if index > 0:
                session = Session.load_from_file(logfiles[index - 1])
                self.current_session = session
                return session
            else:
                return None
        else:
            if len(logfiles) > 0:
                session = Session.load_from_file(logfiles[-1])
                self.current_session = session
                return session
            else:
                return None

    def delete_current_session(self):
        if self.current_session is not None:
            log_path = os.path.join(LOG_DIR, self.current_session.logfile_name)
            if os.path.exists(log_path):
                os.remove(log_path)
            self.current_session = self.create_new_session()
        return self.current_session

    def get_logfiles(self) -> list[str]:
        if not os.path.isdir(LOG_DIR):
            return []
        files = os.listdir(LOG_DIR)
        files = [f for f in files if f.startswith("Session_") and f.endswith(".json")]
        files_sorted = sorted(files, key=lambda x: os.path.getmtime(os.path.join(LOG_DIR, x)), reverse=False)
        return files_sorted
