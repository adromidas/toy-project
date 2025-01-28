## Summary

Project the idea is to get a llm to query google for news articles on a topic, scrape the articles, summarize them, store them in a vector store, and use them in retrival augmented generation.

Not exactly a groupbreaking idea but a toy project for me to get started with langchain.

News is a fun domain to me because it is easy to find a variety of documents on a topic, they are interconnected, and there are lots of other sources of information that can be synthesized with it. 

## Setup

Follow instructions to setup a google search api key and custom search engine id. Copy those values to the constants for `API_KEY` and `CSE_ID` in the code.

To setup the project install ollama

Then pull the model you are using, I am using the 7b parameter version of deepseek-r1. If you want to use a different size make sure to change `MODEL`. If you use a model other than deepseek-r1 you will also need to change the regex usage when we create the documents list, as it relies on the `<thinking>` tag format.

Pull the model with: `ollama pull deepseek-r1:7b`

Also make sure ollama service is running with `ollama serve`

Setup a virtual environment with `python3.10 -m venv venv` and `. ./venv/bin/activate`

Download the requirements with `pip install -r requirements.txt`

## Running

Edit the `SEARCH_TERM` constant to use the search term you would like.

Edit the `NUM_RESULTS` constant to the number of search results you would like to scrape. Remember that every ten will take up one api request and that google is limiting you. Also keep in mind that each search result will take minutes to summarize and that it will take forever.

Run with `python3 search.py`

It will tell you a list of articles it found, begin summarizing them, and then start a loop for you to talk to the retrieval augmented generator.