# -*- coding: UTF-8 -*-

'''
Created on Jun 27, 2013

@author: tanel
'''
import unittest
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst
import _thread
import logging
from kaldigstserver.decoder.KaldiDecoderPipeline import KaldiDecoderPipeline
import time

class DecoderPipelineTests(unittest.TestCase):

    def __init__(self,  *args, **kwargs):
        super(DecoderPipelineTests, self).__init__(*args, **kwargs)
        logging.basicConfig(level=logging.INFO)

    def setUp(cls):
            decoder_conf = {"model" : "/opt/kaldi-gstreamer-server-test/test/models/estonian/tri2b_mmi_pruned/final.mdl",
                            "lda-mat" : "/opt/kaldi-gstreamer-server-test/test/models/estonian/tri2b_mmi_pruned/final.mat",
                            "word-syms" : "/opt/kaldi-gstreamer-server-test/test/models/estonian/tri2b_mmi_pruned/words.txt",
                            "fst" : "/opt/kaldi-gstreamer-server-test/test/models/estonian/tri2b_mmi_pruned/HCLG.fst",
                            "silence-phones" : "6"}
            cls.decoder_pipeline = KaldiDecoderPipeline({"decoder" : decoder_conf})
            cls.words = []
            cls.finished = False

            cls.decoder_pipeline.set_word_handler(cls.word_getter)
            cls.decoder_pipeline.set_eos_handler(cls.set_finished, cls.finished)

            loop = GLib.MainLoop()
            _thread.start_new_thread(loop.run, ())

    def word_getter(cls, word):
        cls.words.append(word)

    def set_finished(cls, finished):
        cls.finished = True

    def send_data(self, data_iterator):
        for block in data_iterator:
            self.decoder_pipeline.process_data(block)

    def testCancelAfterEOS(self):
        self.decoder_pipeline.init_request("testCancelAfterEOS", "audio/x-raw, layout=(string)interleaved, rate=(int)16000, format=(string)S16LE, channels=(int)1")
        f = open("/opt/kaldi-gstreamer-server-test/test/data/1234-5678.raw", "rb")
        self.send_data(iter(lambda: f.read(8000), b''))

        self.decoder_pipeline.end_request()
        self.decoder_pipeline.cancel()
        while not self.finished:
            pass

        self.assertEqual(["üks", "kaks", "kolm", "neli", "<#s>", "viis", "kuus", "seitse", "kaheksa", "<#s>"], self.words)
        


    def test12345678(self):
        self.decoder_pipeline.init_request("test12345678", "audio/x-raw, layout=(string)interleaved, rate=(int)16000, format=(string)S16LE, channels=(int)1")
        f = open("/opt/kaldi-gstreamer-server-test/test/data/1234-5678.raw", "rb")
        self.send_data(iter(lambda: f.read(8000), b''))

        self.decoder_pipeline.end_request()


        while not self.finished:
            pass
        self.assertEqual(["üks", "kaks", "kolm", "neli", "<#s>", "viis", "kuus", "seitse", "kaheksa", "<#s>"], self.words)

    def testWav(self):
        self.decoder_pipeline.init_request("testWav", "")
        f = open("/opt/kaldi-gstreamer-server-test/test/data/lause2.wav", "rb")
        self.send_data(iter(lambda: f.read(int(16000*2*2/4)), b''))

        self.decoder_pipeline.end_request()


        while not self.finished:
            pass
        self.assertEqual("see on teine lause <#s>".split(), self.words)

    def testOgg(self):
        self.decoder_pipeline.init_request("testOgg", "")
        f = open("/opt/kaldi-gstreamer-server-test/test/data/test_2lauset.ogg", "rb")
        self.send_data(iter(lambda: f.read(int(86*1024/8/4)), b''))

        self.decoder_pipeline.end_request()


        while not self.finished:
            pass
        self.assertEqual("see on esimene lause <#s> see on teine lause <#s>".split(), self.words)



    def __testDecoder(self):
        finished = [False]




        def do_shit():
            decoder_pipeline.init_request("test0", "audio/x-raw, layout=(string)interleaved, rate=(int)16000, format=(string)S16LE, channels=(int)1")
            f = open("/opt/kaldi-gstreamer-server-test/test/data/1234-5678.raw", "rb")
            self.send_data(iter(lambda: f.read(8000), b''))
            
            decoder_pipeline.end_request()
    
        do_shit()
    
        while not finished[0]:
            time.sleep(1)
        self.assertEqual(["üks", "kaks", "kolm", "neli", "<#s>", 
                          "viis", "kuus", "seitse", "kaheksa", "<#s>"], words)
        
        words = []
        
        finished[0] = False    
        do_shit()
        while not finished[0]:
            pass
            
        self.assertItemsEqual(["see", "on", "teine", "lause", "<#s>"], words, "Recognition result")
        
        # Now test cancelation of a long submitted file
        words = []        
        decoder_pipeline.init_request("test0", "audio/x-raw, layout=(string)interleaved, rate=(int)16000, format=(string)S16LE, channels=(int)1")
        f = open("/opt/kaldi-gstreamer-server-test/test/data/etteytlus.raw", "rb")
        decoder_pipeline.process_data(f.read())
        time.sleep(3)
        decoder_pipeline.cancel()
        print("Pipeline cancelled")
        
        words = []
        finished[0] = False
        decoder_pipeline.init_request("test0", "audio/x-raw, layout=(string)interleaved, rate=(int)16000, format=(string)S16LE, channels=(int)1")
        # read and send everything
        f = open("/opt/kaldi-gstreamer-server-test/test/data/lause2.raw", "rb")
        decoder_pipeline.process_data(f.read(10*16000))
        decoder_pipeline.end_request()
        while not finished[0]:
            pass
        self.assertItemsEqual(["see", "on", "teine", "lause", "<#s>"], words, "Recognition result")
        
        #test cancelling without anything sent
        decoder_pipeline.init_request("test0", "audio/x-raw, layout=(string)interleaved, rate=(int)16000, format=(string)S16LE, channels=(int)1")
        decoder_pipeline.cancel()
        print("Pipeline cancelled")
        
        words = []
        finished[0] = False
        decoder_pipeline.init_request("test0", "audio/x-wav")
        # read and send everything
        f = open("/opt/kaldi-gstreamer-server-test/test/data/lause2.wav", "rb")
        decoder_pipeline.process_data(f.read())
        decoder_pipeline.end_request()
        while not finished[0]:
            pass
        self.assertItemsEqual(["see", "on", "teine", "lause", "<#s>"], words, "Recognition result")

        words = []
        finished[0] = False
        decoder_pipeline.init_request("test0", "audio/ogg")
        # read and send everything
        f = open("/opt/kaldi-gstreamer-server-test/test/data/test_2lauset.ogg", "rb")
        decoder_pipeline.process_data(f.read(10*16000))

        decoder_pipeline.end_request()
        while not finished[0]:
            pass
        self.assertItemsEqual("see on esimene lause <#s> see on teine lause <#s>".split(), words, "Recognition result")


def main():
    unittest.main()

if __name__ == '__main__':
    main()