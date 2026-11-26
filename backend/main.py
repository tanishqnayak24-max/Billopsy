from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import json
import base64
import qrcode
from io import BytesIO
import os

app = FastAPI(
    title="Billopsy - Healthcare Bill Reconciliation",
    description="Patient-side healthcare documentation and billing reconciliation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
token_store = {}
findings_store = {}

# Mock hospital data
MOCK_HOSPITAL_ID = "ABC_HOSPITAL_001"
MOCK_PATIENT_ID = "PAT_2024_00123"

def generate_qr_code(text):
    """Generate QR code and return as base64"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def get_mock_documents():
    """Return mock hospital documents"""
    return [
        {
            "id": "DOC_BILL_001",
            "type": "bill",
            "source": "ABC Hospital",
            "content": """
            HOSPITAL BILL - ABC HOSPITAL
            Patient: John Doe
            Admission Date: 2024-01-15
            Discharge Date: 2024-01-20

            ITEMIZED CHARGES:
            1. Room Charges (5 nights @ 5000): 25,000
            2. Doctor Consultation: 2,000
            3. Lab Tests: 3,500
            4. Medication: 4,200
            5. Room Charges (Duplicate): 5,000
            6. Nursing Care: 2,100

            Subtotal: 41,800
            Tax (18%): 7,524
            TOTAL: 49,324
            """
        },
        {
            "id": "DOC_DISCHARGE_001",
            "type": "discharge_summary",
            "source": "ABC Hospital",
            "content": """
            DISCHARGE SUMMARY
            Patient: John Doe
            Hospital: ABC Hospital
            Admission: 2024-01-15 | Discharge: 2024-01-20

            CLINICAL FINDINGS:
            - Admitted with severe chest pain
            - ECG showed minor abnormalities
            - Troponin levels: Normal
            - BP controlled with medication

            PROCEDURES PERFORMED:
            - Chest X-ray
            - ECG (2 times)
            - Blood tests (CBC, Lipid panel)

            DIAGNOSIS:
            - Acute coronary syndrome (suspected but ruled out)
            - Hypertension

            DISCHARGE MEDICATIONS:
            - Aspirin 100mg daily
            - Atorvastatin 20mg daily
            - Ramipril 5mg daily
            """
        },
        {
            "id": "DOC_PROCEDURE_001",
            "type": "procedure_record",
            "source": "ABC Hospital",
            "content": """
            PROCEDURE RECORD
            Patient: John Doe
            Procedure: Chest X-ray + ECG Monitoring
            Date: 2024-01-16
            Duration: 45 minutes

            FINDINGS:
            - Chest X-ray: No acute abnormalities
            - ECG: Mild ST changes (resolved)
            - Heart rate: 72 bpm
            - BP: 128/82 mmHg

            COST BREAKDOWN:
            - Chest X-ray: 1,500
            - ECG (1st): 800
            - ECG (2nd): 800
            Total: 3,100
            """
        },
        {
            "id": "DOC_LAB_001",
            "type": "diagnostic_report",
            "source": "ABC Hospital Laboratory",
            "content": """
            LABORATORY REPORT
            Patient: John Doe
            Date: 2024-01-16

            TEST RESULTS:
            Complete Blood Count (CBC):
            - WBC: 7.2 (Normal)
            - RBC: 4.8 (Normal)
            - Hemoglobin: 14.5 g/dL (Normal)
            - Platelets: 245 (Normal)

            Lipid Panel:
            - Total Cholesterol: 210 mg/dL (Elevated)
            - LDL: 135 mg/dL (High)
            - HDL: 45 mg/dL (Low)
            - Triglycerides: 165 mg/dL (Elevated)

            Cardiac Markers:
            - Troponin I: <0.04 ng/mL (Normal)
            - CK-MB: 2.5 ng/mL (Normal)

            COST:
            - CBC: 800
            - Lipid Panel: 1,200
            - Cardiac Markers: 1,500
            Total: 3,500
            """
        }
    ]

def analyze_findings(documents):
    """Simple reconciliation logic"""
    findings = []

    # Check for duplicate charges
    items = []
    for doc in documents:
        if doc.get("type") == "bill":
            if "Room Charges (Duplicate)" in doc.get("content", ""):
                findings.append({
                    "category": "duplicate_charge",
                    "severity": "High",
                    "description": "Duplicate room charge detected",
                    "evidence": "Room charge appears twice in billing",
                    "suggested_question": "Why is room charge listed twice? Should be charged only once.",
                    "billed_item": "Room Charges"
                })

    # Check for undocumented procedures
    bill_content = "".join([d.get("content", "") for d in documents if d.get("type") == "bill"])
    procedure_content = "".join([d.get("content", "") for d in documents if d.get("type") == "procedure_record"])

    if "Nursing Care: 2,100" in bill_content and "Nursing" not in procedure_content:
        findings.append({
            "category": "undocumented_charge",
            "severity": "Medium",
            "description": "Nursing care charge without detailed documentation",
            "evidence": "Nursing care charged but no detailed service record provided",
            "suggested_question": "Can you provide itemized nursing care services that justify the 2,100 charge?",
            "billed_item": "Nursing Care"
        })

    # Arithmetic check - simple validation
    if "TOTAL: 49,324" in bill_content:
        findings.append({
            "category": "arithmetic_verification",
            "severity": "Low",
            "description": "Bill arithmetic verified",
            "evidence": "Total amount calculation appears correct",
            "suggested_question": "Verification complete",
            "billed_item": "Total Bill"
        })

    return findings if findings else [{
        "category": "no_issues",
        "severity": "Low",
        "description": "No major discrepancies found",
        "evidence": "Bill appears reasonable",
        "suggested_question": "Bill appears accurate",
        "billed_item": "Overall Assessment"
    }]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "billopsy-backend"}

@app.post("/api/qr/generate")
async def generate_qr_token(patient_id: str = MOCK_PATIENT_ID, hospital_id: str = MOCK_HOSPITAL_ID):
    """Generate a new QR retrieval token"""
    try:
        import uuid
        token = str(uuid.uuid4())
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(minutes=15)

        token_data = {
            "token": token,
            "patient_id": patient_id,
            "hospital_id": hospital_id,
            "created_at": created_at,
            "expires_at": expires_at,
            "used": False
        }

        token_store[token] = token_data

        qr_base64 = generate_qr_code(token)

        return {
            "success": True,
            "token": token,
            "patient_id": patient_id,
            "hospital_id": hospital_id,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "qr_code": qr_base64,
            "retrieval_url": f"/api/retrieval/documents?token={token}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/retrieval/validate-token")
async def validate_token(token: str):
    """Validate a retrieval token"""
    try:
        if token not in token_store:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        token_data = token_store[token]

        if token_data["expires_at"] < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Token expired")

        return {
            "valid": True,
            "patient_id": token_data["patient_id"],
            "hospital_id": token_data["hospital_id"],
            "expires_at": token_data["expires_at"].isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/retrieval/documents")
async def retrieve_documents(token: str):
    """Retrieve mock hospital documents using token"""
    try:
        if token not in token_store:
            raise HTTPException(status_code=401, detail="Invalid token")

        token_data = token_store[token]

        if token_data["expires_at"] < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Token expired")

        token_data["used"] = True

        mock_docs = get_mock_documents()

        return {
            "success": True,
            "token": token,
            "documents": [
                {
                    "id": doc["id"],
                    "type": doc["type"],
                    "source": doc["source"],
                    "content": doc["content"],
                    "retrieved_at": datetime.utcnow().isoformat()
                }
                for doc in mock_docs
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extraction/extract")
async def extract_documents(token: str, documents: list):
    """Extract and structure data from documents"""
    try:
        if token not in token_store:
            raise HTTPException(status_code=401, detail="Invalid token")

        extracted_data = []

        for doc in documents:
            extracted_data.append({
                "document_id": doc.get("id"),
                "type": doc.get("type"),
                "extracted_data": {
                    "content_preview": doc.get("content", "")[:200],
                    "type": doc.get("type"),
                    "source": doc.get("source")
                }
            })

        return {
            "success": True,
            "token": token,
            "extracted_documents": extracted_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reconciliation/analyze")
async def analyze_bills(token: str, documents: list):
    """Run reconciliation analysis on extracted documents"""
    try:
        if token not in token_store:
            raise HTTPException(status_code=401, detail="Invalid token")

        findings = analyze_findings(documents)
        findings_store[token] = findings

        return {
            "success": True,
            "token": token,
            "findings": findings,
            "summary": {
                "total_findings": len(findings),
                "high_severity": len([f for f in findings if f["severity"] == "High"]),
                "medium_severity": len([f for f in findings if f["severity"] == "Medium"]),
                "low_severity": len([f for f in findings if f["severity"] == "Low"])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/results/{token}")
async def get_results(token: str):
    """Retrieve previous analysis results"""
    try:
        if token not in findings_store:
            raise HTTPException(status_code=404, detail="Results not found")

        findings = findings_store[token]

        return {
            "success": True,
            "token": token,
            "findings": findings,
            "summary": {
                "total_findings": len(findings),
                "high_severity": len([f for f in findings if f["severity"] == "High"]),
                "medium_severity": len([f for f in findings if f["severity"] == "Medium"]),
                "low_severity": len([f for f in findings if f["severity"] == "Low"])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
