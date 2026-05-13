import threading
from concurrent.futures import ThreadPoolExecutor

# Global thread pool for background tasks
# We use a ThreadPoolExecutor to run tasks in the background without blocking the main thread.
executor = ThreadPoolExecutor(max_workers=4)

def run_in_background(func, *args, **kwargs):
    """
    Submits a function to be executed in the background thread pool.
    """
    executor.submit(func, *args, **kwargs)
