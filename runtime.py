import timeit

class RuntimeEstimate:
    def __init__(self):
        self.start_time = None
        self.total_time = None
        self.last_time = None
        self.progress = None
        
    # Start the timer and reset progress
    def start(self):
        self.start_time = timeit.default_timer()
        self.last_time = self.start_time
        self.progress = 0
        
    # Returns how much time has elapsed in seconds since the timer started
    def elapsed_time(self):
        if self.start_time is None:
            raise Exception("Timer not started!")
        return timeit.default_timer() - self.start_time
    
    # Returns how much time the whole process should take from start to finish
    def estimated_total_time(self):
        if self.start_time is None:
            raise Exception("Timer not started!")
        if self.progress is None or self.progress == 0:
            raise Exception("No progress information available!")
        return self.elapsed_time() / self.progress
    
    # Returns an estimate of how much time is left before the process is complete
    def estimated_remaining_time(self):
        if self.start_time is None:
            raise Exception("Timer not started!")
        if self.progress is None or self.progress == 0:
            raise Exception("No progress information available!")
        return self.estimated_total_time() * (1 - self.progress)
    
    # Update with the current amount of progress expressed as a fraction from 0 (not started) to 1 (finished)
    def update_progress(self, progress):
        self.progress = progress
        now = timeit.default_timer()
        self.total_time = now - self.start_time
        self.last_time = now

    def __str__(self):
        if self.start_time is None:
            raise Exception("Timer not started!")
        if self.progress is None:
            return "Elapsed time: {}".format(self.format_time(self.elapsed_time()))
        else:
            return "Elapsed time: {}; Estimated remaining time: {}".format(self.format_time(self.elapsed_time()), self.format_time(self.estimated_remaining_time()))
    
    @staticmethod
    def format_time(seconds):
        if seconds < 60:
            return "{:.2f} seconds".format(seconds)
        elif seconds < 3600:
            return "{:.2f} minutes".format(seconds / 60)
        elif seconds < 86400:
            return "{:.2f} hours".format(seconds / 3600)
        elif seconds < 604800:
            return "{:.2f} days".format(seconds / 86400)
        elif seconds < 2592000:
            return "{:.2f} weeks".format(seconds / 604800)
        elif seconds < 31536000:
            return "{:.2f} months".format(seconds / 2592000)
        else:
            return "{:.2f} years".format(seconds / 31536000)