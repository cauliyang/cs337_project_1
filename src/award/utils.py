import time


class Timer:
    def __init__(self, desc="timer"):
        self.desc = desc
        self.start = 0
        self.end = 0
        self.elapsed = 0

    def __enter__(self):
        self.start = time.time()
        return self  # Optional, allows access to elapsed

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.time()
        self.elapsed = self.end - self.start
        print(f"{self.desc} Elapsed time: {self.elapsed:.4f} seconds")
