from __future__ import print_function

import myo as libmyo
from myo import Pose
from funcs import *
import time
import sys

libmyo.init()

class SequenceListener(libmyo.DeviceListener):
    """
    Listener implementation. Return False from any function to
    stop the Hub.
    """

    max_duration = 3
    interval = 0.05  # Output only 0.05 seconds

    def __init__(self):
        super(SequenceListener, self).__init__()
        self.emg_enabled = False
        self.orientation = None
        self.pose = libmyo.Pose.rest
        self.rssi = None
        self.locked = False
        self.last_time = 0
        self.sequences = {}
        self.curr_sequence = []
        self.curr_start = 0
        self.curr_tweet = ''
        self.curr_audio_ctx = None

    def register_sequence(self, name, seq):
        node = self.sequences
        for i, pose in enumerate(seq):
            if pose not in node:
                node[pose] = {}
            if i + 1 == len(seq):
                node[pose][None] = name
            else:
                node = node[pose]

    def on_connect(self, myo, timestamp):
        print("CONNECTED")
        myo.request_rssi()

    def on_rssi(self, myo, timestamp, rssi):
        self.rssi = rssi

    def on_event(self, kind, event):
        if self.curr_audio_ctx:
            print("WRITE")
            process_audio_frame(self.curr_audio_ctx)
        """
        Called before any of the event callbacks.
        """

    def on_event_finished(self, kind, event):
        """
        Called after the respective event callbacks have been
        invoked. This method is *always* triggered, even if one of
        the callbacks requested the stop of the Hub.
        """

    def on_pair(self, myo, timestamp):
        """
        Called when a Myo armband is paired.
        """

    def on_disconnect(self, myo, timestamp):
        """
        Called when a Myo is disconnected.
        """

    def on_pose(self, myo, timestamp, pose):
        print("Pose: %s" % str(pose))
        self._process_sequence(myo, timestamp, pose)

    # Detect sequences and fire off on_sequence events as appropriate.
    def _process_sequence(self, myo, timestamp, pose):
        # If we aren't currently walking down a seq, set a new
        # start timestamp
        if not len(self.curr_sequence):
            self.curr_start = time.time()

        # Walk up the current sequence
        node = self.sequences
        for curr_pose in self.curr_sequence:
            node = node[curr_pose]

        if pose == libmyo.Pose.fingers_spread:
            myo.vibrate('long')
            self.curr_sequence = []
            return

        # Ignore if we defaulted to rest/the same pose
        if pose == libmyo.Pose.rest or \
            (len(self.curr_sequence) and pose == self.curr_sequence[-1]):
            pass
        # If the current node is in the suffix tree, update our seq
        elif pose in node:
            node = node[pose]
            self.curr_sequence.append(pose)
            myo.vibrate('short')
            if None in node:
                self.on_sequence(myo, timestamp, node[None])
                self.curr_sequence = []
        # Else reset our seq... if necessary
        elif len(self.curr_sequence):
            myo.vibrate('long')
            self.curr_sequence = []

        if pose not in [libmyo.Pose.__fallback__, libmyo.Pose.rest]:
            print("Pose: %s", str(pose))

    def on_orientation_data(self, myo, timestamp, orientation):
        #print("%f" % (orientation.x))
        #print("\r%f %f %f" % (orientation.x, orientation.y, orientation.z), end='')
#        sys.out.flush()
        self.orientation = orientation

    def on_accelerometor_data(self, myo, timestamp, acceleration):
        return
        for i in range(0, 3):
            if acceleration[i] < self.lo[i]:
                self.lo[i] = acceleration[i]
            if self.hi[i] < acceleration[i]:
                self.hi[i] = acceleration[i]

        if True:
            """
            print("\r%.02f %.02f %.02f ---  %.02f %.02f %.02f                " %
                (self.lo[0], self.lo[1], self.lo[2], self.hi[0], self.hi[1], self.hi[2]),
                end=''
            )
            print("\r%.02f -- %.02f                " %
                (self.lo[1], self.hi[1]),
                end=''
            )
            """
        else:
            if acceleration[0] > -3:
                print("SLAP")
            if acceleration[1] < -5:
                print("PANCH")
        pass

    def on_gyroscope_data(self, myo, timestamp, gyroscope):
        pass

    def on_unlock(self, myo, timestamp):
        self.locked = False

    def on_lock(self, myo, timestamp):
        self.locked = True

    def on_sync(self, myo, timestamp, arm, x_direction):
        pass

    def on_unsync(self, myo, timestamp):
        pass

    def on_emg(self, myo, timestamp, emg):
        pass

    def on_sequence(self, myo, timestamp, name):
        if name == 'start' and not self.curr_audio_ctx:
            print("START")
            self.curr_audio_ctx = create_audio_ctx()
        elif name == 'stop' and self.curr_audio_ctx:
            print("END")
            close_audio_ctx(self.curr_audio_ctx)
            self.curr_tweet += ' %s' % speech_to_text()
            self.curr_audio_ctx = None
        elif name == 'clear':
            print("CLEAR")
            self.curr_tweet = ''
        elif name == 'send' and len(self.curr_tweet):
            print("SEND: %s" % self.curr_tweet)
            tweet(self.curr_tweet)
        print("Sequence: %s" % name)

def main():
    listener = SequenceListener()
    listener.register_sequence('start', [Pose.wave_in, Pose.wave_out, Pose.wave_in])
    listener.register_sequence('stop', [Pose.wave_in, Pose.fist])
    listener.register_sequence('clear', [Pose.wave_out, Pose.double_tap])
    listener.register_sequence('send', [Pose.fist, Pose.wave_out, Pose.wave_in])

    print("Connecting to Myo ... Use CTRL^C to exit.")
    print("If nothing happens, make sure the Bluetooth adapter is plugged in,")
    print("Myo Connect is running and your Myo is put on.")
    hub = libmyo.Hub()
    hub.set_locking_policy(libmyo.LockingPolicy.none)
    hub.run(1000, listener)

    # Listen to keyboard interrupts and stop the hub in that case.
    try:
        while hub.running:
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("\nQuitting ...")
    finally:
        print("Shutting down hub...")
        hub.shutdown()


if __name__ == '__main__':
    main()

