from __future__ import print_function
import re
import spacy
from pyclausie import ClausIE

nlp = spacy.load('en')
re_spaces = re.compile(r'\s+')

class Person(object):
    def __init__(self, name, likes=None, has=None, travels=None):
        self.name = name
        self.likes = [] if likes is None else likes
        self.has = [] if has is None else has
        self.travels = [] if travels is None else travels

    def __repr__(self):
        return self.name

class Pet(object):
    def __init__(self, pet_type, name=None):
        self.name = name
        self.type = pet_type

class Trip(object):
    def __init__(self, departs_on, departs_to):
        self.departs_on = departs_on
        self.departs_to = departs_to

persons = []
pets = []
trips = []

def get_data_from_file(file_path='./assignment_01.data'):
    with open(file_path) as infile:
        cleaned_lines = [line.strip() for line in infile if not line.startswith(('$$$', '###', '==='))]

    return cleaned_lines


def select_person(name):
    for person in persons:
        if person.name == name:
            return person

def add_person(name):
    person = select_person(name)

    if person is None:
        new_person = Person(name)
        persons.append(new_person)

        return new_person

    return person

def select_pet(name):
    for pet in pets:
        if pet.name == name:
            return pet

def add_pet(type, name=None):
    pet = None

    if name:
        pet = select_pet(name)

    if pet is None:
        pet = Pet(type, name)
        pets.append(pet)

    return pet

# select trip
def select_trip(departs_to):
    for trip in trips:
        if trip.departs_to == departs_to:
            return trip

# add trip
def add_trip(departs_on, departs_to):
    trip = select_trip(departs_to) # with respect to departs_to

    if trip is None:
        new_trip = Trip(departs_on, departs_to)
        trips.append(new_trip)
        return new_trip
    elif trip and len(trip.departs_on) == 0:
        trip.departs_on == departs_on
        return trip



    return trip

def get_persons_pet(person_name):

    person = select_person(person_name)

    for thing in person.has:
        if isinstance(thing, Pet):
            return thing

# get somebody some trip
def get_persons_trip(person_name):

    person = select_person(person_name)

    for thing in person.travels:
        if isinstance(thing, Trip):
            return thing

def process_data_from_input_file(triplet):
    """
    Process a relation triplet found by ClausIE and store the data

    find relations of types:
    (PERSON, likes, PERSON)
    (PERSON, has, PET)
    (PET, has_name, NAME)
    (PERSON, travels, TRIP)
    (TRIP, departs_on, DATE)
    (TRIP, departs_to, PLACE)

    :param triplet: The relation triplet from ClausIE
    :type triplet: tuple
    :return: a triplet in the formats specified above
    :rtype: tuple
    """

    sentence = triplet.subject + ' ' + triplet.predicate + ' ' + triplet.object
    doc = nlp(unicode(sentence))
    root = doc[0]
    for t in doc:
        if t.pos_ == 'VERB' and t.head == t:
            root = t
        # elif t.pos_ == 'NOUN'

    # also, if only one sentence
    # root = doc[:].root


    """
    CURRENT ASSUMPTIONS:
    - People's names are unique (i.e. there only exists one person with a certain name).
    - Pet's names are unique
    - The only pets are dogs and cats
    - Only one person can own a specific pet
    - A person can own only one pet
    """


    # Process (PERSON, likes, PERSON) relations
    if root.lemma_ == 'like':
        if triplet.subject in [e.text for e in doc.ents if e.label_ == 'PERSON' or e.label_ == 'ORG'] and triplet.object in [e.text for e in doc.ents if e.label_ == 'PERSON' or e.label_ == 'ORG'] and "n't" not in triplet.predicate:
            s = add_person(triplet.subject)
            o = add_person(triplet.object)
            s.likes.append(o)

    if root.lemma_ == 'be' and triplet.object.startswith('friends with'):
        fw_doc = nlp(unicode(triplet.object))
        with_token = [t for t in fw_doc if t.text == 'with'][0]
        fw_who = [t for t in with_token.children if t.dep_ == 'pobj'][0].text
        # fw_who = [e for e in fw_doc.ents if e.label_ == 'PERSON'][0].text

        if triplet.subject in [e.text for e in doc.ents if e.label_ == 'PERSON'] and fw_who in [e.text for e in doc.ents if e.label_ == 'PERSON']:
            s = add_person(triplet.subject)
            o = add_person(fw_who)
            s.likes.append(o)
            o.likes.append(s)
    if root.lemma_ == 'be' and triplet.object == 'friends':
        fw_doc = nlp(unicode(triplet.subject))
        and_token = [t for t in fw_doc if t.text == 'and']
        if and_token:
            and_token = and_token[0].text
        if and_token == 'and' and fw_doc[0].text in [e.text for e in doc.ents if e.label_ == 'PERSON'] and fw_doc[2].text in [e.text for e in doc.ents if e.label_ == 'PERSON']:
            s = add_person(fw_doc[0].text)
            o = add_person(fw_doc[2].text)
            s.likes.append(o)
            o.likes.append(s)

    # Process (PET, has, NAME) Mary's dog's name is Rover
    if triplet.subject.endswith('name') and ('dog' in triplet.subject or 'cat' in triplet.subject):
        obj_span = doc.char_span(sentence.find(triplet.object), len(sentence))

        # handle single names, but what about compound names? Noun chunks might help.
        if (len(obj_span) == 1 or len(obj_span) == 2) and obj_span[-1].pos_ == 'PROPN':
            name = triplet.object
            subj_start = sentence.find(triplet.subject)
            subj_doc = doc.char_span(subj_start, subj_start + len(triplet.subject))

            s_people = [token.text for token in subj_doc if token.ent_type_ == 'PERSON']
            assert len(s_people) == 1
            s_person = select_person(s_people[0])

            pet = get_persons_pet(s_person.name)

            pet.name = name
            s_person.has.append(pet)

    # Process (Who has dog)
    if root.lemma_ == 'have'and ('dog' in triplet.object or 'cat' in triplet.object):
        # find pets name and instantiate name empty str
        obj_span = doc.char_span(sentence.find(triplet.object), len(sentence))
        name = ''

        if obj_span[-1].pos_ == 'PROPN':
            name = obj_span[-1].text
        s = add_person(triplet.subject)
        s_pet_type = 'dog' if 'dog' in triplet.object else 'cat'
        pet = add_pet(s_pet_type, name)
        s.has.append(pet)

    date = [e.text for e in doc.ents if e.label_ == 'DATE']
    gpe = [e.text for e in doc.ents if e.label_ == 'GPE']
    person = [e.text for e in doc.ents if e.label_ == 'PERSON' or e.label_ == 'ORG']
    # if person and GPE exists, we add it into trip(departs_on, departs_to)
    if person and (gpe or date):
        s = add_person(triplet.subject)
        o = add_trip(date, gpe)
        s.travels.append(o)


def preprocess_question(question):
    # remove articles: a, an, the

    q_words = question.split(' ')

    # when won't this work?
    for article in ('a', 'an', 'the'):
        try:
            q_words.remove(article)
        except:
            pass

    return re.sub(re_spaces, ' ', ' '.join(q_words))


def has_question_word(string):
    # note: there are other question words
    for qword in ('who', 'what'):
        if qword in string.lower():
            return True

    return False

def make_sentence_from_triplet(triplet):
    return triplet.subject + ' ' + triplet.predicate + ' ' + triplet.object
def answer_question(question):
    cl = ClausIE.get_instance()
    # q_trip = cl.extract_triples([preprocess_question(question)])[0]
    # triplet_sentence = make_sentence_from_triplet(q_trip) + '?'
    # doc = nlp(unicode(triplet_sentence))
    doc = nlp(unicode(question))
    root = doc[:].root
    if root.text == "'s" and doc[-2].dep_ == 'pobj' and [t.text for t in doc.ents if t.label_ == 'PERSON']:
        answer = '{} has a {} named {}'
        ss = [t.text for t in doc.ents if t.label_ == 'PERSON'][0]
        pet = get_persons_pet(ss)
        if pet.type == doc[-2].text:
                print(answer.format(ss, doc[-2], pet.name))
        else:
            print('I dont know!')
    else:
        q_trip = cl.extract_triples([preprocess_question(question)])[0]
        triplet_sentence = make_sentence_from_triplet(q_trip) + '?'
        doc = nlp(unicode(triplet_sentence))
        doc = nlp(unicode(question))
        root = doc[:].root
        adv = doc[0]
        for t in doc:
            if t.pos_ == 'ADV':
                adv = t

        # (WHO, has, PET)
        # here's one just for dogs
        if q_trip.subject.lower() == 'who' and q_trip.object == 'dog':
            answer = '{} has a {} named {}.'
            # answer_set = set()
            for person in persons:
                pet = get_persons_pet(person.name)
                if pet and pet.type == 'dog':
                    print(answer.format(person.name, 'dog', pet.name))
        # here's one just for cats
        elif q_trip.subject.lower() == 'who' and q_trip.object == 'cat':
            answer = '{} has a {} named {}.'
            # answer_set = set()
            for person in persons:
                pet = get_persons_pet(person.name)
                if pet and pet.type == 'cat':
                    print(answer.format(person.name, 'cat', pet.name))

        # predicate includes like
        elif 'like' in q_trip.predicate:
            # Who likes Mary?
            if q_trip.subject.lower() == 'who':
                answer_set = set()
                answer = '{} likes {}.'

                liked_person = select_person(q_trip.object)

                for person in persons:
                    if person.name != q_trip.object and liked_person in person.likes:
                        new_answer = answer.format(person.name, liked_person.name)
                        answer_set.add(new_answer)
                print(answer_set if len(answer_set) != 0 else 'I dont know!')
            # Who does Joe like?
            elif q_trip.object.lower() == 'who':
                answer = '{} likes {}.'

                like_person = select_person(q_trip.subject)  # q.trip.subject == 'Joe'

                for person in persons:
                    if person.name == q_trip.subject:
                        for p in person.likes:
                            print(answer.format(like_person, p.name))
            # Does Bob like Sally?
            elif doc[1].ent_type_ == 'PERSON' and doc[3].ent_type_ == 'PERSON':
                subject = doc[1].text
                oobject = doc[3].text
                answer_set = set()
                answer = '{} {} likes {}.'
                for person in persons:
                    # print('Persons Name: '+person.name)
                    # print('Question subject ' + subject)
                    if person.name == subject:
                        for p in person.likes:
                            # print('Liked name: '+p.name)
                            # print('Liked name in question '+oobject)
                            if oobject == p.name:
                                new_answer = answer.format('Yes', subject, oobject)
                                answer_set.add(new_answer)
                print(answer_set if len(answer_set) != 0 else 'I dont know!')
                # new_answer  = answer.format('Yes,', subject, oobject)
                # answer_set.add(new_answer)
                # print(answer_set)
        # (WHO, going to| flying to| travelling to| visiting, PLACE)
        elif q_trip.subject.lower() == 'who':
            ent = [str(ent.text) for ent in doc.ents if ent.label_ == 'GPE']
            answer_set = set()
            answer = '{} {} to {}.'
            if ent:
                for person in persons:
                    person = select_person(person.name)
                    for trip in person.travels:
                        if ent == trip.departs_to:
                            new_answer = answer.format(person.name, root, ent[0])
                            answer_set.add(new_answer)
                print(answer_set)
            else:
                print('I dont know!')
        # When is someone going to smplace
        elif str(adv.lemma_) == 'when':
            ent = [str(ent.text) for ent in doc.ents if ent.label_ == 'GPE']
            answer_set = set()
            answer = '{} {} to {} on {}.'
            if ent:
                for person in persons:
                    person = select_person(person.name)
                    if q_trip.subject in person.name:
                        for trip in person.travels:
                            if ent == trip.departs_to:
                                new_answer = answer.format(person.name, root, ent[0], trip.departs_on[0])
                                # answer_set.append(new_answer) if new_answer not in answer_set
                                answer_set.add(new_answer)
                print(answer_set if len(answer_set) != 0 else 'I dont know!')

        else:
            print('I dont know!')

def main():
    sents = get_data_from_file()

    cl = ClausIE.get_instance()
    triples = cl.extract_triples(sents)
    for t in triples:
        r = process_data_from_input_file(t)
    # samp = process_relation_triplet(triples[12])
    # samp1 = process_relation_triplet(triples[15])
    # doc = process_relation_triplet(u'Sally is going to Mexico some time in 2020.')
    question = ' '
    while question[-1] != '?':
        question = raw_input("Please enter your question: ")

        if question[-1] != '?':
            print('This is not a question... please try again')
    answer_question(question)

if __name__ == '__main__':
    main()