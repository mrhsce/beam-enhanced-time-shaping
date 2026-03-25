import numpy as np
import random
import matplotlib.pyplot as plt
import networkx as nx

from pythonProject.helper_functions import time_it
from pythonProject.ue_selection.policies import UEAssignmentAlgorithm


def calculate_bs_ue_channel_gain(channel_matrices):
    """
    Calculate the channel gain between each UE and BS for complex channel matrices.

    :param channel_matrices: A 3D matrix with dimensions [number of BS, number of antennas, number of UEs]
    :return: A 2D matrix with the channel gains between each BS and UE.
    """

    num_bs, num_antennas, num_ue = channel_matrices.shape
    channel_gain_matrix = np.zeros((num_bs, num_ue))

    for i in range(num_bs):
        for j in range(num_ue):
            # Summing the absolute square of each complex coefficient for all antennas
            channel_vector = channel_matrices[i, :, j]
            channel_gain_matrix[i, j] = np.sqrt(np.sum(np.abs(channel_vector) ** 2))

    return channel_gain_matrix


def two_sided_stable_matching_having_channel_gain(channel_gains, N):
    bs_num, ue_num = channel_gains.shape  # Number of Base Stations and User Equipments

    # Initialize lists for the proposals (which UEs each BS holds)
    bs_holds = [[] for _ in range(bs_num)]

    # Initialize the UEs' proposals to keep track of which BS they will propose to next
    next_proposal = [0] * ue_num

    # Preference lists for BSs and UEs
    bs_preference = np.argsort(-channel_gains, axis=1).tolist()
    ue_preference = np.argsort(-channel_gains.T, axis=1).tolist()

    # While there exists a UE that has not been matched but still has BSs to propose to
    proposing_ues = set(range(ue_num))
    while proposing_ues:
        for ue in list(proposing_ues):
            if next_proposal[ue] < bs_num:
                # Get the next BS to propose to
                bs = ue_preference[ue][next_proposal[ue]]
                bs_holds[bs].append((ue, channel_gains[bs, ue]))
                proposing_ues.discard(ue)

                # If BS is over capacity, reject the least preferred UE
                if len(bs_holds[bs]) > N:
                    # Sort BS's UEs based on preference and remove the least preferred if over capacity
                    bs_holds[bs].sort(key=lambda x: -x[1])  # Sort by channel gain, high to low
                    rejected_ue = bs_holds[bs].pop()[0]
                    next_proposal[rejected_ue] += 1
                    if next_proposal[rejected_ue] < bs_num and rejected_ue not in proposing_ues:
                        proposing_ues.add(rejected_ue)
            else:
                proposing_ues.discard(ue)

    # Construct the matching matrix from bs_holds
    alpha = np.zeros((bs_num, ue_num), dtype=int)
    for bs in range(bs_num):
        for ue, _ in bs_holds[bs]:
            alpha[bs, ue] = 1

    return alpha


def visualize_matching_results(matching_result):
    bs_num, ue_num = matching_result.shape

    # Create a graph
    G = nx.Graph()

    # Add nodes with the node attribute "bipartite"
    G.add_nodes_from(['BS{}'.format(i) for i in range(bs_num)], bipartite=0)
    G.add_nodes_from(['UE{}'.format(i) for i in range(ue_num)], bipartite=1)

    # Add edges based on the matching result
    for bs in range(bs_num):
        for ue in range(ue_num):
            if matching_result[bs, ue] == 1:
                G.add_edge('BS{}'.format(bs), 'UE{}'.format(ue))

    # Draw the graph
    pos = nx.bipartite_layout(G, ['BS{}'.format(i) for i in range(bs_num)])
    nx.draw(G, pos, with_labels=True, font_size=7, node_size=400, node_color="lightblue", edge_color="gray")

    plt.title('Graph Visualization of Matching Results')
    plt.axis('off')  # Turn off the axis
    plt.show()


def two_sided_stable_matching(channel_matrices, rf_chain_count):
    return two_sided_stable_matching_having_channel_gain(calculate_bs_ue_channel_gain(channel_matrices),
                                                         rf_chain_count)


def random_matching(channel_matrices, rf_chain_count):
    """
    Randomly matches UEs to BSs based on available RF chains, ignoring channel gains.

    :param channel_matrices: A 3D matrix [number of BS, number of antennas, number of UEs].
    :param rf_chain_count: Maximum number of UEs each BS can handle.
    :return: A 2D matrix indicating UEs' assignments to BSs.
    """
    # Calculate the channel gains to get the dimensions
    channel_gains = calculate_bs_ue_channel_gain(channel_matrices)
    num_bs, num_ue = channel_gains.shape

    # Initialize the assignment matrix
    alpha = np.zeros((num_bs, num_ue), dtype=int)

    # List available BSs for each UE to be randomly assigned to
    available_bs = list(range(num_bs))

    # Shuffle UEs to ensure randomness in assignment
    all_ues = list(range(num_ue))
    random.shuffle(all_ues)

    # Track the count of UEs assigned to each BS
    bs_load = np.zeros(num_bs, dtype=int)

    for ue in all_ues:
        random.shuffle(available_bs)  # Shuffle BSs for random assignment
        for bs in available_bs:
            if bs_load[bs] < rf_chain_count:  # Check if the BS can still accept UEs
                alpha[bs, ue] = 1
                bs_load[bs] += 1
                break

    return alpha

@time_it
def perform_UE_BS_matching(policy, channel_matrices, rf_chain_count, visualize=False):
    """
    Perform UE to BS matching based on the provided policy, with caching for static matches.

    :param policy: An instance of the Policy class, specifying the matching algorithm and other parameters.
    :param channel_matrices: A 3D matrix [number of BS, number of antennas, number of UEs].
    :param rf_chain_count: Maximum number of UEs each BS can handle.
    :param visualize: Whether to visualize the matching results using matplotlib.
    :return: A 2D matrix indicating UEs' assignments to BSs based on the specified policy.
    """
    # Initialize cache on first call
    if not hasattr(perform_UE_BS_matching, 'cache'):
        perform_UE_BS_matching.cache = {}

    # Define a unique key for caching based on the policy and matrix characteristics
    key = (policy.ue_assignment_algorithm, rf_chain_count, channel_matrices.shape)
    alpha = None
    if policy.ue_assignment_algorithm == UEAssignmentAlgorithm.CHANNEL_BASED_STABLE_MARRIAGE:
        alpha = two_sided_stable_matching(channel_matrices, rf_chain_count)
    elif policy.ue_assignment_algorithm == UEAssignmentAlgorithm.RANDOM_ASSIGNMENT:
        alpha = random_matching(channel_matrices, rf_chain_count)
    elif policy.ue_assignment_algorithm == UEAssignmentAlgorithm.QUEUE_AWARE_CHANNEL_BASED_STABLE_MARRIAGE:
        print("Queue-aware channel-based stable marriage algorithm not yet implemented.")
    elif policy.ue_assignment_algorithm == UEAssignmentAlgorithm.CHANNEL_BASED_STABLE_MARRIAGE_STATIC:
        if key not in perform_UE_BS_matching.cache:
            perform_UE_BS_matching.cache[key] = two_sided_stable_matching(channel_matrices, rf_chain_count)
        alpha = perform_UE_BS_matching.cache[key]
    else:
        raise ValueError("Unsupported assignment algorithm specified in policy.")

    if visualize:
        visualize_matching_results(alpha)
    return alpha
