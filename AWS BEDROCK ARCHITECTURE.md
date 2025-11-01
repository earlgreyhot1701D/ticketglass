# TicketGlass - AWS Bedrock Architecture

**Status:** AWS Bedrock Native | SuperHack 2025  
**Tech Stack:** Python + boto3 + AWS Bedrock + Streamlit  
**Date:** 2025-10-28

---

## Why AWS Bedrock?

- ✅ **AWS Hackathon:** Native AWS service 
- ✅ **Scalable:** Designed for production AI workloads
- ✅ **Claude 3 access:** Latest Claude models via managed service
- ✅ **No API key management:** Uses AWS IAM credentials
- ✅ **Built-in observability:** CloudWatch integration
- ✅ **Enterprise ready:** Security, compliance, audit logs

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│ PRESENTATION LAYER (Streamlit)                      │
│ - Timeline view with agent reasoning                │
│ - Feedback widget (Yes/No)                          │
│ - Status tracker                                    │
└──────────────┬───────────────────────────────────────┘
               │ Local function calls
               ↓
┌─────────────────────────────────────────────────────┐
│ AGENT CORE LAYER (Pure Python)                      │
│ - Boto3 Bedrock client initialization               │
│ - Context-aware reasoning (reads history)           │
│ - Sentiment detection + tone matching               │
│ - Never repeats explanations (system prompt)        │
└──────────────┬───────────────────────────────────────┘
               │ boto3.invoke_model() calls
               ↓
┌─────────────────────────────────────────────────────┐
│ AWS BEDROCK LAYER (Managed Service)                 │
│ - Model: anthropic.claude-3-sonnet-20240229-v1:0    │
│ - Runtime: Fully managed by AWS                     │
│ - Scaling: Automatic                                │
│ - Billing: Pay per token                            │
└──────────────┬───────────────────────────────────────┘
               │ API calls
               ↓
┌─────────────────────────────────────────────────────┐
│ DATA LAYER (MVP)                                    │
│ - Mock tickets (8 samples)                          │
│ - DynamoDB-ready (post-MVP)                         │
│ - Adapter pattern for swapping data sources         │
└─────────────────────────────────────────────────────┘
```

---

## Core Files (AWS Bedrock Native)

### `agent/core.py` - Agent Engine
```python
import boto3
import json

class Agent:
    def __init__(self, system_prompt: str, model_id: str, aws_region: str = "us-east-1"):
        """Initialize agent with AWS Bedrock client."""
        self.system_prompt = system_prompt
        self.model_id = model_id
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=aws_region)
    
    def invoke_bedrock(self, messages: list) -> str:
        """Call AWS Bedrock Claude model."""
        response = self.bedrock_client.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-06-01",
                "max_tokens": 1024,
                "system": self.system_prompt,
                "messages": messages
            })
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
```

### `agent/prompts.py` - System Prompt
```python
SYSTEM_PROMPT = """You are TicketGlass, an autonomous IT support agent.

Your role:
- Read context history (what we already tried)
- Never repeat previous explanations
- Detect user frustration and adapt tone
- Suggest next escalation steps if needed
- Provide warm, transparent communication

Voice: "We/team", professional-casual tone with emojis when appropriate.

Key principle: Always acknowledge when previous attempts didn't work and 
explain why we're trying something different."""
```

### `data/adapters.py` - Data Layer (Swappable)
```python
from abc import ABC, abstractmethod

class TicketDataAdapter(ABC):
    """Abstract adapter - swap implementations."""
    
    @abstractmethod
    def fetch_ticket_state(self, ticket_id: str) -> dict:
        pass
    
    @abstractmethod
    def store_feedback(self, ticket_id: str, feedback: dict) -> None:
        pass

class MockTicketAdapter(TicketDataAdapter):
    """MVP: In-memory mock data."""
    
    def __init__(self):
        self.tickets = get_mock_tickets()
    
    def fetch_ticket_state(self, ticket_id: str) -> dict:
        return self.tickets.get(ticket_id)

class DynamoDBAdapter(TicketDataAdapter):
    """Production: AWS DynamoDB (post-MVP)."""
    
    def __init__(self, table_name: str, region: str = "us-east-1"):
        import boto3
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
```

---

## Running Locally (MVP)

```bash
# Install dependencies
pip install -r requirements.txt

# Set AWS credentials (via environment or ~/.aws/credentials)
export AWS_REGION=us-east-1

# Run Streamlit app
streamlit run ui/app.py
```

**Note:** Requires AWS credentials with Bedrock permissions.

---

## Deployment Path (Post-MVP)

### Phase 1 (Current): Local Streamlit
- Use mock data
- AWS Bedrock API calls
- Perfect for demo

### Phase 2: AWS Lambda
```python
# Lambda handler
def lambda_handler(event, context):
    ticket_id = event['ticket_id']
    adapter = DynamoDBAdapter('TicketGlassTable')
    agent = Agent(SYSTEM_PROMPT, BEDROCK_MODEL_ID)
    
    ticket = adapter.fetch_ticket_state(ticket_id)
    result = agent.process_ticket(ticket)
    
    return {'statusCode': 200, 'body': json.dumps(result)}
```

### Phase 3: AWS API Gateway + Lambda
- REST endpoints
- Scale seamlessly
- Agent core unchanged

### Phase 4: Multi-tenant with Cognito
- User authentication
- Per-tenant DynamoDB tables
- Same agent logic

---

## AWS Bedrock Model

**Model:** `anthropic.claude-3-sonnet-20240229-v1:0`

**Why Sonnet:**
- ✅ Great quality/speed ratio
- ✅ Good for agentic tasks
- ✅ Cost-effective
- ✅ Faster than Opus for MVP

**Billing:** Pay per token (input/output)

---

## AWS Services Used (MVP → Production)

| Service | MVP | Phase 2 | Phase 3+ | Purpose |
|---------|-----|---------|----------|---------|
| Bedrock | ✅ | ✅ | ✅ | AI reasoning |
| Lambda | ❌ | ✅ | ✅ | Serverless compute |
| DynamoDB | ❌ | ✅ | ✅ | Data storage |
| API Gateway | ❌ | ❌ | ✅ | REST endpoints |
| CloudWatch | ❌ | ✅ | ✅ | Logging/monitoring |
| Cognito | ❌ | ❌ | ✅ | Authentication |

---

## No Vendor Lock-in

**Swappable components:**
- Change model: Update `model_id` (supports multiple Bedrock models)
- Change data store: Swap `DynamoDBAdapter` for any database
- Change AI: Swap Bedrock for Anthropic API, Azure, Google (agent core unchanged)

**Architecture principle:** Bedrock is implementation detail, not core logic.

---

## Success Criteria

✅ Agent logic works with AWS Bedrock  
✅ Credentials via IAM (no hardcoded keys)  
✅ Streamlit demo works locally  
✅ Ready to deploy to Lambda  
✅ Code is clean, testable, documented  

---

## Questions?

See `BUILD_PLAN.md` for phase breakdown.  
See `POST_MVP_ROADMAP_CTO_CONSOLIDATED.md` for scaling path.
