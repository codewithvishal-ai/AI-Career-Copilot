import os
import re
from datetime import datetime, timezone


_client = None
_client_configuration = None
_users_index_configuration = None
_users_migrated_configuration = None


def _collection():
    global _client, _client_configuration

    uri = os.getenv("MONGODB_URI", "").strip()
    if not uri:
        raise RuntimeError("MONGODB_URI must be configured to use application data.")

    database_name = os.getenv("MONGODB_DATABASE", "ai_career_copilot").strip()
    configuration = (uri, database_name)

    try:
        from pymongo import MongoClient
    except ImportError as error:
        raise RuntimeError(
            "MONGODB_URI is set, but pymongo is not installed. "
            "Install backend/requirements.txt."
        ) from error

    if _client is None or _client_configuration != configuration:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _client_configuration = configuration

    return _client[database_name]["app_data"]


def ping_database():
    _collection().database.command("ping")


def _users_collection():
    global _users_index_configuration, _users_migrated_configuration

    app_data = _collection()
    database_name = _client_configuration[1]
    users = _client[database_name]["users"]

    if _users_index_configuration != _client_configuration:
        users.create_index("username_key", unique=True)
        _users_index_configuration = _client_configuration

    if _users_migrated_configuration != _client_configuration:
        legacy_users = app_data.find_one({"_id": "users"}, {"data": 1})
        if legacy_users:
            for user in legacy_users.get("data", []):
                if not isinstance(user, dict):
                    continue

                username = str(user.get("name", "")).strip()
                password = str(user.get("password", ""))
                if not username or not password:
                    continue

                users.update_one(
                    {"username_key": username.casefold()},
                    {
                        "$setOnInsert": {
                            "name": username,
                            "username_key": username.casefold(),
                            "password": password,
                        }
                    },
                    upsert=True,
                )

            app_data.delete_one({"_id": "users"})

        _users_migrated_configuration = _client_configuration

    return users


def find_user(username):
    username_key = str(username).strip().casefold()
    if not username_key:
        return None
    return _users_collection().find_one({"username_key": username_key})


def create_user(username, password_hash):
    from pymongo.errors import DuplicateKeyError

    username = str(username).strip()
    username_key = username.casefold()
    try:
        _users_collection().insert_one({
            "name": username,
            "username_key": username_key,
            "password": password_hash,
        })
    except DuplicateKeyError:
        return False
    return True


def update_user_password(username, password_hash):
    username_key = str(username).strip().casefold()
    _users_collection().update_one(
        {"username_key": username_key},
        {"$set": {"password": password_hash}},
    )


def load_dataset(file_path, default):
    collection = _collection()
    dataset_id = os.path.splitext(os.path.basename(file_path))[0]
    record = collection.find_one({"_id": dataset_id}, {"data": 1})
    return record.get("data", default) if record else default


def save_dataset(file_path, data):
    collection = _collection()
    dataset_id = os.path.splitext(os.path.basename(file_path))[0]
    collection.replace_one(
        {"_id": dataset_id},
        {
            "_id": dataset_id,
            "data": data,
            "updated_at": datetime.now(timezone.utc),
        },
        upsert=True,
    )


def load_record(record_type, record_id):
    document_id = f"{record_type}:{record_id}"
    record = _collection().find_one({"_id": document_id}, {"data": 1})
    return record.get("data") if record else None


def save_record(record_type, record_id, data):
    document_id = f"{record_type}:{record_id}"
    _collection().replace_one(
        {"_id": document_id},
        {
            "_id": document_id,
            "data": data,
            "updated_at": datetime.now(timezone.utc),
        },
        upsert=True,
    )


def load_records(record_type, field=None, value=None):
    prefix = re.escape(f"{record_type}:")
    query = {"_id": {"$regex": f"^{prefix}"}}
    if field and value is not None:
        query[f"data.{field}"] = {
            "$regex": f"^{re.escape(str(value))}$",
            "$options": "i",
        }

    records = _collection().find(
        query,
        {"data": 1},
    )
    return [record["data"] for record in records if "data" in record]