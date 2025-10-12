# Quick Start Guide

Get the Healthcare NLP API running in under 2 minutes!

## Option 1: Docker (Recommended) 🐳

### Prerequisites
- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))

### Steps
```bash
# 1. Clone the repository
git clone https://github.com/beloveddie/OnyeBackend.git
cd backend

# 2. Start the application
docker-compose up -d

# 3. Check it's running
curl http://localhost:8000

# 4. View the interactive docs
# Open browser: http://localhost:8000/docs
```

**That's it!** The API is now running at `http://localhost:8000`

### Test It Out
```bash
curl -X POST http://localhost:8000/fhir-query \
  -H "Content-Type: application/json" \
  -d '{"query": "show me 10 diabetic patients over 50"}'
```

---

## Option 2: Local Python Installation

### Prerequisites
- Python 3.8+ installed
- pip package manager

### Steps
```bash
# 1. Navigate to backend folder
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Download spaCy model
python -m spacy download en_core_web_sm

# 6. Run the application
uvicorn app:app --reload
```

The API is now running at `http://localhost:8000`

---

## First API Call

### Using curl
```bash
curl -X POST http://localhost:8000/extract-intent \
  -H "Content-Type: application/json" \
  -d '{"query": "find diabetic patients"}'
```

### Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/extract-intent",
    json={"query": "find diabetic patients"}
)
print(response.json())
```

### Using Browser
1. Open http://localhost:8000/docs
2. Click on `/extract-intent` endpoint
3. Click "Try it out"
4. Enter query: `"show me diabetic patients"`
5. Click "Execute"

---

## Useful Commands

### Docker
```bash
# View logs
docker-compose logs -f

# Stop application
docker-compose down

# Restart application
docker-compose restart

# Rebuild after changes
docker-compose up --build
```

### Using Makefile (if available)
```bash
# Build and run
make run

# View logs
make logs

# Stop
make stop

# Clean everything
make clean
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/extract-intent` | POST | Extract intent and entities |
| `/fhir-query` | POST | Get FHIR mock data |
| `/analyze/{query}` | GET | Analyze query |
| `/docs` | GET | Interactive API documentation |

---

## Example Queries

Try these queries in the API:

1. **Simple patient query**
   ```json
   {"query": "show me all patients"}
   ```

2. **With condition**
   ```json
   {"query": "find diabetic patients"}
   ```

3. **With age filter**
   ```json
   {"query": "show patients over 65"}
   ```

4. **Complex query**
   ```json
   {"query": "show me 20 hypertensive patients over 50"}
   ```

5. **FHIR query**
   ```json
   {"query": "get 5 diabetic patients"}
   ```

---

## Troubleshooting

### Port 8000 already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8080:8000"  # Use port 8080 instead
```

### Container won't start
```bash
# Check logs
docker-compose logs

# Rebuild
docker-compose up --build --force-recreate
```

### spaCy model not found
```bash
# Rebuild Docker image
docker-compose build --no-cache
```

---

## Next Steps

- 📖 Read the full [README.md](README.md) for detailed documentation
- 🐳 See [DOCKER.md](DOCKER.md) for advanced Docker usage
- 🔒 Review [HIPAA_COMPLIANCE.md](HIPAA_COMPLIANCE.md) for security information

---

**Need help?** Open an issue on GitHub or check the documentation!
