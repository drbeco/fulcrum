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
CachedPackages = 10 # Number of cached packages to keep in memory before connecting to Random.Org
MinimumEntropy = 650 # Minimum system's entropy before starting feeding bits (default 650)
MinimumRequests = 10 # Minimum requests available from Random.Org
SleepLong = 3600 # sleep one hour
SleepError = 5 # Time to sleep in case of error
SleepInfo = 2 # Time to sleep in case of info or warning
DEVNULL = open(os.devnull, 'wb') # /dev/null
APIDIR = './'
#APIDIR = '/usr/local/bin/fulcrum/'
LOGDIR = '/tmp/'
#LOGDIR = '/var/log/'
LOGFORMAT = '%(asctime)s:%(levelname)s:%(name)s:%(message)s'
BINDIR = '/tmp/'
#BINDIR = '/var/cache/fulcrum'

logging.basicConfig(format=LOGFORMAT, filename=LOGDIR + 'fulcrum.log', level=logging.INFO, datefmt='%Y%m%d.%H%M%S')
logger = logging.getLogger('fulcrum')
for handler in logging.root.handlers:
    handler.addFilter(logging.Filter('fulcrum'))
 
printonce = 0 # 'Entropy is OK' message only once
flagKey = True
flagProto = 0

try:
    fd = open("%s.api-randomorg.txt" % APIDIR, "r")
    keyn = fd.readline()
    fd.close()
    key = keyn.rstrip()
except Exception as ex:
    logger.error('Unexpected error while reading api key: %s' % ex.message)
    flagKey = False # Do not attempt to use API, just HTTP

try:
    r = RandomOrgClient(key, blocking_timeout=3600.0, http_timeout=30.0)
except:
    flagKey = False # Do not attempt to use API, just HTTP

#check if wrong key
try:
    abl = r.get_bits_left()
    arl = r.get_requests_left()
except Exception as ex:
    logger.error('Unexpected error while using api key: %s' % ex.message)
    flagKey = False # Do not attempt to use API, just HTTP
    abl = 0
    arl = 0
    #sys.exit(1)

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

# flagExit  Action
#   0        API (available both API and HTTP)
#   1        HTTP
#   2        HTTP
#   3        HTTP
#   4        API
#   5, 6, 7  Nothing available

shouldExit = {5:True, 6:True, 7:True}.get(flagProto, False)
if shouldExit:
    logger.error("No API nor HTTP bits at start. Long sleeping (%d seconds)" % SleepLong)
    time.sleep(SleepLong)
    #sys.exit(1)

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

    if flagKey:
        abl = r.get_bits_left()
        arl = r.get_requests_left()
    else:
        abl = 0
        arl = 0
        logger.error("No API keys")

    hblt = requests.get('https://www.random.org/quota/?format=plain')
    hbl = int(hblt.text.rstrip())

    #if abl < 3400000: # debug
    if abl < FeedBits+1:
        flagProto = 1
        if flagKey:
            logger.error("Not enough API bits at Random.Org (%d bits)" % abl)
        #time.sleep(SleepError)

    if arl < MinimumRequests:
        flagProto += 2
        if flagKey:
            logger.error("API requests depleted for Random.Org (%d requests)" % arl)
        #time.sleep(SleepError)

    #if hbl < 360000: # debug
    if hbl < FeedBits+1:
        flagProto += 4
        logger.error("Not enough HTTPS bits at Random.Org (%d bits)" % hbl)
        #time.sleep(SleepError)

    #switch(flagProto):
    shouldLoop = {5:True, 6:True, 7:True}.get(flagProto, False)
    if shouldLoop:
        logger.error("Not enough bits to help. Good luck! I'm going to sleep for a while (%d seconds)" % SleepLong)
        time.sleep(SleepLong)
        continue

    if flagProto & 1 == 0 and flagKey:
        logger.info("API Bits left: %d (or %d bytes)" % (abl, abl/8))
    if flagProto & 2 == 0 and flagKey:
        logger.info("API Requests left: %d " % arl)
    if flagProto & 4 == 0:
        logger.info("HTTP Bits left: %d (or %d bytes)" % (hbl, hbl/8))
    logger.info("Total Bits left: %d (or %d bytes)" % (abl+hbl, (abl+hbl)/8))
    #time.sleep(SleepInfo)

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
        fbin = open("%sfulcrum_output.bin" % BINDIR, "wb")
        fbin.write(bindata)
        fbin.close
    except:
        logger.error("Cannot write to %sfulcrum_output.bin file" % BINDIR)
        sys.exit(1)
        #logger.error('Sleeping for a while (%d seconds)' % SleepLong)
        #time.sleep(SleepLong)
        #continue

    #rngdcommand = "sudo rngd -f -t1 -r /tmp/fulcrum_output.bin" # debug
    rngdcommand = "rngd -f -t1 -r /tmp/fulcrum_output.bin"
    try:
        subprocess.check_call(rngdcommand.split(), stdout=DEVNULL, stderr=DEVNULL)
    except:
        logger.error("Subprocess rngd error")
        sys.exit(1)
#Loop while True back

#* ------------------------------------------------------------------- *
#* Python config for Vim modeline                                      *
#* vi: set ai et ts=4 sw=4 sts=4 tw=72 wm=0 fo=croql :                *
#* Template by Dr. Beco <rcb at beco dot cc> Version 20170322.131248   *

