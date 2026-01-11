# Firestore -> MongoDB Migration

This migration helps move Firestore data into MongoDB according to the schemas in `firestore_structure.md` and `mongodb_structure.md`.

Overview
- The script `scripts/migrate_firestore_to_mongo.py` reads the Firestore collections:
  * `users`
  * `digital_twins` (and its subcollections `conversations` -> `messages`)
- It writes to MongoDB collections:
  * `users`
  * `digital_twins`
  * `conversations`
  * `avatar_conversations` (one document per message)

Important rule enforced by this migration
- "If a key does not match in the Firestore object structure, drop the key." That means we only copy fields defined in the Firestore schema; we do not invent or fill Mongo-only keys.

Mapping decisions
1. Users
   - Copied fields: `user_id` (doc id if missing), `username`, `email`, `created_at`, `last_login`, `currently_logged_in`, `digital_twins`, `last_used_digital_twin`.
2. Digital twins (avatars)
   - Copied fields: `digital_twin_id` (doc id if missing), `user_id`, `name`, `description`, `created_at`, `icon`, `reference_audio`, `files`, `system_prompt_*`, `default_conversation`.
3. Conversations
   - Each Firestore conversation is stored in `conversations` with: `conversation_id`, `digital_twin_id`, `summary`, `created_at`, `updated_at`, `message_count`.
4. Messages
   - Each Firestore message becomes a document in `avatar_conversations` with: `message_id`, `digital_twin_id`, `conversation_id`, `sender` (from `role`), `message` (from `content`), `media`, `timestamp`, `type`.
   - `type` is `text` when `content` is present and `media` is empty, otherwise it is the first media item's `type` or `media`.

How the script works (step-by-step)
1. Initialize Firestore client using `GOOGLE_APPLICATION_CREDENTIALS` or `--firebase-service-account` (service account JSON).
2. Initialize MongoDB client using `MONGODB_URI` or `--mongo-uri`. Use `--mongo-db` to select the database (default `app`).
3. Optionally run with `--dry-run` to only report counts and intended upserts without writing to MongoDB.
4. Iterate Firestore `users` collection and upsert each user into MongoDB `users`.
5. Iterate Firestore `digital_twins` collection; for each digital twin:
   - Upsert the Digital Twin into `digital_twins` collection.
   - Iterate its `conversations` subcollection and upsert conversation docs into `conversations`.
   - For each conversation, iterate `messages` subcollection and upsert message docs into `avatar_conversations`.
6. Timestamps are parsed and stored as datetimes (pymongo turns them into BSON datetimes).
7. The script logs counts and a summary at the end.

Running the script

Install dependencies:

```bash
pip install google-cloud-firestore pymongo python-dateutil
```

Dry run (no writes):

```bash
export MONGODB_URI="mongodb://localhost:27017"
export FIREBASE_SERVICE_ACCOUNT="/path/to/service-account.json"
python scripts/migrate_firestore_to_mongo.py --dry-run --mongo-uri $MONGODB_URI
```

Real run (writes to MongoDB):

```bash
python scripts/migrate_firestore_to_mongo.py --mongo-uri $MONGODB_URI
```

Notes & next steps
- The script uses upserts to avoid duplicate inserts; you can extend it to add commit/transaction safety if needed.
- A smoke test / dry-run in a staging Firestore and a dev MongoDB is recommended before migrating production.
- The script intentionally does not add Mongo-only keys; if you need compatibility fields (e.g., `avatar_id`), add them in a post-processing step or request an update to the mapping rules.

