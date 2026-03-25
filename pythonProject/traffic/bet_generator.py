import random
import numpy as np

from pythonProject.traffic.frame import Frame  # Assuming you have a generic Frame class
# If you have a specialized BET_Frame class, import/use it instead.

class BET_Generator:
    def __init__(self, environment, mtu=1500):
        """
        Initialize the BET_Generator.

        :param environment: The PhysicalEnvironment instance containing UEs, BSs, ConnectionManager, etc.
        :param mtu: The maximum transmission unit (in bytes) for splitting large traffic into frames.
        """
        self.environment = environment
        self.mtu = mtu

    def random_poisson(self, poisson_coefficient, current_time=0.0):
        """
        Generate best-effort traffic for all UEs using a Poisson distribution.

        1. For each UE:
           a) Draw total traffic in bytes from np.random.poisson(poisson_coefficient).
           b) Randomly choose another UE as destination (or adapt to pick from BSs, Switches, etc.).
           c) Split traffic into frames based on self.mtu.
           d) Enqueue those frames into the UE's uplink BET queue.

        :param poisson_coefficient: The mean (lambda) used in the Poisson distribution for traffic size.
        :param current_time: A timestamp indicating when this traffic generation starts (optional).
        """
        all_ues = self.environment.ues

        for ue in all_ues:
            # 1) Draw total traffic in bytes for this UE
            total_bytes = np.random.poisson(poisson_coefficient)
            if total_bytes <= 0:
                # No traffic to send for this UE in this time slot
                continue

            # 2) Pick a random destination UE (not the same as source)
            #    If you prefer choosing among all possible nodes, adapt accordingly.
            possible_destinations = [u for u in all_ues if u != ue]
            if not possible_destinations:
                # Edge case: only one UE in the environment
                continue
            destination_ue = random.choice(possible_destinations)

            # 3) Split traffic into frames of at most self.mtu bytes
            num_frames = (total_bytes + self.mtu - 1) // self.mtu

            for i in range(num_frames):
                chunk_size = min(self.mtu, total_bytes - i * self.mtu)

                # Create a best-effort frame
                bet_frame = Frame(
                    frame_type="BET",
                    payload_size=chunk_size,
                    source_node=ue,
                    destination_node=destination_ue,
                    creation_time=current_time,
                    arrival_time=None,
                    delay_tolerance=None  # Best-effort typically has no strict tolerance
                )

                # 4) Enqueue the frame into the UE->BS wireless link's BET queue
                #    (We assume there's exactly one wireless uplink from UE to its serving BS).
                #    If your environment has a different structure (multiple BS links, etc.),
                #    modify accordingly.
                uplink = self._find_wireless_uplink(ue)
                if uplink is not None:
                    # Append/Enqueue to the best-effort (BET) queue on that link
                    uplink.bet_queue.add_frame(bet_frame)
                else:
                    print(f"Warning: No wireless uplink found for UE {ue} to enqueue BET frame.")

    def _find_wireless_uplink(self, ue):
        """
        A helper method to find the 'wireless' link going *out* of the given UE.
        Assumes one wireless link from UE -> BS in your environment.

        :param ue: The UE node for which to find an uplink.
        :return: The Link object if found, otherwise None.
        """
        for link in self.environment.connection_manager.links:
            if link.node1 == ue and link.link_type == "wireless":
                # UE is the source (node1) and it's a wireless link
                return link
        return None
