import os
import psutil


def usage():
    process = psutil.Process(os.getpid())
    return process.memory_info()[0] / float(2**20)
