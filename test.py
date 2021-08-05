import spacy

nlp = spacy.load("en_core_web_lg")
doc = nlp("I ate the entire fucking fucnig fuckig and now my stomach feels like dogshit.")

print()

vectors = [doc[4].vector, doc[5].vector, doc[6].vector]

for i in vectors:
    num = 0
    for o in i:
        num += o

    avg = num/len(i)
    print(avg)