from langchain_core.prompts import ChatPromptTemplate 
from langchain_ollama import ChatOllama 
from pydantic import BaseModel , Field
from typing import List , Optional
from image_analyser import ImageAnalyser
import os
from tqdm import tqdm
length = 7 
class ImageTextEmbedderDocument(BaseModel):
    captions : List[str] = Field(description="List of the captions extracted from the given description" , min_length=length , max_length=length)
class prompts():
    def __init__(self):
        self.system = """
You are an AI assistant that generates five semantically distinct captions for a vector search database from a detailed image summary. Your goal is to produce captions that capture different levels of generality and perspective, enabling diverse and accurate search matches.

Follow this structure precisely:

1. Broad Concept: A short, high-level caption summarizing the main idea or scene.
2. Broad Activity: A short caption describing the primary action or context.
3. Specific Entity Description: A detailed caption highlighting the key subject or object with identifying traits (atleast 50 words) . 
4. Spatial Description: A detailed caption describing body position, layout, or physical arrangement of elements in the scene.
5. Integrated mild detailed Summary: A fluent, natural sentence combining the scene`s subject, action, and contextual details , atleast (50 words)
6. Predict Very short caption which user will likely search 
7. Predict another Very short caption which user will likely search 
Output only a numbered list of the seven captions (Also do not number the captions 1. 2. (dont do this))
"""
        self.human = """Here is the description of the image: \n {description}"""
        
        self.prompt_template = ChatPromptTemplate(
            [
                ("system" , self.system),
                ("human" , self.human)
            ]
        )
class ImageTextDocument():
    def __init__(self):
        self.model = ChatOllama(model = "qwen3:8b").with_structured_output(ImageTextEmbedderDocument)
        self.prompts = prompts()
        self.image_analyser = ImageAnalyser()
    def create_documents(self , path : str):
        prompt_chain = self.prompts.prompt_template | self.model
        if(os.path.isdir(path)):
            captions = []
            metadata = []
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))] 
            descriptions = []
            for file in tqdm(files,desc = "Processing Images : " , unit="Image"):
                fullpath = os.path.join(path,file)
                description = self.image_analyser.analyse_image(path=fullpath)  
                descriptions.append({"description":description})
                caption_obj = prompt_chain.invoke({"description":description})
                captions += caption_obj.captions 
                metadata += [{"path":fullpath}]*length
            # --> We can also do this using batch to increase speed , but concern is about  VRAM consumption of gpu ... 
            # response = prompt_chain.batch(descriptions)
            # captions = [caption for r in response for caption in r.captions]
            return captions , metadata
        else: 
            description = self.image_analyser.analyse_image(path=path) 
            caption_obj = prompt_chain.invoke({"description":description})
            metadata = [{"path":path}]*len(caption_obj.captions)
            return caption_obj.captions , metadata   
        
if __name__ == "__main__":
    image_text_doc = ImageTextDocument()
    print(image_text_doc.create_documents("D:/langchain tutorials/ai based image searcher/image2"))