from elasticsearch import Elasticsearch
import json

def test_elastic_search(es_nodes, index_name="resume_index"):
    # Connect to Elasticsearch
    es = Elasticsearch(
        hosts=[{'host': node, 'port': 9200, 'scheme': "http"} for node in es_nodes]
    )

    # Check if the index exists
    if not es.indices.exists(index=index_name):
        print(f"Index '{index_name}' does not exist.")
        return

    # Get index stats
    stats = es.indices.stats(index=index_name)
    doc_count = stats['indices'][index_name]['total']['docs']['count']
    print(f"Total documents in index '{index_name}': {doc_count}")

    # Perform a sample search
    search_query = {
        "query": {
            "match_all": {}
        },
        "size": 5  # Limit to 5 results for brevity
    }

    results = es.search(index=index_name, body=search_query)

    # Display search results
    print("\nSample documents:")
    for hit in results['hits']['hits']:
        print(f"\nParagraph ID: {hit['_source']['paragraph_id']}")
        print(f"Text: {hit['_source']['text'][:100]}...")  # Show first 100 characters
        print(f"Tags: {', '.join(hit['_source']['tags'])}")

    # Get unique tags
    tags_query = {
        "size": 0,
        "aggs": {
            "unique_tags": {
                "terms": {
                    "field": "tags",
                    "size": 10  # Get top 10 tags
                }
            }
        }
    }

    tags_results = es.search(index=index_name, body=tags_query)

    # Display unique tags
    print("\nTop 10 unique tags:")
    for tag in tags_results['aggregations']['unique_tags']['buckets']:
        print(f"{tag['key']}: {tag['doc_count']}")

if __name__ == "__main__":
    es_nodes = ["192.168.2.200", "192.168.2.201"]  # Your Elasticsearch nodes
    test_elastic_search(es_nodes)
