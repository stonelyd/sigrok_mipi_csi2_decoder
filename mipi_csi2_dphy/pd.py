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
SYNC_MARKER = 0xB8  # Start of Transmission / Sync byte

# D-PHY Lane States
LANE_STATE_LP_11 = 'LP-11'  # Low Power Stop state
LANE_STATE_LP_01 = 'LP-01'  # Low Power Turn-around
LANE_STATE_LP_00 = 'LP-00'  # Low Power Turn-around
LANE_STATE_LP_10 = 'LP-10'  # Low Power Turn-around
LANE_STATE_THS_SETTLE = 'THS-SETTLE'  # High Speed Settle (custom state)
LANE_STATE_HS = 'HS'        # High Speed Data
LANE_STATE_HS_SYNC = 'HS-SYNC'  # High Speed Sync
LANE_STATE_HS_TRAIL = 'HS-TRAIL'  # High Speed Trail (packet end)

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
CSI2_DT_RAW16 = 0x2E
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
    CSI2_DT_RAW16: 'RAW16',
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
        {'id': 'clk_n', 'name': 'CLK_N', 'desc': 'Clock lane negative'},
        {'id': 'clk_p', 'name': 'CLK_P', 'desc': 'Clock lane positive'},
        {'id': 'data0_n', 'name': 'DATA0_N', 'desc': 'Data lane 0 negative'},
        {'id': 'data0_p', 'name': 'DATA0_P', 'desc': 'Data lane 0 positive'},
    )

    # Optional channels (can be None)
    optional_channels = (
        {'id': 'data1_n', 'name': 'DATA1_N', 'desc': 'Data lane 1 negative (optional)'},
        {'id': 'data1_p', 'name': 'DATA1_P', 'desc': 'Data lane 1 positive (optional)'},
        {'id': 'data2_n', 'name': 'DATA2_N', 'desc': 'Data lane 2 negative (optional)'},
        {'id': 'data2_p', 'name': 'DATA2_P', 'desc': 'Data lane 2 positive (optional)'},
        {'id': 'data3_n', 'name': 'DATA3_N', 'desc': 'Data lane 3 negative (optional)'},
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
        ('packet-header', 'Packet header'),
        ('na-placeholder', 'Placeholder'),
        ('payload', 'Packet payload'),
        ('footer', 'Packet footer'),
        ('error', 'Protocol error'),
        ('data-type', 'Data type'),
        ('virtual-channel', 'Virtual channel'),
        ('lane0-state', 'Lane 0 state'),
        ('lane1-state', 'Lane 1 state'),
        ('lane2-state', 'Lane 2 state'),
        ('lane3-state', 'Lane 3 state'),
        ('lane0-sync', 'Lane 0 sync byte'),
        ('lane1-sync', 'Lane 1 sync byte'),
        ('lane2-sync', 'Lane 2 sync byte'),
        ('lane3-sync', 'Lane 3 sync byte'),
        ('pixel-data', 'Decoded pixel data'),
    )

    # Annotation rows for grouping
    annotation_rows = (
        ('packets', 'Packets', (3, 4, 5, 6)),
        ('errors', 'Errors', (7,)),
        ('metadata', 'Metadata', (8, 9)),
        ('lane0-info', 'Lane 0', (10, 14)),
        ('lane1-info', 'Lane 1', (11, 15)),
        ('lane2-info', 'Lane 2', (12, 16)),
        ('lane3-info', 'Lane 3', (13, 17)),
        ('pixel-data', 'Pixel Data', (18,)),
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
        self.byte_synchronized = [False] * 4  # Track if byte boundaries are synchronized
        self.packet_state = 'IDLE'  # Track packet parsing state
        self.packet_buffer = []  # Buffer for current packet
        self.expected_packet_length = 0  # Expected total packet length
        self.packet_end_detected = [False] * 4  # Track if packet end detected per lane

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
            pass  # print(f"DEBUG: Received samplerate = {value} Hz from sigrok")

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


    def putg(self, ss, es, cls, text):
        self.put(ss, es, self.out_ann, [cls, [text]])

    def putp(self, ss, es, data):
        self.put(ss, es, self.out_python, data)

    def putb(self, ss, es, data):
        self.put(ss, es, self.out_binary, data)

    def detect_lane_state(self, lane, data_p, data_n):
        """Detect D-PHY lane state with THS-SETTLE and simplified HS detection"""
        if data_p is None:
            return None

        # Handle missing data_n (single-ended fallback)
        if data_n is None:
            data_n = 0  # Assume data_n=0 for single-ended signals

        # Initialize tracking state
        if not hasattr(self, 'lane_prev_state'):
            self.lane_prev_state = [LANE_STATE_LP_11] * 4
            self.lane_in_ths_settle = [False] * 4
            self.lane_sync_detected = [False] * 4
            self.lane_was_lp00 = [False] * 4

        prev_state = self.lane_prev_state[lane]

        # Determine current physical state based on differential pair
        if data_p == 1 and data_n == 1:
            physical_state = LANE_STATE_LP_11  # Stop state
        elif data_p == 0 and data_n == 1:
            physical_state = LANE_STATE_LP_01  # Turnaround
        elif data_p == 0 and data_n == 0:
            physical_state = LANE_STATE_LP_00  # Turnaround
        elif data_p == 1 and data_n == 0:
            physical_state = LANE_STATE_LP_10  # Turnaround
        else:
            # Invalid state - should not happen with proper differential signals
            physical_state = LANE_STATE_LP_11

        # State machine logic with THS-SETTLE

        # 1. Return to LP-11 from any state
        if physical_state == LANE_STATE_LP_11:
            self.lane_in_ths_settle[lane] = False
            self.lane_sync_detected[lane] = False
            self.lane_prev_state[lane] = LANE_STATE_LP_11
            return LANE_STATE_LP_11

        # 2. Track LP-00 state for THS-SETTLE detection
        if physical_state == LANE_STATE_LP_00:
            self.lane_was_lp00[lane] = True
        elif physical_state == LANE_STATE_LP_11:
            self.lane_was_lp00[lane] = False

        # 3. Transition to THS-SETTLE when leaving LP-00 after the sequence
        if (prev_state == LANE_STATE_LP_00 and physical_state != LANE_STATE_LP_00 and
            self.lane_was_lp00[lane]):
            self.lane_in_ths_settle[lane] = True
            self.lane_was_lp00[lane] = False  # Reset flag
            self.lane_prev_state[lane] = LANE_STATE_THS_SETTLE
            return LANE_STATE_THS_SETTLE

        # 4. Stay in THS-SETTLE until sync detected
        if self.lane_in_ths_settle[lane]:
            # Check if sync has been detected (will be set by sync detection logic)
            if self.lane_sync_detected[lane]:
                self.lane_in_ths_settle[lane] = False
                self.lane_prev_state[lane] = LANE_STATE_HS
                return LANE_STATE_HS
            else:
                # Stay in THS-SETTLE regardless of physical state
                return LANE_STATE_THS_SETTLE

        # 5. Transition from HS to HS-TRAIL when packet end is detected
        if prev_state == LANE_STATE_HS:
            if self.packet_end_detected[lane]:
                # Transition to HS-TRAIL state after packet end
                self.packet_end_detected[lane] = False  # Reset flag
                self.lane_prev_state[lane] = LANE_STATE_HS_TRAIL
                return LANE_STATE_HS_TRAIL
            elif physical_state == LANE_STATE_LP_11:
                # Direct transition from HS to LP-11 (if no packet end detected)
                pass
            else:
                # Stay in HS mode
                return LANE_STATE_HS

        # 6. Transition from HS-TRAIL to LP-11
        if prev_state == LANE_STATE_HS_TRAIL:
            if physical_state == LANE_STATE_LP_11:
                self.lane_prev_state[lane] = LANE_STATE_LP_11
                return LANE_STATE_LP_11
            else:
                # Stay in HS-TRAIL until LP-11 is reached
                return LANE_STATE_HS_TRAIL

        # 7. Default: follow physical state for normal LP states
        self.lane_prev_state[lane] = physical_state
        return physical_state

    def update_lane_state(self, lane, new_state, ss):
        """Update lane state and annotate if changed"""
        if new_state is None:
            return

        if self.lane_states[lane] != new_state:
            old_state = self.lane_states[lane]
            old_start = self.lane_state_start[lane]

            # Annotate the previous state duration
            if old_start is not None:
                self.putg(old_start, ss, 10 + lane, f'L{lane}: {old_state}')

            # Update state tracking
            self.lane_states[lane] = new_state
            self.lane_state_start[lane] = ss
            self.putp(ss, ss, ['LANE_STATE', [lane, new_state]])

            # Immediately annotate LP-11 state to ensure it's always visible
            if new_state == LANE_STATE_LP_11:
                # Use a longer annotation period for LP-11 to ensure visibility
                self.putg(ss, ss + 100, 10 + lane, f'L{lane}: LP-11')

            # Add transition markers for key state changes
            if new_state == LANE_STATE_HS and old_state == LANE_STATE_THS_SETTLE:
                pass  # HS Start transition
            elif new_state == LANE_STATE_HS_TRAIL and old_state == LANE_STATE_HS:
                pass  # Packet End transition
            elif new_state == LANE_STATE_LP_11 and old_state == LANE_STATE_HS_TRAIL:
                # HS End transition - annotate the return to LP-11
                # self.putg(ss, ss + 1, 10 + lane, f'L{lane}: HS-END')

            # Track transitions to HS state for lane detection
            if new_state in [LANE_STATE_HS, LANE_STATE_HS_SYNC]:
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
        all_lane_info = []

        # First, gather info about all lanes for debugging
        for lane in range(4):
            transitions = self.lane_transition_count[lane]
            has_sync = self.lane_sync_detected[lane]
            start_time = self.lane_activity_start[lane]
            duration = (self.samplenum - start_time) if start_time is not None else 0
            all_lane_info.append(f"L{lane}:T{transitions}:S{int(has_sync)}:D{duration}")

        print(f"DEBUG: Lane activity analysis: {' | '.join(all_lane_info)}")

        for lane in range(4):
            # A lane is considered active if it has sufficient transitions and sustained activity
            if (self.lane_transition_count[lane] >= self.lane_detection_threshold and
                self.lane_activity_start[lane] is not None and
                (self.samplenum - self.lane_activity_start[lane]) >= self.lane_activity_duration):

                # Improved multi-lane detection logic:
                # Lane 0: Always counted if it meets basic criteria (it typically carries sync)
                # Other lanes: Count if they have significant activity (reduced threshold from 50 to 20)
                if lane == 0 or self.lane_transition_count[lane] >= 20:
                    active_lanes += 1
                    sync_status = "SYNC" if self.lane_sync_detected[lane] else "DATA"
                    lane_details.append(f"Lane{lane}({self.lane_transition_count[lane]},{sync_status})")
                    print(f"DEBUG: Lane {lane} counted as active - transitions: {self.lane_transition_count[lane]}, sync: {self.lane_sync_detected[lane]}")

        if active_lanes != self.detected_lanes:
            self.detected_lanes = active_lanes
            print(f"DEBUG: Detected {self.detected_lanes} active lanes: {', '.join(lane_details)}")
            self.putp(self.samplenum, self.samplenum + 1, ['LANE_COUNT', [self.detected_lanes]])

    def shift_bits(self, lane, bit_value, ss):
        """Shift bits into the bit shifter for a lane (LSB first)"""
        if lane >= 4:
            return

        # Shift in the new bit (LSB first - MIPI CSI-2 standard)
        self.bit_shifters[lane] = (self.bit_shifters[lane] >> 1) | (bit_value << 7)
        self.bit_counters[lane] += 1

        if not self.sync_detected[lane]:
            byte_value = self.bit_shifters[lane] & 0xFF
            # self.bit_counters[lane] = 0  # Reset counter for next byte

            print(f"DEBUG: Lane{lane}: Pre-sync Byte 0x{byte_value:02X}")
        else:
            if self.bit_counters[lane] >= 8:
                byte_value = self.bit_shifters[lane] & 0xFF
                self.bit_shifters[lane] = 0  # Reset for next byte
                self.bit_counters[lane] = 0  # Reset counter for next byte
                print(f"DEBUG: Lane{lane}: Post-sync Byte 0x{byte_value:02X}")

                self.process_packet_byte(lane, byte_value, ss)

        # Check for sync byte detection - look for 0xB8 or start processing after seeing non-zero data
        if not self.sync_detected[lane]:
            if byte_value == SYNC_MARKER:
                self.sync_detected[lane] = True
                self.lane_sync_detected[lane] = True
                self.byte_synchronized[lane] = True
                self.bit_counters[lane] = 0  # Reset bit counter after sync
                self.packet_state = 'COLLECTING_PACKET'
                self.packet_buffer = []
                self.putg(ss - 7, ss + 1, 14 + lane, f'Lane{lane}: SYNC 0x{byte_value:02X}')
                self.putp(ss - 7, ss + 1, ['SYNC', None])
                print(f"DEBUG: Sync detected on lane {lane}: 0x{byte_value:02X}")
                return

    def process_packet_byte(self, lane, byte_value, ss):
        """Process a complete byte in packet context"""
        print(f"DEBUG: Processing packet byte 0x{byte_value:02X} on lane {lane}, state: {self.packet_state}")

        # After sync detection, we expect packet data (DataID is first byte)
        if self.packet_state == 'COLLECTING_PACKET':
            # Add byte to packet buffer
            self.packet_buffer.append(byte_value)
            print(f"DEBUG: Added byte 0x{byte_value:02X} to packet buffer (length: {len(self.packet_buffer)})")

            # Check if we have enough bytes for a packet header (4 bytes minimum)
            if len(self.packet_buffer) == 4:
                word_count = self.analyze_packet_header(ss)
                self.expected_packet_length = word_count

            # Check if we've received the complete packet based on expected length
            if self.expected_packet_length > 0 and len(self.packet_buffer) >= self.expected_packet_length:
                print(f"DEBUG: Packet complete - received {len(self.packet_buffer)} bytes, expected {self.expected_packet_length}")
                self.process_complete_packet(ss)
                self.packet_state = 'IDLE'
                self.putp(ss - 7, ss + 1, ['PACKET_COMPLETE', None])
                # Mark packet end detected for triggering HS-TRAIL state
                for l in range(4):
                    if self.byte_synchronized[l]:
                        self.packet_end_detected[l] = True
                # Reset for next packet
                self.packet_buffer = []
                self.expected_packet_length = 0
                # Reset sync detection to allow detection of next packet's sync byte
                for l in range(4):
                    if self.byte_synchronized[l]:
                        self.sync_detected[l] = False
                        print(f"DEBUG: Reset sync_detected for lane {l} after packet completion")

    def analyze_packet_header(self, ss):
        """Analyze packet header to determine packet type and length"""
        if len(self.packet_buffer) < 4:
            return 0

        # First 4 bytes form the packet header (after sync byte 0xB8)
        # CSI-2 packet format: [DataID, Data_Byte1, Data_Byte2, ECC]
        header = self.packet_buffer[:4]
        data_id = header[0]  # DataID contains the actual data type
        data_type = data_id  # For short packets, DataID IS the data type
        virtual_channel = 0  # VC is typically 0 for basic packets, or embedded in DataID upper bits
        data_field = (header[2] << 8) | header[1]  # 16-bit data field from data bytes

        print(f"DEBUG: Header analysis - DataID: 0x{data_id:02X} (DT: 0x{data_type:02X}), Data: 0x{data_field:04X}, ECC: 0x{header[3]:02X}")

        # Determine packet type based on data type value
        # Data types 0x00-0x07 and 0x08-0x0F are typically short packets
        # Data types 0x10+ are typically long packets (image data)
        if data_type <= 0x0F:
            # Short packet - always exactly 4 bytes total
            print(f"DEBUG: Short packet detected - DT: 0x{data_type:02X}")
            word_count = 4  # Short packets are always 4 bytes
            # Create properly formatted header for decode function: [DataID, VC+DT, Data_Low, Data_High]
            formatted_header = [data_id, (virtual_channel << 6) | data_type, header[1], header[2]]
            self.decode_short_packet(ss, formatted_header)
            return word_count
        else:
            # Long packet - the data field is actually word count for long packets
            word_count = 4 + data_field + 2  # header + payload + checksum
            print(f"DEBUG: Long packet detected, expecting {data_field} payload bytes + 2 checksum bytes (total: {word_count})")
            return word_count


    def process_complete_packet(self, ss):
        """Process a complete packet when EOT is received"""
        if len(self.packet_buffer) >= 4:
            header = self.packet_buffer[:4]
            # Use the same parsing logic as analyze_packet_header
            data_id = header[0]  # DataID contains the actual data type
            data_type = data_id  # For short packets, DataID IS the data type

            # For short packets (DT 0x00-0x0F), there's no separate word count
            # The packet is always exactly 4 bytes: [DataID, Data1, Data2, ECC]
            if data_type <= 0x0F:
                # Short packet - already processed in analyze_packet_header, no need to reprocess
                print(f"DEBUG: Short packet complete - DT: 0x{data_type:02X}")
            else:
                # Long packet - use data bytes as word count
                word_count = (header[2] << 8) | header[1]  # Use data bytes as word count for long packets
                if len(self.packet_buffer) >= 4 + word_count + 2:
                    payload = self.packet_buffer[4:4+word_count]
                    checksum = self.packet_buffer[4+word_count:4+word_count+2]
                    self.decode_long_packet(ss, header, payload, checksum)
                else:
                    print(f"DEBUG: Incomplete long packet - expected {4+word_count+2} bytes, got {len(self.packet_buffer)}")

        self.packet_buffer = []
        self.packet_state = 'SYNC_DETECTED'  # Ready for next packet

    def decode_sot(self, ss, es):
        """Decode Start of Transmission marker"""
        self.state = 'PACKET'
        self.packet_start = ss
        self.packet_data = []

        self.putp(ss, es, ['SOT', None])

    def decode_eot(self, ss, es):
        """Decode End of Transmission marker"""
        self.state = 'IDLE'

        self.putp(ss, es, ['EOT', None])

    def decode_sync(self, ss, es):
        """Decode lane synchronization"""
        self.putp(ss, es, ['SYNC', None])

    def decode_short_packet(self, ss, header):
        """Decode short packet with proper CSI-2 format"""
        if len(header) < 4:
            self.putg(ss, ss + 32, 7, f'Short packet too short: {len(header)} bytes')
            return

        data_id = header[0]
        vc_dt = header[1]
        virtual_channel = (vc_dt >> 6) & 0x03  # Upper 2 bits
        data_type = vc_dt & 0x3F  # Lower 6 bits
        data_field = (header[3] << 8) | header[2]  # 16-bit data field (little endian)

        # Decode short packet types based on CSI-2 specification
        packet_info = self.decode_short_packet_type(data_type, data_field)

        dt_name = DATA_TYPE_NAMES.get(data_type, f'0x{data_type:02X}')

        # TODO: adjust time for lane count
        self.putp(ss-30, ss, ['SHORT_PACKET', [data_type, virtual_channel, data_field]])
        self.putg(ss-30, ss, 3, f'Short: {packet_info} VC{virtual_channel}')
        self.putg(ss-30, ss, 8, f'DT: {dt_name}')
        self.putg(ss-30, ss, 9, f'VC: {virtual_channel}')

        print(f"DEBUG: Short packet decoded - DT: 0x{data_type:02X} ({packet_info}), VC: {virtual_channel}, Data: 0x{data_field:04X}")

        # Binary output
        self.putb(ss, ss + 32, header)

    def decode_short_packet_type(self, data_type, data_field):
        """Decode specific short packet types according to CSI-2 spec"""
        # Short packet data types (from CSI-2 spec)
        short_packet_types = {
            0x00: f"Frame Start (Frame: {data_field})",
            0x01: f"Frame End (Frame: {data_field})",
            0x02: f"Line Start (Line: {data_field})",
            0x03: f"Line End (Line: {data_field})",
            0x08: f"Generic Short 1 (Data: 0x{data_field:04X})",
            0x09: f"Generic Short 2 (Data: 0x{data_field:04X})",
            0x0A: f"Generic Short 3 (Data: 0x{data_field:04X})",
            0x0B: f"Generic Short 4 (Data: 0x{data_field:04X})",
            0x0C: f"Generic Short 5 (Data: 0x{data_field:04X})",
            0x0D: f"Generic Short 6 (Data: 0x{data_field:04X})",
            0x0E: f"Generic Short 7 (Data: 0x{data_field:04X})",
            0x0F: f"Generic Short 8 (Data: 0x{data_field:04X})",
        }

        return short_packet_types.get(data_type, f"Unknown Short (0x{data_type:02X}, Data: 0x{data_field:04X})")

    def decode_pixel_data(self, ss, es, data_type, payload):
        """Decode pixel data from long packet payload based on data type"""
        if not payload or len(payload) < 1:
            return

        # Calculate time per byte for individual pixel annotations
        # The payload time span (es - ss) represents the actual time used by the payload
        # Individual pixels should be distributed across this full time span
        total_time = es - ss

        if data_type == CSI2_DT_RAW8:
            # RAW8: 1 byte per pixel
            for i in range(len(payload)):
                pixel_value = payload[i]
                pixel_start = ss + (i * total_time) // len(payload)
                pixel_end = ss + ((i + 1) * total_time) // len(payload)
                self.putg(pixel_start, pixel_end, 18, f"{pixel_value:02X}")
        elif data_type == CSI2_DT_RAW10:
            # RAW10: 5 bytes contain 4 pixels (10 bits each, packed)
            for i in range(0, len(payload), 5):
                if i + 5 <= len(payload):
                    # Unpack 4 pixels from 5 bytes
                    # RAW10 format: 4 pixels packed into 5 bytes
                    # Bytes: [P0[9:2], P1[9:2], P2[9:2], P3[9:2], P3[1:0]P2[1:0]P1[1:0]P0[1:0]]
                    b0, b1, b2, b3, b4 = payload[i:i+5]
                    pixels = [
                        (b0 << 2) | ((b4 >> 6) & 0x03),  # P0: high 8 bits + low 2 bits
                        (b1 << 2) | ((b4 >> 4) & 0x03),  # P1: high 8 bits + low 2 bits
                        (b2 << 2) | ((b4 >> 2) & 0x03),  # P2: high 8 bits + low 2 bits
                        (b3 << 2) | (b4 & 0x03)          # P3: high 8 bits + low 2 bits
                    ]
                    # Annotate each of the 4 pixels from this 5-byte group
                    for j, pixel_value in enumerate(pixels):
                        # Calculate time position based on pixel index within the group
                        pixel_idx = (i // 5) * 4 + j
                        total_pixels = (len(payload) // 5) * 4
                        pixel_start = ss + (pixel_idx * total_time) // total_pixels
                        pixel_end = ss + ((pixel_idx + 1) * total_time) // total_pixels
                        self.putg(pixel_start, pixel_end, 18, f"{pixel_value:03X}")
        elif data_type == CSI2_DT_RAW16:
            # RAW16: 2 bytes per pixel (16 bits each, little endian)
            for i in range(0, len(payload), 2):
                if i + 1 < len(payload):
                    # Combine two bytes into 16-bit pixel value (little endian)
                    pixel_value = payload[i] | (payload[i + 1] << 8)
                    pixel_start = ss + (i * total_time) // len(payload)
                    pixel_end = ss + ((i + 2) * total_time) // len(payload)
                    self.putg(pixel_start, pixel_end, 18, f"{pixel_value:04X}")
        elif data_type == CSI2_DT_RGB888:
            # RGB888: 3 bytes per pixel (R, G, B)
            for i in range(0, len(payload), 3):
                if i + 2 < len(payload):
                    r, g, b = payload[i:i+3]
                    # Create annotation spanning the 3 bytes for this pixel
                    pixel_start = ss + (i * total_time) // len(payload)
                    pixel_end = ss + ((i + 3) * total_time) // len(payload)
                    self.putg(pixel_start, pixel_end, 18, f"{r:02X}{g:02X}{b:02X}")
        elif data_type == CSI2_DT_YUV422_8BIT:
            # YUV422: 4 bytes per 2 pixels (Y0/U0/Y1/V0 pattern)
            for i in range(0, len(payload), 4):
                if i + 3 < len(payload):
                    y0, u, y1, v = payload[i:i+4]
                    # First pixel (Y0/U)
                    pixel_start = ss + (i * total_time) // len(payload)
                    pixel_mid = ss + ((i + 2) * total_time) // len(payload)
                    pixel_end = ss + ((i + 4) * total_time) // len(payload)
                    self.putg(pixel_start, pixel_mid, 18, f"Y:{y0:02X} U:{u:02X}")
                    # Second pixel (Y1/V)
                    self.putg(pixel_mid, pixel_end, 18, f"Y:{y1:02X} V:{v:02X}")
                elif i + 1 < len(payload):
                    # Handle incomplete YUV422 data (fallback for odd cases)
                    y, uv = payload[i:i+2]
                    pixel_start = ss + (i * total_time) // len(payload)
                    pixel_end = ss + ((i + 2) * total_time) // len(payload)
                    component = "U" if (i // 2) % 2 == 1 else "Y"
                    self.putg(pixel_start, pixel_end, 18, f"Y:{y:02X} {component}:{uv:02X}")
        else:
            # Generic hex dump for unknown formats - 1 byte per pixel
            for i in range(len(payload)):
                pixel_start = ss + (i * total_time) // len(payload)
                pixel_end = ss + ((i + 1) * total_time) // len(payload)
                self.putg(pixel_start, pixel_end, 18, f"{payload[i]:02X}")

    def decode_long_packet(self, ss, header, payload, checksum):
        """Decode long packet with payload and checksum"""
        # Use the same parsing logic as analyze_packet_header for consistency
        # CSI-2 long packet format: [DataID, WC_Low, WC_High, ECC]
        data_id = header[0]  # DataID contains the actual data type
        data_type = data_id  # For long packets, DataID IS the data type
        virtual_channel = 0  # VC is typically 0 for basic packets, or embedded in DataID upper bits
        word_count = (header[2] << 8) | header[1]  # Word count from data bytes
        ecc = header[3]  # Error correction code

        dt_name = DATA_TYPE_NAMES.get(data_type, f'0x{data_type:02X}')

        # Account for active lane count in timing calculations
        # Use number of lanes with sync detected as fallback if lane detection hasn't triggered
        sync_lanes_detected = sum(1 for lane_sync in self.lane_sync_detected if lane_sync)
        active_lanes = max(1, self.detected_lanes if self.num_lanes == 0 else self.num_lanes)
        if active_lanes == 1 and sync_lanes_detected > 1:
            active_lanes = sync_lanes_detected
        payload_time_per_lane = (len(payload) * 8) // active_lanes
        header_time_per_lane = 32 // active_lanes  # 4 header bytes scaled for lanes
        footer_time_per_lane = 16 // active_lanes  # 2 footer bytes scaled for lanes

        self.putp(ss - (header_time_per_lane + payload_time_per_lane + footer_time_per_lane), ss, ['LONG_PACKET', [data_type, virtual_channel, word_count, payload]])
        self.putg(ss - (header_time_per_lane + payload_time_per_lane), ss - payload_time_per_lane, 3, f'Long: {dt_name} VC{virtual_channel} WC:{word_count}')
        self.putg(ss - (header_time_per_lane + payload_time_per_lane), ss - payload_time_per_lane, 8, f'DT: {dt_name}')
        self.putg(ss - (header_time_per_lane + payload_time_per_lane), ss - payload_time_per_lane, 9, f'VC: {virtual_channel}')

        if payload:
            self.putg(ss - payload_time_per_lane, ss, 5, f'Payload: {len(payload)} bytes')
            self.putb(ss - payload_time_per_lane, ss, payload)

            # Decode pixel data from payload
            self.decode_pixel_data(ss - payload_time_per_lane, ss, data_type, payload)

        # Annotate the footer/checksum (2 bytes at the end of long packets)
        if checksum:
            footer_start = ss
            footer_end = ss + footer_time_per_lane
            self.putg(footer_start, footer_end, 6, f'Footer: {len(checksum)} bytes (0x{checksum[0]:02X}{checksum[1]:02X})')
            self.putp(footer_start, footer_end, ['FOOTER', checksum])
            self.putb(footer_start, footer_end, checksum)


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
            # Wait for any signal change, not just clock edges
            pins = self.wait({0: 'e'})  # Wait for clock edge
            ss = self.samplenum  # Test without scaling
            # print(f"DEBUG: RAW samplenum={self.samplenum}, SCALED sample={ss}, Pins: {pins}")


            # Extract differential channels (clk_p, clk_n, data0_p, data0_n, ...)
            clk_n = pins[0] if len(pins) > 0 else None
            clk_p = pins[1] if len(pins) > 1 else None
            data0_n = pins[2] if len(pins) > 2 else None
            data0_p = pins[3] if len(pins) > 3 else None
            data1_n = pins[4] if len(pins) > 4 else None
            data1_p = pins[5] if len(pins) > 5 else None
            data2_n = pins[6] if len(pins) > 6 else None
            data2_p = pins[7] if len(pins) > 7 else None
            data3_n = pins[8] if len(pins) > 8 else None
            data3_p = pins[9] if len(pins) > 9 else None

            # Process each lane
            data_lanes_p = [data0_p, data1_p, data2_p, data3_p]
            data_lanes_n = [data0_n, data1_n, data2_n, data3_n]

            for lane in range(4):
                data_p = data_lanes_p[lane]
                data_n = data_lanes_n[lane]
                if data_p is not None:
                    # Detect lane state using single-ended signals
                    lane_state = self.detect_lane_state(lane, data_p, data_n)
                    self.update_lane_state(lane, lane_state, ss)
                    # print(f"DEBUG: Lane {lane} state: {lane_state}")

                    # If in HS or THS-SETTLE state, shift bits (process on all lanes to detect sync)
                    if lane_state in [LANE_STATE_HS, LANE_STATE_THS_SETTLE]:
                        bit_value = 1 if data_p > data_n else 0
                        self.shift_bits(lane, bit_value, ss)

            # Use detected lane count if auto-detect is enabled
            active_lanes = self.detected_lanes if self.num_lanes == 0 else self.num_lanes
            if active_lanes == 0:
                active_lanes = 1  # Default to 1 lane if none detected yet