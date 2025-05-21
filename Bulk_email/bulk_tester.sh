#!/bin/bash

# File paths
VIDEO_FILE="/home/satyam/TEST_FILES/video.mp4"
IMAGE_FILE="/home/satyam/TEST_FILES/test2.png"
RECIPIENTS_FILE="small.txt"

# Encode attachments to base64
base64 "$VIDEO_FILE" > video_base64.txt
base64 "$IMAGE_FILE" > q11_base64.txt

# Read all recipients from file into a JSON array
RECIPIENTS_JSON=$(jq -Rn '[inputs]' < "$RECIPIENTS_FILE")

# Create JSON payload
cat > payload.json << EOF
{
    "subject": "Video and Screenshot Attached",
    "body": "Please find the attached video and screenshot.",
    "recipients": $RECIPIENTS_JSON,
    "embedded_links": ["https://google.com"],
    "cc": ["gamermg474@gmail.com"],
    "bcc": ["220110014@iitdh.ac.in"],
    "attachments": [
        {
            "filename": "myvideo.mp4",
            "content": "$(cat video_base64.txt)",
            "mime_type": "video/mp4"
        },
        {
            "filename": "q11.png",
            "content": "$(cat q11_base64.txt)",
            "mime_type": "image/png"
        }
    ]
}
EOF

# Send POST request
curl -X POST http://localhost:8000/send-email/ \
     -H "Content-Type: application/json" \
     -d @payload.json

# Clean up
rm video_base64.txt q11_base64.txt payload.json
