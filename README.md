# MIPI CSI-2 D-PHY Protocol Decoder for Sigrok

A sigrok protocol decoder for MIPI Camera Serial Interface 2 (CSI-2) using D-PHY physical layer.

## Overview

This decoder implements support for MIPI CSI-2 D-PHY protocol, which is commonly used in camera applications for high-speed serial data transmission. The decoder can parse:

- D-PHY lane signals (clock + data lanes)
- CSI-2 packet structure
- Start/End of Transmission (SoT/EoT) markers
- Short and long packet types
- Lane synchronization
- Various data types (YUV, RGB, RAW, JPEG)

## Features

- **Multi-lane support**: Configurable 1-4 data lanes
- **Packet parsing**: Short packets (control) and long packets (image data)
- **Data type recognition**: Common CSI-2 data types
- **Virtual channel support**: Multiple virtual channels
- **Comprehensive annotations**: Detailed protocol analysis
- **Binary output**: Raw packet data export

## Installation

### Prerequisites

- Python 3.x
- Sigrok (libsigrokdecode)

### Setup

1. Clone or copy the `mipi_csi2_dphy` directory to your sigrok decoders directory:
   ```bash
   cp -r mipi_csi2_dphy /path/to/libsigrokdecode/decoders/
   ```

2. Restart your sigrok frontend (PulseView, etc.)

## Usage

### Channel Configuration

Connect your signals as follows:

- **CLK**: Clock lane (required)
- **DATA0**: Data lane 0 (required)
- **DATA1**: Data lane 1 (optional)
- **DATA2**: Data lane 2 (optional)
- **DATA3**: Data lane 3 (optional)

### Decoder Options

- **Number of data lanes**: 1-4 (default: 1)
- **Expected bitrate**: 500-2500 Mbps (default: 1000)

### Annotations

The decoder provides several annotation types:

#### Markers
- **SOT**: Start of Transmission
- **EOT**: End of Transmission
- **SYNC**: Lane synchronization

#### Packets
- **Short packet**: Control packets
- **Long packet**: Image data packets
- **Payload**: Packet payload data
- **Footer**: Packet footer/checksum

#### Metadata
- **Data type**: YUV, RGB, RAW, JPEG formats
- **Virtual channel**: Channel number
- **Frame count**: Frame identifier
- **Line count**: Line number
- **Pixel count**: Pixel count

#### Errors
- **Protocol error**: Decoding errors

## Protocol Details

### MIPI CSI-2 D-PHY

MIPI CSI-2 D-PHY is a high-speed serial interface that uses:
- **D-PHY physical layer**: Differential signaling
- **CSI-2 protocol**: Packet-based data transmission
- **Multiple lanes**: Parallel data transmission for higher bandwidth

### Packet Structure

1. **SoT (Start of Transmission)**: 0xB8 marker
2. **Packet Header**: Data type, virtual channel, metadata
3. **Payload**: Image or control data
4. **EoT (End of Transmission)**: 0x9C marker

### Data Types

Common CSI-2 data types supported:
- **YUV formats**: YUV420, YUV422 (8-bit, 10-bit)
- **RGB formats**: RGB444, RGB555, RGB565, RGB666, RGB888
- **RAW formats**: RAW6, RAW7, RAW8, RAW10, RAW12, RAW14
- **JPEG**: JPEG compressed data

## Testing

Run the test script to verify the decoder structure:

```bash
python3 test_decoder_mock.py
```

This will test:
- Decoder import and instantiation
- Channel configuration
- Annotation definitions
- Method functionality

## Development

### Project Structure

```
mipi_csi2_dphy/
├── __init__.py          # Module metadata and imports
├── pd.py               # Main decoder implementation
└── README.md           # This file
```

### Key Components

- **Decoder class**: Main decoder implementation
- **Channel definitions**: Signal input configuration
- **Annotation system**: Protocol analysis output
- **Binary output**: Raw data export
- **State machine**: Protocol state tracking

### Extending the Decoder

The decoder is designed to be extensible:

1. **Add new data types**: Extend the `DATA_TYPE_NAMES` dictionary
2. **Enhance packet parsing**: Modify the decode methods
3. **Add new annotations**: Extend the annotations tuple
4. **Improve lane handling**: Enhance multi-lane support

## Limitations

Current implementation includes:
- Basic packet detection framework
- Simplified lane synchronization
- Core CSI-2 data type support

Future enhancements could include:
- Advanced lane synchronization
- Error detection and recovery
- Timing analysis
- Performance optimization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This decoder is licensed under GPLv2+ (GNU General Public License v2 or later).

## References

- [MIPI Alliance CSI-2 Specification](https://www.mipi.org/specifications/csi-2)
- [Sigrok Protocol Decoder HOWTO](http://sigrok.org/wiki/Protocol_decoder_HOWTO)
- [Sigrok Project](https://sigrok.org/)

## TODO

- [ ] Implement advanced lane synchronization
- [ ] Add error detection and recovery
- [ ] Enhance timing analysis
- [ ] Add performance optimization
- [ ] Create unit tests with real signal data
- [ ] Add documentation for advanced features