from hobonaut.models.redis_connection import rc, rn
import time


"""Slogan is cached locally by having a module-wide global var for it
"""
slogan = None


def get():
    global slogan
    if slogan is None:
        slogan = rc().get(rn('slogan'))
    return slogan


def save(new_slogan):
    global slogan
    slogan = new_slogan
    rc().set(rn('slogan'), new_slogan)
    rc().zadd(rn('slogans'), int(time.time()), new_slogan)