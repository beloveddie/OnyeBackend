from typing import Union, Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import pandas as pd
from anthropic import Anthropic
import os
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Healthcare FHIR Agent API", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjusted for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Load FHIR data into pandas DataFrames
def load_fhir_data():
    """Load FHIR JSON data and convert to pandas DataFrames"""
    with open('fhir_generated_data.json', 'r') as f:
        fhir_bundle = json.load(f)
    
    # Extract resources by type
    patients = []
    conditions = []
    medications = []
    medication_requests = []
    observations = []
    practitioners = []
    
    for entry in fhir_bundle['entry']:
        resource = entry['resource']
        resource_type = resource['resourceType']
        
        if resource_type == 'Patient':
            patients.append({
                'id': resource['id'],
                'name': f"{resource['name'][0]['given'][0]} {resource['name'][0]['family']}",
                'gender': resource['gender'],
                'birthDate': resource['birthDate'],
                'age': datetime.now().year - int(resource['birthDate'].split('-')[0])
            })
        elif resource_type == 'Condition':
            conditions.append({
                'id': resource['id'],
                'patient_id': resource['subject']['reference'].split('/')[1],
                'condition': resource['code']['text'],
                'status': resource['clinicalStatus']['coding'][0]['code'],
                'onset': resource.get('onsetDateTime', '')
            })
        elif resource_type == 'Medication':
            medications.append({
                'id': resource['id'],
                'name': resource['code']['text'],
                'status': resource['status'],
                'form': resource['form']['text']
            })
        elif resource_type == 'MedicationRequest':
            medication_requests.append({
                'id': resource['id'],
                'patient_id': resource['subject']['reference'].split('/')[1],
                'medication_id': resource['medicationReference']['reference'].split('/')[1],
                'status': resource['status'],
                'authored_date': resource.get('authoredOn', '')
            })
        elif resource_type == 'Observation':
            observations.append({
                'id': resource['id'],
                'patient_id': resource['subject']['reference'].split('/')[1],
                'code': resource['code']['text'],
                'value': resource.get('valueQuantity', {}).get('value', ''),
                'unit': resource.get('valueQuantity', {}).get('unit', ''),
                'date': resource.get('effectiveDateTime', '')
            })
        elif resource_type == 'Practitioner':
            practitioners.append({
                'id': resource['id'],
                'name': f"{resource['name'][0]['given'][0]} {resource['name'][0]['family']}",
                'gender': resource['gender']
            })
    
    return {
        'patients': pd.DataFrame(patients),
        'conditions': pd.DataFrame(conditions),
        'medications': pd.DataFrame(medications),
        'medication_requests': pd.DataFrame(medication_requests),
        'observations': pd.DataFrame(observations),
        'practitioners': pd.DataFrame(practitioners)
    }

# Load data on startup
fhir_data = load_fhir_data()


# Pydantic Models
class QueryRequest(BaseModel):
    query: str


class AgentResponse(BaseModel):
    query: str
    generated_code: str
    result: Any
    data: Optional[Dict[str, Any]] = None  # Structured data for visualizations
    natural_language_response: str
    execution_time: float


# Agent System Prompt
AGENT_SYSTEM_PROMPT = """You are a healthcare data analyst AI assistant with access to a FHIR database loaded as pandas DataFrames.

Available DataFrames:
1. `patients` - Columns: id, name, gender, birthDate, age
2. `conditions` - Columns: id, patient_id, condition, status, onset
3. `medications` - Columns: id, name, status, form
4. `medication_requests` - Columns: id, patient_id, medication_id, status, authored_date
5. `observations` - Columns: id, patient_id, code, value, unit, date
6. `practitioners` - Columns: id, name, gender

Your job is to:
1. Understand the user's natural language query about the FHIR data
2. Write pandas code to answer their question
3. Return ONLY the pandas code, no explanations

Rules:
- Use the DataFrame names as provided: patients, conditions, medications, medication_requests, observations, practitioners
- Write clean, efficient pandas code
- Handle edge cases (empty results, type conversions)
- **IMPORTANT: Always return the actual data/records, not just counts**
- For queries asking "how many", return the filtered DataFrame so we can count AND see the data
- For filtering, use boolean indexing
- Join DataFrames when needed using merge()
- Return the code wrapped in ```python and ``` markers
- Do NOT include print statements
- The code should evaluate to a result that can be displayed

Example queries:
- "How many patients have diabetes?" → patients.merge(conditions, left_on='id', right_on='patient_id')[conditions['condition'].str.contains('diabetes', case=False, na=False)][['name', 'gender', 'age', 'condition']].drop_duplicates()
- "List all female patients over 60" → patients[(patients['gender'] == 'female') & (patients['age'] > 60)]
- "What medications is patient-1 taking?" → medication_requests[medication_requests['patient_id'] == 'patient-1'].merge(medications, left_on='medication_id', right_on='id')[['name', 'status', 'form']]
- "Show me patients with hypertension" → patients.merge(conditions, left_on='id', right_on='patient_id')[conditions['condition'].str.contains('hypertension', case=False, na=False)][['name', 'gender', 'age', 'condition']]
"""


def generate_pandas_code(query: str) -> str:
    """Use Anthropic Claude to generate pandas code from natural language query"""
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.1,
            system=AGENT_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Write pandas code to answer this query: {query}"
                }
            ]
        )
        
        code = response.content[0].text.strip()
        
        # Extract code from markdown code blocks
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
        
        return code
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate code: {str(e)}")


def execute_pandas_code(code: str) -> Any:
    """Safely execute pandas code with access to FHIR DataFrames"""
    try:
        # Create a safe execution environment with only necessary globals
        safe_globals = {
            'pd': pd,
            'patients': fhir_data['patients'],
            'conditions': fhir_data['conditions'],
            'medications': fhir_data['medications'],
            'medication_requests': fhir_data['medication_requests'],
            'observations': fhir_data['observations'],
            'practitioners': fhir_data['practitioners'],
            'datetime': datetime
        }
        
        # Execute the code
        result = eval(code, safe_globals)
        
        # Convert result to serializable format
        if isinstance(result, pd.DataFrame):
            return result.to_dict('records')
        elif isinstance(result, pd.Series):
            return result.to_dict()
        elif hasattr(result, 'item'):  # numpy types
            return result.item()
        else:
            return result
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Code execution error: {str(e)}")


def generate_natural_language_response(query: str, result: Any) -> str:
    """Convert the pandas result back to natural language"""
    try:
        result_str = str(result)
        if len(result_str) > 2000:
            result_str = result_str[:2000] + "... (truncated)"
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            temperature=0.7,
            system="You are a helpful healthcare assistant. Convert the data analysis result into a clear, natural language response. Be concise but informative.",
            messages=[
                {
                    "role": "user",
                    "content": f"User query: {query}\n\nAnalysis result: {result_str}\n\nProvide a natural language response to the user's query based on this result."
                }
            ]
        )
        
        return response.content[0].text.strip()
    except Exception as e:
        return f"Result: {result}"


def format_data_for_visualization(result: Any, query: str) -> Dict[str, Any]:
    """Format result into visualization-friendly data structures"""
    data = {
        "type": None,
        "value": None,
        "count": None,
        "table": None,
        "chart": None,
        "cards": None
    }
    
    try:
        # Handle different result types
        if isinstance(result, (int, float)):
            # Single numeric value - good for cards and simple displays
            data["type"] = "numeric"
            data["value"] = result
            data["count"] = result
            data["cards"] = [{"label": query, "value": result}]
            
        elif isinstance(result, list) and len(result) > 0:
            # List of records (DataFrame.to_dict('records'))
            data["type"] = "table"
            data["count"] = len(result)
            data["table"] = {
                "columns": list(result[0].keys()) if result else [],
                "rows": result,
                "total": len(result)
            }
            
            # Try to extract numeric data for charts
            first_record = result[0]
            numeric_fields = [k for k, v in first_record.items() if isinstance(v, (int, float))]
            label_fields = [k for k, v in first_record.items() if isinstance(v, str)]
            
            if numeric_fields and label_fields:
                # Create chart data
                data["chart"] = {
                    "labels": [str(r.get(label_fields[0], '')) for r in result[:20]],  # Limit to 20 for readability
                    "datasets": [
                        {
                            "label": field,
                            "data": [r.get(field, 0) for r in result[:20]]
                        } for field in numeric_fields[:3]  # Limit to 3 datasets
                    ]
                }
            
            # Create summary cards with count
            summary_cards = [{"label": "Total Count", "value": len(result)}]
            
            if len(result) <= 10:
                summary_cards.extend([
                    {"label": f"Record {i+1}", "data": r}
                    for i, r in enumerate(result)
                ])
            else:
                summary_cards.extend([
                    {"label": "Showing", "value": f"{min(10, len(result))} of {len(result)} records"},
                    {"label": "First Record", "data": result[0]},
                    {"label": "Last Record", "data": result[-1]}
                ])
            
            data["cards"] = summary_cards
                
        elif isinstance(result, dict):
            # Dictionary result (Series.to_dict() or custom dict)
            data["type"] = "dict"
            data["count"] = len(result)
            data["table"] = {
                "columns": ["Key", "Value"],
                "rows": [{"Key": k, "Value": v} for k, v in result.items()],
                "total": len(result)
            }
            
            # Check if values are numeric for chart
            numeric_values = [v for v in result.values() if isinstance(v, (int, float))]
            if len(numeric_values) == len(result):
                data["chart"] = {
                    "labels": list(result.keys())[:20],
                    "datasets": [{
                        "label": "Values",
                        "data": list(result.values())[:20]
                    }]
                }
            
            # Create cards
            data["cards"] = [
                {"label": str(k), "value": v}
                for k, v in list(result.items())[:10]
            ]
            
        elif isinstance(result, list) and len(result) == 0:
            # Empty list
            data["type"] = "table"
            data["count"] = 0
            data["table"] = {
                "columns": [],
                "rows": [],
                "total": 0
            }
            data["cards"] = [{"label": "Total Count", "value": 0}]
            
        elif isinstance(result, str):
            # String result
            data["type"] = "text"
            data["value"] = result
            data["cards"] = [{"label": "Result", "value": result}]
            
        else:
            # Fallback
            data["type"] = "unknown"
            data["value"] = str(result)
            data["cards"] = [{"label": "Result", "value": str(result)}]
            
    except Exception as e:
        # If formatting fails, return basic structure
        data["type"] = "error"
        data["value"] = str(result)
        data["error"] = str(e)
    
    return data


@app.get("/")
def read_root():
    return {
        "message": "Healthcare FHIR Agent API with Anthropic Claude",
        "version": "2.0.0",
        "model": "claude-3-5-sonnet-20241022",
        "endpoints": {
            "/query": "POST - Query FHIR data using natural language",
            "/data-summary": "GET - Get summary of available data",
            "/health": "GET - Health check"
        },
        "features": [
            "Natural language to pandas queries",
            "Anthropic Claude-powered code generation",
            "FHIR R4 data support",
            "Natural language responses"
        ]
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_loaded": all(len(df) > 0 for df in fhir_data.values())
    }


@app.get("/data-summary")
def data_summary():
    """Get summary of loaded FHIR data"""
    return {
        "patients": len(fhir_data['patients']),
        "conditions": len(fhir_data['conditions']),
        "medications": len(fhir_data['medications']),
        "medication_requests": len(fhir_data['medication_requests']),
        "observations": len(fhir_data['observations']),
        "practitioners": len(fhir_data['practitioners']),
        "sample_queries": [
            "How many patients do we have?",
            "Show me all patients with diabetes",
            "What is the average age of patients?",
            "List all female patients over 60",
            "How many patients have hypertension?",
            "What medications are being prescribed?",
            "Show me patients with multiple conditions",
            "What are the most common conditions?",
            "List all observations for patient-1"
        ]
    }


@app.post("/query", response_model=AgentResponse)
def query_fhir_data(request: QueryRequest):
    """
    Query FHIR data using natural language.
    The AI agent will generate pandas code and return results in natural language.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Check for Anthropic API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY environment variable not set"
        )
    
    start_time = datetime.now()
    
    try:
        # Step 1: Generate pandas code using Anthropic Claude
        generated_code = generate_pandas_code(request.query)
        print(f"Generated Code:\n{generated_code}")
        
        # Step 2: Execute the code
        result = execute_pandas_code(generated_code)
        print(f"Execution Result:\n{result}")
        
        # Step 3: Convert result to natural language
        nl_response = generate_natural_language_response(request.query, result)
        print(f"Natural Language Response:\n{nl_response}")
        
        # Step 4: Format data for visualizations
        formatted_data = format_data_for_visualization(result, request.query)
        print(f"Formatted Data Type: {formatted_data.get('type')}")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgentResponse(
            query=request.query,
            generated_code=generated_code,
            result=result,
            data=formatted_data,
            natural_language_response=nl_response,
            execution_time=execution_time
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/query-simple/{query}")
def query_simple(query: str):
    """Simple GET endpoint for quick queries"""
    return query_fhir_data(QueryRequest(query=query))


# Example advanced endpoint with streaming
@app.post("/query-stream")
async def query_stream(request: QueryRequest):
    """
    Stream the agent's response in real-time (for future implementation)
    """
    # This could be implemented with Server-Sent Events or WebSockets
    # For now, return the standard response
    return query_fhir_data(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
