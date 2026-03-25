class Path:
    def __init__(self, small_scale_fading, azimuth, elevation, max_doppler_shift, direction_of_motion):
        self.small_scale_fading = small_scale_fading
        self.azimuth = azimuth
        self.elevation = elevation
        self.max_doppler_shift = max_doppler_shift
        self.direction_of_motion = direction_of_motion