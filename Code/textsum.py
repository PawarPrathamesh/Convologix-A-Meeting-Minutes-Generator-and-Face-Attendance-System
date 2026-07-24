from transformers import BertTokenizerFast



from transformers import pipeline

#summarizer= pipeline ('summarization')

# article = """ since data can have different formats and structures companies need to consider different storage systems based on the type of data that needs to be captured data management teams help to set standards around data storage and structure which facilitate workflows around analytics machine learning and deep learning models this stage includes cleaning data deduplicating transforming and combining the data using etl extract transform load jobs or other data integration technologies this data preparation is essential for promoting data quality before loading into a data warehouse data lake or other repository data scientists conduct an exploratory data analysis to examine biases patterns ranges and distributions of values within the data this data analytics exploration drives hypothesis generation for a b testing it also allows analysts to determine the data’s relevance for use within modeling efforts for predictive analytics machine learning and or deep learning depending on a model’s accuracy organizations can become reliant on these insights for business decision making allowing them to drive more scalability finally insights are presented as reports and other data visualizations that make the insights and their impact on business easier for business analysts and other decision-makers to understand a data science programming language such as r or python includes components for generating visualizations alternately data scientists can use dedicated visualization tools"""

# summarizer(article, max_length=130, min_length=40,do_sample=False)

#######################################################################

#!pip install transformers
#from transformers import pipeline

# Function to add commas to the summarized text

def add_commas(text):
    continuation_words = ['and', 'but', 'or', 'yet', 'so', 'however', 'although', 'though', 'nevertheless', 'furthermore', 'meanwhile', 'moreover', 'instead']
    words = text.split()
    final_text = words[0].capitalize() if words[0] else ''
    for word in words[1:]:
        if word in continuation_words:
            final_text += ', ' + word
        else:
            final_text += ' ' + word
    if not final_text.endswith('.'):
        final_text += '.'
    return final_text


def sum(tx):
    # Initialize the summarization pipeline
    summarizer = pipeline('summarization')

    # Define your article
    article = tx
    length_text=len(article)
    max_length = int(length_text * 50)
    min_length=int(length_text * 10)

    # Summarize the article
    summarized_text = summarizer(article, max_length, min_length, do_sample=False)

    # Extract the summary text
    summary_text = summarized_text[0]['summary_text'].strip()

    # Add commas to the summarized text
    processed_summary = add_commas(summary_text)

    # Print the processed summary
    # print("")
    # print("")
    # print("The Given Text:-")
    # print("")
    # print(article)
    print("#"*150)
    # print("")
    # print("")
    # print("Summary:")
    # print("")
    print(processed_summary)
    print("#"*150)
    return processed_summary



