class SpectrumManager:
    def __init__(self, total_spectrum, uplink_percentage=50, downlink_percentage=50, guard_band=100):
        """
        Initialize the OFDM Manager.

        :param total_spectrum: Total available spectrum in Hz.
        :param uplink_percentage: Percentage of spectrum allocated for uplink (0-100).
        :param downlink_percentage: Percentage of spectrum allocated for downlink (0-100).
        :param guard_band: Guard band spectrum in Hz.
        """
        self.total_spectrum = total_spectrum
        self.uplink_percentage = uplink_percentage
        self.downlink_percentage = downlink_percentage
        self.guard_band = guard_band

    def assign_bands(self, uplink_percentage, downlink_percentage):
        """
        Assign the specified percentage of spectrum for uplink and downlink.

        :param uplink_percentage: Percentage of spectrum allocated for uplink (0-100).
        :param downlink_percentage: Percentage of spectrum allocated for downlink (0-100).
        """
        self.uplink_percentage = uplink_percentage
        self.downlink_percentage = downlink_percentage

    def assign_bands_by_downlink_bandwidth(self, downlink_bandwidth):
        """
        Adjusts the uplink and downlink percentage based on a given downlink bandwidth.

        :param downlink_bandwidth: The desired downlink bandwidth in Hz.
        :raises ValueError: If the requested downlink bandwidth exceeds the available spectrum.
        """
        available_spectrum = self.total_spectrum - self.guard_band

        if downlink_bandwidth > available_spectrum:
            raise ValueError("Requested downlink bandwidth exceeds the available spectrum.")

        # Calculate new downlink and uplink percentages
        downlink_percentage = (downlink_bandwidth / available_spectrum) * 100
        uplink_percentage = 100 - downlink_percentage  # Assign remaining spectrum to uplink

        # Assign the calculated percentages
        self.assign_bands(uplink_percentage, downlink_percentage)

    def get_downlink_bandwidth(self):
        """
        Calculate the bandwidth allocated for downlink.

        :return: Downlink bandwidth in Hz.
        """
        available_spectrum = self.total_spectrum - self.guard_band
        return available_spectrum * (self.downlink_percentage / 100)

    def get_uplink_bandwidth(self):
        """
        Calculate the bandwidth allocated for uplink.

        :return: Uplink bandwidth in Hz.
        """
        available_spectrum = self.total_spectrum - self.guard_band
        return available_spectrum * (self.uplink_percentage / 100)


    def is_bandwidth_allocation_valid(self, downlink_bw, uplink_bw):
        total_allocated = downlink_bw + uplink_bw + self.guard_band
        return total_allocated <= self.total_spectrum

    def get_downlink_bandwidth_range(self, downlink_bw, uplink_bw):
        available_spectrum = self.total_spectrum - self.guard_band
        max_downlink_bw = available_spectrum - uplink_bw

        return downlink_bw, max_downlink_bw