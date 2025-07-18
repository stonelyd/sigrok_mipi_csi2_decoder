#!/usr/bin/env python3
"""
Test script for the MIPI CSI-2 D-PHY decoder using mock sigrokdecode
"""

import sys
import os

# Add the decoder directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock sigrokdecode module
sys.modules['sigrokdecode'] = __import__('mock_sigrokdecode')

try:
    from mipi_csi2_dphy import Decoder
    print("✅ Successfully imported MIPI CSI-2 D-PHY decoder")

    # Create decoder instance
    decoder = Decoder()
    print(f"✅ Decoder created successfully")
    print(f"   ID: {decoder.id}")
    print(f"   Name: {decoder.name}")
    print(f"   Long Name: {decoder.longname}")
    print(f"   Description: {decoder.desc}")
    print(f"   API Version: {decoder.api_version}")
    print(f"   License: {decoder.license}")
    print(f"   Inputs: {decoder.inputs}")
    print(f"   Outputs: {decoder.outputs}")
    print(f"   Tags: {decoder.tags}")
    print(f"   Channels: {len(decoder.channels)}")
    print(f"   Optional Channels: {len(decoder.optional_channels)}")
    print(f"   Options: {len(decoder.options)}")
    print(f"   Annotations: {len(decoder.annotations)}")
    print(f"   Annotation Rows: {len(decoder.annotation_rows)}")
    print(f"   Binary outputs: {len(decoder.binary)}")

    print("\n📋 Channel Configuration:")
    for i, channel in enumerate(decoder.channels):
        print(f"   {i}: {channel['name']} ({channel['id']}) - {channel['desc']}")

    print("\n📋 Optional Channels:")
    for i, channel in enumerate(decoder.optional_channels):
        print(f"   {i}: {channel['name']} ({channel['id']}) - {channel['desc']}")

    print("\n📋 Options:")
    for i, option in enumerate(decoder.options):
        print(f"   {i}: {option['id']} - {option['desc']} (default: {option['default']})")

    print("\n📋 Annotations:")
    for i, (ann_id, ann_desc) in enumerate(decoder.annotations):
        print(f"   {i}: {ann_id} - {ann_desc}")

    print("\n📋 Annotation Rows:")
    for i, (row_id, row_name, ann_indices) in enumerate(decoder.annotation_rows):
        print(f"   {i}: {row_id} - {row_name} (annotations: {ann_indices})")

    print("\n📋 Binary Outputs:")
    for i, (bin_id, bin_desc) in enumerate(decoder.binary):
        print(f"   {i}: {bin_id} - {bin_desc}")

    # Test decoder methods
    print("\n🧪 Testing decoder methods:")
    decoder.reset()
    print("   ✅ reset() method works")

    decoder.metadata('samplerate', 1000000)
    print("   ✅ metadata() method works")

    decoder.start()
    print("   ✅ start() method works")

    print("\n✅ All tests passed! Decoder structure is correct!")

except ImportError as e:
    print(f"❌ Failed to import decoder: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error testing decoder: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)