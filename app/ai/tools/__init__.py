"""
AI Tools

Tools available to the AI concierge for taking actions
and retrieving information.
"""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ToolDefinition:
    """Definition of a tool available to the AI."""
    name: str
    description: str
    parameters: dict
    handler: Callable | None = None


# Define available tools
AVAILABLE_TOOLS = [
    ToolDefinition(
        name="query_balance",
        description="Get the current balance of any token on any supported chain. "
                    "Use this to check how much of a token the user has.",
        parameters={
            "type": "object",
            "properties": {
                "chain": {
                    "type": "string",
                    "description": "The blockchain to query",
                    "enum": ["ethereum", "bitcoin", "solana", "arbitrum", "optimism", "base"]
                },
                "token": {
                    "type": "string",
                    "description": "Token symbol (e.g., 'ETH', 'USDC') or contract address"
                }
            },
            "required": ["chain"]
        }
    ),
    
    ToolDefinition(
        name="get_transaction_history",
        description="Retrieve recent transaction history for the user. "
                    "Can filter by chain or time period.",
        parameters={
            "type": "object",
            "properties": {
                "chain": {
                    "type": "string",
                    "description": "Filter by blockchain (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of transactions to return",
                    "default": 10
                },
                "days": {
                    "type": "integer",
                    "description": "Only return transactions from last N days",
                    "default": 30
                }
            }
        }
    ),
    
    ToolDefinition(
        name="simulate_transaction",
        description="Simulate a transaction to preview its effects before signing. "
                    "Shows balance changes, approvals granted, and risks.",
        parameters={
            "type": "object",
            "properties": {
                "chain": {
                    "type": "string",
                    "description": "The blockchain for the transaction"
                },
                "to": {
                    "type": "string",
                    "description": "Destination address"
                },
                "value": {
                    "type": "string",
                    "description": "Value to send in native units"
                },
                "data": {
                    "type": "string",
                    "description": "Transaction data for contract calls (optional)"
                }
            },
            "required": ["chain", "to"]
        }
    ),
    
    ToolDefinition(
        name="get_current_policies",
        description="Get the user's currently active security policies. "
                    "Use this to understand what rules govern their transactions.",
        parameters={
            "type": "object",
            "properties": {}
        }
    ),
    
    ToolDefinition(
        name="suggest_policy",
        description="Generate a policy recommendation based on user behavior. "
                    "Analyze patterns and suggest protective rules.",
        parameters={
            "type": "object",
            "properties": {
                "policy_type": {
                    "type": "string",
                    "description": "Type of policy to suggest",
                    "enum": ["velocity", "whitelist", "timelock", "chain"]
                },
                "context": {
                    "type": "string",
                    "description": "Additional context for the recommendation"
                }
            },
            "required": ["policy_type"]
        }
    ),
    
    ToolDefinition(
        name="get_gas_prices",
        description="Get current gas prices across supported chains. "
                    "Helps users decide when to transact for lower fees.",
        parameters={
            "type": "object",
            "properties": {
                "chains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of chains to check (default: all)"
                }
            }
        }
    ),
    
    ToolDefinition(
        name="get_token_price",
        description="Get the current price of a token in USD.",
        parameters={
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "Token symbol (e.g., 'ETH', 'BTC', 'SOL')"
                }
            },
            "required": ["token"]
        }
    ),
    
    ToolDefinition(
        name="analyze_contract",
        description="Analyze a smart contract for security risks. "
                    "Checks verification status, known exploits, and permissions.",
        parameters={
            "type": "object",
            "properties": {
                "chain": {
                    "type": "string",
                    "description": "The blockchain where the contract is deployed"
                },
                "address": {
                    "type": "string",
                    "description": "The contract address"
                }
            },
            "required": ["chain", "address"]
        }
    ),
    
    ToolDefinition(
        name="get_bridge_routes",
        description="Find optimal bridge routes between chains for a token. "
                    "Compares fees, speed, and security of different bridges.",
        parameters={
            "type": "object",
            "properties": {
                "from_chain": {
                    "type": "string",
                    "description": "Source chain"
                },
                "to_chain": {
                    "type": "string",
                    "description": "Destination chain"
                },
                "token": {
                    "type": "string",
                    "description": "Token to bridge"
                },
                "amount": {
                    "type": "string",
                    "description": "Amount to bridge"
                }
            },
            "required": ["from_chain", "to_chain", "token", "amount"]
        }
    ),
    
    ToolDefinition(
        name="escalate_to_human",
        description="Escalate the conversation to a human concierge. "
                    "Use for complex issues or when explicitly requested.",
        parameters={
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Reason for escalation"
                },
                "priority": {
                    "type": "string",
                    "description": "Priority level",
                    "enum": ["normal", "urgent", "critical"]
                }
            },
            "required": ["reason"]
        }
    )
]


async def execute_tool(tool_name: str, params: dict) -> Any:
    """
    Execute a tool by name with given parameters.
    
    In production, this dispatches to actual implementations.
    """
    # Tool implementations would go here
    # For now, return mock data
    
    if tool_name == "query_balance":
        return {
            "chain": params.get("chain"),
            "balances": [
                {"token": "ETH", "balance": "10.5", "usd_value": "25000"},
                {"token": "USDC", "balance": "50000", "usd_value": "50000"}
            ]
        }
    
    elif tool_name == "get_gas_prices":
        return {
            "ethereum": {"fast": 25, "standard": 20, "slow": 15},
            "arbitrum": {"fast": 0.1, "standard": 0.1, "slow": 0.1},
            "optimism": {"fast": 0.001, "standard": 0.001, "slow": 0.001}
        }
    
    elif tool_name == "get_token_price":
        prices = {
            "ETH": 2500, "BTC": 45000, "SOL": 100,
            "USDC": 1, "USDT": 1
        }
        token = params.get("token", "").upper()
        return {"token": token, "price_usd": prices.get(token, 0)}
    
    return {"error": f"Tool {tool_name} not implemented"}
