import discord
import random
import time
import asyncio
import spacy

def lanuage_init():

	global nlp
	global adjectives
	global adjectives_affliction
	global adverbs 
	global addons_singular
	global addons_plural
	global nouns_singular
	global nouns_plural
	global nouns_bodyparts
	global nouns_places_proper
	global nouns_places_vague
	global nouns_names_full
	global nouns_names_first_male
	global nouns_names_first_female
	global nouns_names_last
	global verbs_past
	global verbs_past_participle
	global verbs_present
	global verbs_future
	global verbs_gerund

	nlp = spacy.load("en_core_web_lg")

	adjectives = open("text/components/adjectives.txt", "r").readlines()
	adjectives_affliction = open("text/components/adjectives_affliction.txt", "r").readlines()
	adverbs = open("text/components/adverbs.txt", "r").readlines()
	addons_singular = open("text/components/addons_singular.txt", "r").readlines()
	addons_plural = open("text/components/addons_plural.txt", "r").readlines()
	nouns_singular = open("text/components/nouns_singular.txt", "r").readlines()
	nouns_plural = open("text/components/nouns_plural.txt", "r").readlines()
	nouns_bodyparts = open("text/components/nouns_bodyparts.txt", "r").readlines()
	nouns_places_proper = open("text/components/nouns_places_proper.txt", "r").readlines()
	nouns_places_vague = open("text/components/nouns_places_vague.txt", "r").readlines()
	nouns_names_full = open("text/components/nouns_names_full.txt", "r").readlines()
	nouns_names_first_male = open("text/components/nouns_names_first_male.txt", "r").readlines()
	nouns_names_first_female = open("text/components/nouns_names_first_female.txt", "r").readlines()
	nouns_names_last = open("text/components/nouns_names_last.txt", "r").readlines()
	verbs_past = open("text/components/verbs_past.txt", "r").readlines()
	verbs_past_participle = open("text/components/verbs_past_participle.txt", "r").readlines()
	verbs_present = open("text/components/verbs_present.txt", "r").readlines()
	verbs_future = open("text/components/verbs_future.txt", "r").readlines()
	verbs_gerund = open("text/components/verbs_gerund.txt", "r").readlines()

def replace_text_by_pos_tag(text, replacement, *tags):

	doc = nlp(text)
	new_text = ""

	for token in doc:
		new_word = token.text

		if token.tag_ in tags:
			if token.is_title:
				new_word = replacement.capitalize()
			else:
				new_word = replacement.lower()
		new_text += new_word
		new_text += token.whitespace_

	return new_text

def replace_text_tags(text):

	capitalization_flag = False
	if text.find("<") == 0:
		capitalization_flag = True

	new_text = text

	while "<a>" in new_text:
		word = adjectives[random.randrange(len(adjectives))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<a>", word, 1)

	while "<aa>" in new_text:
		word = adjectives_affliction[random.randrange(len(adjectives_affliction))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<aa>", word, 1)

	while "<ad>" in new_text:
		word = adverbs[random.randrange(len(adverbs))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<ad>", word, 1)

	while "<adds>" in new_text:
		word = addons_singular[random.randrange(len(addons_singular))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<adds>", word, 1)

	while "<addp>" in new_text:
		word = addons_plural[random.randrange(len(addons_plural))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<addp>", word, 1)

	while "<addf>" in new_text:
		if random.randrange(0, 2) == 1:
			word = addons_singular[random.randrange(len(addons_singular))].strip()
			if capitalization_flag:
				word = word.capitalize()
				capitalization_flag = False
			new_text = new_text.replace("<addf>", word, 1)
		else:
			word = addons_plural[random.randrange(len(addons_plural))].strip()
			if capitalization_flag:
				word = word.capitalize()
				capitalization_flag = False
			new_text = new_text.replace("<addf>", word, 1)

	while "<ns>" in new_text:
		word = nouns_singular[random.randrange(len(nouns_singular))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<ns>", word, 1)

	while "<np>" in new_text:
		word = nouns_plural[random.randrange(len(nouns_plural))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<np>", word, 1)

	while "<nf>" in new_text:
		if random.randrange(0, 2) == 1:
			word = nouns_singular[random.randrange(len(nouns_singular))].strip()
			if capitalization_flag:
				word = word.capitalize()
				capitalization_flag = False
			new_text = new_text.replace("<nf>", word, 1)
		else:
			word = nouns_plural[random.randrange(len(nouns_plural))].strip()
			if capitalization_flag:
				word = word.capitalize()
				capitalization_flag = False
			new_text = new_text.replace("<nf>", word, 1)

	while "<nbp>" in new_text:
		word = nouns_bodyparts[random.randrange(len(nouns_bodyparts))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<nbp>", word, 1)

	while "<nplp>" in new_text:
		word = nouns_places_proper[random.randrange(len(nouns_places_proper))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<nplp>", word, 1)		

	while "<nplv>" in new_text:
		word = nouns_places_vague[random.randrange(len(nouns_places_vague))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<nplv>", word, 1)

	while "<nnf>" in new_text:
		word = nouns_names_full[random.randrange(len(nouns_names_full))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<nnf>", word, 1)

	while "<nnfm>" in new_text:
		word = nouns_names_first_male[random.randrange(len(nouns_names_first_male))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<nnfm>", word, 1)

	while "<nnff>" in new_text:
		word = nouns_names_first_female[random.randrange(len(nouns_names_first_female))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<nnff>", word, 1)

	while "<nnffl>" in new_text:
		if random.randrange(0, 2) == 1:
			word = nouns_names_first_male[random.randrange(len(nouns_names_first_male))].strip()
			if capitalization_flag:
				word = word.capitalize()
				capitalization_flag = False
			new_text = new_text.replace("<nnffl>", word, 1)
		else:
			word = nouns_names_first_female[random.randrange(len(nouns_names_first_female))].strip()
			if capitalization_flag:
				word = word.capitalize()
				capitalization_flag = False
			new_text = new_text.replace("<nnffl>", word, 1)

	while "<nnl>" in new_text:
		word = nouns_names_last[random.randrange(len(nouns_names_last))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<nnl>", word, 1)

	while "<vpa>" in new_text:
		word = verbs_past[random.randrange(len(verbs_past))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<vpa>", word, 1)

	while "<vpr>" in new_text:
		word = verbs_present[random.randrange(len(verbs_present))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<vpr>", word, 1)

	while "<vf>" in new_text:
		word = verbs_future[random.randrange(len(verbs_future))].strip()
		if capitalization_flag:
			word = word.capitalize()
			capitalization_flag = False
		new_text = new_text.replace("<vf>", word, 1)

	while "<random>" in new_text:
		new_text = new_text.replace("<random>", str(random.randrange(1, 1000)), 1)

	return new_text

def advanced_auto_text_replace(text):

	doc = nlp(text)

	new_text = ""

	for token in doc:
		new_word = token.text

		if token.tag_ == "NN" and not token.is_stop:
			new_word = nouns_singular[random.randrange(len(nouns_singular))].strip()

		if token.tag_ == "NNS" and not token.is_stop:
			new_word = nouns_plural[random.randrange(len(nouns_plural))].strip()

		if token.tag_ == "JJ" and  not token.is_stop:
			new_word = adjectives[random.randrange(len(adjectives))].strip()

		if token.tag_ == "VB" and not token.is_stop:
			new_word = verbs_present[random.randrange(len(verbs_present))].strip()

		if token.tag_ == "VBD" and not token.is_stop:
			new_word = verbs_past[random.randrange(len(verbs_past))].strip()

		if token.tag_ == "VBG" and not token.is_stop:
			new_word = verbs_gerund[random.randrange(len(verbs_gerund))].strip()

		if token.tag_ == "VBN" and not token.is_stop:
			new_word = verbs_past_participle[random.randrange(len(verbs_past_participle))].strip()

		if token.is_title:
			new_word = new_word.capitalize()

		new_text += new_word
		new_text += token.whitespace_

	return new_text

