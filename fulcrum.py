#!/usr/bin/python2
############################################################################
# fulcrum.py                                       version 20170320.171017
#
# By Dr. Beco <rcb@beco.cc>                            License GNU/GPL 2.0
#
# Brief description:
# Feed entropy (randomness) to /dev/random from Random.Org
# 
# Usage:
#       Keep it running as background
#
############################################################################

import subprocess
import sys
import time
import Queue
import base64
import logging
import os
import requests
import binascii
from rdoclient import RandomOrgClient

## Defines
FeedBits = 80000 # package of bits to ask from Random.Org
CachedPackages = 5 # Number of cached packages to keep in memory before connecting to Random.Org
MinimumEntropy = 600 # Minimum system's entropy before starting feeding bits
MinimumRequests = 10 # Minimum requests available from Random.Org
SleepLong = 3600 # sleep one hour
SleepError = 5 # Time to sleep in case of error
SleepInfo = 2 # Time to sleep in case of info or warning
DEVNULL = open(os.devnull, 'wb') # /dev/null
APIDIR = './'
#APIDIR = '/usr/local/bin/fulcrum/'

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s', filename='fulcrum.log', level=logging.INFO, datefmt='%Y%m%d.%H%M%S')
logger = logging.getLogger('fulcrum')
for handler in logging.root.handlers:
    handler.addFilter(logging.Filter('fulcrum'))
 
printonce = 0 # 'Entropy is OK' message only once


try:
    fd = open("%s.api-randomorg.txt" % APIDIR, "r")
    keyn = fd.readline()
    fd.close()
    key = keyn.rstrip()
except:
    logger.error('Unexpected error while reading api key')
    sys.exit(1)

r = RandomOrgClient(key, blocking_timeout=3600.0, http_timeout=30.0)

flagProto = 0

abl = r.get_bits_left()
arl = r.get_requests_left()

hblt = requests.get('https://www.random.org/quota/?format=plain')
hbl = int(hblt.text.rstrip())

if abl < FeedBits+1:
    logger.error("Not enough API bits at Random.Org. (%d bits)" % abl)
    flagProto = 1

if arl < MinimumRequests:
    logger.error("API requests depleted. (%d requests)" % arl)
    flagProto += 2

if hbl < FeedBits+1:
    logger.error("Not enough HTTPS bits at Random.Org (%d bits)" % hbl)
    flagProto += 4

shouldExit = {5:True, 6:True, 7:True}.get(flagProto, False)
if shouldExit:
    logger.error("Exiting: no API nor HTTP bits at start")
    sys.exit(1)

# flagExit  Action
#   0       API
#   1       HTTP
#   2       HTTP
#   3       HTTP
#   4       API

while True:
    time.sleep(1)
    try:
        fe = open('/proc/sys/kernel/random/entropy_avail', "r")
        ean = fe.readline()
        fe.close()
        iea = int(ean.rstrip())
    except:
        logger.error('Unexpected error while reading entropy_avail')
        time.sleep(SleepError)
        continue

    if iea > MinimumEntropy:
        if printonce == 0:
            printonce = 1
            logger.info("System's entropy is just fine (%d bits of 4096 max)" % iea)
        time.sleep(SleepInfo)
        continue
    else:
        printonce = 0
        logger.warning("System's entropy low (%d bits of 4096 max)" % iea)

    flagProto = 0

    abl = r.get_bits_left()
    arl = r.get_requests_left()

    hblt = requests.get('https://www.random.org/quota/?format=plain')
    hbl = int(hblt.text.rstrip())

    #if abl < 3400000:
    if abl < FeedBits+1:
        logger.error("Not enough API bits at Random.Org (%d bits)" % abl)
        flagProto = 1
        time.sleep(SleepError)

    if arl < MinimumRequests:
        logger.error("API requests depleted for Random.Org (%d requests)" % arl)
        flagProto += 2
        time.sleep(SleepError)

    #if hbl < 360000:
    if hbl < FeedBits+1:
        logger.error("Not enough HTTPS bits at Random.Org (%d bits)" % hbl)
        flagProto += 4
        time.sleep(SleepError)

    #switch(flagProto):
    shouldLoop = {5:True, 6:True, 7:True}.get(flagProto, False)
    if shouldLoop:
        logger.error('Sleeping for a while (%d seconds)' % SleepLong)
        time.sleep(SleepLong)
        continue

    if flagProto & 1 == 0:
        logger.info("API Bits left: %d (or %d bytes)" % (abl, abl/8))
    if flagProto & 2 == 0:
        logger.info("API Requests left: %d " % arl)
    if flagProto & 4 == 0:
        logger.info("HTTP Bits left: %d (or %d bytes)" % (hbl, hbl/8))
    time.sleep(SleepInfo)

    #if flagProto == 9: #debug
    if flagProto == 0 or flagProto == 4: # API available
        logger.warning("Feeding entropy to the system from API")
        if 'rcache' not in locals():
            rcache = r.create_blob_cache(1, FeedBits, cache_size=CachedPackages)
            time.sleep(3)
        i=0
        while i<5:
            try:
                s = rcache.get()[0]
                i += 1
                break # skip else logger.error...
            except Queue.Empty:
                time.sleep(SleepError)
            except:
                logger.error("Unexpected error while getting data from cache")
                time.sleep(SleepError)
        else:
            logger.error("Cache queue empty. Too many attempts to fill it")
            time.sleep(SleepError)
            continue
            #sys.exit(1)
        bindata = base64.b64decode(s)
    else: # HTTP available
        logger.warning("Feeding entropy to the system from HTTP")
        by = FeedBits/8
        #https://www.random.org/integers/?num=10000&min=0&max=255&col=1&base=16&format=plain&rnd=new
        strhttp = 'https://www.random.org/integers/?num=%d&min=0&max=255&col=1&base=16&format=plain&rnd=new' % by
        sh = requests.get(strhttp)
        sl = sh.text.replace('\n', '')
        bindata = binascii.unhexlify(sl)

    try:
        fbin = open("/tmp/output.bin", "wb")
        fbin.write(bindata)
        fbin.close
    except:
        logger.error("Cannot write to /tmp/output.bin file")
        sys.exit(1)
        #time.sleep(SleepError)
        #continue

    rngdcommand = "sudo rngd -f -t1 -r /tmp/output.bin"
    try:
        subprocess.check_call(rngdcommand.split(), stdout=DEVNULL, stderr=DEVNULL)
    except:
        logger.error("Subprocess rngd error")
        sys.exit(1)
#Loop while True back

############ draft
#sl = sh.text.rstrip().split('\n') # list of hexas
#bindata = binascii.unhexlify(''.join(sl))
#process = subprocess.Popen(rngdcommand.split(), stdout=subprocess.PIPE)
#output, error = process.communicate()
#  val = array.array('i', [0])
#  fcntl.ioctl (fd.fileno(), RNDGETENTCNT, val.buffer_info()[0])
#import ctypes
#import os
#import ioctl
#import ioctl.linux
#RNDGETENTCNT = ioctl.linux.IOR('R', 0x00, ctypes.c_int)
#rndgetentcnt = ioctl.ioctl_fn_ptr_r(RNDGETENTCNT, ctypes.c_int)
#fd = os.open('/dev/random', os.O_RDONLY)
#entropy_avail = rndgetentcnt(fd)
#print('entropy_avail:', entropy_avail)
#fd.os.close()

