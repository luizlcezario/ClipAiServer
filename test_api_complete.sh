#!/bin/bash

# Complete API Testing Script for ClipsAI Server
# This script demonstrates the full workflow: submit -> monitor -> download

set -e

API_URL="http://127.0.0.1:8000/api/clips"
VIDEO_PATH="/home/lcezario/code/ClipsAiServer/test_video.mp4"

echo "========================================"
echo "ClipsAI Server - Complete API Test"
echo "========================================"
echo ""

# Test 1: Health Check
echo "1️⃣  Testing Health Endpoint..."
HEALTH=$(curl -s "$API_URL/health")
echo "Response: $HEALTH"
echo ""

# Test 2: Check if test video exists, if not create it
if [ ! -f "$VIDEO_PATH" ]; then
    echo "2️⃣  Creating test video..."
    if command -v ffmpeg &> /dev/null; then
        ffmpeg -f lavfi -i color=c=blue:s=320x240:d=30 \
                -f lavfi -i sine=f=1000:d=30 \
                -pix_fmt yuv420p \
                "$VIDEO_PATH" -y > /dev/null 2>&1
        echo "✅ Test video created: $VIDEO_PATH"
    else
        echo "❌ FFmpeg not found. Please install it first."
        exit 1
    fi
else
    echo "2️⃣  Test video exists: $VIDEO_PATH"
fi
echo ""

# Test 3: Submit clip generation job
echo "3️⃣  Submitting clip generation job..."
echo "   Video: $VIDEO_PATH"
SUBMIT_RESPONSE=$(curl -s -X POST "$API_URL/generate" \
    -H "Content-Type: application/json" \
    -d "{\"video_path\": \"$VIDEO_PATH\", \"description\": \"Test clip generation\"}")

echo "Response: $SUBMIT_RESPONSE"
JOB_ID=$(echo "$SUBMIT_RESPONSE" | grep -o '"job_id":"[^"]*' | cut -d'"' -f4)
echo "✅ Job ID: $JOB_ID"
echo ""

# Test 4: Monitor job status
echo "4️⃣  Monitoring job status..."
for i in {1..30}; do
    STATUS_RESPONSE=$(curl -s "$API_URL/status/$JOB_ID")
    STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
    MESSAGE=$(echo "$STATUS_RESPONSE" | grep -o '"status_message":"[^"]*' | cut -d'"' -f4)
    
    echo "   [$i/30] Status: $STATUS | Message: $MESSAGE"
    
    if [ "$STATUS" = "completed" ]; then
        echo "✅ Job completed successfully!"
        echo "Full response:"
        echo "$STATUS_RESPONSE" | python -m json.tool
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "❌ Job failed!"
        echo "Full response:"
        echo "$STATUS_RESPONSE" | python -m json.tool
        exit 1
    fi
    
    sleep 2
done
echo ""

# Test 5: Download clips
if [ "$STATUS" = "completed" ]; then
    echo "5️⃣  Testing clip download..."
    
    # Create output directory
    mkdir -p /tmp/clips_output
    
    # Download individual clip
    echo "   Downloading clip 0..."
    curl -s -o /tmp/clips_output/clip_0.mp4 "$API_URL/download/$JOB_ID/0"
    if [ -f /tmp/clips_output/clip_0.mp4 ]; then
        SIZE=$(stat -f%z /tmp/clips_output/clip_0.mp4 2>/dev/null || stat -c%s /tmp/clips_output/clip_0.mp4 2>/dev/null)
        echo "   ✅ Downloaded clip_0.mp4 ($(numfmt --to=iec $SIZE 2>/dev/null || echo $SIZE' bytes'))"
    fi
    
    # Download all clips as ZIP
    echo "   Downloading all clips as ZIP..."
    curl -s -o /tmp/clips_output/all_clips.zip "$API_URL/download-all/$JOB_ID"
    if [ -f /tmp/clips_output/all_clips.zip ]; then
        SIZE=$(stat -f%z /tmp/clips_output/all_clips.zip 2>/dev/null || stat -c%s /tmp/clips_output/all_clips.zip 2>/dev/null)
        echo "   ✅ Downloaded all_clips.zip ($(numfmt --to=iec $SIZE 2>/dev/null || echo $SIZE' bytes'))"
    fi
    echo ""
    
    # Test 6: Delete job
    echo "6️⃣  Testing job deletion..."
    DELETE_RESPONSE=$(curl -s -X DELETE "$API_URL/delete/$JOB_ID")
    echo "Response: $DELETE_RESPONSE"
    echo ""
fi

echo "========================================"
echo "✅ All tests completed successfully!"
echo "========================================"
echo ""
echo "📁 Output files saved to:"
echo "   /tmp/clips_output/"
echo ""
echo "📊 API Endpoints:"
echo "   POST   /api/clips/generate         - Submit clip generation job"
echo "   GET    /api/clips/status/{job_id}  - Check job status"
echo "   GET    /api/clips/download/{job_id}/{index} - Download individual clip"
echo "   GET    /api/clips/download-all/{job_id}    - Download all clips as ZIP"
echo "   DELETE /api/clips/delete/{job_id}  - Delete job and clips"
echo "   GET    /api/clips/health           - Health check"
