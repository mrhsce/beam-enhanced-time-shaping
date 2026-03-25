import matplotlib.pyplot as plt
import numpy as np
import os
import math
from matplotlib.animation import FuncAnimation


def visualize_movement_and_save(status_reports, video_filename='ue_bs_movement', ue_tag=True, bs_tag=False):
    fig, ax = plt.subplots(figsize=(16, 12), subplot_kw={'projection': '3d'})

    # Prepare for dynamic limits based on your data
    ax.set_xlim([0, 120])
    ax.set_ylim([0, 80])
    ax.set_zlim([0, 10])

    plt.tight_layout()
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    def animate(i):
        i *= 10
        ax.clear()  # Clear previous frame
        ax.set_box_aspect([12, 8, 1])  # Equal aspect ratio in all directions

        # Re-apply the fixed limits after clearing
        ax.set_xlim([0, 120])
        ax.set_ylim([0, 80])
        ax.set_zlim([0, 10])

        # Reset labels and title since ax.clear() removes them
        ax.set_xlabel('X-axis')
        ax.set_ylabel('Y-axis')
        ax.set_zlabel('Z-axis')

        ue_positions = np.array([list(v.values()) for v in status_reports[i]['environment']['UEs'].values()])
        bs_positions = np.array([list(v.values()) for v in status_reports[i]['environment']['BSs'].values()])

        # Plot UE and BS positions
        if len(ue_positions) > 0:
            ue_scatter = ax.scatter(ue_positions[:, 0], ue_positions[:, 1], ue_positions[:, 2], c='b', marker='o')
            if ue_tag:
                for idx, pos in enumerate(ue_positions):
                    ax.text(pos[0], pos[1], pos[2], f'UE{idx+1}', color='blue')

        if len(bs_positions) > 0:
            bs_scatter = ax.scatter(bs_positions[:, 0], bs_positions[:, 1], bs_positions[:, 2], c='r', marker='^')
            if bs_tag:
                for idx, pos in enumerate(bs_positions):
                    ax.text(pos[0], pos[1], pos[2], f'BS{idx+1}', color='red')

    ani = FuncAnimation(fig, animate, frames=math.floor(len(status_reports) / 10), blit=False, interval=1)

    # Save the animation
    output_directory = 'output'
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    ani.save(f'{output_directory}/{video_filename}.mp4', writer='ffmpeg', fps=10, dpi=300)

    print(f'Video saved as {video_filename}')
