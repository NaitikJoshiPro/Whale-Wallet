"""
AI Concierge API Endpoints

White-glove AI-powered support interface for Whale Wallet users.
Provides technical assistance, transaction analysis, and
personalized recommendations.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.v1.auth import get_current_user
from app.config import get_settings, Settings

logger = structlog.get_logger(__name__)
router = APIRouter()


# === Schemas ===

class ChatMessage(BaseModel):
    """Individual chat message."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict | None = None


class ConversationRequest(BaseModel):
    """New message in a conversation."""
    message: str
    conversation_id: UUID | None = None
    context: dict | None = None  # Optional context like current screen


class ConversationResponse(BaseModel):
    """Response from the concierge."""
    conversation_id: UUID
    message: ChatMessage
    suggested_actions: list[dict] | None = None
    escalate_to_human: bool = False


class TransactionAnalysisRequest(BaseModel):
    """Request to analyze a specific transaction."""
    chain: str
    tx_hash: str | None = None
    contract_address: str | None = None
    raw_data: str | None = None


class TransactionAnalysis(BaseModel):
    """AI analysis of a transaction or contract."""
    summary: str
    risk_assessment: str
    detailed_explanation: str
    recommendations: list[str]
    similar_scams: list[dict] | None = None


class PolicyRecommendation(BaseModel):
    """AI-recommended policy based on user behavior."""
    rule_type: str
    name: str
    rationale: str
    config: dict
    confidence: float


# === Endpoints ===

@router.post("/chat", response_model=ConversationResponse)
async def chat_with_concierge(
    request: ConversationRequest,
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
) -> ConversationResponse:
    """
    Send a message to the AI concierge.
    
    The concierge can help with:
    - Technical questions about crypto and DeFi
    - Transaction analysis and risk assessment
    - Policy configuration recommendations
    - Bridge and swap routing assistance
    - General wallet usage questions
    
    For complex issues, the concierge may escalate to a human agent.
    """
    if not settings.enable_ai_concierge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI Concierge feature not enabled"
        )
    
    # Check tier - Blue tier gets priority
    tier = current_user.get("tier", "orca")
    
    logger.info(
        "Concierge chat message",
        user_id=current_user["user_id"],
        tier=tier,
        conversation_id=str(request.conversation_id) if request.conversation_id else "new"
    )
    
    conversation_id = request.conversation_id or uuid4()
    
    # In production, this would:
    # 1. Load conversation history from memory
    # 2. Build context with user's wallet state, policies, etc.
    # 3. Call LLM with appropriate system prompt
    # 4. Parse response and extract actions
    # 5. Save to memory for future context
    
    # Mock response
    response_content = await _generate_ai_response(
        request.message,
        current_user,
        settings
    )
    
    return ConversationResponse(
        conversation_id=conversation_id,
        message=ChatMessage(
            role="assistant",
            content=response_content
        ),
        suggested_actions=[
            {
                "type": "policy_suggestion",
                "label": "Add velocity limit",
                "action": "create_policy",
                "params": {"rule_type": "velocity"}
            }
        ] if "policy" in request.message.lower() else None,
        escalate_to_human=False
    )


@router.post("/chat/stream")
async def chat_with_concierge_stream(
    request: ConversationRequest,
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
):
    """
    Stream a response from the AI concierge.
    
    Returns a Server-Sent Events stream for real-time response display.
    This provides a better UX for longer responses.
    """
    if not settings.enable_ai_concierge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI Concierge feature not enabled"
        )
    
    async def generate():
        # In production, stream from LLM
        # For now, simulate streaming
        response = await _generate_ai_response(request.message, current_user, settings)
        
        # Simulate word-by-word streaming
        words = response.split(" ")
        for i, word in enumerate(words):
            yield f"data: {word}"
            if i < len(words) - 1:
                yield " "
        yield "\n\ndata: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.post("/analyze/transaction", response_model=TransactionAnalysis)
async def analyze_transaction(
    request: TransactionAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
) -> TransactionAnalysis:
    """
    Get AI analysis of a transaction or contract.
    
    This provides:
    - Plain English explanation of what the transaction does
    - Risk assessment with specific concerns
    - Comparison to known scam patterns
    - Recommendations for proceeding
    """
    if not settings.enable_ai_concierge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI Concierge feature not enabled"
        )
    
    logger.info(
        "Transaction analysis requested",
        user_id=current_user["user_id"],
        chain=request.chain,
        tx_hash=request.tx_hash
    )
    
    # In production:
    # 1. Fetch transaction/contract data from chain
    # 2. Decode function calls and parameters
    # 3. Check against known malicious contract database
    # 4. Generate AI explanation and risk assessment
    
    return TransactionAnalysis(
        summary="This transaction approves the Uniswap V3 Router to spend unlimited USDC from your wallet.",
        risk_assessment="MEDIUM - Unlimited approval to verified contract",
        detailed_explanation="""
This is a standard ERC-20 approval transaction that grants the Uniswap V3 Router 
contract permission to move USDC tokens on your behalf. This is required before 
you can swap USDC on Uniswap.

The approval amount is set to the maximum (unlimited), which is common practice 
but does carry some risk if the approved contract is ever compromised.

The Uniswap V3 Router (0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45) is a 
well-audited, widely-used contract by Uniswap Labs.
        """.strip(),
        recommendations=[
            "Consider using a limited approval amount instead of unlimited",
            "This is a verified contract - proceeding is generally safe",
            "Monitor your USDC balance after approval"
        ],
        similar_scams=None
    )


@router.post("/analyze/contract", response_model=TransactionAnalysis)
async def analyze_contract(
    request: TransactionAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
) -> TransactionAnalysis:
    """
    Get AI analysis of a smart contract before interacting with it.
    
    Provides security assessment of the contract's code and permissions.
    """
    if not request.contract_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="contract_address is required"
        )
    
    # In production, decompile and analyze contract code
    
    return TransactionAnalysis(
        summary="Verified Uniswap V3 Router contract",
        risk_assessment="LOW - Well-audited protocol contract",
        detailed_explanation="""
This contract is the official Uniswap V3 SwapRouter deployed by Uniswap Labs.

Key characteristics:
- Source code is verified on Etherscan
- Multiple professional audits completed
- High Total Value Locked (TVL) - $5B+ across pools
- No admin keys or upgrade capabilities after deployment

This is one of the most battle-tested contracts in DeFi.
        """.strip(),
        recommendations=[
            "Safe to interact with this contract",
            "Always verify you're interacting with the correct address"
        ]
    )


@router.get("/recommendations/policies", response_model=list[PolicyRecommendation])
async def get_policy_recommendations(
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
) -> list[PolicyRecommendation]:
    """
    Get AI-generated policy recommendations based on user behavior.
    
    The AI analyzes:
    - Transaction patterns
    - Current policies
    - Account balance and tier
    - Common attack vectors
    
    And suggests policies that would improve security.
    """
    if not settings.enable_ai_concierge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI Concierge feature not enabled"
        )
    
    # In production, analyze user's transaction history and current policies
    
    return [
        PolicyRecommendation(
            rule_type="velocity",
            name="Daily Spending Limit",
            rationale="Based on your transaction history, you rarely transfer more than $20,000 in a day. A limit would protect against draining attacks.",
            config={
                "max_daily_usd": 25000,
                "require_2fa_above_usd": 10000
            },
            confidence=0.85
        ),
        PolicyRecommendation(
            rule_type="whitelist",
            name="Known Addresses Only",
            rationale="You primarily interact with 5 addresses. Whitelisting would block transfers to unknown addresses.",
            config={
                "mode": "warn_unknown",
                "quarantine_hours_for_new": 24
            },
            confidence=0.72
        )
    ]


@router.post("/escalate")
async def escalate_to_human(
    conversation_id: UUID,
    reason: str,
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
) -> dict:
    """
    Escalate conversation to a human concierge.
    
    Available for Blue tier members only.
    Human concierge operates during business hours (9 AM - 6 PM UTC).
    """
    tier_limits = settings.tier_limits.get(current_user["tier"], {})
    
    if not tier_limits.get("concierge"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Human concierge is only available for Blue tier members"
        )
    
    logger.info(
        "Escalating to human concierge",
        user_id=current_user["user_id"],
        conversation_id=str(conversation_id),
        reason=reason
    )
    
    return {
        "status": "escalated",
        "conversation_id": str(conversation_id),
        "message": "A human concierge will join this conversation shortly. Expected wait time: 5-10 minutes.",
        "ticket_id": f"TKT-{uuid4().hex[:8].upper()}"
    }


# === Helper Functions ===

async def _generate_ai_response(
    message: str,
    current_user: dict,
    settings: Settings
) -> str:
    """
    Generate AI response using configured LLM.
    
    In production, this would:
    1. Build context from user's wallet state
    2. Load conversation history
    3. Call Anthropic Claude or other LLM
    4. Parse and validate response
    """
    # Mock response based on message content
    message_lower = message.lower()
    
    if "bridge" in message_lower:
        return """To bridge assets between chains, I recommend using well-established bridges. For your current holdings:

**ETH to Arbitrum/Optimism**: Use the official bridges (bridge.arbitrum.io or app.optimism.io)
**Cross-chain**: Stargate or Across Protocol offer good liquidity

Would you like me to check the current bridge fees for a specific amount?"""
    
    elif "policy" in message_lower or "limit" in message_lower:
        return """I can help you set up protective policies. Based on your account, I recommend:

1. **Velocity Limit**: Cap daily transfers at $50,000 to prevent draining attacks
2. **Time Lock**: Block transfers between 11 PM - 6 AM as extra protection
3. **Whitelist Mode**: Require confirmation for new addresses

Would you like me to create any of these policies for you?"""
    
    elif "inheritance" in message_lower or "heir" in message_lower:
        return """Whale Wallet's Sovereign Inheritance feature ensures your crypto passes to your heirs safely.

**How it works**:
1. You designate guardians (3 recommended)
2. Each guardian holds a key shard
3. If you don't authenticate for 180 days (customizable), recovery initiates
4. Guardians combine shards to access funds

No lawyers or probate required. Would you like to configure this now?"""
    
    else:
        return f"""I'm your Whale Wallet concierge. I can help you with:

• **Security**: Set up policies, analyze transactions, configure duress mode
• **Operations**: Bridge assets, optimize gas, manage approvals  
• **Planning**: Configure inheritance, rotate keys, export reports

What would you like assistance with today?"""
