# Web Scraping Agent System

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone  https://github.com/daromsartof/smart-scrapping.git
cd qa-agent-system
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional (with defaults)
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=30000
REQUEST_TIMEOUT=30
LLM_TIMEOUT=60
```

### 3. Build and Run with Docker Compose
```bash
# Build the image
docker-compose build

# Run in detached mode
docker-compose up -d

# Or run interactively
docker-compose run --rm web-scraping-agent
```

### 4. Direct Docker Run
```bash
# Build image
docker build -t web-scraping-agent .

# Run container
docker run --rm \
  -e GOOGLE_API_KEY=your_api_key \
  -v $(pwd)/output:/app/output \
  web-scraping-agent
```

## 🚀 Development

### Local Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run application
python main.py
```