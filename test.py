import spacy

nlp = spacy.load("en_core_web_trf")
doc = nlp("I ate the entire fucking cake and now my stomach feels like dogshit.")

text = ""
for token in doc:
    print(token.text, token.tag_, token.dep_)