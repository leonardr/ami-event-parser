from collections import Counter
from datetime import datetime
import json
from pdb import set_trace

from model import *
from textblob import TextBlob

all_text = []
c = Counter()

ignored = open("1-ignored.ndjson", "w")
uninteresting = open("1-uninteresting.ndjson", "w")
interesting = open("1-events.ndjson", "w")
#not_cataloged = open("1-not-catalogued.ndjson", "w")
#not_created = open("1-not-created.ndjson", "w")

for i in open(filename):
    line = json.loads(i)
    item = Item(line)
    events = list(item.events)

    #if not any(x for x in events if x.action_type == 'Cataloged'):
    #    not_cataloged.write(i)
    #if not any(x for x in events if x.action_type == 'Created'):
    #    not_created.write(i)

    # An item is ignored if it does not have any events other than
    # 'Cataloged' and 'Created' events.
    if not any(x for x in events if x.action_type not in ('Cataloged', 'Created')):
        ignored.write(i)
    else:
        for event in events:
            if event.interesting:
                output = interesting
            else:
                output = uninteresting
            output.write(event.as_json + "\n")
