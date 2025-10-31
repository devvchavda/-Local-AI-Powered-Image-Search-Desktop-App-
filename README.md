# -Local-AI-Powered-Image-Search-Desktop-App-
**About This Project**
> This repository contains an AI-based 🤖 image search application that runs **100% locally** 💻 using Ollama models.
>
> The system is built to be flexible ⚙️; while it's designed for local-first use, a developer can adapt it to use other models via API calls ☁️. You'll notice this project does not use a traditional CLIP model. This was a deliberate choice ✅ due to the complexities of finding a good, self-hostable, or affordably-priced CLIP API 💰.
>
> Nevertheless, the search results 🔍 achieved with the current multi-captioning strategy are impressive ✨.


## 🚀 Setup & Installation

Follow these steps to get the project running on your local machine.

### 1. Prerequisites
Before you begin, ensure you have the following installed:

* **Python:** (Version 3.9 or newer is recommended).
* **Ollama:** You must have [Ollama](https://ollama.com/) installed and running on your system.
* **AI Models:** You must pull the specific models this project uses. Open your terminal and run:
    ```bash
    ollama pull gemma3:4b
    ollama pull qwen3:8b
    ollama pull qwen3-embedding:4b
    ```

### 2. Installation
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/devvchavda/-Local-AI-Powered-Image-Search-Desktop-App.git](https://github.com/devvchavda/-Local-AI-Powered-Image-Search-Desktop-App.git)
    cd -Local-AI-Powered-Image-Search-Desktop-App
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # Create the environment
    python -m venv venv

    # Activate it (on Windows)
    .\venv\Scripts\activate
    ```

3.  **Install the required packages:**
    (Make sure you have your `requirements.txt` file in the folder)
    ```bash
    pip install -r requirements.txt
    ```

  ## 🔬 Code Breakdown

This project is modular, with each file handling a specific part of the search pipeline. Here's what each script does:

### 1. `image_analyser.py`
This script performs the  "visual analysis" . Its main purpose is to **generate a detailed summary** of an image. It takes a file path, loads the image, and uses the `gemma3:4b` multimodal model to generate a rich, descriptive text of what's in the picture. This detailed summary is the raw "context" that will be used for indexing.

### 2. `manage_documents.py`
This is where the core "captioning strategy" happens. This script takes the single, detailed summary from `image_analyser.py` and feeds it to the `qwen3:8b` model. Using a structured prompt, it **generates the 7 distinct semantic captions** (like "Broad Concept," "Specific Entity," "Spatial Description," etc.). This "multi-caption" approach tries to make the searching releavant images effectively , as it indexes the image from multiple perspectives.

### 3. `vec_store.py`
This script is the project's "memory." It's a dedicated wrapper class for the **FAISS vector store**. Its job is to:
* Initialize or load the `faiss_index` from the disk.
* Take the 7 captions and use the `qwen3-embedding:4b` model to create and store the vectors.
* Handle adding, deleting, and searching for vectors.
* Persist any changes back to the local `faiss_index` directory.

### 4. `image_search.py`
This is the **main backend controller**. It acts as the central hub that connects all the other modules. It initializes the `ImageTextDocument` (from `manage_documents.py`) and `VectorStore` classes. It provides the high-level methods that the desktop app and watcher will use, such as `process_dir()` (to run the full indexing pipeline) and `search()` (to query the vector store). It also holds the configuration for your `linked_directories`.

### 5. `directory_watcher.py`
This is the **live-indexing service**. It's a background script that uses the `watchdog` library to monitor the folders you defined in `linked_directories`. When it detects a **new image file** has been added (`on_created`) in the mentioned linked directories , it automatically triggers the `image_searcher.process_dir()` method to analyze, caption, and index it in real-time. It also uses `win11toast` to send you a system notification that the image has been added.

### 6. `dekstop_app.py`
This is the **frontend graphical user interface (GUI)**. It's a complete, modern desktop application built with **PySide6**. It provides the main search bar, the list for displaying results, and the pannable/zoomable image preview. It connects to the `ImageSearcher` backend to run searches and add new files. This I have created through Claude Ai as main focus was to explore the search part only. 
