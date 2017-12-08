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

for i in open(filename):
    line = json.loads(i)
    item = Item(line)
    events = list(item.events)
    if len(events) <= 2:
        # The creation and digitization events are more or less
        # universal, and not obtained by looking at the note. If these
        # are the only events the Item has, it means the Item's notes
        # were ignored.
        ignored.write(i)
    else:
        for event in item.events:
            if event.interesting:
                output = interesting
            else:
                output = uninteresting
            output.write(event.as_json + "\n")
