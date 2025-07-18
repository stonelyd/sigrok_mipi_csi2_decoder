##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2024 sigrok contributors
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

import sigrokdecode as srd

'''
OUTPUT_PYTHON format:

Packet:
[<ptype>, <pdata>]

<ptype>:
 - 'SOT' (Start of Transmission)
 - 'EOT' (End of Transmission)
 - 'SHORT_PACKET' (Short packet header)
 - 'LONG_PACKET' (Long packet header)
 - 'PAYLOAD' (Packet payload data)
 - 'FOOTER' (Packet footer/checksum)
 - 'SYNC' (Lane synchronization)
 - 'ERROR' (Protocol error)
 - 'LANE_STATE' (Lane state change)
 - 'LANE_COUNT' (Detected lane count)

<pdata> contains the relevant data for each packet type:
 - For SHORT_PACKET: [data_type, virtual_channel, data]
 - For LONG_PACKET: [data_type, virtual_channel, frame_count, line_count, pixel_count]
 - For PAYLOAD: [data_bytes]
 - For LANE_STATE: [lane_number, state_name]
 - For LANE_COUNT: [detected_count]
 - For others: None or error description
'''

# Protocol constants
SOT_MARKER = 0xB8
EOT_MARKER = 0x9C
SYNC_MARKER = 0xB8

# D-PHY Lane States
LANE_STATE_LP_11 = 'LP-11'  # Low Power Stop state
LANE_STATE_LP_01 = 'LP-01'  # Low Power Turn-around
LANE_STATE_LP_00 = 'LP-00'  # Low Power Turn-around
LANE_STATE_LP_10 = 'LP-10'  # Low Power Turn-around
LANE_STATE_HS_0 = 'HS-0'    # High Speed Data 0
LANE_STATE_HS_1 = 'HS-1'    # High Speed Data 1
LANE_STATE_HS_SYNC = 'HS-SYNC'  # High Speed Sync

# CSI-2 Data Types (most common ones)
CSI2_DT_YUV420_8BIT = 0x18
CSI2_DT_YUV420_10BIT = 0x19
CSI2_DT_YUV422_8BIT = 0x1E
CSI2_DT_YUV422_10BIT = 0x1F
CSI2_DT_RGB444 = 0x20
CSI2_DT_RGB555 = 0x21
CSI2_DT_RGB565 = 0x22
CSI2_DT_RGB666 = 0x23
CSI2_DT_RGB888 = 0x24
CSI2_DT_RAW6 = 0x28
CSI2_DT_RAW7 = 0x29
CSI2_DT_RAW8 = 0x2A
CSI2_DT_RAW10 = 0x2B
CSI2_DT_RAW12 = 0x2C
CSI2_DT_RAW14 = 0x2D
CSI2_DT_JPEG = 0x30

# Data type names mapping
DATA_TYPE_NAMES = {
    CSI2_DT_YUV420_8BIT: 'YUV420_8BIT',
    CSI2_DT_YUV420_10BIT: 'YUV420_10BIT',
    CSI2_DT_YUV422_8BIT: 'YUV422_8BIT',
    CSI2_DT_YUV422_10BIT: 'YUV422_10BIT',
    CSI2_DT_RGB444: 'RGB444',
    CSI2_DT_RGB555: 'RGB555',
    CSI2_DT_RGB565: 'RGB565',
    CSI2_DT_RGB666: 'RGB666',
    CSI2_DT_RGB888: 'RGB888',
    CSI2_DT_RAW6: 'RAW6',
    CSI2_DT_RAW7: 'RAW7',
    CSI2_DT_RAW8: 'RAW8',
    CSI2_DT_RAW10: 'RAW10',
    CSI2_DT_RAW12: 'RAW12',
    CSI2_DT_RAW14: 'RAW14',
    CSI2_DT_JPEG: 'JPEG',
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'mipi_csi2_dphy'
    name = 'MIPI CSI-2 D-PHY'
    longname = 'MIPI Camera Serial Interface 2 D-PHY'
    desc = 'High-speed serial interface for camera applications using D-PHY.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['mipi_csi2_dphy']
    tags = ['Embedded/industrial', 'Camera']

    # Channel definitions
    channels = (
        {'id': 'clk_p', 'name': 'CLK_P', 'desc': 'Clock lane positive'},
        {'id': 'data0_p', 'name': 'DATA0_P', 'desc': 'Data lane 0 positive'},
    )

    # Optional channels (can be None)
    optional_channels = (
        {'id': 'data1_p', 'name': 'DATA1_P', 'desc': 'Data lane 1 positive (optional)'},
        {'id': 'data2_p', 'name': 'DATA2_P', 'desc': 'Data lane 2 positive (optional)'},
        {'id': 'data3_p', 'name': 'DATA3_P', 'desc': 'Data lane 3 positive (optional)'},
    )

    # Decoder options
    options = (
        {'id': 'lanes', 'desc': 'Number of data lanes (0=auto-detect)',
         'default': '0', 'values': ('0', '1', '2', '3', '4')},
        {'id': 'bitrate', 'desc': 'Expected bitrate (Mbps)',
         'default': '1000', 'values': ('500', '1000', '1500', '2000', '2500')},
    )

    # Annotations
    annotations = (
        ('sot', 'Start of Transmission'),
        ('eot', 'End of Transmission'),
        ('sync', 'Lane synchronization'),
        ('short-packet', 'Short packet'),
        ('long-packet', 'Long packet'),
        ('payload', 'Packet payload'),
        ('footer', 'Packet footer'),
        ('error', 'Protocol error'),
        ('data-type', 'Data type'),
        ('virtual-channel', 'Virtual channel'),
        ('lane-state', 'Lane state'),
        ('lane-count', 'Detected lane count'),
        ('bit-shift', 'Bit shifting'),
        ('sync-byte', 'Sync byte detected'),
    )

    # Annotation rows for grouping
    annotation_rows = (
        ('markers', 'Markers', (0, 1, 2)),
        ('packets', 'Packets', (3, 4, 5, 6)),
        ('errors', 'Errors', (7,)),
        ('metadata', 'Metadata', (8, 9)),
        ('lane-info', 'Lane Information', (10, 11, 12, 13)),
    )

    # Binary outputs
    binary = (
        ('short-packet', 'Short packet data'),
        ('long-packet', 'Long packet data'),
        ('payload', 'Payload data'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.num_lanes = 0  # 0 = auto-detect
        self.detected_lanes = 0
        self.expected_bitrate = 1000

        # State variables
        self.state = 'IDLE'
        self.lane_states = [LANE_STATE_LP_11] * 4  # Track lane states
        self.lane_state_start = [0] * 4  # Track when each lane state started
        self.packet_start = None
        self.packet_data = []
        self.current_lane = 0

        # Serial bit shifting
        self.bit_shifters = [0] * 4  # Bit shifters for each lane
        self.bit_counters = [0] * 4  # Bit counters for each lane
        self.sync_detected = [False] * 4  # Sync detection per lane
        self.byte_buffers = [[] for _ in range(4)]  # Byte buffers per lane

        # Lane detection
        self.lane_detection_active = True
        self.lane_transition_count = [0] * 4  # Count transitions to HS state
        self.lane_detection_threshold = 10  # Minimum transitions to consider lane active
        self.lane_activity_start = [None] * 4  # Track when each lane started showing activity
        self.lane_activity_duration = 5000  # Minimum duration (samples) for lane to be considered active
        self.lane_sync_detected = [False] * 4  # Track if sync byte was detected on each lane

        # Output registers
        self.out_python = None
        self.out_ann = None
        self.out_binary = None

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_binary = self.register(srd.OUTPUT_BINARY)

        # Get configuration options
        if hasattr(self, 'options') and isinstance(self.options, dict):
            self.num_lanes = int(self.options.get('lanes', '0'))
            self.expected_bitrate = int(self.options.get('bitrate', '1000'))
        else:
            # Use defaults for testing
            self.num_lanes = 0  # Auto-detect
            self.expected_bitrate = 1000

        # Add a test annotation to verify decoder is working
        self.putg(0, 1000, 0, 'MIPI CSI-2 D-PHY Decoder Started')

        # Add a more prominent test annotation for lane states
        self.putg(10000, 12000, 10, 'LANE STATE TEST - Should be visible')

        # Add very prominent test annotations that should definitely be visible
        self.putg(5000, 15000, 10, 'VERY LONG LANE STATE TEST')
        self.putg(5000, 15000, 11, 'VERY LONG LANE COUNT TEST')
        self.putg(5000, 15000, 12, 'VERY LONG BIT SHIFT TEST')

    def putg(self, ss, es, cls, text):
        self.put(ss, es, self.out_ann, [cls, [text]])

    def putp(self, ss, es, data):
        self.put(ss, es, self.out_python, data)

    def putb(self, ss, es, data):
        self.put(ss, es, self.out_binary, data)

    def detect_lane_state(self, lane, data_p, data_n=None):
        """Detect the state of a lane based on signals"""
        if data_p is None:
            return None

        # For MIPI CSI-2 with single-ended signals, we need to be more careful
        # Static signals (high or low) should be treated as LP state
        # Only consider HS state when we see actual transitions

        # Store the previous signal value for this lane
        if not hasattr(self, 'lane_prev_signal'):
            self.lane_prev_signal = [None] * 4

        # If this is the first sample for this lane, assume LP state
        if self.lane_prev_signal[lane] is None:
            self.lane_prev_signal[lane] = data_p
            return LANE_STATE_LP_11

        # Check if the signal has changed (indicating HS activity)
        if self.lane_prev_signal[lane] != data_p:
            # Signal changed - this indicates HS activity
            self.lane_prev_signal[lane] = data_p
            if data_p == 1:
                return LANE_STATE_HS_1
            else:
                return LANE_STATE_HS_0
        else:
            # Signal hasn't changed - this is likely LP state
            self.lane_prev_signal[lane] = data_p
            return LANE_STATE_LP_11

    def update_lane_state(self, lane, new_state, ss):
        """Update lane state and annotate if changed"""
        if new_state is None:
            return

        if self.lane_states[lane] != new_state:
            old_state = self.lane_states[lane]
            self.lane_states[lane] = new_state
            self.lane_state_start[lane] = ss

                                                # Annotate state change - make it more visible with longer duration
            self.putg(self.lane_state_start[lane], ss + 1000, 10, f'Lane{lane}: {old_state}→{new_state}')
            self.putp(self.lane_state_start[lane], ss, ['LANE_STATE', [lane, new_state]])

            # Also add a more visible annotation for significant state changes
            if new_state in [LANE_STATE_HS_0, LANE_STATE_HS_1]:
                self.putg(self.lane_state_start[lane], ss + 2000, 2, f'Lane{lane} HS: {new_state}')

            # Track transitions to HS state for lane detection
            if new_state in [LANE_STATE_HS_0, LANE_STATE_HS_1, LANE_STATE_HS_SYNC]:
                self.lane_transition_count[lane] += 1

                # Record when lane first started showing activity
                if self.lane_activity_start[lane] is None:
                    self.lane_activity_start[lane] = ss

                # Auto-detect lane count
                if self.lane_detection_active and self.lane_transition_count[lane] >= self.lane_detection_threshold:
                    self.detect_active_lanes()

    def detect_active_lanes(self):
        """Detect how many lanes are actually active"""
        active_lanes = 0
        lane_details = []
        for lane in range(4):
            # A lane is considered active if it has sufficient transitions and sustained activity
            # For now, focus on the most active lane (lane 0) and ignore others unless they have sync
            if (self.lane_transition_count[lane] >= self.lane_detection_threshold and
                self.lane_activity_start[lane] is not None and
                (self.samplenum - self.lane_activity_start[lane]) >= self.lane_activity_duration):

                # Only count lane 0 as active by default, unless other lanes have both sync AND significant activity
                if lane == 0 or (self.lane_sync_detected[lane] and self.lane_transition_count[lane] >= 50):
                    active_lanes += 1
                    lane_details.append(f"Lane{lane}({self.lane_transition_count[lane]})")

        if active_lanes != self.detected_lanes:
            self.detected_lanes = active_lanes
            print(f"DEBUG: Detected {self.detected_lanes} active lanes: {', '.join(lane_details)}")
            self.putg(self.samplenum, self.samplenum + 1, 11, f'Detected: {self.detected_lanes} lanes')
            self.putp(self.samplenum, self.samplenum + 1, ['LANE_COUNT', [self.detected_lanes]])

    def shift_bits(self, lane, bit_value, ss):
        """Shift bits into the bit shifter for a lane (LSB first)"""
        if lane >= 4:
            return

        # Shift in the new bit (LSB first - MIPI CSI-2 standard)
        # For LSB first: new bit goes to the rightmost position
        self.bit_shifters[lane] = (self.bit_shifters[lane] >> 1) | (bit_value << 7)
        self.bit_counters[lane] += 1

        # Annotate bit shifting
        self.putg(ss, ss + 1, 12, f'Lane{lane}: {bit_value}')

        # Check for sync byte when we have 8 bits
        if self.bit_counters[lane] >= 8:
            byte_value = self.bit_shifters[lane] & 0xFF
            self.bit_shifters[lane] = 0
            self.bit_counters[lane] = 0

            print(f"DEBUG: Lane{lane}: 0x{byte_value:02X}")
            # Check for sync byte (try both 0xAB and 0x55)
            if (byte_value == SYNC_MARKER ) and not self.sync_detected[lane]:
                self.sync_detected[lane] = True
                self.lane_sync_detected[lane] = True  # Mark lane as having sync
                self.putg(ss - 7, ss + 1, 13, f'Lane{lane}: SYNC 0x{byte_value:02X}')
                self.putp(ss - 7, ss + 1, ['SYNC', None])
                print(f"DEBUG: Sync byte detected on lane {lane}: 0x{byte_value:02X}")

            # Add to byte buffer
            self.byte_buffers[lane].append(byte_value)

            # Process complete bytes
            self.process_lane_bytes(lane, ss)

    def process_lane_bytes(self, lane, ss):
        """Process complete bytes from a lane"""
        if not self.byte_buffers[lane]:
            return

        # Process all available bytes
        while self.byte_buffers[lane]:
            byte_val = self.byte_buffers[lane].pop(0)

            # Check for markers
            if byte_val == SOT_MARKER:
                self.decode_sot(ss - 8, ss + 1)
            elif byte_val == EOT_MARKER:
                self.decode_eot(ss - 8, ss + 1)
            elif byte_val == SYNC_MARKER:
                # Already handled in shift_bits
                pass
            else:
                # Regular data byte
                self.packet_data.append(byte_val)

    def decode_sot(self, ss, es):
        """Decode Start of Transmission marker"""
        self.state = 'PACKET'
        self.packet_start = ss
        self.packet_data = []

        self.putp(ss, es, ['SOT', None])
        self.putg(ss, es, 0, 'SOT')

    def decode_eot(self, ss, es):
        """Decode End of Transmission marker"""
        self.state = 'IDLE'

        self.putp(ss, es, ['EOT', None])
        self.putg(ss, es, 1, 'EOT')

    def decode_sync(self, ss, es):
        """Decode lane synchronization"""
        self.putp(ss, es, ['SYNC', None])
        self.putg(ss, es, 2, 'SYNC')

    def decode_short_packet(self, ss, es, data):
        """Decode short packet header"""
        if len(data) < 4:
            self.putg(ss, es, 7, f'Short packet too short: {len(data)} bytes')
            return

        data_type = data[0]
        virtual_channel = data[1] & 0x03
        payload_data = data[2:4]

        dt_name = DATA_TYPE_NAMES.get(data_type, f'Unknown({data_type:02X})')

        self.putp(ss, es, ['SHORT_PACKET', [data_type, virtual_channel, payload_data]])
        self.putg(ss, es, 3, f'Short: {dt_name} VC{virtual_channel}')
        self.putg(ss, es, 8, f'DT: {dt_name}')
        self.putg(ss, es, 9, f'VC: {virtual_channel}')

        # Binary output
        self.putb(ss, es, data)

    def decode_long_packet(self, ss, es, data):
        """Decode long packet header"""
        if len(data) < 6:
            self.putg(ss, es, 7, f'Long packet too short: {len(data)} bytes')
            return

        data_type = data[0]
        virtual_channel = data[1] & 0x03
        frame_count = data[2]
        line_count = (data[3] << 8) | data[4]
        pixel_count = (data[5] << 8) | data[6] if len(data) > 6 else 0

        dt_name = DATA_TYPE_NAMES.get(data_type, f'Unknown({data_type:02X})')

        self.putp(ss, es, ['LONG_PACKET', [data_type, virtual_channel, frame_count, line_count, pixel_count]])
        self.putg(ss, es, 4, f'Long: {dt_name} VC{virtual_channel}')
        self.putg(ss, es, 8, f'DT: {dt_name}')
        self.putg(ss, es, 9, f'VC: {virtual_channel}')
        self.putg(ss, es, 10, f'Frame: {frame_count}')
        self.putg(ss, es, 11, f'Line: {line_count}')
        self.putg(ss, es, 12, f'Pixel: {pixel_count}')

        # Binary output
        self.putb(ss, es, data)

    def decode_payload(self, ss, es, data):
        """Decode packet payload"""
        self.putp(ss, es, ['PAYLOAD', data])
        self.putg(ss, es, 5, f'Payload: {len(data)} bytes')

        # Binary output
        self.putb(ss, es, data)

    def decode_footer(self, ss, es, data):
        """Decode packet footer/checksum"""
        self.putp(ss, es, ['FOOTER', data])
        self.putg(ss, es, 6, f'Footer: {len(data)} bytes')

    def decode_error(self, ss, es, error_msg):
        """Decode protocol error"""
        self.putp(ss, es, ['ERROR', error_msg])
        self.putg(ss, es, 7, f'Error: {error_msg}')

    def decode(self):
        """Main decode function with state machine and serial bit shifting"""
        while True:
            # Wait for clock edge on clk_p
            pins = self.wait({0: 'e'})

            # Extract the channels we need (simplified for positive signals only)
            if len(pins) >= 5:
                clk_p, data0_p, data1_p, data2_p, data3_p = pins[0:5]
            else:
                # Fallback if fewer channels are available
                clk_p = pins[0] if len(pins) > 0 else None
                data0_p = pins[1] if len(pins) > 1 else None
                data1_p = pins[2] if len(pins) > 2 else None
                data2_p = pins[3] if len(pins) > 3 else None
                data3_p = pins[4] if len(pins) > 4 else None

            # Process each lane
            data_lanes = [data0_p, data1_p, data2_p, data3_p]

            for lane in range(4):
                data_p = data_lanes[lane]
                if data_p is not None:
                    # Detect lane state using single-ended signals
                    lane_state = self.detect_lane_state(lane, data_p)
                    self.update_lane_state(lane, lane_state, self.samplenum)
                    # print(f"DEBUG: Lane {lane} state: {lane_state}")

                    # If in HS state, shift bits (process on all lanes to detect sync)
                    if lane_state in [LANE_STATE_HS_0, LANE_STATE_HS_1]:
                        bit_value = 1 if lane_state == LANE_STATE_HS_1 else 0
                        self.shift_bits(lane, bit_value, self.samplenum)

            # Use detected lane count if auto-detect is enabled
            active_lanes = self.detected_lanes if self.num_lanes == 0 else self.num_lanes
            if active_lanes == 0:
                active_lanes = 1  # Default to 1 lane if none detected yet