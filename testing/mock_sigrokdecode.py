"""
Mock sigrokdecode module for testing the MIPI CSI-2 D-PHY decoder
"""

# Mock constants
SRD_CONF_SAMPLERATE = 'samplerate'
OUTPUT_PYTHON = 'python'
OUTPUT_ANN = 'annotation'
OUTPUT_BINARY = 'binary'
OUTPUT_META = 'meta'

class Decoder:
    """Mock base decoder class"""
    def __init__(self):
        pass

    def register(self, output_type):
        """Mock register method"""
        return f"mock_{output_type}_output"

    def put(self, ss, es, output, data):
        """Mock put method"""
        pass

    def wait(self, conditions):
        """Mock wait method"""
        return (0, 0, 0, 0, 0)  # Mock return values