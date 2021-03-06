

# session = dryscrape.Session()
# session.visit(my_url)
# response = session.body()
# soup = BeautifulSoup(response)
# soup.find(id="topicTitle")

import re
import requests
import nltk
import ssl
import pandas as pd
from requests_html import HTMLSession
from bs4 import BeautifulSoup as Soup
import spacy
from spacy import displacy
nlp = spacy.load('en_core_web_sm')

from spacy.matcher import Matcher 
from spacy.tokens import Span 

import networkx as nx

import matplotlib.pyplot as plt
from tqdm import tqdm

pd.set_option('display.max_colwidth', 200)
# %matplotlib inline

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt')


# text = "Apple acquired Zoom in China on Wednesday 6th May 2020.\
# This news has made Apple and Google stock jump by 5% on Dow Jones Index in the \
# United States of America"
# r.html.render()
# script = r.html.raw_html
# script = r.html.html

# script = r.html.html
# print(script)
# print(dir(r))


url = 'https://www.uptodate.com/contents/treatment-for-potentially-resectable-exocrine-pancreatic-cancer?search=prancreas&source=search_result&selectedTitle=10~150&usage_type=default&display_rank=10'

def scrapper(my_url):
    session = HTMLSession()

    r = session.get(my_url)
    r.html.render(timeout=20)

    script = r.html.html

    page_soup = Soup(script, "html.parser")
    title = page_soup.find("div", {"id": "topicTitle"})
    title = title.text

    content = page_soup.find("div", {"id": "topicText"})
    content = content.text
    
    return title, content

title,content = scrapper(url)

# print(title + '\n' + content)

#Sentence
sentence = nltk.sent_tokenize(content)


sentence_df = pd.DataFrame(sentence, columns =['Sentence'])
# print(sentence_df.head)

def get_entities(sent):
  ## chunk 1
  ent1 = ""
  ent2 = ""

  prv_tok_dep = ""    # dependency tag of previous token in the sentence
  prv_tok_text = ""   # previous token in the sentence

  prefix = ""
  modifier = ""
  
  for tok in nlp(sent):
    ## chunk 2
    # if token is a punctuation mark then move on to the next token
    if tok.dep_ != "punct":
      # check: token is a compound word or not
      if tok.dep_ == "compound":
        prefix = tok.text
        # if the previous word was also a 'compound' then add the current word to it
        if prv_tok_dep == "compound":
          prefix = prv_tok_text + " "+ tok.text
      
      # check: token is a modifier or not
      if tok.dep_.endswith("mod") == True:
        modifier = tok.text
        # if the previous word was also a 'compound' then add the current word to it
        if prv_tok_dep == "compound":
          modifier = prv_tok_text + " "+ tok.text
      
      ## chunk 3
      if tok.dep_.find("subj") == True:
        ent1 = modifier +" "+ prefix + " "+ tok.text
        prefix = ""
        modifier = ""
        prv_tok_dep = ""
        prv_tok_text = ""      

      ## chunk 4
      if tok.dep_.find("obj") == True:
        ent2 = modifier +" "+ prefix +" "+ tok.text
        
      ## chunk 5  
      # update variables
      prv_tok_dep = tok.dep_
      prv_tok_text = tok.text

  return [ent1.strip(), ent2.strip()]

# Test = get_entities("the film had 200 patents")
# print(Test)




entity_pairs = []

for i in tqdm(sentence_df["Sentence"]):
  entity_pairs.append(get_entities(i))




def get_relation(sent):

  doc = nlp(sent)

  # Matcher class object 
  matcher = Matcher(nlp.vocab)

  #define the pattern 
  pattern = [{'DEP':'ROOT'}, 
            {'DEP':'prep','OP':"?"},
            {'DEP':'agent','OP':"?"},  
            {'POS':'ADJ','OP':"?"}] 

  matcher.add("matching_1", [pattern], on_match=None) 

  matches = matcher(doc)
  k = len(matches) - 1

  span = doc[matches[k][1]:matches[k][2]] 

  return(span.text)

# print(get_relation("John completed the task"))

relations = [get_relation(i) for i in tqdm(sentence_df['Sentence'])]

# extract subject
source = [i[0] for i in entity_pairs]

# extract object
target = [i[1] for i in entity_pairs]

kg_df = pd.DataFrame({'source':source, 'target':target, 'edge':relations})

# create a directed-graph from a dataframe
G=nx.from_pandas_edgelist(kg_df, "source", "target", edge_attr=True, create_using=nx.MultiDiGraph())

plt.figure(figsize=(12,12))

pos = nx.spring_layout(G)
nx.draw(G, with_labels=True, node_color='skyblue', edge_cmap=plt.cm.Blues, pos = pos)
plt.show()