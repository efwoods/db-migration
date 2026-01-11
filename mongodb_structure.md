# avatar_conversations (these are actually individual messages; each avatar has only one conversation and this conversation needs to be created)
<!-- structure -->
{
  "_id": "a8bbc654-7a5e-4606-822e-b7c28c4a495e",
  "avatar_id": "03631b03-2607-4a64-a3a6-f6ada35adf6c",
  "user_id": "27df12d9-9881-4369-bd75-e5c9538b0ea2",
  "type": "text",
  "message": "Hey Shivon!",
  "media": [],
  "timestamp": {
    "$date": "2025-08-26T02:43:08.303Z"
  },
  "sender": "user"
}

# Avatar Structure (avatars are now named digital_twins; avatar is a digitial_twin; use snake case and prefer single vs many plurality when naming; using plural where using this naming convention makes sense.)
{
  "_id": {
    "$oid": "68a9519a6f5f192b8724fb0f"
  },
  "avatar_id": "03631b03-2607-4a64-a3a6-f6ada35adf6c",
  "user_id": "27df12d9-9881-4369-bd75-e5c9538b0ea2",
  "name": "Shivon Zilis",
  "description": "Great Mother, Partner to Elon, Very Intelligent, Kind, Friendly, Good-Heart, Leader",
  "created_at": {
    "$date": "2025-08-23T05:28:58.285Z"
  },
  "icon": null,
  "files": [],
  "messages": [],
  "system_prompt_reference_image_description": "",
  "system_prompt_reference_audio_description": "",
  "system_prompt_description": ""
}

# User Structure
{
  "_id": {
    "$oid": "68a946f2887bd9474a4c4fa4"
  },
  "user_id": "27df12d9-9881-4369-bd75-e5c9538b0ea2",
  "username": "string",
  "email": "user@example.com",
  "created_at": {
    "$date": "2025-08-23T04:43:30.342Z"
  },
  "last_login": {
    "$date": "2025-11-28T19:36:25.964Z"
  },
  "currently_logged_in": false,
  "personal_image": "users/27df12d9-9881-4369-bd75-e5c9538b0ea2/image/future-of-humanity.png",
  "neural_nexus_api_key": null,
  "grok_api_key": null,
  "enable_grok_imagine": false,
  "elevenlabs_api_key": null,
  "enable_elevenlabs": false,
  "api_usage": {
    "requests_made": 0,
    "tokens_used": 0
  },
  "billing_history": [],
  "credit_card": null,
  "avatars": [
    "03631b03-2607-4a64-a3a6-f6ada35adf6c",
    "d838b7b2-c6db-4569-853d-309327a8ecbf",
    "246876a7-8328-4a19-93e2-38ea259ad59f",
    "0e26495c-69da-436a-8c98-0320f30e5102",
    "637f8739-38a1-43fa-91f0-7b3c112fc6cf",
    "3ecbdbd6-8222-4bb3-aa62-2eb7d43086c2",
    "a71f4b4f-faeb-42a0-8d2a-d20617fc8451",
    "48352054-4ead-4c79-a288-de2523ae6b3e",
    "7a2bf347-3c71-4cb3-ac04-616dd5497e6d",
    "012bc1cd-b6b8-4262-8c48-aa4c4c54e347"
  ],
  "last_used_avatar": "246876a7-8328-4a19-93e2-38ea259ad59f",
  "avatar_adapter_management_api_endpoint": "https://nn-adapter-api-915579649879.us-central1.run.app:8080",
  "avatar_data_collection_api_endpoint": "",
  "avatar_messaging_api_cpu_endpoint": "http://34.23.82.134:8080",
  "avatar_messaging_api_gpu_endpoint": "http://34.23.82.134:8080",
  "avatar_vectorstore_management_api_endpoint": "https://https://nn-vectorstore-api-915579649879.us-central1.run.app:8080",
  "migrated_to_supabase": true,
  "migration_timestamp": {
    "$date": "2025-12-06T18:51:18.616Z"
  }
}