from collections import Counter
from datetime import datetime
import json
from pdb import set_trace

from model import *
from textblob import TextBlob

all_text = []
c = Counter()

for i in open(filename):
    line = json.loads(i)
    item = Item(line)
    for event in item.events:
        if event.interesting:
            print event.as_json
    
#for k, v in Event.UNUSED.most_common():
#    print k, v
