from pythonProject.link.link import Link


class ConnectionManager:
    def __init__(self, environment):
        """
        Initialize the ConnectionManager with a reference to the PhysicalEnvironment.
        """
        self.environment = environment
        self.links = []

    def create_link(self, node1, node2, link_type):
        """
        Create two directional links between two nodes. Both nodes must exist in the environment.
        If a link of the same type already exists in any direction, raise an error for that direction.
        """
        if node1 not in self.environment.ues + self.environment.bss + self.environment.switches:
            raise ValueError(f"Node {node1} is not registered in the environment.")
        if node2 not in self.environment.ues + self.environment.bss + self.environment.switches:
            raise ValueError(f"Node {node2} is not registered in the environment.")

        # Check for an existing link from node1 to node2
        for link in self.links:
            if link.node1 == node1 and link.node2 == node2 and link.link_type == link_type:
                raise ValueError(f"A {link_type} link already exists from {node1} to {node2}.")

        # Create the link from node1 to node2
        link1 = Link(node1, node2, link_type)
        self.links.append(link1)
        # print(f"Created a {link_type} link from {node1} to {node2}.")

        # Check for an existing link from node2 to node1
        for link in self.links:
            if link.node1 == node2 and link.node2 == node1 and link.link_type == link_type:
                raise ValueError(f"A {link_type} link already exists from {node2} to {node1}.")

        # Create the link from node2 to node1
        link2 = Link(node2, node1, link_type)
        self.links.append(link2)
        # print(f"Created a {link_type} link from {node2} to {node1}.")

    def remove_link(self, node1, node2):
        """
        Remove both directional links between two nodes.
        """
        links_to_remove = []
        for link in self.links:
            if (link.node1 == node1 and link.node2 == node2) or (link.node1 == node2 and link.node2 == node1):
                links_to_remove.append(link)

        for link in links_to_remove:
            self.links.remove(link)
            # print(f"Removed link between {link.node1} and {link.node2}.")

    def find_path(self, start_node, end_node):
        """
        Find a path between two nodes using DFS. Return the sequence of links.
        """
        visited = set()
        path = []

        def dfs(current_node, target_node, current_path):
            if current_node in visited:
                return False

            visited.add(current_node)

            if current_node == target_node:
                return True

            for link in self.links:
                if link.node1 == current_node:
                    next_node = link.node2
                else:
                    continue

                if dfs(next_node, target_node, current_path):
                    current_path.append(link)
                    return True

            return False

        if dfs(start_node, end_node, path):
            return list(reversed(path))
        else:
            return None

    def get_all_wired_links(self):
        """
        Get all wired links using the get_links_by_type method.

        :return: A list of all links with the type 'wired'.
        """
        return self.get_links_by_type('wired')

    def get_all_wireless_links(self, downlink=False, uplink=False):
        """
        Get all wireless links, optionally filtering by outgoing or incoming links.

        :param outgoing: If True, return only outgoing wireless links.
        :param incoming: If True, return only incoming wireless links.
        :return: A list of wireless links based on the specified criteria.
        """
        if downlink and uplink:
            raise ValueError("Cannot filter for both outgoing and incoming links simultaneously.")

        wireless_links = self.get_links_by_type("wireless")

        if downlink:
            return [link for link in wireless_links if link.node1 in self.environment.bss]
        elif uplink:
            return [link for link in wireless_links if link.node2 in self.environment.bss]

        return wireless_links  # Return all wireless links if no filter is applied

    def check_link_status(self, link):
        """
        Check the status of a link to determine if it is uplink, downlink, or peer-to-peer.

        :param link: The link to check.
        :return: A string indicating the status ('uplink', 'downlink', 'peer-to-peer').
        """
        if link.node1 in self.environment.ues and link.node2 in self.environment.bss:
            return 'uplink'
        elif link.node1 in self.environment.bss and link.node2 in self.environment.ues:
            return 'downlink'
        else:
            return 'peer-to-peer'

    def get_links_by_type(self, link_type):
        """
        Get all links of a specific type.

        :param link_type: The type of links to retrieve.
        :return: A list of links of the specified type.
        """
        return [link for link in self.links if link.link_type == link_type]

    def get_all_wireless_link_pairs(self):
        """
        Get all UE-BS wireless links as an array of tuples. Each tuple contains:
        (downlink link, uplink link, BS, UE).

        :return: A list of tuples with downlink link, uplink link, and BS.
        """
        wireless_link_pairs = []
        for link in self.links:
            if link.link_type == 'wireless':
                status = self.check_link_status(link)
                if status == 'downlink':
                    uplink = self.get_link_pair(link)
                    if uplink and self.check_link_status(uplink) == 'uplink':
                        wireless_link_pairs.append((link, uplink, link.node1, link.node2))
        return wireless_link_pairs

    def find_connected_links(self, node, outgoing=False, incoming=False):
        """
        Find all links connected to a given node. Optionally filter by outgoing or incoming links.

        :param node: The node to find connected links for.
        :param outgoing: If True, only include outgoing links (from the node).
        :param incoming: If True, only include incoming links (to the node).
        :return: A list of links connected to the node.
        """
        if outgoing and incoming:
            raise ValueError("Cannot filter for both outgoing and incoming links simultaneously.")

        connected_links = []

        for link in self.links:
            if outgoing and link.node1 == node:
                connected_links.append(link)
            elif incoming and link.node2 == node:
                connected_links.append(link)
            elif not outgoing and not incoming and (link.node1 == node or link.node2 == node):
                connected_links.append(link)

        return connected_links

    def get_link_pair(self, link):
        """
        Get the link that represents the other side of the given link.

        :param link: The link for which the pair is to be found.
        :return: The paired link if it exists, otherwise None.
        """
        for candidate in self.links:
            if candidate.node1 == link.node2 and candidate.node2 == link.node1 and candidate.link_type == link.link_type:
                return candidate
        return None

    def get_link(self, node1, node2):
        """
        Get information about a link between two nodes.
        """
        for link in self.links:
            if link.node1 == node1 and link.node2 == node2:
                return link
        return None

    def get_connected_bs(self, ue):
        """
        Get the Base Station (BS) connected to the given User Equipment (UE).

        :param ue: The UE object.
        :return: The connected BS or None if no connection exists.
        """
        for link in self.links:
            if link.node1 == ue and link.node2 in self.environment.bss:
                return link.node2
        return None

    def get_connected_ues(self, bs):
        """
        Get all User Equipment (UEs) connected to the given Base Station (BS).

        :param bs: The BS object.
        :return: A distinct list of connected UEs.
        """
        connected_ues = set()
        for link in self.links:
            if link.node1 == bs and link.node2 in self.environment.ues:
                connected_ues.add(link.node2)
        return list(connected_ues)

    def get_ue_and_bs(self, link):
        """
        Determines the User Equipment (UE) and Base Station (BS) for a given wireless link.

        :param link: The link to analyze.
        :return: A tuple (UE, BS) if the link is valid, otherwise None.
        """
        if link.link_type != "wireless":
            return None  # Only consider wireless links

        if link.node1 in self.environment.ues and link.node2 in self.environment.bss:
            return link.node1, link.node2  # (UE, BS)
        elif link.node1 in self.environment.bss and link.node2 in self.environment.ues:
            return link.node2, link.node1  # (UE, BS)

        return None  # The link does not represent a valid UE-BS connection

