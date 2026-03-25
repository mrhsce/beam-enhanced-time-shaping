class BeamweightManager:
    def __init__(self):
        # Dictionary to store beamweights with UE objects as keys
        self._beamweights = {}

    def get_assigned_ues(self):
        """
        Get all assigned UEs and their corresponding weights.

        :return: A tuple (assigned_UEs, assigned_UEs_weights).
        """
        ues = list(self._beamweights.keys())
        weights = list(self._beamweights.values())
        return ues, weights

    def get_active_ues(self):
        """
        Get all active UEs (beamweight > 0) and their corresponding weights.

        :return: A tuple (active_UEs, active_UEs_weights).
        """
        active_ues = []
        active_weights = []
        for ue, weight in self._beamweights.items():
            if weight > 0:
                active_ues.append(ue)
                active_weights.append(weight)
        return active_ues, active_weights

    def set_beamweight(self, ue, beamweight):
        """
        Set the beamweight for a specific UE.

        :param ue: The UE (User Equipment) object.
        :param beamweight: The beamweight to set for the UE.
        """
        if ue is None:
            raise ValueError("UE object cannot be None")
        self._beamweights[ue] = beamweight

    def get_beamweight(self, ue):
        """
        Get the beamweight for a specific UE.

        :param ue: The UE (User Equipment) object.
        :return: The beamweight of the UE or None if not set.
        """
        if ue is None:
            raise ValueError("UE object cannot be None")
        return self._beamweights.get(ue, None)

    def remove_beamweight(self, ue):
        """
        Remove the beamweight for a specific UE.

        :param ue: The UE (User Equipment) object.
        """
        if ue in self._beamweights:
            del self._beamweights[ue]

    def clear_all(self):
        """
        Clear all stored beamweights.
        """
        self._beamweights.clear()

    def __str__(self):
        """
        Return a string representation of all beamweights.
        """
        return f"BeamweightManager({self._beamweights})"