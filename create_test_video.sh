#!/bin/bash
# Create a simple test video file using ffmpeg

OUTPUT_FILE="test_video.mp4"

echo "Creating test video: $OUTPUT_FILE"

# Create a 30-second video with test pattern
ffmpeg -f lavfi -i testsrc=size=320x240:duration=30:rate=1 \
       -f lavfi -i sine=frequency=440:duration=30 \
       -pix_fmt yuv420p \
       -c:v libx264 -c:a aac \
       "$OUTPUT_FILE" -y 2>/dev/null

if [ -f "$OUTPUT_FILE" ]; then
    echo "✓ Test video created: $OUTPUT_FILE ($(du -h "$OUTPUT_FILE" | cut -f1))"
    echo ""
    echo "You can now test the API:"
    echo "  python test_api.py $OUTPUT_FILE"
else
    echo "✗ Failed to create test video"
    echo "Make sure ffmpeg is installed: sudo apt-get install ffmpeg"
fi
