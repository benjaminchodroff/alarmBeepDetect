#!/usr/bin/env python
# This program is for educational purposes only and should never be used in any production or safety system
# Benjamin Chodroff benjamin.chodroff@gmail.com

import pyaudio
from numpy import zeros,linspace,short,fromstring,hstack,transpose,log
from scipy import fft
from time import sleep

#Volume Sensitivity, 0.05: Extremely Sensitive, may give false alarms
#             0.1: Probably Ideal volume
#             1: Poorly sensitive, will only go off for relatively loud
SENSITIVITY= 1
# Alarm frequency (Hz) to detect (Set frequencyoutput to True if you need to detect what frequency to use)
TONE = 3500
#Bandwidth for detection (i.e., detect frequencies +- within this margin of error of the TONE)
BANDWIDTH = 30
#How many 46ms blips before we declare a beep? (Set frequencyoutput to True if you need to determine how many blips are found, then subtract some)
beeplength=8
# How many beeps before we declare an alarm? (Avoids false alarms)
alarmlength=5
# How many false 46ms blips before we declare there are no more beeps? (May need to be increased if there are expected long pauses between beeps) 
resetlength=10
# How many reset counts until we clear an active alarm? (Keep the alarm active even if we don't hear this many beeps)
clearlength=30
# Enable blip, beep, and reset debug output (useful for understanding when blips, beeps, and resets are being found)
debug=False
# Show the most intense frequency detected (useful for configuration of the frequency and beep lengths)
frequencyoutput=False


# Audio Sampler
NUM_SAMPLES = 2048
SAMPLING_RATE = 44100
pa = pyaudio.PyAudio()
_stream = pa.open(format=pyaudio.paInt16,
                  channels=1, rate=SAMPLING_RATE,
                  input=True,
                  frames_per_buffer=NUM_SAMPLES)

print("Alarm detector working. Press CTRL-C to quit.")

blipcount=0
beepcount=0
resetcount=0
clearcount=0
alarm=False

while True:
    while _stream.get_read_available()< NUM_SAMPLES: sleep(0.01)
    audio_data  = fromstring(_stream.read(
         _stream.get_read_available()), dtype=short)[-NUM_SAMPLES:]
    # Each data point is a signed 16 bit number, so we can normalize by dividing 32*1024
    normalized_data = audio_data / 32768.0
    intensity = abs(fft(normalized_data))[:NUM_SAMPLES/2]
    frequencies = linspace(0.0, float(SAMPLING_RATE)/2, num=NUM_SAMPLES/2)
    if frequencyoutput:
        which = intensity[1:].argmax()+1
        # use quadratic interpolation around the max
        if which != len(intensity)-1:
            y0,y1,y2 = log(intensity[which-1:which+2:])
            x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
            # find the frequency and output it
            thefreq = (which+x1)*SAMPLING_RATE/NUM_SAMPLES
        else:
            thefreq = which*SAMPLING_RATE/NUM_SAMPLES
    if max(intensity[(frequencies < TONE+BANDWIDTH) & (frequencies > TONE-BANDWIDTH )]) > max(intensity[(frequencies < TONE-1000) & (frequencies > TONE-2000)]) + SENSITIVITY:
        if frequencyoutput:
            print "\t\t\t\tfreq=",thefreq
        blipcount+=1
        resetcount=0
        if debug: print "\t\tBlip",blipcount
        if (blipcount>=beeplength):
            blipcount=0
            resetcount=0
            beepcount+=1
            if debug: print "\tBeep",beepcount
            if (beepcount>=alarmlength):
                clearcount=0
                alarm=True
                print "Alarm!"
                beepcount=0
    else:
        if frequencyoutput:
            print "\t\t\t\tfreq="
        blipcount=0
        resetcount+=1
        if debug: print "\t\t\treset",resetcount
        if (resetcount>=resetlength):
            resetcount=0
            beepcount=0
            if alarm:
                clearcount+=1
                if debug: print "\t\tclear",clearcount
                if clearcount>=clearlength:
                    clearcount=0
                    print "Cleared alarm!"
                    alarm=False
    sleep(0.01)
