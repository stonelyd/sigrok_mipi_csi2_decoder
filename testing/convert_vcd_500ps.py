#!/usr/bin/env python3
import re

# Read the original VCD file
with open('test_csi2_long_packet_yuv422_4lane.vcd', 'r') as f:
    content = f.read()

# Change timescale from 1ps to 500ps
content = re.sub(r'\$timescale\s+1ps', r'$timescale\n\t500ps', content)

# Scale all timestamps by 500 (500ps = 500 * 1ps)
def scale_timestamp(match):
    timestamp = int(match.group(1))
    return f'#{timestamp // 500}'

content = re.sub(r'#(\d+)', scale_timestamp, content)

# Write the converted VCD
with open('test_csi2_long_packet_yuv422_4lane_500ps.vcd', 'w') as f:
    f.write(content)

print("Converted VCD with 500ps timescale created as test_csi2_long_packet_yuv422_4lane_500ps.vcd")