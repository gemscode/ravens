from elasticsearch import Elasticsearch
import sys
import getopt

class ElasticSearcher:
    def __init__(self, es_nodes, es_index="resume_index"):
        self.es_index = es_index
        self.es = self._connect_elasticsearch(es_nodes)

    def _connect_elasticsearch(self, es_nodes):
        es = Elasticsearch(
            hosts=[{'host': node, 'port': 9200, 'scheme': "http"} for node in es_nodes]
        )
        if not es.ping():
            raise ConnectionError("Could not connect to Elasticsearch!")
        print("Connected to Elasticsearch")
        return es

    def search_paragraphs(self, keyword, context="p"):
        search_query = {
            "query": {
                "multi_match": {
                    "query": keyword,
                    "fields": ["text", "tags"]
                }
            },
            "highlight": {
                "fields": {
                    "text": {}
                },
                "fragment_size": 300,
                "number_of_fragments": 1
            },
            "size": 10
        }

        try:
            results = self.es.search(index=self.es_index, body=search_query)
            hits = results['hits']['hits']

            if not hits:
                print(f"No results found for keyword '{keyword}'.")
                return

            print(f"Search results for keyword '{keyword}':")
            for hit in hits:
                paragraph_id = hit['_source']['paragraph_id']
                print(f"  Paragraph ID: {paragraph_id}")

                if context == "pb":
                    before_paragraph = self._get_paragraph(paragraph_id - 1)
                    if before_paragraph:
                        print("  Paragraph Before:")
                        print(f"    {before_paragraph}")

                if 'highlight' in hit:
                    print("  Relevant Paragraph:")
                    for fragment in hit['highlight']['text']:
                        print(f"    {fragment}")
                else:
                    print("  No relevant paragraph found.")

                if context == "pa":
                    after_paragraph = self._get_paragraph(paragraph_id + 1)
                    if after_paragraph:
                        print("  Paragraph After:")
                        print(f"    {after_paragraph}")

                print("-" * 30)

        except Exception as e:
            print(f"Error during Elasticsearch search: {e}")

    def _get_paragraph(self, paragraph_id):
        get_query = {"query": {"term": {"paragraph_id": paragraph_id}}}
        try:
            result = self.es.search(index=self.es_index, body=get_query, size=1)
            hit = result['hits']['hits']
            if hit:
                return hit[0]['_source']['text']
            else:
                return None
        except Exception as e:
            print(f"Error retrieving paragraph {paragraph_id}: {e}")
            return None

if __name__ == '__main__':
    es_nodes = ["192.168.2.200", "192.168.2.201"]  # Your Elasticsearch nodes
    context = "p"  # Default to just the paragraph
    keyword = None

    if len(sys.argv) != 3:
        print("Usage: python SearchElastic.py [-p | -pa | -pb] <keyword>")
        sys.exit(2)

    option = sys.argv[1]
    if option not in ["-p", "-pa", "-pb"]:
        print("Invalid option. Use -p, -pa, or -pb.")
        print("Usage: python SearchElastic.py [-p | -pa | -pb] <keyword>")
        sys.exit(2)

    context = option[1:]  # Remove the leading '-'
    keyword = sys.argv[2]

    searcher = ElasticSearcher(es_nodes)
    searcher.search_paragraphs(keyword, context)
