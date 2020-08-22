"""Test interrupt handling."""
import sys
import time

from dagster.serdes.ipc import setup_interrupt_support

if __name__ == "__main__":
    setup_interrupt_support()
    started_sentinel, interrupt_sentinel = (sys.argv[1], sys.argv[2])
    with open(started_sentinel, "w") as fd:
        fd.write("setup_interrupt_support")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        with open(interrupt_sentinel, "w") as fd:
            fd.write("received_keyboard_interrupt")
