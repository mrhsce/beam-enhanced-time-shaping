from enum import Enum


class OperationMode(Enum):
    COOPERATIVE_FULLY_DIGITAL = 1
    NON_COOPERATIVE_FULLY_DIGITAL = 2
    COOPERATIVE_HYBRID = 3
    NON_COOPERATIVE_HYBRID = 4


class UEAssignmentAlgorithm(Enum):
    RANDOM_ASSIGNMENT = 1
    CHANNEL_BASED_STABLE_MARRIAGE = 2
    CHANNEL_BASED_STABLE_MARRIAGE_STATIC = 3
    QUEUE_AWARE_CHANNEL_BASED_STABLE_MARRIAGE = 4


class RFChainConnection(Enum):
    FULLY_CONNECTED = 1
    STATIC_SUBARRAY = 2
    DYNAMIC_SUBARRAY = 3


class AnalogBeamformingTechnique(Enum):
    CODEBOOK_SWEEPING = 1


class DigitalBeamformingTechnique(Enum):
    ZERO_FORCING_DYNAMIC_RF_CHAIN = 1
    ZERO_FORCING_MAX_RF_CHAIN = 2


class UESelectionAlgorithm(Enum):
    GREEDY = 1
    ADAPTIVE_TOP_K = 2
    SERVING_ALL = 3


class UESelectionUtilityFunction(Enum):
    BITRATE_MAXIMIZATION = 1
    PF_MAXIMIZATION = 2
    QUEUE_LENGTH_MINIMIZATION = 3
    QUEUE_AWARE_PF_MAXIMIZATION = 4


class SubcoherenceTimeAllocation(Enum):
    NONE = 1
    OMISSION_AND_CONTINUE = 2
    FIXED_SIZE_SPECULATIVE = 3


class Policy:
    def __init__(self, operation_mode: OperationMode = OperationMode.NON_COOPERATIVE_HYBRID,
                 ue_assignment_algorithm: UEAssignmentAlgorithm = UEAssignmentAlgorithm.CHANNEL_BASED_STABLE_MARRIAGE,
                 rf_chain_connection: RFChainConnection = RFChainConnection.FULLY_CONNECTED,
                 analog_beamforming_technique: AnalogBeamformingTechnique = AnalogBeamformingTechnique.CODEBOOK_SWEEPING,
                 digital_beamforming_technique: DigitalBeamformingTechnique = DigitalBeamformingTechnique.ZERO_FORCING_DYNAMIC_RF_CHAIN,
                 ue_selection_algorithm: UESelectionAlgorithm = UESelectionAlgorithm.GREEDY,
                 utility_function: UESelectionUtilityFunction = UESelectionUtilityFunction.QUEUE_AWARE_PF_MAXIMIZATION,
                 subcoherence_time_allocation: SubcoherenceTimeAllocation = SubcoherenceTimeAllocation.NONE,
                 frame_injection_rate=1, downlink_queue_size=None, sub_coherence_time_division_count=10):
        self.operation_mode = operation_mode
        self.ue_assignment_algorithm = ue_assignment_algorithm
        self.rf_chain_connection = rf_chain_connection
        self.analog_beamforming_technique = analog_beamforming_technique
        self.digital_beamforming_technique = digital_beamforming_technique
        self.ue_selection_algorithm = ue_selection_algorithm
        self.utility_function = utility_function
        self.subcoherence_time_allocation = subcoherence_time_allocation
        self.frame_injection_rate = frame_injection_rate
        self.downlink_queue_size = downlink_queue_size
        self.sub_coherence_time_division_count = sub_coherence_time_division_count

    def __repr__(self):
        return (f"Policy(operation_mode={self.operation_mode}, "
                f"ue_assignment_algorithm={self.ue_assignment_algorithm}, "
                f"rf_chain_connection={self.rf_chain_connection}, "
                f"analog_beamforming_technique={self.analog_beamforming_technique}, "
                f"digital_beamforming_technique={self.digital_beamforming_technique}, "
                f"ue_selection_algorithm={self.ue_selection_algorithm}, "
                f"utility_function={self.utility_function}, "
                f"subcoherence_time_allocation={self.subcoherence_time_allocation})")
