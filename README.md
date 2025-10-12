# Healthcare NLP API with FHIR Integration

A FastAPI-based Natural Language Processing API that extracts intent and entities from healthcare queries and simulates FHIR (Fast Healthcare Interoperability Resources) API responses. Built with spaCy for entity recognition and intent detection.

## Features

- 🧠 **Intent Detection**: Automatically identifies user intent from natural language queries
- 🏷️ **Entity Extraction**: Extracts patients, conditions, ages, and other medical entities
- 🔬 **Medical NLP**: Custom entity recognition for medical conditions (diabetic, hypertensive, etc.)
- 🏥 **FHIR Simulation**: Generates mock FHIR-compliant Patient and Condition resources
- 📊 **Pattern Matching**: Uses spaCy's matcher for accurate intent classification
- 🚀 **RESTful API**: Clean REST endpoints with automatic OpenAPI documentation

## Table of Contents

- [Installation](#installation)
- [Setup](#setup)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Entity Types](#entity-types)
- [Intent Types](#intent-types)
- [FHIR Resources](#fhir-resources)
- [API Documentation](#api-documentation)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Step 1: Clone or Navigate to the Project

```bash
cd backend
```

### Step 2: Create a Virtual Environment (Optional but Recommended)

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download spaCy Language Model

```bash
python -m spacy download en_core_web_sm
```

## Setup

The `requirements.txt` file includes:
```
fastapi
uvicorn
spacy
```

After installation, the spaCy English language model (`en_core_web_sm`) must be downloaded for NLP functionality.

## Running the Application

### Start the Development Server

```bash
uvicorn app:app --reload
```

The API will be available at: `http://localhost:8000`

### Start on a Custom Port

```bash
uvicorn app:app --reload --port 8080
```

### Production Mode (without reload)

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with API information |
| POST | `/extract-intent` | Extract intent and entities from a query |
| GET | `/analyze/{query}` | Analyze query via GET request |
| POST | `/fhir-query` | Convert query to FHIR request and get mock data |
| GET | `/items/{item_id}` | Legacy endpoint with optional query analysis |

## Usage Examples

### Example 1: Extract Intent from Simple Query

**Request:**
```bash
curl -X POST "http://localhost:8000/extract-intent" \
  -H "Content-Type: application/json" \
  -d '{"query": "show me all patients"}'
```

**Response:**
```json
{
  "query": "show me all patients",
  "intent": "get_patient",
  "entities": [],
  "confidence": 0.9,
  "tokens": ["show", "me", "all", "patients"],
  "pos_tags": ["VERB", "PRON", "DET", "NOUN"]
}
```

### Example 2: Query with Medical Condition

**Request:**
```bash
curl -X POST "http://localhost:8000/extract-intent" \
  -H "Content-Type: application/json" \
  -d '{"query": "find diabetic patients"}'
```

**Response:**
```json
{
  "query": "find diabetic patients",
  "intent": "get_patient",
  "entities": [
    {
      "text": "diabetic",
      "label": "CONDITION",
      "start": 5,
      "end": 13
    }
  ],
  "confidence": 0.9,
  "tokens": ["find", "diabetic", "patients"],
  "pos_tags": ["VERB", "ADJ", "NOUN"]
}
```

### Example 3: Complex Query with Age and Count

**Request:**
```bash
curl -X POST "http://localhost:8000/extract-intent" \
  -H "Content-Type: application/json" \
  -d '{"query": "show me 50 diabetic patients over 65"}'
```

**Response:**
```json
{
  "query": "show me 50 diabetic patients over 65",
  "intent": "get_patient",
  "entities": [
    {
      "text": "50",
      "label": "NUMBER",
      "start": 8,
      "end": 10
    },
    {
      "text": "diabetic",
      "label": "CONDITION",
      "start": 11,
      "end": 19
    },
    {
      "text": "65",
      "label": "NUMBER",
      "start": 35,
      "end": 37
    }
  ],
  "confidence": 0.9,
  "tokens": ["show", "me", "50", "diabetic", "patients", "over", "65"],
  "pos_tags": ["VERB", "PRON", "NUM", "ADJ", "NOUN", "ADP", "NUM"]
}
```

### Example 4: FHIR Query with Mock Data

**Request:**
```bash
curl -X POST "http://localhost:8000/fhir-query" \
  -H "Content-Type: application/json" \
  -d '{"query": "show me 5 diabetic patients over 50"}'
```

**Response:**
```json
{
  "query": "show me 5 diabetic patients over 50",
  "intent": "get_patient",
  "entities": [
    {
      "text": "5",
      "label": "NUMBER",
      "start": 8,
      "end": 9
    },
    {
      "text": "diabetic",
      "label": "CONDITION",
      "start": 10,
      "end": 18
    },
    {
      "text": "50",
      "label": "NUMBER",
      "start": 34,
      "end": 36
    }
  ],
  "fhir_request": {
    "method": "GET",
    "url": "/Patient",
    "params": {
      "resourceType": "Patient",
      "birthdate": "le1975",
      "_has:Condition:patient:code": "diabetic"
    }
  },
  "fhir_response": {
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 5,
    "entry": [
      {
        "fullUrl": "http://example.com/fhir/Patient/patient-1",
        "resource": {
          "resourceType": "Patient",
          "id": "patient-1",
          "name": [
            {
              "use": "official",
              "family": "Smith",
              "given": ["John"]
            }
          ],
          "gender": "male",
          "birthDate": "1960-05-15",
          "age": 65
        }
      },
      {
        "fullUrl": "http://example.com/fhir/Condition/condition-patient-1",
        "resource": {
          "resourceType": "Condition",
          "id": "condition-patient-1",
          "clinicalStatus": {
            "coding": [
              {
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": "active",
                "display": "Active"
              }
            ]
          },
          "code": {
            "coding": [
              {
                "system": "http://snomed.info/sct",
                "code": "44054006",
                "display": "Type 2 diabetes mellitus"
              }
            ],
            "text": "Type 2 diabetes mellitus"
          },
          "subject": {
            "reference": "Patient/patient-1"
          },
          "onsetDateTime": "2018-01-01T00:00:00Z"
        }
      }
    ]
  }
}
```

### Example 5: GET Request via URL

**Request:**
```bash
curl -X GET "http://localhost:8000/analyze/find%20hypertensive%20patients"
```

**Response:**
```json
{
  "query": "find hypertensive patients",
  "intent": "get_patient",
  "entities": [
    {
      "text": "hypertensive",
      "label": "CONDITION",
      "start": 5,
      "end": 17
    }
  ],
  "confidence": 0.9,
  "tokens": ["find", "hypertensive", "patients"],
  "pos_tags": ["VERB", "ADJ", "NOUN"]
}
```

## Entity Types

The API recognizes the following entity types:

| Entity Type | Description | Examples |
|-------------|-------------|----------|
| `PERSON` | Patient or person names (spaCy) | "John Smith" |
| `ORG` | Organizations (spaCy) | "Mayo Clinic" |
| `GPE` | Geopolitical entities (spaCy) | "U.K.", "California" |
| `CARDINAL` | Numbers (spaCy) | "1 billion" |
| `NUMBER` | Numeric values (custom) | "50", "65" |
| `CONDITION` | Medical conditions (custom) | "diabetic", "hypertensive", "asthmatic" |

## Intent Types

The system detects the following intents:

### Pattern-Based Intents

- **`get_patient`**: Retrieve or list patients
  - Patterns: "get patient", "find patient", "show patients", "list patients"
  
- **`create_patient`**: Create or register new patient
  - Patterns: "create patient", "add patient", "register patient"
  
- **`search_condition`**: Search for medical conditions
  - Patterns: "search condition", "find diagnosis", "list conditions"
  
- **`get_observation`**: Retrieve observations or vitals
  - Patterns: "get observation", "show vitals", "retrieve measurements"

### Fallback Intent

- **`action_{verb}`**: Generic action based on the main verb in the query
  - Example: "action_show", "action_retrieve"

## FHIR Resources

The API generates mock FHIR R4 compliant resources:

### Patient Resource

```json
{
  "resourceType": "Patient",
  "id": "patient-1",
  "name": [{
    "use": "official",
    "family": "Smith",
    "given": ["John"]
  }],
  "gender": "male",
  "birthDate": "1960-05-15",
  "age": 65
}
```

### Condition Resource

```json
{
  "resourceType": "Condition",
  "id": "condition-patient-1",
  "clinicalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active",
      "display": "Active"
    }]
  },
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "44054006",
      "display": "Type 2 diabetes mellitus"
    }],
    "text": "Type 2 diabetes mellitus"
  },
  "subject": {
    "reference": "Patient/patient-1"
  },
  "onsetDateTime": "2018-01-01T00:00:00Z"
}
```

### Supported Conditions with SNOMED CT Codes

| Condition | SNOMED Code | Display Name |
|-----------|-------------|--------------|
| diabetic/diabetes | 44054006 | Type 2 diabetes mellitus |
| hypertensive/hypertension | 38341003 | Hypertensive disorder |
| asthmatic/asthma | 195967001 | Asthma |
| cardiac | 56265001 | Heart disease |

## API Documentation

### Interactive API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API documentation where you can test endpoints directly in your browser.

### Request/Response Models

#### QueryRequest
```json
{
  "query": "string"
}
```

#### IntentResponse
```json
{
  "query": "string",
  "intent": "string | null",
  "entities": [
    {
      "text": "string",
      "label": "string",
      "start": 0,
      "end": 0
    }
  ],
  "confidence": 0.0,
  "tokens": ["string"],
  "pos_tags": ["string"]
}
```

#### FHIRQueryResponse
```json
{
  "query": "string",
  "intent": "string | null",
  "entities": [...],
  "fhir_request": {
    "method": "GET",
    "url": "/Patient",
    "params": {}
  },
  "fhir_response": {
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 0,
    "entry": []
  }
}
```

## Architecture

### Technology Stack

- **FastAPI**: Modern web framework for building APIs
- **spaCy**: Industrial-strength NLP library
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server for running FastAPI applications

### NLP Pipeline

1. **Text Processing**: Input query is processed by spaCy
2. **Intent Detection**: Pattern matching using spaCy's Matcher
3. **Entity Extraction**: Named Entity Recognition (NER) + custom rules
4. **FHIR Translation**: Converts entities to FHIR query parameters
5. **Response Generation**: Creates mock FHIR-compliant responses

### Custom Entity Recognition

The system enhances spaCy's built-in NER with custom rules:

- **Medical Conditions**: Detects keywords like "diabetic", "hypertensive", "asthmatic"
- **Numeric Entities**: Extracts all numbers with context-aware interpretation
  - Numbers < 20 or > 120: likely patient count
  - Numbers 20-120: likely age thresholds

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Successful request
- `400`: Bad request (empty query)
- `422`: Validation error (invalid request format)
- `500`: Internal server error

Example error response:
```json
{
  "detail": "Query cannot be empty"
}
```

## Development

### Project Structure

```
backend/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── __pycache__/       # Python cache (gitignore)
```

### Adding New Intent Patterns

Edit the `patterns` dictionary in `app.py`:

```python
patterns = {
    "your_intent": [
        [{"LOWER": "keyword1"}, {"LOWER": "keyword2"}],
        # Add more patterns
    ]
}
```

### Adding New Medical Conditions

Update the condition list in `extract_intent()`:

```python
if token.text.lower() in ["diabetic", "hypertensive", "your_condition"]:
    # Extraction logic
```

And add SNOMED codes in `generate_mock_conditions()`:

```python
condition_codes = {
    "your_condition": {"code": "SNOMED_CODE", "display": "Display Name"}
}
```

## Testing

### Using curl

```bash
# Test intent extraction
curl -X POST http://localhost:8000/extract-intent \
  -H "Content-Type: application/json" \
  -d '{"query": "your test query"}'

# Test FHIR query
curl -X POST http://localhost:8000/fhir-query \
  -H "Content-Type: application/json" \
  -d '{"query": "show me diabetic patients"}'
```

### Using Python requests

```python
import requests

response = requests.post(
    "http://localhost:8000/fhir-query",
    json={"query": "show me 10 diabetic patients over 60"}
)
print(response.json())
```

### Using the Interactive Docs

Navigate to http://localhost:8000/docs and use the built-in testing interface.

## Troubleshooting

### spaCy Model Not Found

**Error**: `Can't find model 'en_core_web_sm'`

**Solution**:
```bash
python -m spacy download en_core_web_sm
```

### Port Already in Use

**Error**: `Address already in use`

**Solution**: Use a different port
```bash
uvicorn app:app --reload --port 8080
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

## Future Enhancements

- [ ] Integration with real FHIR servers
- [ ] Support for more resource types (Observation, Medication, etc.)
- [ ] Advanced query parsing with dependency trees
- [ ] Machine learning-based intent classification
- [ ] Multi-language support
- [ ] Authentication and authorization
- [ ] Rate limiting and caching
- [ ] Database integration for storing queries and results

## License

This project is provided as-is for educational and demonstration purposes.

## Contact

For questions or support, please open an issue in the repository.

Reach out to Eddie Otudor @ edbeeotudor@gmail.com

---

**Built with ❤️ using FastAPI and spaCy**
