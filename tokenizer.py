import nltk.data
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
punkt_param = PunktParameters()
abbreviations = [
    'a.c',    # Archival Copy?
    'a.o',    # Archival Original
    'ach',    # Misspelling of 'arch'
    'add',    # Additional
    'arch',   # Archival
    'acrh',   # Misspelling of 'arch'
    'ca',     # Circa
    'ch',     # Channel
    'col',    # Color?
    'comp',   # Composite?
    'd.m.f',  # ???
    'e.m',    # Edit Master
    'f.v.c',  # ???
    'in',     # Inches
    'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',       # Months of the year
    'min',    # Minutes
    'mm',     # Millimeter
    'ms',     # Term of address -- should be in vanilla punkt.
    'neg',    # Negative
    'orig',   # Original
    'pic',    # Picture?
    'p.m',    # Preservation Master?
    'pres',   # Preservation
    'prt',    # Print?
    'rec',    # Received
    'v.c',    # ???
    'v.p.m',  # Video Preservation Master
    'vid',    # Video
    'view',   # Viewing    
]
punkt_param.abbrev_types = set(abbreviations)
tokenizer = PunktSentenceTokenizer(punkt_param)
