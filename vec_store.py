from langchain_ollama import OllamaEmbeddings , ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import os
import numpy as np
import faiss
from langchain_community.vectorstores.utils import DistanceStrategy

class VectorStore():
     def __init__(self):
          self.model = OllamaEmbeddings(
               model="qwen3-embedding:4b"
          )
          self.load_vector_store()
     def load_vector_store(self):
          self.vector_store = None
          if os.path.exists("faiss_index"):
               self.vector_store = FAISS.load_local("faiss_index" , embeddings=self.model , allow_dangerous_deserialization=True )
          return self.vector_store
     def add_document(self , text : str , metadata : dict , tosave = True):
          doc = [Document(page_content=text , metadata = metadata)]
          if(not self.vector_store):
               self.vector_store = FAISS.from_documents(documents=doc , embedding=self.model)
          else:
               self.vector_store.add_documents(documents=doc)
          if(tosave):
               self.vector_store.save_local("faiss_index")
     def add_documents(self , docs : list , metadata: list ,tosave=True):
          documents = [Document(page_content=doc , metadata=mtdata) for doc,mtdata in zip(docs,metadata)]
          if(not self.vector_store):
               self.vector_store = FAISS.from_documents(documents , embedding=self.model)
          else:
               self.vector_store.add_documents(documents)
          if(tosave):
               self.vector_store.save_local("faiss_index")
     def retrieve_best(self , query:str , k = 3 , fetch_k = 10):
          vector_store = self.vector_store
          res = None
          if(vector_store):
               res = vector_store.similarity_search(query , k=k , fetch_k=fetch_k)
          
          return res
     def remove_documents(self, target_path):
          if not self.vector_store :
               return 

          delete_ids = [doc_id for doc_id,doc in self.vector_store.docstore._dict.items() if doc.metadata.get("path")==target_path]
          if delete_ids :
               self.vector_store.delete(delete_ids)
               self.vector_store.save_local("faiss_index")
     def get_documents(self):
          if not self.vector_store:
               return 
          return self.vector_store.docstore._dict.values()
     def create_text_file(self , name:str):
          docs = self.get_documents()
          with open(name, "w") as f:
               for i,doc in enumerate(docs):
                    f.write(f"{i+1} -> Path : {doc.metadata['path']} \nCaption : {doc.page_content} \n\n")
     def get_all_paths(self)->set:
          paths = set(doc.metadata['path'] for doc in self.get_documents())
          return paths

if __name__ == "__main__":
     vecstore = VectorStore()
     vecstore.create_text_file("docs.txt")