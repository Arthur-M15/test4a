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

def normalize_text(text, size=8):
    text_size = len(text)
    diff = abs(size - text_size)
    if text_size < size:
        text += " " * diff
    elif text_size > size:
        text = text[:size]  # Correction ici : on coupe à "size" et non à "diff"
    return text  # Il faut retourner la valeur normalisée