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

'''
MIPI CSI-2 D-PHY is a high-speed serial interface for camera applications.
It uses D-PHY physical layer with differential signaling for clock and data lanes.

The protocol supports multiple data lanes (typically 1-4) plus a clock lane.
CSI-2 packets include SoT/EoT markers, short packets (control), and long packets (image data).

Connect the clock lane to the CLK channel and data lanes to DATA0, DATA1, etc.
'''

__version__ = "0.1.0"

from .pd import Decoder