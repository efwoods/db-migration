#!/usr/bin/env python3
"""
migrate_firestore_to_mongo.py

Usage:
  - Set environment variables or pass flags:
    * MONGODB_URI (or --mongo-uri)
    * MONGODB_DB (default: 'app')
    * FIREBASE_SERVICE_ACCOUNT (path to service account json) optional if GOOGLE_APPLICATION_CREDENTIALS is set
  - Run with --dry-run to see counts and planned actions without writing to MongoDB

What it does:
  - Reads Firestore collections: users, digital_twins and their subcollections (conversations -> messages)
  - For each document, maps and copies only fields present in the Firestore schema to MongoDB
  - Writes to MongoDB collections: users, digital_twins, conversations, avatar_conversations

Design notes:
  - Keys that don't exist in the Firestore document are not created in MongoDB documents (per requirement)
  - Timestamps are converted to Python datetimes and stored as-is (pymongo will convert to BSON datetimes)

"""
import argparse
import logging
import os
import sys
from typing import Any, Dict, Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from google.cloud import firestore
from google.oauth2 import service_account
from dateutil.parser import isoparse
from datetime import datetime


LOG = logging.getLogger("migration")


def parse_args():
    p = argparse.ArgumentParser(description="Migrate Firestore data to MongoDB")
    p.add_argument("--mongo-uri", help="MongoDB connection string", default=os.getenv("MONGODB_URI"))
    p.add_argument("--mongo-db", help="MongoDB database name", default=os.getenv("MONGODB_DB", "app"))
    p.add_argument("--firebase-service-account", help="Path to Firebase service account JSON", default=os.getenv("FIREBASE_SERVICE_ACCOUNT"))
    p.add_argument("--dry-run", help="Do not write to MongoDB, only report", action="store_true")
    p.add_argument("--verbose", help="Verbose logging", action="store_true")
    return p.parse_args()


def get_firestore_client(sa_path: Optional[str]) -> firestore.Client:
    if sa_path:
        creds = service_account.Credentials.from_service_account_file(sa_path)
        client = firestore.Client(credentials=creds)
    else:
        client = firestore.Client()
    return client


def get_mongo_client(uri: str) -> MongoClient:
    return MongoClient(uri)


def to_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    # Firestore Timestamp -> datetime
    try:
        # google.cloud.firestore_v1._helpers.Timestamp? It usually becomes a datetime
        if hasattr(value, "ToDatetime"):
            return value.ToDatetime()
        # If it's already a datetime
        if isinstance(value, datetime):
            return value
        # If it's a dict like {"$date": "..."}
        if isinstance(value, dict) and "$date" in value:
            return isoparse(value["$date"])
        # ISO string
        if isinstance(value, str):
            return isoparse(value)
    except Exception:
        LOG.exception("Failed to parse timestamp: %s", value)
    return None


# Allowed fields (only copy these from Firestore -> Mongo, per requirement)
USER_KEYS = [
    "user_id",
    "username",
    "email",
    "created_at",
    "last_login",
    "currently_logged_in",
    "digital_twins",
    "last_used_digital_twin",
]

DIGITAL_TWIN_KEYS = [
    "digital_twin_id",
    "user_id",
    "name",
    "description",
    "created_at",
    "icon",
    "reference_audio",
    "files",
    "system_prompt_reference_image_description",
    "system_prompt_reference_audio_description",
    "system_prompt_description",
    "default_conversation",
]

CONVERSATION_KEYS = ["conversation_id", "digital_twin_id", "summary", "created_at", "updated_at", "message_count"]

MESSAGE_KEYS = ["message_id", "digital_twin_id", "conversation_id", "sender", "message", "media", "timestamp", "type"]


def snapshot_to_dict_keys(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    # Helper to copy keys and do conversions for timestamps
    out = {}
    for k, v in snapshot.items():
        if "_" == k[0] and k != "_id":
            # skip internal fields if any
            continue
        if isinstance(v, dict) and "$date" in v:
            out[k] = to_datetime(v)
        else:
            out[k] = v
    return out


def copy_user(doc, dry_run: bool, users_col: Collection):
    data = doc.to_dict() or {}
    user_doc = {}

    # prefer explicit user_id if provided, else use document id
    user_doc["user_id"] = data.get("user_id", doc.id)

    for k in USER_KEYS:
        if k == "user_id":
            continue
        if k in data:
            # convert timestamp-like fields
            if k in ("created_at", "last_login"):
                user_doc[k] = to_datetime(data[k])
            else:
                user_doc[k] = data[k]

    LOG.debug("Prepared user doc for %s: %s", doc.id, user_doc)

    if dry_run:
        return {"action": "upsert", "filter": {"user_id": user_doc["user_id"]}, "doc": user_doc}

    users_col.update_one({"user_id": user_doc["user_id"]}, {"$set": user_doc}, upsert=True)
    return {"action": "upsert", "id": user_doc["user_id"]}


def copy_digital_twin(doc, dry_run: bool, dt_col: Collection):
    data = doc.to_dict() or {}
    dt_doc = {}

    dt_doc["digital_twin_id"] = data.get("digital_twin_id", doc.id)

    for k in DIGITAL_TWIN_KEYS:
        if k == "digital_twin_id":
            continue
        if k in data:
            if k == "created_at":
                dt_doc[k] = to_datetime(data[k])
            else:
                dt_doc[k] = data[k]

    LOG.debug("Prepared digital twin doc for %s: %s", doc.id, dt_doc)

    if dry_run:
        return {"action": "upsert", "filter": {"digital_twin_id": dt_doc["digital_twin_id"]}, "doc": dt_doc}

    dt_col.update_one({"digital_twin_id": dt_doc["digital_twin_id"]}, {"$set": dt_doc}, upsert=True)
    return {"action": "upsert", "id": dt_doc["digital_twin_id"]}


def copy_conversation(doc, digital_twin_id: str, dry_run: bool, conv_col: Collection):
    data = doc.to_dict() or {}
    conv_doc = {
        "conversation_id": data.get("conversation_id", doc.id),
        "digital_twin_id": digital_twin_id,
    }
    for k in ["summary", "created_at", "updated_at", "message_count"]:
        if k in data:
            conv_doc[k] = to_datetime(data[k]) if k.endswith("_at") or (isinstance(data[k], dict) and "$date" in data[k]) else data[k]

    LOG.debug("Prepared conversation doc for %s: %s", doc.id, conv_doc)

    if dry_run:
        return {"action": "upsert", "filter": {"conversation_id": conv_doc["conversation_id"]}, "doc": conv_doc}

    conv_col.update_one({"conversation_id": conv_doc["conversation_id"]}, {"$set": conv_doc}, upsert=True)
    return {"action": "upsert", "id": conv_doc["conversation_id"]}


def copy_message(doc, digital_twin_id: str, conversation_id: str, dry_run: bool, msg_col: Collection):
    data = doc.to_dict() or {}
    msg_doc = {
        "message_id": data.get("message_id", doc.id),
        "digital_twin_id": digital_twin_id,
        "conversation_id": conversation_id,
        "sender": data.get("role"),
        "message": data.get("content"),
        "media": data.get("media", []),
        "timestamp": to_datetime(data.get("timestamp")),
    }

    # determine type
    if msg_doc.get("message") and not msg_doc.get("media"):
        msg_doc["type"] = "text"
    elif msg_doc.get("media"):
        first = msg_doc["media"][0]
        msg_doc["type"] = first.get("type") if isinstance(first, dict) and first.get("type") else "media"
    else:
        msg_doc["type"] = "text"

    # remove None values to respect "drop keys that don't match"
    msg_doc = {k: v for k, v in msg_doc.items() if v is not None}

    LOG.debug("Prepared message doc for %s: %s", doc.id, msg_doc)

    if dry_run:
        return {"action": "upsert", "filter": {"message_id": msg_doc["message_id"]}, "doc": msg_doc}

    msg_col.update_one({"message_id": msg_doc["message_id"]}, {"$set": msg_doc}, upsert=True)
    return {"action": "upsert", "id": msg_doc["message_id"]}


def migrate(firestore_client: firestore.Client, mongo_db, dry_run: bool = True):
    users_col = mongo_db["users"]
    dt_col = mongo_db["digital_twins"]
    conv_col = mongo_db["conversations"]
    msg_col = mongo_db["avatar_conversations"]

    results = {"users": 0, "digital_twins": 0, "conversations": 0, "messages": 0}

    LOG.info("Starting users migration...")
    for doc in firestore_client.collection("users").stream():
        copy_user(doc, dry_run, users_col)
        results["users"] += 1

    LOG.info("Starting digital_twins migration...")
    for dt_doc in firestore_client.collection("digital_twins").stream():
        copy_digital_twin(dt_doc, dry_run, dt_col)
        results["digital_twins"] += 1

        # conversations subcollection
        conversations_ref = dt_doc.reference.collection("conversations")
        for conv_doc in conversations_ref.stream():
            copy_conversation(conv_doc, dt_doc.id, dry_run, conv_col)
            results["conversations"] += 1

            # messages subcollection
            messages_ref = conv_doc.reference.collection("messages")
            for msg_doc in messages_ref.stream():
                copy_message(msg_doc, dt_doc.id, conv_doc.id, dry_run, msg_col)
                results["messages"] += 1

    LOG.info("Migration finished. Summary: %s", results)
    return results


def main():
    args = parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if not args.mongo_uri:
        LOG.error("Missing MongoDB URI (set MONGODB_URI or pass --mongo-uri)")
        sys.exit(1)

    LOG.info("Initializing Firestore client...")
    fs_client = get_firestore_client(args.firebase_service_account)

    LOG.info("Connecting to MongoDB...")
    mongo_client = get_mongo_client(args.mongo_uri)
    mongo_db = mongo_client[args.mongo_db]

    LOG.info("Starting migration (dry_run=%s)...", args.dry_run)
    summary = migrate(fs_client, mongo_db, dry_run=args.dry_run)

    LOG.info("Done. Summary: %s", summary)


if __name__ == "__main__":
    main()
