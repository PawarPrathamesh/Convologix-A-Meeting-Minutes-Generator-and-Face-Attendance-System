#from gensim.summarization import summarize as gensim_summarize
#from gensim.summarization import summarize
import textsum as t
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.text_rank import TextRankSummarizer
from transformers import pipeline

# def summarize_with_gensim(text):
#     return summarize(text)

def summarize_with_lexrank(text):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LexRankSummarizer()
    summary = summarizer(parser.document, sentences_count=2)
    return " ".join(str(sentence) for sentence in summary)

def summarize_with_textrank(text):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = TextRankSummarizer()
    summary = summarizer(parser.document, sentences_count=2)
    return " ".join(str(sentence) for sentence in summary)

def summarize_with_transformers(text):
    summarization_pipeline = pipeline("summarization")
    summary = summarization_pipeline(text, max_length=150, min_length=30, do_sample=False)
    return summary[0]['summary_text']

# Sample text
text = "Data science is an interdisciplinary field that employs scientific methods, algorithms, and systems to extract insights from data. It involves collecting and cleaning data, exploring its structure and patterns through exploratory data analysis, and building predictive models using machine learning algorithms such as regression, classification, and clustering. Data scientists also employ techniques like big data analytics, natural language processing, and data visualization to derive actionable insights from large and complex datasets. Ethical considerations regarding data privacy and responsible use are paramount in data science practice. Finally, deploying and monitoring models in production environments ensures ongoing performance and relevance to business needs."



# #Summarize using Gensim's TextRank
# print("Summarization using Gensim's TextRank:")
# print(summarize_with_gensim(text))
# print()

# Summarize using Sumy's LexRank
print("Summarization using Sumy's LexRank:")
print(summarize_with_lexrank(text))
print()

# Summarize using Sumy's TextRank
print("Summarization using Sumy's TextRank:")
print(summarize_with_textrank(text))
print()

# Summarize using Transformers library
print("Summarization using Transformers:")
print(summarize_with_transformers(text))



Summary=t.sum(text)
print("Summarization using :")
print(Summary)