import time
import cProfile
import pstats

def measure_function(information, function, *args, **kwargs):
    start = time.time()
    result = function(*args, **kwargs)
    interval = time.time() - start
    if interval > 0.01:
        print(f"{function.__name__}: {interval:.5f}")
        print(information)
    return result

def print_time(interval, tag="default", threshold = 0.05, information=""):
    if interval > threshold:
        print(f"{tag} : {interval:.5f}")
        print(information)
        return True
    return False