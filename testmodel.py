from utils import custom_analyzer
from sklearn.feature_extraction.text import CountVectorizer

cvec = CountVectorizer(analyzer=custom_analyzer)
cvec.fit(['text','cat'])
