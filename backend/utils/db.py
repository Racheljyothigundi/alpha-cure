"""utils/db.py - database connection manager with local dev fallback"""

import json
import os
from copy import deepcopy
from datetime import datetime
from threading import RLock

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

_client = None
_db = None


def _serialize_value(value):
    if isinstance(value, ObjectId):
        return {'__type__': 'objectid', 'value': str(value)}
    if isinstance(value, datetime):
        return {'__type__': 'datetime', 'value': value.isoformat()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_value(val) for key, val in value.items()}
    return value


def _deserialize_value(value):
    if isinstance(value, list):
        return [_deserialize_value(item) for item in value]
    if isinstance(value, dict):
        if value.get('__type__') == 'objectid':
            return ObjectId(value['value'])
        if value.get('__type__') == 'datetime':
            return datetime.fromisoformat(value['value'])
        return {key: _deserialize_value(val) for key, val in value.items()}
    return value


def _apply_projection(document, projection):
    if not projection:
        return deepcopy(document)

    # This app only uses exclusion projections.
    result = deepcopy(document)
    excluded = {key for key, val in projection.items() if val == 0}
    if excluded:
        for key in excluded:
            result.pop(key, None)
        return result

    included = {key for key, val in projection.items() if val}
    if not included:
        return result

    projected = {key: deepcopy(result[key]) for key in included if key in result}
    if projection.get('_id', 1) and '_id' in result:
        projected['_id'] = deepcopy(result['_id'])
    return projected


def _matches(document, query):
    if not query:
        return True

    for key, expected in query.items():
        actual = document.get(key)
        if isinstance(expected, dict):
            if '$in' in expected:
                if actual not in expected['$in']:
                    return False
            else:
                return False
        elif actual != expected:
            return False
    return True


class _InsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class _UpdateResult:
    def __init__(self, matched_count=0, modified_count=0, upserted_id=None):
        self.matched_count = matched_count
        self.modified_count = modified_count
        self.upserted_id = upserted_id


class LocalJsonCollection:
    def __init__(self, database, name):
        self.database = database
        self.name = name

    def create_index(self, *args, **kwargs):
        return None

    def find_one(self, query=None, projection=None):
        for document in self.database._get_collection(self.name):
            if _matches(document, query):
                return _apply_projection(document, projection)
        return None

    def find(self, query=None, projection=None, sort=None, limit=0):
        results = [
            _apply_projection(document, projection)
            for document in self.database._get_collection(self.name)
            if _matches(document, query)
        ]

        if sort:
            for key, direction in reversed(sort):
                reverse = direction == -1
                results.sort(key=lambda doc: doc.get(key), reverse=reverse)

        if limit:
            results = results[:limit]

        return results

    def insert_one(self, document):
        doc = deepcopy(document)
        doc.setdefault('_id', ObjectId())
        self.database._get_collection(self.name).append(doc)
        self.database._save()
        return _InsertOneResult(doc['_id'])

    def update_one(self, query, update, upsert=False):
        collection = self.database._get_collection(self.name)
        for index, document in enumerate(collection):
            if not _matches(document, query):
                continue

            updated_document = deepcopy(document)
            self._apply_update_ops(updated_document, update, is_insert=False)
            collection[index] = updated_document
            self.database._save()
            return _UpdateResult(matched_count=1, modified_count=1)

        if not upsert:
            return _UpdateResult()

        new_document = {}
        for key, value in (query or {}).items():
            if not isinstance(value, dict):
                new_document[key] = deepcopy(value)
        new_document['_id'] = ObjectId()
        self._apply_update_ops(new_document, update, is_insert=True)
        collection.append(new_document)
        self.database._save()
        return _UpdateResult(matched_count=0, modified_count=0, upserted_id=new_document['_id'])

    def count_documents(self, query):
        return sum(1 for document in self.database._get_collection(self.name) if _matches(document, query))

    def _apply_update_ops(self, document, update, is_insert):
        for op, changes in update.items():
            if op == '$set':
                for key, value in changes.items():
                    document[key] = deepcopy(value)
            elif op == '$push':
                for key, value in changes.items():
                    document.setdefault(key, [])
                    document[key].append(deepcopy(value))
            elif op == '$setOnInsert' and is_insert:
                for key, value in changes.items():
                    document.setdefault(key, deepcopy(value))
            else:
                raise NotImplementedError(f'Unsupported update operator: {op}')


class LocalJsonDatabase:
    def __init__(self, filepath):
        self.filepath = filepath
        self.lock = RLock()
        self.data = self._load()

    def __getattr__(self, item):
        return LocalJsonCollection(self, item)

    @property
    def name(self):
        return 'alphacure_local'

    def _load(self):
        if not os.path.exists(self.filepath):
            return {}

        with open(self.filepath, 'r', encoding='utf-8') as handle:
            raw = json.load(handle)
        return _deserialize_value(raw)

    def _save(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with self.lock:
            with open(self.filepath, 'w', encoding='utf-8') as handle:
                json.dump(_serialize_value(self.data), handle, indent=2)

    def _get_collection(self, name):
        with self.lock:
            self.data.setdefault(name, [])
            return self.data[name]


def _use_local_fallback(uri, error):
    env_choice = os.getenv('ENABLE_LOCAL_DB_FALLBACK')
    if env_choice is not None:
        return env_choice.lower() in {'1', 'true', 'yes', 'on'}

    flask_env = os.getenv('FLASK_ENV', '').lower()
    return flask_env != 'production' and (
        uri.startswith('mongodb://localhost')
        or uri.startswith('mongodb://127.0.0.1')
        or uri.startswith('mongodb+srv://')
    )


def init_db():
    global _client, _db
    uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/alphacure')

    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        _client.server_info()
        _db = _client.get_default_database()
        _db.users.create_index('email', unique=True)
        _db.predictions.create_index('user_id')
        _db.messages.create_index([('room_id', 1), ('timestamp', 1)])
        print(f"[DB] Connected to MongoDB: {_db.name}")
        return _db
    except Exception as exc:
        if not _use_local_fallback(uri, exc):
            raise

        local_db_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'local_dev_db.json'
        )
        _client = None
        _db = LocalJsonDatabase(local_db_path)
        _db.users.create_index('email', unique=True)
        _db.predictions.create_index('user_id')
        _db.messages.create_index([('room_id', 1), ('timestamp', 1)])
        print(f"[DB] MongoDB unavailable ({exc})")
        print(f"[DB] Using local development database: {local_db_path}")
        return _db


def get_db():
    global _db
    if _db is None:
        init_db()
    return _db
