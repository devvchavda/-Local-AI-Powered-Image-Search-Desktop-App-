from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage , AIMessage , SystemMessage
import base64
from PIL import Image
import io


class ImageAnalyser():
    def __init__(self):
        self.model = ChatOllama(
            model = "gemma3:4b" 
        ) 
        self.system = SystemMessage(
            content=(
                "You are an expert visual analyst specializing in generating **detailed, accurate, and retrieval-optimized descriptions** of images.\n\n"
                "Your goal is to produce comprehensive textual summaries that can be used to find and match similar images in a database.\n\n"
                "Follow these exact requirements:\n"
                "1. **Detailed Summary** — Describe everything visible in the image clearly: objects, people, scenes, activities, colors, positions, and relationships. atleast 100 words . Describe the image in DETAIL and generate the summary point wise.\n"
                "2. **Text Extraction** — If any text appears inside the image, include it in a separate section exactly as:\n"
                "   `Text: // extracted text here //`\n"
                "   If no text is visible, write: `Text: // none //`.\n"
                "3. **Factual Tone** — Do not invent or assume; describe only what is visually identifiable.\n"
                "4. **Purpose Reminder** — The output will be used for visual search and retrieval. Ensure it is rich in relevant visual and contextual details.\n\n"
            )
        )

    def analyse_image(self , path : str , prompt = "Describe the given image in full detail ") -> str :
        image = Image.open(path)
        with io.BytesIO() as buffer:
            image.save(buffer,format="PNG")
            image_bytes = buffer.getvalue()
        encode = base64.b64encode(image_bytes).decode('utf-8') 
        msg = HumanMessage(
        content=[{
            "type":"text",
            "text":prompt,
        },
        {
            "type":"image_url",
            "image_url": f"data:image/png;base64,{encode}"
        }]
        )
        response = self.model.invoke([self.system , msg])
        return response.content 
    
if __name__ == "__main__":
    print(ImageAnalyser().analyse_image(path="C:/Users/devch/Pictures/2025-08-01"))