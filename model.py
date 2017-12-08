import datetime
import json
from pdb import set_trace
from tokenizer import tokenizer
import re
filename = "ami-catalog-notes_2017-12-07.ndjson"

verbs = [x.strip() for x in open("common-verbs.txt")]
verb_partials = ["rec"]

class Event(object):

    verb_re = [re.compile(r'\b(%s)\b' % verb, re.I) for verb in verbs]
    verb_partial_re = re.compile(r'\b(%s)\.' % "|".join(verb_partials), re.I)

    _date_templates = [
        ("in [0-9]{4}", "in %Y"),
        ("[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}", "%m/%d/%Y"),
        ("[0-9]{1,2}/[0-9]{1,2}/[0-9]{2}", "%m/%d/%y"),
        ("[0-9]{4}-[0-9]{2}-[0-9]{2}", "%Y-%m-%d"),
        ("[0-9]{1,2}/[0-9]{4}", "%m/%Y"),
        ("[0-9]{1,2}/[0-9]{2}", "%m/%y"),
        ("[A-Za-z]{4,} +[0-9]{1,2}, [0-9]{4}", "%B %d, %Y"),
        ("[A-Za-z]{4,}\. +[0-9]{1,2}, [0-9]{4}", "%B. %d, %Y"),
        ("[A-Za-z]{4,} +[0-9]{4}", "%B %Y"),
        ("[A-Za-z]{3} +[0-9]{4}", "%b %Y"),
        ("[A-Za-z]{3}. +[0-9]{4}", "%b. %Y"),
    ]
    date_templates = []
    date_range_templates = []
    for r, p in _date_templates:
        date_templates.append((re.compile("(%s)" % r), p))
        pattern = "(%s)-(%s)" % (r,r)
        date_range_templates.append((re.compile(pattern), p))

    date_range_templates.append(
        (re.compile("between ([0-9]{4}) and ([0-9]{4})"), "%Y")
    )

    date_range_templates.append(
        (re.compile("from ([0-9]{4}) to ([0-9]{4})"), "%Y")
    )

    # It's hard to determine whether a four-digit number that looks
    # like a year actually represents the year that the event
    # happened, but it's believable that two years next to each other
    # represent a span of time.
    for r, p in [
            ('[0-9]{4}-[0-9]{4}', '%Y'),
    ]:
        date_range_templates.append((re.compile(pattern), p))

    def __init__(self, note, format, original, start, end=None, type=None):
        self.format = format
        self.original = original
        self.start = start
        self.end = end
        self.note = note
        if isinstance(note, Item):
            self.item = note
        else:
            self.item = note.item
        self.type = type

    @classmethod
    def from_clause(cls, note, format, clause, type=None):
        event_date = None
        if any(x in clause for x in ('-', 'between', 'from')):
            # This might be a span of time.
            for regex, template in cls.date_range_templates:
                matches = regex.findall(clause)
                for (start, finish) in matches:
                    try:
                        start_date = datetime.datetime.strptime(start, template).date()
                        finish_date = datetime.datetime.strptime(finish, template)
                        return Event(note, format, clause, start_date, finish_date, type=type)
                    except ValueError, e:
                        pass

        for regex, template in cls.date_templates:
            match = regex.findall(clause)
            if match:
                previous_failure = False
                for match_against in match:
                    try:
                        event_date = datetime.datetime.strptime(match_against, template).date()
                        #if previous_failure:
                        #    print "Never mind, found it."
                    except ValueError, e:
                        pass
                        #print "Could not get format %s: %s" % (template, clause)
                        #previous_failure = True
                if event_date:
                    return Event(note, format, clause, event_date, type=type)

        # If the only thing in the clause is a believable year, treat
        # that as the date.
        if len(clause) == 4:
            try:
                year = int(clause)
                if year <= datetime.datetime.utcnow().year and year > 1960:
                    event_date = datetime.date(year=year, month=1, day=1)
                    return Event(note, format, clause, event_date, type=type)
            except ValueError, e:
                pass
        return None

    @property
    def action(self):
        check = self.original
        for reg in [
                "until +[^a-zA-Z]+ +this was",
                "until +[^a-zA-Z]+ +(was|were)",
                "(was|were) .* (un)?til",
                "in Princeton ReCAP Regular Storage",
                "[io]n .* as of",
                "on library repository",
                "gift of",
                "record updated",
                "straight dub",
                "in repository",
                "print from",
                "down conversion from",
        ]:
            action = self._extract_action(reg)
            if action:
                return action

        lowered = self.original.lower()
        if ". copy, " in lowered:
            i = lowered.index('. copy, ')
            return self.original[i+2:].strip()

        for r in self.verb_re + [self.verb_partial_re]:
            match = r.search(self.original)
            if match:
                return self.original[match.start():]

        for reg in [
                "from pres. master",
        ]:
            action = self._extract_action(reg)
            if action:
                return action

        # We couldn't reduce the original text to an action; return
        # the entire original text as its action.
        return self.original

    def _extract_action(self, reg):
        match = re.compile(reg, re.I).search(self.original)
        if match:
            action = self.original[match.start():]
            if action.startswith('.'):
                action = action[1:]
            return action.strip()

    def _format_date(self, date):
        if not date:
            return None
        real_year = str(date.year)
        if date.year < 1900:
            # This will stop strftime from choking.
            date = datetime.date(year=1900, month=date.month,
                                 day=date.day)
        return real_year + '/' + date.strftime('%m/%d')

    @property
    def as_json(self):
        data = dict(
            event_type=self.action_type,
            uuid=self.item.representation['uuid'],
            event=self.action,
            media = self.format,
            full_event=self.original,
            event_start=self._format_date(self.start),
            event_end=self._format_date(self.end),
        )
        if isinstance(self.note, Note):
            data['full_note'] = self.note.text
        else:
            data['full_note'] = None
        return json.dumps(data)

    event_mapping = {
        "Acquired" : ["donated", "received", "deposited", "purchased", "acquired", "dontated", "recieved"],
        "Captured": ["shot", "recorded", "videotaped"],
        "Ignorable - Irrelevant Event" : ["contained", "loaned", "added", "removed", "transferred", "exported", "struck", "created", "destroyed", "withdrawn", "edited", "stored", "made", "delivered", "replaced", "pulled", "discovered", "assembled", "shown", "combined", "provided", "found", "assigned", "revised", "identified", "damaged", "supplied", "returned", "paid", "given", "lost", "dubbed", "transfered", "taped", "labeled", "processed"]
    }

    media_mapping = {
        "Ignorable - Irrelevant Media Type" : ["service copy", "edit master", "add copy", "former view", "replaces", "vid view copy", "vid view copy", "vid view copies", "view copy", "viewing copies", "viewing copy"],
        "Reformatted" : ["arch orig", "archival original"],
        "Digitized": ["digital preservation master", "digital pres master", "digital pres master", "preservation master", "vid pres master", "vid pres master", "pres master"],
    }

    # If an item is in one of these media, then its events are likely
    # to be 'Digitized' or 'Reformatted' events.
    digital_transfer_media = ['vid pres master 1', 'vid pres master 2']
    
    from collections import Counter
    UNUSED = Counter()

    @property
    def interesting(self):
        return not self.action_type.startswith("Ignorable")

    @property
    def action_type(self):
        if self.type:
            return self.type
        multispace = re.compile("  +")
        action = multispace.sub(" ", self.action.lower())

        # Sometimes, we can deduce the event type from the verb used
        # to describe the action. e.g. "videotaped" means a capture
        # event.
        for k, actions in self.event_mapping.items():
            if any(action.startswith(x) for x in actions):
                return k

        # This is either copied, reformatted, or digitized.

        if not action.startswith('copied'):
            return "Ignorable - Irrelevant Event"

        if not self.format:
            return "Ignorable - Unknown Format"

        media = multispace.sub(" ", self.format.lower()).replace(". ", " ")
        if any(media.startswith(x) for x in self.digital_transfer_media):
            full_text = self.note.text.lower()
            if 'digital' in full_text and full_text.index('digital') < full_text.index('copied'):
                return "Digitized"
            else:
                return "Reformatted"
        
        for k, values in self.media_mapping.items():
            # Sometimes, if we know the media of the item, we can
            # deduce what must have happened to it.
            if any(x in media for x in values):
                return k     

        self.UNUSED[media] += 1
        return 'Unknown'

class Note(object):

    # There is no way a string has a usable date unless it contains two
    # adjacent digits.
    potential_date = re.compile("[0-9][0-9]")

    # There is no way a string is an event unless it contains an alphabetic
    # character explaining what happened.
    alphabetic = re.compile("[A-Za-z]")

    reset = object()

    sentence_scrubbers = [
        ('E.M.;', 'E.M.'),
        ("copied from P.M. 2, 120/2012", "copied from P.M. 2, 12/2012"),
    ]

    def __init__(self, item, representation, force_event_type=None):
        self.item = item
        self.force_event_type = force_event_type
        if isinstance(representation, basestring):
            self.representation = None
            self.text = representation
        else:
            self.representation = representation
            self.text = self.representation.get('note_text')

    # We want to split clauses on a semicolon, but when a
    # parenthetical statement contains a semicolon we want 
    # to keep the parenthetical intact, and not split.
    semicolon_not_in_parentheses = re.compile(";(?![^(]*\))")

    def clauses(self, with_resets=True):
        if with_resets:
            yield self.reset, None
        for format, sentence in self.sentences:
            clauses = self.semicolon_not_in_parentheses.split(sentence)
            for clause in clauses:
                clause = clause.strip()
                yield format, clause
            if with_resets:
                yield self.reset, None

    def scrub_sentence(self, sentence):
        # Fix dataset-specific problems that cause problems
        # with tokenization or date parsing
        for scrub, replace_with in self.sentence_scrubbers:
            sentence = sentence.replace(scrub, replace_with)
        return sentence

    @property
    def sentences(self):
        for sentence in tokenizer.tokenize(self.text):
            sentence = self.scrub_sentence(sentence)
            yield self.extract_format(sentence)

    def extract_format(self, sentence):
        r = re.compile("^([^,:]+):")
        match = r.search(sentence)
        if match:
            format = match.groups()[0]
            # format = re.compile("( +[0-9])$").sub("", format.strip())
            return format.strip(), sentence[match.end():].strip()
        return None, sentence

    @property
    def events(self):
        for format, clause in self.clauses(with_resets=True):
            if format == self.reset:
                previous_clause = None
                previous_clause_could_be_description = False
                previous_clause_could_be_date = False
                previous_clause_was_event = False
                continue
            could_be_date = self.potential_date.search(clause)
            could_be_description = self.alphabetic.search(clause)
            event = None
            if could_be_date:
                if could_be_description:
                    # This has some numbers and some letters.
                    event = Event.from_clause(
                        self, format, clause, self.force_event_type
                    )
                else:
                    # This has numbers but no letters; maybe it
                    # should be combined with the previous clause.
                    if previous_clause_could_be_description and not previous_clause_was_event:
                        clause = "%s ; %s" % (previous_clause, clause)
                        event = Event.from_clause(
                            self, format, clause, self.force_event_type
                        )
            if event:
                yield event
            previous_clause = clause
            previous_clause_could_be_description = could_be_description
            previous_clause_could_be_date = could_be_date
            previous_clause_was_event = (event is not None)


class Item(object):

    def __init__(self, representation):
        self.representation = representation

        cataloged_string = representation.get('date_cataloged')
        self.date_cataloged = None
        if cataloged_string:
            note = Note(self, cataloged_string)
            self.date_cataloged = Event.from_clause(
                note, None, cataloged_string, type='Cataloged'
            )

        created_string = representation.get('date_created')
        self.date_created = None
        if created_string:
            note = Note(self, created_string)
            self.date_created = Event.from_clause(
                note, None, created_string, type='Created'
            )

        self.notes = []

        title = representation.get('title')
        note = Note(self, title, force_event_type='Created')        
        self.notes.append(note)

        event_note = representation.get('event_note')
        if event_note:
            self.notes.append(
                Note(self, event_note, force_event_type='Captured')
            )

        for note in representation.get('notes', []):
            note = Note(self, note)
            self.notes.append(note)

    @property
    def events(self):
        if self.date_cataloged:
            yield self.date_cataloged
        if self.date_created:
            yield self.date_created
        for note in self.notes:
            for event in note.events:
                yield event
