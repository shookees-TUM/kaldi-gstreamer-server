import json
import os
import Queue
import sys
import threading

from ws4py.client.threadedclient import WebSocketClient


class MyClient(WebSocketClient):

    def __init__(self, audiofile, url, protocols=None, extensions=None,
                 heartbeat_freq=None, byterate=32000,
                 save_adaptation_state_filename=None,
                 send_adaptation_state_filename=None):
        super(MyClient, self).__init__(url, protocols,
                                       extensions, heartbeat_freq)
        self.final_hyps = []
        self.audiofile = audiofile
        self.byterate = byterate
        self.final_hyp_queue = Queue.Queue()
        self.save_adaptation_state_filename = save_adaptation_state_filename
        self.send_adaptation_state_filename = send_adaptation_state_filename

    @rate_limited(4)
    def send_data(self, data):
        self.send(data, binary=True)

    def opened(self):
        def send_data_to_ws():
            if self.send_adaptation_state_filename is not None:
                print("Sending adaptation state from {}".format(
                      self.send_adaptation_state_filename), file=sys.stderr)
                try:
                    adaptation_state_props = json.load(
                        open(self.send_adaptation_state_filename, "r"))
                    self.send(json.dumps
                              (dict(adaptation_state=adaptation_state_props)))
                except:
                    e = sys.exc_info()[0]
                    print("Failed to send adaptation state: {}".format(e),
                          file=sys.stderr)
            with self.audiofile as audiostream:
                for block in iter(lambda:
                                  audiostream.read(self.byterate/4), ""):
                    self.send_data(block)
            print("Audio sent, now sending EOS", file=sys.stderr)
            self.send("EOS")

        t = threading.Thread(target=send_data_to_ws)
        t.start()

    def received_message(self, m):
        response = json.loads(str(m))
        if response['status'] == 0:
            if 'result' in response:
                trans = response['result']['hypotheses'][0]['transcript']
                if response['result']['final']:
                    self.final_hyps.append(trans)
                    print('\r{}'.format(trans.replace("\n", "\\n")), file=sys.stderr)
                else:
                    print_trans = trans.replace("\n", "\\n")
                    if len(print_trans) > 80:
                        print_trans = "... %s" % print_trans[-76:]
                    print('\r{}'.format(print_trans), file=sys.stderr)
            if 'adaptation_state' in response:
                if self.save_adaptation_state_filename:
                    print("Saving adaptation state to {}".format(
                          self.save_adaptation_state_filename), file=sys.stderr)
                    with open(self.save_adaptation_state_filename, "w") as f:
                        f.write(json.dumps(response['adaptation_state']))
        else:
            print("Received error from server (status {})".format(
                  response['status']), file=sys.stderr)
            if 'message' in response:
                print("Error message: {}".format(response['message']),
                      file=sys.stderr)

    def get_full_hyp(self, timeout=60):
        return self.final_hyp_queue.get(timeout)

    def closed(self, code, reason=None):
        self.final_hyp_queue.put(" ".join(self.final_hyps))
