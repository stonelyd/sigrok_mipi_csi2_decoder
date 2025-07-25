# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a sigrok protocol decoder for MIPI CSI-2 D-PHY, implementing high-speed serial interface parsing for camera applications. The decoder handles D-PHY lane signals, CSI-2 packet structure, and various image data formats (YUV, RGB, RAW, JPEG).

## Development Commands

### Testing

```bash
# Test with sigrok-cli using VCD files (requires SIGROKDECODE_DIR environment variable)
timeout 60s bash -c 'SIGROKDECODE_DIR=/home/stonelyd/sigrok_mipi_csi2_decoder sigrok-cli --input-file test_csi2_500ps.vcd --channels clk_n,clk_p,data0_n,data0_p,data1_n,data1_p,data2_n,data2_p,data3_n,data3_p -P mipi_csi2_dphy --loglevel 5'

```

substitue vcd_file for test vectors
test_csi2_frame_end_500ps.vcd -> Frame End Short Packet, 1 lane, vc=0
test_csi2_frame_start_500ps.vcd -> Frame Start Short Packet, 1 lane, vc=0
test_csi2_long_packet_500ps.vcd -> Raw8 long Packet, 1 lane, 32 bytes, vc=0
test_csi2_frame_500ps.vcd -> Full Frame test with short and long packets, 1-lane, vc=0
test_csi2_frame_start_2lane_500ps.vcd -> Frame Start Short Packet, 2 lances, vc=0

## Mipi csi-2 specifications.

```
attached_assets/
├──441578464-mipi-D-PHY-specification-v2-5-pdf.pdf      # D-phy Specs
├──703695522-Mipi-CSI-2-Specification-v4-0-1.pdf        # CSI-2 Specs
```

## Architecture

### Core Decoder Structure (`mipi_csi2_dphy/pd.py`)
- **Main Decoder Class**: Implements sigrok's protocol decoder API (api_version 3)
- **State Machine**: Handles IDLE/PACKET states with lane state tracking
- **Multi-lane Support**: Configurable 1-4 data lanes with auto-detection
- **Serial Bit Processing**: LSB-first bit shifting with sync detection per lane
- **Packet Parsing**: Short packets (control) and long packets (image data)

### Key Components
- **Lane State Detection**: Monitors D-PHY states (LP-11, HS-0, HS-1, HS-SYNC)
- **Sync Detection**: Identifies 0xB8 sync markers across lanes
- **Packet Decoding**: Handles SoT (0xB8), EoT (0x9C), headers, and payload
- **Data Type Recognition**: Supports common CSI-2 formats with name mapping
- **Virtual Channel Support**: Multi-channel parsing with metadata extraction

### Channel Configuration
- **Required**: CLK_P (clock lane), DATA0_P (data lane 0)
- **Optional**: DATA1_P, DATA2_P, DATA3_P (additional data lanes)
- **Options**: Number of lanes (0=auto-detect), expected bitrate (500-2500 Mbps)

### Annotation System
The decoder provides structured annotations in rows:
- **Markers**: SOT, EOT, SYNC
- **Packets**: Short/long packets, payload, footer
- **Errors**: Protocol violations
- **Metadata**: Data types, virtual channels
- **Lane Information**: State changes, lane count, bit shifting

### Output Formats
- **Python Output**: Structured packet data for downstream processing
- **Binary Output**: Raw packet data export
- **Annotations**: Human-readable protocol analysis

## Testing Notes

The decoder includes comprehensive lane detection logic that may be overly conservative for some test scenarios. Lane 0 is prioritized, and additional lanes require both sync detection and significant activity to be counted as active.

## File Structure

```
mipi_csi2_dphy/
├── __init__.py          # Module metadata and decoder import
├── pd.py               # Main decoder implementation (500+ lines)
testing/
├── test_decoder_mock.py # Structure verification with mock sigrok
├── mock_sigrokdecode.py # Mock sigrok module for testing
├── test_decoder.py     # Additional test utilities
└── example_usage.py    # Usage examples
```