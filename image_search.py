from manage_documents import ImageTextDocument
from vec_store import VectorStore
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
import mimetypes 
from watchdog.events import FileSystemEventHandler


            
    
class ImageSearcher():
    def __init__(self):
        self.imagedocs = ImageTextDocument()
        self.linked_directories = ["D:/langchain tutorials/ai based image searcher/images"]
        self.vecstore = VectorStore()
    def process_dir(self , path , via_background=False):
        captions,metadata = self.imagedocs.create_documents(path)
        self.vecstore.add_documents(captions,metadata)
        if(via_background):
            self.vecstore.load_vector_store()
    def search(self , query:str , show=False):
        if(not self.vecstore):
            return []
        results = self.vecstore.retrieve_best(query,k=20 , fetch_k=30)  
        paths = [res.metadata.get('path') for res in results]
        seen = set()
        temp = []
        for path in paths:
            if path in seen:
                continue 
            if not os.path.exists(path):
                self.remove_image(path)
                continue
            temp.append(path)
            seen.add(path)
        paths = temp 
        if(show):
            for path in paths:
                img = mpimg.imread(path)
                plt.imshow(img)
                plt.title(path.split('/')[-1])
                plt.axis('off')
                plt.show()
        return paths
    def remove_image(self , path:str):
        self.vecstore.remove_documents(path)            
if __name__ == "__main__":
    ImageSearcher().process_dir("D:/langchain tutorials/ai based image searcher/image2")