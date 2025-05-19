import os
from docx import Document
from elasticsearch import Elasticsearch
import spacy  # Import spacy


class ElasticProcessor:
    def __init__(self, es_nodes, es_index="resume_index", spacy_model="en_core_web_sm"):
        """
        Initializes the ElasticProcessor with Elasticsearch and SpaCy configurations.

        Args:
            es_nodes (list): List of Elasticsearch node IPs.
            es_index (str): Elasticsearch index name.
            spacy_model (str): SpaCy model name (e.g., "en_core_web_sm", "en_core_web_lg").
        """
        self.es_nodes = es_nodes
        self.es_index = es_index
        self.spacy_model = spacy_model
        self.es = self._connect_elasticsearch()
        self.nlp = self._load_spacy_model()
        self._create_index()

    def _connect_elasticsearch(self):
        """
        Connects to Elasticsearch.
        """
        es = Elasticsearch(
            hosts=[{'host': node, 'port': 9200, 'scheme': "http"} for node in self.es_nodes]
        )
        if not es.ping():
            raise ConnectionError("Could not connect to Elasticsearch!")
        print("Connected to Elasticsearch")
        return es

    def _load_spacy_model(self):
        """
        Loads the SpaCy model.
        """
        try:
            nlp = spacy.load(self.spacy_model)
            print(f"Loaded SpaCy model: {self.spacy_model}")
            return nlp
        except OSError:
            raise OSError(f"Could not load SpaCy model: {self.spacy_model}. "
                          f"Please download it using: python -m spacy download {self.spacy_model}")

    def _create_index(self):
        """
        Creates the Elasticsearch index with a mapping for paragraph_id, text, and tags.
        """
        if not self.es.indices.exists(index=self.es_index):
            mapping = {
                "properties": {
                    "paragraph_id": {"type": "integer"},
                    "text": {"type": "text"},
                    "tags": {"type": "keyword"}  # Use 'keyword' for exact match on tags
                }
            }
            self.es.indices.create(index=self.es_index, mappings=mapping)
            print(f"Index '{self.es_index}' created with mapping.")
        else:
            print(f"Index '{self.es_index}' already exists.")

    def extract_tags_spacy(self, text):
        """
        Extracts relevant tags (nouns, proper nouns, verbs) from a text using SpaCy.
        """
        doc = self.nlp(text)
        tags = []
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN", "VERB"]:  # You can adjust these POS tags
                tags.append(token.text)
        return tags

    def process_word_document(self, doc_path):
        """
        Processes a Word document, extracts tags, and indexes each paragraph into Elasticsearch.
        """
        try:
            doc = Document(doc_path)
            for i, paragraph in enumerate(doc.paragraphs):
                text = paragraph.text
                tags = self.extract_tags_spacy(text)
                es_doc = {
                    'paragraph_id': i,
                    'text': text,
                    'tags': tags
                }
                self._index_document(es_doc)  # Using the internal method
            print(f"Successfully processed and indexed document: {doc_path}")

        except Exception as e:
            print(f"Error processing document {doc_path}: {e}")

    def _index_document(self, es_doc):
        """
        Indexes a document into Elasticsearch.
        """
        try:
            response = self.es.index(index=self.es_index, document=es_doc)
            print(f"Indexed paragraph {es_doc['paragraph_id']}: {response['result']}")
        except Exception as e:
            print(f"Error indexing paragraph {es_doc['paragraph_id']}: {e}")


# Example Usage
if __name__ == '__main__':
    # Elasticsearch Configuration
    es_nodes = ["192.168.2.200", "192.168.2.201"]  # Master and data node IPs

    # Initialize ElasticProcessor
    processor = ElasticProcessor(es_nodes=es_nodes)

    # Path to your Word document
    doc_path = "./test-resume.docx"  # Replace with the actual path

    # Process the document
    processor.process_word_document(doc_path)
