import numpy as np


def poisson(total_users, rate_per_minute):
    """
    Simulate a Poisson process with a given rate of users per minute.

    Parameters:
    total_users (int): The total number of users.
    rate_per_minute (float): The rate of users per minute.

    Returns:
    numpy.ndarray: An array of arrival times.
    """
    # Calculate the rate parameter lambda
    lam = rate_per_minute / 60

    # Generate inter-arrival times
    inter_arrival_times = np.random.exponential(1/lam, total_users)

    # Return the cumulative sum of these times, which gives the arrival time of each event
    # return np.cumsum(inter_arrival_times)
    return inter_arrival_times


def poisson_per_time(total_time, rate_per_minute):
    """
    Simulate a Poisson process with a given rate of events per minute.

    Parameters:
    total_time (float): The total time in minutes.
    rate_per_minute (float): The rate of events per minute.

    Returns:
    numpy.ndarray: An array of event times.
    """
    # Calculate the rate parameter lambda
    lam = rate_per_minute / 60
    # Calculate the total number of events
    total_events = int(total_time * rate_per_minute)
    # Generate inter-event times
    inter_event_times = np.random.exponential(1/lam, total_events)
    # Return the cumulative sum of these times, which gives the event time of each event
    # return np.cumsum(inter_event_times)
    return inter_event_times


def zipf(total_videos, samples, alpha):
    zipf_dist = [1.0 / (i ** alpha) for i in range(1, total_videos + 1)]
    zipf_dist = [x / sum(zipf_dist) for x in zipf_dist]

    indices = np.random.choice(total_videos, samples, p=zipf_dist)
    data = np.random.permutation(np.arange(1, total_videos + 1))

    elements = [data[i] for i in indices]

    return elements


def main():
    videos = zipf(total_videos=10, samples=60, alpha=2.0)
    print(videos)
    
    print("----------------------")
    
    arrival_times = poisson(total_users=60, rate_per_minute=5)
    print(arrival_times)

    print("----------------------")
    
    arrival_times = poisson_per_time(total_time=60, rate_per_minute=5)
    print(arrival_times)
    print(len(arrival_times))


if __name__ == "__main__":
    main()