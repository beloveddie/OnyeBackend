from typing import Union, Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import spacy
from spacy.matcher import Matcher
from datetime import datetime
import random

app = FastAPI()

# Load spaCy model (install with: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except:
    raise RuntimeError("Please install spaCy model: python -m spacy download en_core_web_sm")

# Initialize matcher for pattern-based intent detection
matcher = Matcher(nlp.vocab)

# Define intent patterns
patterns = {
    "get_patient": [
        [{"LOWER": "get"}, {"LOWER": "patient"}],
        [{"LOWER": "find"}, {"LOWER": "patient"}],
        [{"LOWER": "retrieve"}, {"LOWER": "patient"}],
        [{"LOWER": "show"}, {"LOWER": "patient"}],
        [{"LOWER": "show"}, {"LOWER": "me"}, {"LOWER": "patient"}],
        [{"LOWER": "show"}, {"OP": "?"}, {"LOWER": {"IN": ["patient", "patients"]}}],
        [{"LOWER": "list"}, {"LOWER": {"IN": ["patient", "patients"]}}],
        [{"LOWER": {"IN": ["get", "find", "show", "list"]}}, {"OP": "*"}, {"LOWER": {"IN": ["patient", "patients"]}}]
    ],
    "create_patient": [
        [{"LOWER": "create"}, {"LOWER": "patient"}],
        [{"LOWER": "add"}, {"LOWER": "patient"}],
        [{"LOWER": "register"}, {"LOWER": "patient"}]
    ],
    "search_condition": [
        [{"LOWER": "search"}, {"LOWER": "condition"}],
        [{"LOWER": "find"}, {"LOWER": "diagnosis"}],
        [{"LOWER": "list"}, {"LOWER": "conditions"}]
    ],
    "get_observation": [
        [{"LOWER": "get"}, {"LOWER": "observation"}],
        [{"LOWER": "show"}, {"LOWER": "vitals"}],
        [{"LOWER": "retrieve"}, {"LOWER": "measurements"}]
    ]
}

# Add patterns to matcher
for intent, pattern_list in patterns.items():
    matcher.add(intent, pattern_list)


class QueryRequest(BaseModel):
    query: str


class Entity(BaseModel):
    text: str
    label: str
    start: int
    end: int


class IntentResponse(BaseModel):
    query: str
    intent: Union[str, None]
    entities: List[Entity]
    confidence: float
    tokens: List[str]
    pos_tags: List[str]


class FHIRPatient(BaseModel):
    resourceType: str = "Patient"
    id: str
    name: List[Dict[str, Any]]
    gender: str
    birthDate: str
    age: int


class FHIRCondition(BaseModel):
    resourceType: str = "Condition"
    id: str
    clinicalStatus: Dict[str, Any]
    code: Dict[str, Any]
    subject: Dict[str, str]
    onsetDateTime: Optional[str] = None


class FHIRBundle(BaseModel):
    resourceType: str = "Bundle"
    type: str = "searchset"
    total: int
    entry: List[Dict[str, Any]]


class FHIRQueryResponse(BaseModel):
    query: str
    intent: Union[str, None]
    entities: List[Entity]
    fhir_request: Dict[str, Any]
    fhir_response: FHIRBundle


def extract_intent(query: str) -> IntentResponse:
    """Extract intent and entities from query using spaCy"""
    # Process the original query to preserve entities, but create lowercase version for matching
    doc = nlp(query)
    doc_lower = nlp(query.lower())
    
    # Find intent using matcher on lowercase version
    matches = matcher(doc_lower)
    intent = None
    confidence = 0.0
    
    if matches:
        match_id, start, end = matches[0]
        intent = nlp.vocab.strings[match_id]
        confidence = 0.9  # High confidence for pattern match
    else:
        # Fallback: simple verb-based intent detection
        for token in doc_lower:
            if token.pos_ == "VERB":
                intent = f"action_{token.lemma_}"
                confidence = 0.5
                break
    
    # Extract entities from the original doc (not lowercased) for better accuracy
    entities = [
        {
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char
        }
        for ent in doc.ents
    ]
    
    # Add custom medical/numeric entity extraction
    for token in doc:
        # Extract numbers (age, quantities)
        if token.like_num or token.pos_ == "NUM":
            entities.append({
                "text": token.text,
                "label": "NUMBER",
                "start": token.idx,
                "end": token.idx + len(token.text)
            })
        # Extract potential medical conditions (adjectives that might be conditions)
        if token.text.lower() in ["diabetic", "hypertensive", "asthmatic", "cardiac"]:
            entities.append({
                "text": token.text,
                "label": "CONDITION",
                "start": token.idx,
                "end": token.idx + len(token.text)
            })
    
    # Extract tokens and POS tags from original doc
    tokens = [token.text for token in doc]
    pos_tags = [token.pos_ for token in doc]
    
    return IntentResponse(
        query=query,
        intent=intent,
        entities=entities,
        confidence=confidence,
        tokens=tokens,
        pos_tags=pos_tags
    )


def generate_mock_patients(count: int, condition: str = None, min_age: int = None) -> List[FHIRPatient]:
    """Generate mock FHIR Patient resources"""
    patients = []
    first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa", "James", "Mary"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    
    for i in range(count):
        age = random.randint(min_age if min_age else 30, 80)
        birth_year = datetime.now().year - age
        
        patient = FHIRPatient(
            id=f"patient-{i+1}",
            name=[{
                "use": "official",
                "family": random.choice(last_names),
                "given": [random.choice(first_names)]
            }],
            gender=random.choice(["male", "female"]),
            birthDate=f"{birth_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            age=age
        )
        patients.append(patient)
    
    return patients


def generate_mock_conditions(patient_id: str, condition_name: str) -> FHIRCondition:
    """Generate mock FHIR Condition resource"""
    condition_codes = {
        "diabetic": {"code": "44054006", "display": "Type 2 diabetes mellitus"},
        "diabetes": {"code": "44054006", "display": "Type 2 diabetes mellitus"},
        "hypertensive": {"code": "38341003", "display": "Hypertensive disorder"},
        "hypertension": {"code": "38341003", "display": "Hypertensive disorder"},
        "asthmatic": {"code": "195967001", "display": "Asthma"},
        "asthma": {"code": "195967001", "display": "Asthma"},
        "cardiac": {"code": "56265001", "display": "Heart disease"}
    }
    
    condition_info = condition_codes.get(condition_name.lower(), {
        "code": "unknown",
        "display": condition_name
    })
    
    return FHIRCondition(
        id=f"condition-{patient_id}",
        clinicalStatus={
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": "active",
                "display": "Active"
            }]
        },
        code={
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": condition_info["code"],
                "display": condition_info["display"]
            }],
            "text": condition_info["display"]
        },
        subject={"reference": f"Patient/{patient_id}"},
        onsetDateTime=f"{datetime.now().year - random.randint(1, 10)}-01-01T00:00:00Z"
    )


def build_fhir_query(query: str, intent: str, entities: List[Entity]) -> FHIRQueryResponse:
    """Convert natural language query to FHIR request and generate mock response"""
    
    # Extract parameters from entities
    condition = None
    age_threshold = None
    count = 10  # default
    
    for entity in entities:
        if entity.label == "CONDITION":
            condition = entity.text
        elif entity.label == "NUMBER":
            # Could be age or count - use context to determine
            num_value = int(entity.text)
            if num_value > 20 and num_value < 120:  # likely an age
                age_threshold = num_value
            elif num_value <= 100:  # likely a count
                count = min(num_value, 50)  # cap at 50 for demo
    
    # Build FHIR query parameters
    fhir_params = {
        "resourceType": "Patient"
    }
    
    if age_threshold:
        fhir_params["birthdate"] = f"le{datetime.now().year - age_threshold}"
    
    if condition:
        fhir_params["_has:Condition:patient:code"] = condition
    
    # Generate mock FHIR response
    patients = generate_mock_patients(count, condition, age_threshold)
    
    # Build bundle entries
    entries = []
    for patient in patients:
        patient_entry = {
            "fullUrl": f"http://example.com/fhir/Patient/{patient.id}",
            "resource": patient.dict()
        }
        entries.append(patient_entry)
        
        # Add condition if specified
        if condition:
            condition_resource = generate_mock_conditions(patient.id, condition)
            condition_entry = {
                "fullUrl": f"http://example.com/fhir/Condition/{condition_resource.id}",
                "resource": condition_resource.dict()
            }
            entries.append(condition_entry)
    
    # Create FHIR Bundle
    bundle = FHIRBundle(
        total=len(patients),
        entry=entries
    )
    
    return FHIRQueryResponse(
        query=query,
        intent=intent,
        entities=entities,
        fhir_request={
            "method": "GET",
            "url": "/Patient",
            "params": fhir_params
        },
        fhir_response=bundle
    )


@app.get("/")
def read_root():
    return {
        "message": "FastAPI Intent Extraction API with spaCy & FHIR Simulation",
        "endpoints": {
            "/extract-intent": "POST - Extract intent from query",
            "/analyze/{query}": "GET - Analyze query intent",
            "/fhir-query": "POST - Convert natural language to FHIR query and get mock data"
        }
    }


@app.post("/extract-intent", response_model=IntentResponse)
def extract_intent_endpoint(request: QueryRequest):
    """Extract intent from a given query using spaCy"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    result = extract_intent(request.query)
    return result


@app.post("/fhir-query", response_model=FHIRQueryResponse)
def fhir_query_endpoint(request: QueryRequest):
    """Convert natural language query to FHIR request and return mock FHIR data"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Extract intent and entities
    intent_result = extract_intent(request.query)
    
    # Build FHIR query and get mock response
    fhir_result = build_fhir_query(
        request.query,
        intent_result.intent,
        intent_result.entities
    )
    
    return fhir_result


@app.get("/analyze/{query}", response_model=IntentResponse)
def analyze_query(query: str):
    """Analyze query intent via GET request"""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    result = extract_intent(query)
    return result


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    """Original endpoint - optionally extract intent from query parameter"""
    response = {"item_id": item_id, "q": q}
    
    if q:
        intent_result = extract_intent(q)
        response["intent_analysis"] = intent_result
    
    return response