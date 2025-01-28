from googleapiclient.discovery import build
from newspaper import Article
from ollama import chat
from ollama import ChatResponse
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from langchain.schema import Document
import re

SEARCH_TERM = "egg prices"
NUM_RESULTS = 30
DEEPSEEK_ANSWER_PATTERN = r"<think>(.*?)</think>(.*)"
MODEL = "deepseek-r1:7b"
API_KEY = ""
CSE_ID = ""

def google_search_with_pagination(search_term, api_key, cse_id, num_results=NUM_RESULTS):
    """
    Conducts a Google search using the Custom Search JSON API with pagination.

    Args:
        search_term (str): The query to search for.
        api_key (str): Your Google API key.
        cse_id (str): Your Custom Search Engine ID.
        num_results (int): Total number of search results to fetch.

    Returns:
        list: A list of search result items, each as a dictionary.
    """
    try:
        # Build the search engine service
        service = build("customsearch", "v1", developerKey=api_key)
        
        all_results = []
        start = 1  # Start index for results

        while len(all_results) < num_results:
            # Fetch results (max 10 per request)
            results_to_fetch = min(10, num_results - len(all_results))
            response = service.cse().list(
                q=search_term,
                cx=cse_id,
                start=start,
                num=results_to_fetch
            ).execute()

            # Extract items from the response
            items = response.get("items", [])
            all_results.extend(items)

            # Update the start index for the next page
            start += len(items)

            # Break if no more results are available
            if len(items) < results_to_fetch:
                break

        return all_results

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# get the search results
query = "news " + SEARCH_TERM # maybe use google news api instead lol
results = google_search_with_pagination(query, API_KEY, CSE_ID)

# scrape the articles
corpus = []
print("scraping articles:")
for item in results:
    print(item['title'])
    print(item['link'])
    url = item['link']
    try:
      url_i = Article(url=url, language='en')
      url_i.download()
      url_i.parse()
      item['text'] = url_i.text
      corpus.append(item)
    except Exception as e:
      print(f"\nfailed to fetch article: {item['title']}\n from url: {item['link']}\n with exception: {e}\n")

# use ai to generate a summary of each article, TIME INTENSIVE, this should probably be a batch job in the cloud where we store all articles for later use or something
for index, item in enumerate(corpus):
    print(f"\nsummarizing article: {item['title']}")
    response: ChatResponse = chat(model=MODEL, messages=[
      {
        'role': 'system',
        'content': 'You will recieve a news article scraped from the internet related to a search topic. Please provide a summary, including as much factual detail from the article as possible. Try to note who wrote the article if you can determine it from the source url or content. If parts of it seem biased point it out.',
      },
      {
        'role': 'user',
        'content': f"Search Topic: {SEARCH_TERM}\nArticle Title: {item['title']}\n Source: {item['displayLink']}\n Text Scaped from Source:\n\n {item['text']}"
      }
    ])
    print(response.message.content)

    item['summary'] = response.message.content
    corpus[index] = item

# now we can put the summaries in a vector database
texts = [f"Title: {item['title']}, Source: {item['displayLink']} Summary: {re.match(DEEPSEEK_ANSWER_PATTERN, item['summary'], re.DOTALL).group(2).strip()}" for item in corpus]
documents = [Document(page_content=text) for text in texts] # I should think about if there are any other Document features I should write
embedding_model_name = "distilbert-base-uncased"
embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)
vectorstore = FAISS.from_documents(documents, embeddings) 
vectorstore.save_local("faiss_index_")
persisted_vectorstore = FAISS.load_local("faiss_index_", embeddings, allow_dangerous_deserialization=True)
# now we can make our RAG
retriever = persisted_vectorstore.as_retriever()
llm = Ollama(model=MODEL)
qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
# Interactive query loop
while True:
    query = input("Type your query about the news corpus (or type 'Exit' to quit): \n")
    if query.lower() == "exit":
        break
    result = qa.run(query)
    print(result)