# TicketGlass Tech Stack - CLEAR STATEMENT

**Date:** 2025-10-28  
**Hackathon:** SuperHack 2025 (AWS-focused)  
**Status:** AWS Bedrock Native ✅

---

## OUR TECH STACK

### Backend / AI Engine
- **AWS Bedrock** (managed LLM service)
- **Claude 3 Sonnet** (via Bedrock)
- **boto3** (AWS SDK for Python)
- **Python 3.10+**

### Frontend / UI
- **Streamlit** (simple, fast web UI)
- **Local development** (no cloud needed for MVP)

### Data
- **Mock data** (MVP - in-memory)
- **DynamoDB** (post-MVP production)

### Deployment (Post-MVP)
- **AWS Lambda** (serverless compute)
- **AWS API Gateway** (REST endpoints)
- **AWS CloudWatch** (logging)
- **AWS Cognito** (authentication - future)

---

## Why THIS Stack for THIS Hackathon

| Choice | Why |
|--------|-----|
| AWS Bedrock | ✅ AWS hackathon → AWS services required |
| Claude 3 Sonnet | ✅ Best quality/speed ratio for agentic tasks |
| boto3 | ✅ Native Python AWS SDK |
| Streamlit | ✅ Fast UI prototyping, perfect for MVP |
| DynamoDB | ✅ Serverless DB, scales automatically, cheap |
| Lambda | ✅ Pay only for execution, no server ops |

---

## NOT Our Stack

- ❌ **Anthropic SDK** (we use AWS Bedrock instead)
- ❌ **OpenAI API** (we use AWS Bedrock)
- ❌ **Google Vertex AI** (we use AWS Bedrock)
- ❌ **Local LLM** (we use managed AWS Bedrock)

---

## Code Example (AWS Bedrock Native)

```python
import boto3

# Initialize Bedrock client (handles AWS auth automatically)
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# Call Claude via Bedrock
response = bedrock.invoke_model(
    modelId='anthropic.claude-3-sonnet-20240229-v1:0',
    body=json.dumps({
        "anthropic_version": "bedrock-2023-06-01",
        "max_tokens": 1024,
        "system": "You are an IT support agent...",
        "messages": [{"role": "user", "content": "Help with my ticket..."}]
    })
)

# Extract response
result = json.loads(response['body'].read())
print(result['content'][0]['text'])
```

**Key:** All AWS auth is handled by boto3 + IAM. No API key management.

---

## MVP vs Production

### MVP (Current)
- Streamlit UI (localhost)
- AWS Bedrock for AI
- Mock data (in-memory)
- No deployment needed
- Runs on your machine

### Post-MVP Production (If Hackathon Wins)
- Same agent logic
- Replace mock data → DynamoDB
- Wrap agent in Lambda function
- Add API Gateway for REST endpoints
- Deploy to AWS account
- **Agent core: UNCHANGED**

---

## Deployment Checklist

```
✅ Use AWS Bedrock for AI reasoning
✅ Use boto3 for AWS integration
✅ Use Streamlit for local MVP demo
✅ Mock data for MVP demo
✅ Architecture diagram shows DynamoDB + Lambda post-MVP
✅ Code shows AWS Bedrock model ID (anthropic.claude-3-*)
✅ Credentials handled via AWS IAM (not hardcoded)
✅ Ready to deploy to Lambda without refactoring
```

---

## Files That Reference AWS Bedrock

- ✅ `agent/core.py` - Uses boto3 bedrock-runtime client
- ✅ `agent/prompts.py` - Bedrock-compatible prompts
- ✅ `data/adapters.py` - Swappable, includes DynamoDBAdapter
- ✅ `data/mock_tickets.py` - Data independent of backend
- ✅ `ui/app.py` - Will import and use agent/core.py

---

## Credentials Setup

```bash
# Option 1: AWS CLI configured (easiest)
aws configure
# (enters AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, region)

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=xxxxx
export AWS_SECRET_ACCESS_KEY=xxxxx
export AWS_REGION=us-east-1

# Option 3: IAM role (Lambda/EC2 - automatic)
# No setup needed when running on AWS

# Python will automatically use configured credentials
import boto3
client = boto3.client('bedrock-runtime')  # Uses credentials above
```

---

## Bottom Line

**We are 100% AWS Bedrock native.**

No Anthropic SDK. No manual API keys. No vendor lock-in.

Just pure AWS services, scalable from day 1.

Perfect for SuperHack 2025. ✅
