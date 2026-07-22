import os
import importlib


def test_sqlite_crud_and_filters(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SQLITE_DB_DIR", str(tmp_path / "db"))
    import src.database.sqlite_manager as module
    module.SQLiteManager._instance = None
    manager = module.SQLiteManager()
    table = manager.transcriptions
    inserted = table.insert_one({"_id": "t1", "filename": "note.md", "raw_content": "hello"})
    assert inserted.inserted_id == "t1"
    assert table.find_one({"_id": "t1"})["filename"] == "note.md"
    assert table.count_documents({"filename": {"$regex": "note"}}) == 1
    table.update_one({"_id": "t1"}, {"$set": {"processed": 1}})
    assert table.find_one({"processed": {"$ne": 0}})["processed"] == 1
    assert list(table.find({"$or": [{"filename": "none"}, {"_id": "t1"}]}).limit(1))[0]["_id"] == "t1"
    assert table.delete_one({"_id": "t1"}).deleted_count == 1
    assert table.find_one({"_id": "t1"}) is None
    manager.close()
    module.SQLiteManager._instance = None


def test_segments_and_cursor_operations(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SQLITE_DB_DIR", str(tmp_path / "db"))
    import src.database.sqlite_manager as module
    module.SQLiteManager._instance = None
    manager = module.SQLiteManager()
    manager.transcriptions.insert_one({"_id": "t1", "filename": "n", "raw_content": ""})
    segments = manager.segments
    assert segments.insert_many([{"_id": "s1", "transcription_id": "t1", "content": "a", "sequence": 1}, {"_id": "s2", "transcription_id": "t1", "content": "b", "sequence": 2}]) == 2
    rows = segments.find({"transcription_id": "t1"}).sort("sequence", 1).limit(1)
    assert list(rows)[0]["content"] == "a"
    assert segments.find_one({"_id": "s1"})["_id"] == "s1"
    assert segments.delete_many({"transcription_id": "t1"}).deleted_count == 2
    manager.close()
    module.SQLiteManager._instance = None
