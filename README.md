# AI Vector Similarity Search Engine using HNSW

A full-stack application that implements a semantic search system. It converts text into vector embeddings and uses a custom-built Hierarchical Navigable Small World (HNSW) graph for fast Approximate Nearest Neighbor (ANN) search.

## Overview

The system allows users to:
1. Upload datasets (JSON or CSV format) or load pre-defined sample data.
2. Convert the text into embeddings using `sentence-transformers` (`all-MiniLM-L6-v2`).
3. Store the embeddings in a custom HNSW index.
4. Search for semantically similar documents via a web interface.
5. Visualize the HNSW graph structure and view a 2D projection of the embeddings.

## Project Architecture

```
User Query (Frontend) -> FastAPI Server -> SentenceTransformer Embedding -> HNSW Graph Search -> Top K Results -> Frontend Display
```

### Tech Stack
* **Backend:** Python, FastAPI, NumPy, sentence-transformers, Custom HNSW Implementation
* **Frontend:** React, Tailwind CSS, Vite, Axios, Plotly.js for Visualizations

## Project Structure

```
AI-HNSW-Search/
├── backend/
│   ├── main.py               # FastAPI application endpoints
│   ├── embedding_model.py    # sentence-transformers wrapper
│   ├── hnsw_index.py         # Custom HNSW algorithm implementation
│   ├── search_engine.py      # Combines embedding & index logic
│   ├── dataset_loader.py     # Parses JSON/CSV datasets
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── App.jsx           # Main layout & state
│   │   ├── SearchBar.jsx     # Search input 
│   │   ├── Results.jsx       # Search results display
│   │   ├── UploadDataset.jsx # Upload interface
│   │   ├── GraphVisualization.jsx # Plotly HNSW node visualization
│   │   └── EmbeddingPlot.jsx # 2D vector projection visualization
│   └── package.json          # Node dependencies
└── README.md                 # Project documentation
```

## Setup & Installation

### 1. Backend Setup

Prerequisites: Python 3.9+

```bash
 

# (Optional) Create a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Frontend Setup

Prerequisites: Node.js 18+

```bash
cd frontend

# Install dependencies
npm install
```

## Running the Application

### 1. Start the Backend

```bash
cd backend
python main.py
```
The FastAPI server will start on `http://localhost:8000`.

### 2. Start the Frontend

```bash
cd frontend
npm run dev
```
The application will be available at `http://localhost:5173`.

## Usage & Example Queries

1. Open the application in your browser.
2. Click **Load Sample Data** or upload your own dataset containing a `text` field.
3. In the Search tab, try the following semantic queries:
   - *"How to bake a cake"* (matches food/cooking documents)
   - *"Coding in Python"* (matches programming/tech documents)
   - *"AI crash course"* (matches machine learning guides)
4. View real-time search latency, similarity scores, and distance metrics.
5. Switch to the **HNSW Graph** tab to visualize the graph structure across layers.
6. Switch to the **Embeddings** tab to see a Plotly scatterplot of the document embeddings.
