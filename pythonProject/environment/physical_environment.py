import random
import matplotlib.pyplot as plt
import numpy as np

from pythonProject.environment.channel_model.channel_model import generate_path_clusters, calculate_channel_matrices
from pythonProject.helper_functions import store

from pythonProject.nodes.bs import BS
from pythonProject.nodes.ue import UE
from pythonProject.nodes.switch import Switch

from pythonProject.environment.connection_manager import ConnectionManager

from pythonProject.environment.coordinates import Coordinates


class PhysicalEnvironment:
    def __init__(self, x_dimension=120, y_dimension=80, z_dimension=10):
        self.ues = []
        self.bss = []
        self.switches = []
        self.path_clusters_matrix = []
        self.channel_matrices = []
        self.x_dimension = x_dimension
        self.y_dimension = y_dimension
        self.z_dimension = z_dimension
        self.connection_manager = ConnectionManager(self)  # Instantiate the connection manager

        # NEW: history of UE positions over time
        # Each entry: [(x,y,z) for UE0..UE_{N-1}] in the same order as self.ues
        self.history = []

    # -----------------------------
    # NEW: history utilities
    # -----------------------------
    def clear_history(self):
        """Clear stored UE trajectory history."""
        self.history = []

    def visualize_history(
            self,
            out_mp4_path="ue_history.mp4",
            fps=20,
            trail_len=25,
            ue_tag=False,
            bs_tag=True,
            switch_tag=True,
            show_links=False
    ):
        """
        Visualize stored UE history as a top-down 2D MP4 video.

        Requirements:
          - self.history must be populated using move_ues(..., store_move=True)
          - ffmpeg should be installed so matplotlib can write MP4

        History format:
          self.history[t] = [(x,y,z) for each UE in self.ues order]
        """
        if not self.history:
            raise ValueError("history is empty. Call move_ues(..., store_move=True) for multiple steps first.")

        from matplotlib.animation import FuncAnimation, FFMpegWriter

        frames = len(self.history)
        ue_count = len(self.ues)

        fig, ax = plt.subplots(figsize=(16, 12))
        ax.set_xlim(0, self.x_dimension)
        ax.set_ylim(0, self.y_dimension)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("X-axis")
        ax.set_ylabel("Y-axis")
        ax.set_title("UE Mobility History (Top-Down)")

        # Static: BS / Switch
        if self.bss:
            ax.scatter([bs.coordinates.x for bs in self.bss],
                       [bs.coordinates.y for bs in self.bss],
                       c="r", marker="^", s=90)
            if bs_tag:
                for idx, bs in enumerate(self.bss):
                    ax.text(bs.coordinates.x, bs.coordinates.y, f"BS{idx}", color="red", fontsize=9)

        if self.switches:
            ax.scatter([sw.coordinates.x for sw in self.switches],
                       [sw.coordinates.y for sw in self.switches],
                       c="g", marker="s", s=90)
            if switch_tag:
                for idx, sw in enumerate(self.switches):
                    ax.text(sw.coordinates.x, sw.coordinates.y, f"SW{idx}", color="green", fontsize=9)

        # UE scatter
        x0 = [p[0] for p in self.history[0]]
        y0 = [p[1] for p in self.history[0]]
        ue_scatter = ax.scatter(x0, y0, c="b", marker="o", s=40)

        # Trails
        trail_lines = []
        for _ in range(ue_count):
            (ln,) = ax.plot([], [], linewidth=1, alpha=0.35)
            trail_lines.append(ln)

        # UE labels (optional)
        ue_texts = []
        if ue_tag:
            for i in range(ue_count):
                ue_texts.append(ax.text(x0[i], y0[i], f"UE{i}", color="blue", fontsize=8))

        # Links (optional): endpoints move, so redraw each frame
        link_lines = []

        def _clear_links():
            nonlocal link_lines
            for ln in link_lines:
                ln.remove()
            link_lines = []

        def _draw_links():
            nonlocal link_lines
            if not show_links:
                return
            _clear_links()
            for link in self.connection_manager.links:
                ln, = ax.plot(
                    [link.node1.coordinates.x, link.node2.coordinates.x],
                    [link.node1.coordinates.y, link.node2.coordinates.y],
                    c="k", linewidth=0.8, alpha=0.5
                )
                link_lines.append(ln)

        def update(t):
            cur = self.history[t]  # [(x,y,z)...]
            xs = [p[0] for p in cur]
            ys = [p[1] for p in cur]

            ue_scatter.set_offsets(list(zip(xs, ys)))

            # Update trails using history
            start = max(0, t - trail_len + 1)
            for i in range(ue_count):
                tx = [self.history[k][i][0] for k in range(start, t + 1)]
                ty = [self.history[k][i][1] for k in range(start, t + 1)]
                trail_lines[i].set_data(tx, ty)

            # Update UE tags
            if ue_tag:
                for i, txt in enumerate(ue_texts):
                    txt.set_position((xs[i], ys[i]))

            _draw_links()

            artists = [ue_scatter, *trail_lines]
            if ue_tag:
                artists.extend(ue_texts)
            if show_links:
                artists.extend(link_lines)
            return artists

        anim = FuncAnimation(fig, update, frames=frames, interval=1000 / fps, blit=True)

        writer = FFMpegWriter(fps=fps)
        anim.save(out_mp4_path, writer=writer)
        plt.close(fig)

        return out_mp4_path

    # -----------------------------
    # Existing methods
    # -----------------------------
    def add_ue(self, ue):
        self.ues.append(ue)

    def add_bs(self, bs):
        self.bss.append(bs)

    def add_switch(self, switch):
        self.switches.append(switch)

    def find_ue_index(self, ue):
        """
        Find the index of a given UE in the list of UEs.
        :param ue: The UE object to find.
        :return: The index of the UE in the list or -1 if not found.
        """
        try:
            return self.ues.index(ue)
        except ValueError:
            return -1  # UE not found

    def find_bs_index(self, bs):
        """
        Find the index of a given BS in the list of BSs.
        :param bs: The BS object to find.
        :return: The index of the BS in the list or -1 if not found.
        """
        try:
            return self.bss.index(bs)
        except ValueError:
            return -1  # BS not found

    def connect_bss_to_switch(self):
        """
        Automatically connect BSs to the closest switch using the ConnectionManager.
        Each connection is made with a Manhattan distance-based latency.
        """
        for bs in self.bss:
            closest_switch = min(self.switches, key=lambda sw: bs.coordinates.calculate_distance(sw.coordinates))
            distance = bs.coordinates.calculate_manhattan_distance(closest_switch.coordinates)

            # Create bidirectional wired links using the connection manager
            self.connection_manager.create_link(
                node1=bs,
                node2=closest_switch,
                link_type="wired",
            )

    def connect_ues_to_closest_bs(self):
        """
        Connect each UE to the closest Base Station (BS) using the ConnectionManager.
        The connection is made with a latency based on the Euclidean distance between the UE and BS.
        """
        for ue in self.ues:
            closest_bs = min(self.bss, key=lambda bs: ue.coordinates.calculate_distance(bs.coordinates))
            distance = ue.coordinates.calculate_distance(closest_bs.coordinates)

            # Create a wireless link using the connection manager
            self.connection_manager.create_link(
                node1=ue,
                node2=closest_bs,
                link_type="wireless",
            )

    def generate_path_clusters_matrix(self):
        distance_matrix = self.get_distance_matrix()
        self.path_clusters_matrix = generate_path_clusters(distance_matrix)

    def short_term_fading_effect_on_path_clusters(self):
        for i in range(len(self.path_clusters_matrix)):
            for j in range(len(self.path_clusters_matrix[i])):
                for k in range(len(self.path_clusters_matrix[i][j])):
                    self.path_clusters_matrix[i][j][k].small_scale_fading_effect()

    def generate_channel_matrices(self, antenna_array):
        self.channel_matrices = calculate_channel_matrices(self.path_clusters_matrix, antenna_array)
        return self.channel_matrices

    def move_ues(self, time, store_move=False):
        """
        Move the UEs based on their mobility model.

        :param time: Time increment for the movement, unit: seconds.
        :param store_move: If True, store UE positions after moving into self.history
        """
        for ue in self.ues:
            ue.move(time)

        if store_move:
            snapshot = [(ue.coordinates.x, ue.coordinates.y, ue.coordinates.z) for ue in self.ues]
            self.history.append(snapshot)

    def randomly_spread_bs(self, count, margin, padding):
        for _ in range(count):
            x = random.uniform(margin, self.x_dimension - margin)
            y = random.uniform(margin, self.y_dimension - margin)
            z = random.uniform(margin, self.z_dimension - margin)

            new_bs = BS(Coordinates(x, y, z))
            self.add_bs(new_bs)

    def evenly_spread_items_over_the_ceiling(self, count, distance_from_ceiling, target_list, create_item_fn,
                                             add_item_fn, rows=None, columns=None):
        rows = int((count / (self.x_dimension / self.y_dimension)) ** 0.5) if rows is None else rows
        columns = int(count / rows) + (1 if count % rows > 0 else 0) if columns is None else columns

        if rows * columns < count:
            rows += 1

        x_spacing = self.x_dimension / columns
        y_spacing = self.y_dimension / rows

        for row in range(rows):
            for col in range(columns):
                if len(target_list) >= count:
                    break
                x = (col + 0.5) * x_spacing
                y = (row + 0.5) * y_spacing
                z = self.z_dimension - distance_from_ceiling

                new_item = create_item_fn(Coordinates(x, y, z))
                add_item_fn(new_item)

    # Updated functions
    def evenly_spread_bs_over_the_ceiling(self, count, distance_from_ceiling, rows=None, columns=None,
                                          bs_total_spectrum=1000, bs_guard_band=100):
        self.evenly_spread_items_over_the_ceiling(
            count,
            distance_from_ceiling,
            self.bss,
            lambda coords: BS(coords, total_spectrum=bs_total_spectrum, guard_band=bs_guard_band, ),
            self.add_bs,
            rows,
            columns
        )

    def evenly_spread_switches_over_the_ceiling(self, count, distance_from_ceiling, rows=None, columns=None):
        self.evenly_spread_items_over_the_ceiling(
            count,
            distance_from_ceiling,
            self.switches,
            lambda coords: Switch(coords),
            self.add_switch,
            rows,
            columns
        )

    def randomly_spread_ue(self, count, padding, mobility_logic="lanegraph"):
        ue_coordinates = []

        margin_percentage = 0.01
        x_margin = self.x_dimension * margin_percentage
        y_margin = self.y_dimension * margin_percentage
        z_margin = self.z_dimension * margin_percentage

        for _ in range(count):
            x = random.uniform(x_margin, self.x_dimension - x_margin)
            y = random.uniform(y_margin, self.y_dimension - y_margin)
            z = random.uniform(z_margin, self.z_dimension - z_margin)

            new_ue_coordinates = Coordinates(x, y, z)

            while any(new_ue_coordinates.calculate_distance(bs.coordinates) < padding for bs in self.bss):
                x = random.uniform(x_margin, self.x_dimension - x_margin)
                y = random.uniform(y_margin, self.y_dimension - y_margin)
                z = random.uniform(z_margin, self.z_dimension - z_margin)
                new_ue_coordinates = Coordinates(x, y, z)

            ue_coordinates.append(new_ue_coordinates)
            new_ue = UE(new_ue_coordinates, mobility_logic=mobility_logic)
            self.add_ue(new_ue)

    def randomly_spread_ue_over_ue_plane(self, count, padding, ue_plane_height=1, mobility_logic="lanegraph"):
        ue_coordinates = []

        margin_percentage = 0.01
        x_margin = self.x_dimension * margin_percentage
        y_margin = self.y_dimension * margin_percentage
        z_margin = 0.5

        for _ in range(count):
            x = random.uniform(x_margin, self.x_dimension - x_margin)
            y = random.uniform(y_margin, self.y_dimension - y_margin)
            z = random.uniform(ue_plane_height - z_margin, ue_plane_height + z_margin)

            new_ue_coordinates = Coordinates(x, y, z)

            while any(new_ue_coordinates.calculate_distance(bs.coordinates) < padding for bs in self.bss):
                x = random.uniform(x_margin, self.x_dimension - x_margin)
                y = random.uniform(y_margin, self.y_dimension - y_margin)
                z = random.uniform(ue_plane_height - z_margin, ue_plane_height + z_margin)
                new_ue_coordinates = Coordinates(x, y, z)

            ue_coordinates.append(new_ue_coordinates)
            new_ue = UE(new_ue_coordinates, mobility_logic=mobility_logic)
            self.add_ue(new_ue)

    def get_distance_matrix(self):
        ue_count = len(self.ues)
        bs_count = len(self.bss)

        distance_matrix = np.zeros((bs_count, ue_count))
        for i, bs in enumerate(self.bss):
            for j, ue in enumerate(self.ues):
                distance_matrix[i][j] = bs.coordinates.calculate_distance(ue.coordinates)

        return distance_matrix

    def visualize_environment(self, simulation_name="sim", ue_tag=True, bs_tag=True, switch_tag=True, show_links=True,
                              view_2d=False):
        """
        Visualize the physical environment in 2D or 3D, including nodes and links with distinct link names for uplink and downlink.
        """
        if view_2d:
            # 2D Plot
            fig, ax = plt.subplots(figsize=(16, 12))
            ax.set_xlim([0, self.x_dimension])
            ax.set_ylim([0, self.y_dimension])

            # Plot UEs
            for idx, ue in enumerate(self.ues):
                ax.scatter(ue.coordinates.x, ue.coordinates.y, c='b', marker='o')
                if ue_tag:
                    ax.text(ue.coordinates.x, ue.coordinates.y, f'UE{idx}', color='blue')

            # Plot BSs
            for idx, bs in enumerate(self.bss):
                ax.scatter(bs.coordinates.x, bs.coordinates.y, c='r', marker='^')
                if bs_tag:
                    ax.text(bs.coordinates.x, bs.coordinates.y, f'BS{idx}', color='red')

            # Plot Switches
            for idx, switch in enumerate(self.switches):
                ax.scatter(switch.coordinates.x, switch.coordinates.y, c='g', marker='s')
                if switch_tag:
                    ax.text(switch.coordinates.x, switch.coordinates.y, f'SW{idx}', color='green')

            # Plot Links
            if show_links:
                for link in self.connection_manager.links:
                    ax.plot(
                        [link.node1.coordinates.x, link.node2.coordinates.x],
                        [link.node1.coordinates.y, link.node2.coordinates.y],
                        c='k'
                    )
                    midpoint_x = (link.node1.coordinates.x + link.node2.coordinates.x) / 2
                    midpoint_y = (link.node1.coordinates.y + link.node2.coordinates.y) / 2

                    if self.connection_manager.check_link_status(link) == "uplink":
                        ax.text(midpoint_x, midpoint_y + 0.5, link.name, color='black', fontsize=8)
                    elif self.connection_manager.check_link_status(link) == "downlink":
                        ax.text(midpoint_x, midpoint_y - 0.5, link.name, color='black', fontsize=8)

            ax.set_xlabel('X-axis')
            ax.set_ylabel('Y-axis')
            ax.set_title('2D Top-Down View of Environment')
            plt.tight_layout()
            store(plt, f"{simulation_name}_2D_environment.png")

        else:
            # 3D Plot
            fig, ax = plt.subplots(figsize=(16, 12), subplot_kw={'projection': '3d'})

            ax.set_xlim([0, self.x_dimension])
            ax.set_ylim([0, self.y_dimension])
            ax.set_zlim([0, self.z_dimension])

            # Plot UEs
            for idx, ue in enumerate(self.ues):
                ax.scatter(ue.coordinates.x, ue.coordinates.y, ue.coordinates.z, c='b', marker='o')
                if ue_tag:
                    ax.text(ue.coordinates.x, ue.coordinates.y, ue.coordinates.z, f'UE{idx}', color='blue')

            # Plot BSs
            for idx, bs in enumerate(self.bss):
                ax.scatter(bs.coordinates.x, bs.coordinates.y, bs.coordinates.z, c='r', marker='^')
                if bs_tag:
                    ax.text(bs.coordinates.x, bs.coordinates.y, bs.coordinates.z, f'BS{idx}', color='red')

            # Plot Switches
            for idx, switch in enumerate(self.switches):
                ax.scatter(switch.coordinates.x, switch.coordinates.y, switch.coordinates.z, c='g', marker='s')
                if switch_tag:
                    ax.text(switch.coordinates.x, switch.coordinates.y, switch.coordinates.z, f'SW{idx}',
                            color='green')

            # Plot Links
            if show_links:
                for link in self.connection_manager.links:
                    ax.plot(
                        [link.node1.coordinates.x, link.node2.coordinates.x],
                        [link.node1.coordinates.y, link.node2.coordinates.y],
                        [link.node1.coordinates.z, link.node2.coordinates.z],
                        c='k'
                    )
                    midpoint_x = (link.node1.coordinates.x + link.node2.coordinates.x) / 2
                    midpoint_y = (link.node1.coordinates.y + link.node2.coordinates.y) / 2
                    midpoint_z = (link.node1.coordinates.z + link.node2.coordinates.z) / 2

                    if self.connection_manager.check_link_status(link) == "uplink":
                        ax.text(midpoint_x, midpoint_y, midpoint_z + 0.5, link.name, color='black', fontsize=8)
                    elif self.connection_manager.check_link_status(link) == "downlink":
                        ax.text(midpoint_x, midpoint_y, midpoint_z - 0.5, link.name, color='black', fontsize=8)

            ax.set_xlabel('X-axis')
            ax.set_ylabel('Y-axis')
            ax.set_zlabel('Z-axis')
            ax.set_title('3D Environment with UEs, BSs, and Switches')
            ax.set_box_aspect([12, 8, 1])
            plt.tight_layout()
            store(plt, f"{simulation_name}_3D_environment.png")

    def report_status(self):
        """
        Generate a report of the current environment, including nodes and links.
        """
        report = {
            'UEs': {f'UE_{i}': ue.coordinates.__dict__ for i, ue in enumerate(self.ues)},
            'BSs': {f'BS_{i}': bs.coordinates.__dict__ for i, bs in enumerate(self.bss)},
            'Switches': {f'SW_{i}': sw.coordinates.__dict__ for i, sw in enumerate(self.switches)},
            'Links': [link for link in self.connection_manager.links]
        }
        return report
