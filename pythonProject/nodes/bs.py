from pythonProject.beamforming.digital_beamforming.beamweight_manager import BeamweightManager
from pythonProject.environment.ofdm.spectrum_manager import SpectrumManager
from pythonProject.nodes.node import Node



class BS(Node):
    def __init__(self, coordinates, total_spectrum=1000, uplink_percentage=50, downlink_percentage=50, guard_band=100):
        """
        Base Station (BS) node.

        :param coordinates: Coordinates of the BS.
        :param total_spectrum: Total available spectrum for this BS in kHz.
        :param uplink_percentage: Percentage of spectrum allocated for uplink (0-100).
        :param downlink_percentage: Percentage of spectrum allocated for downlink (0-100).
        :param guard_band: Guard band spectrum in Hz.
        """
        super().__init__(coordinates, node_type="BS")
        self.spectrum_manager = SpectrumManager(total_spectrum, uplink_percentage, downlink_percentage, guard_band)
        self.beamweight_manager = BeamweightManager()
