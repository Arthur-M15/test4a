import time
import cProfile
import pstats

def measure_function(function, *args, **kwargs):
    start = time.time()
    function(*args, **kwargs)
    interval = time.time() - start

    #result = f"{function.__name__}: {interval:.5f} sec"
    return interval

def print_time(interval, tag="default", threshold = 0.05, information=""):
    if interval > threshold:
        print(f"{tag} : {interval:.5f}")
        print(information)
        return True
    return False

def normalize_text(text, size=8):
    var_type = type(text)
    if var_type != str:
        text = str(text)
    text_size = len(text)
    diff = abs(size - text_size)
    if text_size < size:
        text += " " * diff
    elif text_size > size:
        text = text[:size]  # Correction ici : on coupe à "size" et non à "diff"
    return text  # Il faut retourner la valeur normalisée