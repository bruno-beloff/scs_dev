#!/usr/bin/env python3

"""
Created on 12 Sep 2020

@author: Bruno Beloff (bruno.beloff@southcoastscience.com)

example:
csv_reader.py -l 10 pm2p5-h1-validation.csv | ./pmx_inference_test.py


example CSV:
label,
praxis.meteo.val.hmd, praxis.meteo.val.tmp, praxis.pmx.val.per, praxis.pmx.val.bin:0, praxis.pmx.val.bin:1,
praxis.pmx.val.bin:2, praxis.pmx.val.bin:3, praxis.pmx.val.bin:4, praxis.pmx.val.bin:5, praxis.pmx.val.bin:6,
praxis.pmx.val.bin:7, praxis.pmx.val.bin:8, praxis.pmx.val.bin:9, praxis.pmx.val.bin:10, praxis.pmx.val.bin:11,
praxis.pmx.val.bin:12, praxis.pmx.val.bin:13, praxis.pmx.val.bin:14, praxis.pmx.val.bin:15, praxis.pmx.val.bin:16,
praxis.pmx.val.bin:17, praxis.pmx.val.bin:18, praxis.pmx.val.bin:19, praxis.pmx.val.bin:20, praxis.pmx.val.bin:21,
praxis.pmx.val.bin:22, praxis.pmx.val.bin:23,
praxis.pmx.val.mtf1, praxis.pmx.val.mtf3, praxis.pmx.val.mtf5, praxis.pmx.val.mtf7,
praxis.pmx.val.sfr, praxis.pmx.val.sht.hmd, praxis.pmx.val.sht.tmp
"""

import json
import os
import sys
import time

from scs_core.comms.uds_client import UDSClient

from scs_core.data.datum import Datum
from scs_core.data.json import JSONify
from scs_core.data.path_dict import PathDict

from scs_core.model.pmx.s1.pmx_request import PMxRequest

from scs_core.sample.sample import Sample

from scs_core.sys.logging import Logging

from scs_host.comms.domain_socket import DomainSocket
from scs_host.sys.host import Host


# --------------------------------------------------------------------------------------------------------------------
# references...

uds_path = 'pipes/lambda-model-pmx-s1.uds'

document_count = 0
processed_count = 0
start_time = None


# --------------------------------------------------------------------------------------------------------------------
# resources...

# logger...
Logging.config(__name__, verbose=True)

# inference client...
client = UDSClient(DomainSocket, os.path.join(Host.scs_path(), uds_path))
print("pmx_inference_test: %s" % client, file=sys.stderr)


# --------------------------------------------------------------------------------------------------------------------
# run...

try:
    client.open()

    start_time = time.time()

    for line in sys.stdin:
        # request...
        datum = PathDict.construct_from_jstr(line)

        document_count += 1

        if datum is None:
            break

        datum.append('praxis.pmx.src', 'N3')

        sample = Sample.construct_from_jdict(datum.node('praxis.pmx'))
        climate = Sample.construct_from_jdict(datum.node('praxis.meteo'))
        label = Datum.float(datum.node('label'), 1)

        combined = PMxRequest(sample, climate)

        # inference...
        client.request(JSONify.dumps(combined.as_json()))
        response = client.wait_for_response()

        jdict = json.loads(response)

        # response...
        if jdict is None:
            print("pmx_inference_test: inference rejected: %s" % JSONify.dumps(combined.as_json()), file=sys.stderr)
            sys.stderr.flush()
            break

        opc_sample = Sample.construct_from_jdict(jdict)

        jdict = opc_sample.as_json()
        jdict['label'] = label

        print(JSONify.dumps(jdict))
        sys.stdout.flush()

        processed_count += 1


# ---------------------------------------------------------------------------------------------------------------------
# end...

except KeyboardInterrupt:
    print(file=sys.stderr)

finally:
    client.close()

    print("pmx_inference_test: documents: %d processed: %d" % (document_count, processed_count),
          file=sys.stderr)

    if start_time and processed_count > 0:
        elapsed_time = round(time.time() - start_time, 1)
        avg_per_inference = round(elapsed_time / processed_count, 3)

        print("pmx_inference_test: elapsed time: %s avg_per_inference: %s" % (elapsed_time, avg_per_inference),
              file=sys.stderr)
