#!/usr/bin/env python3
"""
Example usage of the MIPI CSI-2 D-PHY decoder
"""

import sys
import os

# Add the decoder directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mipi_csi2_dphy'))

# Mock sigrokdecode module
sys.modules['sigrokdecode'] = __import__('mock_sigrokdecode')

from mipi_csi2_dphy import Decoder

def main():
    """Demonstrate decoder usage with sample data"""

    print("🔧 MIPI CSI-2 D-PHY Decoder Example")
    print("=" * 50)

    # Create decoder instance
    decoder = Decoder()

    # Configure decoder
    decoder.options = {
        'lanes': '2',      # Use 2 data lanes
        'bitrate': '1500'  # 1.5 Gbps
    }

    # Initialize decoder
    decoder.reset()
    decoder.metadata('samplerate', 1000000000)  # 1 GHz sample rate
    decoder.start()

    print(f"✅ Decoder initialized with {decoder.num_lanes} lanes at {decoder.expected_bitrate} Mbps")

    # Sample MIPI CSI-2 D-PHY data
    print("\n📊 Sample Protocol Analysis:")
    print("-" * 30)

    # Example: SOT marker
    print("1. Start of Transmission (SOT) marker detected")
    decoder.decode_sot(1000, 1001)

    # Example: Short packet (control data)
    print("2. Short packet detected")
    sample_data = [0x18, 0x00, 0x00, 0x00]  # YUV420_8BIT, VC0
    decoder.decode_short_packet(1002, 1006, sample_data)

    # Example: Long packet header
    print("3. Long packet header detected")
    header_data = [0x2A, 0x01, 0x00, 0x00, 0x10, 0x00, 0x20]  # RAW8, VC1, frame 0, line 16, pixel 32
    decoder.decode_long_packet(1007, 1014, header_data)

    # Example: Payload data
    print("4. Payload data detected")
    payload_data = bytes([0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF])
    decoder.decode_payload(1015, 1021, payload_data)

    # Example: EOT marker
    print("5. End of Transmission (EOT) marker detected")
    decoder.decode_eot(1022, 1023)

    # Example: Sync marker
    print("6. Lane synchronization detected")
    decoder.decode_sync(1024, 1025)

    # Example: Error condition
    print("7. Protocol error detected")
    decoder.decode_error(1026, 1027, "Invalid packet length")

    print("\n✅ Example completed successfully!")
    print("\n📋 Decoder Features Demonstrated:")
    print("   • SOT/EoT marker detection")
    print("   • Short packet parsing (control data)")
    print("   • Long packet parsing (image data)")
    print("   • Payload data handling")
    print("   • Lane synchronization")
    print("   • Error detection and reporting")
    print("   • Multiple data types (YUV, RAW)")
    print("   • Virtual channel support")
    print("   • Frame/line/pixel metadata")

    print("\n🔧 Next Steps:")
    print("   1. Integrate with real sigrok environment")
    print("   2. Connect actual MIPI CSI-2 D-PHY signals")
    print("   3. Configure for your specific camera setup")
    print("   4. Analyze captured data in PulseView or other sigrok frontend")

if __name__ == "__main__":
    main()