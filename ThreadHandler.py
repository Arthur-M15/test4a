
import threading

class ThreadWorker(threading.Thread):
    def __init__(self, function, *args):
        super().__init__()
        self.function = function
        self.args = args
        self.running = True  # Allows the thread to stop gracefully

    def run(self):
        """ Main loop executed in the thread """
        while self.running:
            self.function(*self.args)  # Execute the function with its arguments

    def stop(self):
        """ Request the thread to stop """
        self.running = False
        self.join()  # Wait for the thread to fully stop


class ThreadHandler:
    def __init__(self):
        self.threads = {}

    def create(self, function, *args):
        """ Create and start a new thread running a function in a loop """
        name = function.__name__
        if name in self.threads:
            print(f"[ThreadHandler] A thread for {name} is already running.")
            return

        thread = ThreadWorker(function, *args)
        self.threads[name] = thread
        thread.start()

    def stop(self, function_name):
        """ Stop a specific thread """
        if function_name in self.threads:
            self.threads[function_name].stop()
            del self.threads[function_name]

    def stop_all(self):
        """ Stop all running threads """
        for name in list(self.threads.keys()):  # Convert keys to a list to avoid modification issues
            self.stop(name)
