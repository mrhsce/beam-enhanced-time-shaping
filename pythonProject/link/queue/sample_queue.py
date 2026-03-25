import numpy as np


class DownlinkQueues:
    def __init__(self, number_of_users, initial_frame_count, initial_time=0, queue_max_length=None):
        self.frame_size = 2304 * 8  # MTU of WIFI, adjust if necessary
        self.queue_max_length = queue_max_length
        # Initialize the queue with frame information (size, creation time, exit time)
        self.queues = [[(self.frame_size, initial_time, None)] * initial_frame_count for _ in range(number_of_users)]
        self.delays = [[] for _ in range(number_of_users)]  # Store delays for each user

    def get_queue(self, user_id):
        # Return the queue of a specific user
        return self.queues[user_id]

    def get_delays(self, user_id):
        return self.delays[user_id]

    def get_average_delay(self, user_id, current_time, period):
        # Filter delays to only consider those within the time period [current_time - d, current_time]
        relevant_delays = [delay for delay, _, exit_time in self.delays[user_id] if
                           exit_time and (current_time - period) <= exit_time <= current_time]
        if relevant_delays:
            return sum(relevant_delays) / len(relevant_delays)
        return 0

    def get_all_queue_lengths(self):
        # Return a list containing the length of each user's queue
        return np.array([len(queue) for queue in self.queues])

    def get_all_users_average_delay(self, current_time, period=None, decimals=2):
        if period is None:
            period = current_time
        return [round(self.get_average_delay(user_id, current_time, period), decimals) for user_id in range(len(self.queues))]


    def remove_frame_by_data_rate(self, user_data_rates, time_period, current_time):
        frames_removed = [0] * len(user_data_rates)

        for user_id, data_rate in enumerate(user_data_rates):
            total_data = data_rate * time_period
            while self.queues[user_id] and total_data >= self.frame_size:
                total_data -= self.frame_size
                _, creation_time, _ = self.queues[user_id].pop(0)
                exit_time = current_time
                delay = exit_time - creation_time
                self.delays[user_id].append((delay, creation_time, exit_time))
                frames_removed[user_id] += 1

        return frames_removed

    def insert_frames_by_poisson(self, time_period, lambda_rate, current_time):
        dropped_frames_count = [0] * len(self.queues)
        for user_id in range(len(self.queues)):
            frame_count = np.random.poisson(lambda_rate * time_period)
            for _ in range(frame_count):
                if self.queue_max_length is None or len(self.queues[user_id]) < self.queue_max_length:
                    self.queues[user_id].append((self.frame_size, current_time, None))
                else:
                    dropped_frames_count[user_id] += 1

        return dropped_frames_count
