#!/usr/bin/env python3
"""
Simple test script for the MIPI CSI-2 D-PHY decoder
"""

import sys
import os

# Add the decoder directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mipi_csi2_dphy'))

try:
    from mipi_csi2_dphy import Decoder
    print("✅ Successfully imported MIPI CSI-2 D-PHY decoder")

    # Create decoder instance
    decoder = Decoder()
    print(f"✅ Decoder created successfully")
    print(f"   ID: {decoder.id}")
    print(f"   Name: {decoder.name}")
    print(f"   API Version: {decoder.api_version}")
    print(f"   Channels: {len(decoder.channels)}")
    print(f"   Optional Channels: {len(decoder.optional_channels)}")
    print(f"   Annotations: {len(decoder.annotations)}")
    print(f"   Binary outputs: {len(decoder.binary)}")

    print("\n📋 Channel Configuration:")
    for i, channel in enumerate(decoder.channels):
        print(f"   {i}: {channel['name']} ({channel['id']}) - {channel['desc']}")

    print("\n📋 Annotations:")
    for i, (ann_id, ann_desc) in enumerate(decoder.annotations):
        print(f"   {i}: {ann_id} - {ann_desc}")

    print("\n✅ Decoder structure looks correct!")

except ImportError as e:
    print(f"❌ Failed to import decoder: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error testing decoder: {e}")
    sys.exit(1)