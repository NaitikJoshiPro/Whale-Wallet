"""
Prompt Templates

Reusable prompt templates for specific AI tasks
like transaction analysis and policy recommendations.
"""


ANALYSIS_PROMPT = """Analyze this blockchain transaction:

**Chain**: {chain}
**To Address**: {to_address}
**Value**: {value} ({value_usd} USD)
**Contract Interaction**: {is_contract}
**Function**: {function_name}
**Contract Verified**: {contract_verified}

**Decoded Parameters**:
{parameters}

**Simulation Result**:
{simulation_result}

Provide your analysis in this format:

## Summary
A 1-2 sentence plain English explanation of what this transaction does.

## Risk Assessment
Rate as LOW / MEDIUM / HIGH / CRITICAL with brief justification.

## Detailed Explanation
- What exactly will happen when this transaction executes?
- What permissions or approvals are being granted?
- Are there any time-sensitive elements?

## Warnings
List any specific concerns:
- ⚠️ Warning 1
- ⚠️ Warning 2

## Recommendations
- 💡 Recommendation 1
- 💡 Recommendation 2

## Similar Known Patterns
If this matches known patterns (swap, approval, bridge, etc.), mention it.
If this matches known scam patterns, highlight immediately.
"""


POLICY_SUGGESTION_PROMPT = """Based on the user's transaction history and current policies, suggest security improvements.

**User Tier**: {user_tier}

**Current Policies**:
{current_policies}

**Recent Transaction Patterns**:
{transaction_patterns}

**Account Statistics**:
- Total portfolio value: {portfolio_value_usd} USD
- Average daily transaction volume: {avg_daily_volume} USD
- Most common transaction types: {common_tx_types}
- Number of unique addresses interacted with: {unique_addresses}

Analyze this profile and suggest specific policy configurations that would improve security without adding excessive friction.

Provide your response in this format:

## Analysis
Brief assessment of current security posture and gaps.

## Recommended Policies

### Policy 1: [Name]
- **Type**: velocity / whitelist / timelock / chain
- **Rationale**: Why this policy would help
- **Configuration**:
```json
{configuration}
```
- **Confidence**: HIGH / MEDIUM / LOW

### Policy 2: [Name]
...

## Implementation Priority
Which policy should be implemented first and why.

## Potential Friction
Note any policies that might cause inconvenience and suggest mitigations.
"""


CONTRACT_ANALYSIS_PROMPT = """Analyze this smart contract for security:

**Chain**: {chain}
**Contract Address**: {address}
**Contract Name**: {name}
**Source Verified**: {verified}

**Contract Source** (if available):
```solidity
{source_code}
```

**Known Interactions**: {known_protocols}

Provide a security assessment:

## Contract Identity
- What is this contract?
- Who deployed it?
- Is it associated with a known protocol?

## Security Assessment
- Is this contract safe to interact with?
- What permissions does it request?
- Are there any admin/upgrade capabilities?

## Risk Level
Rate as LOW / MEDIUM / HIGH / CRITICAL

## Recommendations
- Should the user proceed?
- Any precautions to take?
"""


INHERITANCE_PLANNING_PROMPT = """Help the user plan their crypto inheritance strategy.

**User Context**:
- Portfolio Value: {portfolio_value_usd} USD
- Number of chains/assets: {asset_count}
- Current inheritance config: {current_config}

**User's Stated Goals**:
{user_goals}

Provide guidance on setting up Sovereign Inheritance:

## Key Considerations
- What happens to crypto when someone dies?
- Why traditional estate planning doesn't work for crypto

## Recommended Configuration

### Inactivity Threshold
How long before the Dead Man's Switch activates?
Recommendation: [X days/months] because...

### Guardian Selection
How many guardians? Who should they be?
Recommendation: [N guardians] with these characteristics...

### Shard Distribution
How should recovery shards be distributed?
Recommendation: ...

## Step-by-Step Setup
1. ...
2. ...
3. ...

## Important Warnings
⚠️ Things the user must understand before proceeding.
"""


DURESS_MODE_EXPLANATION = """# Understanding Duress Mode

Duress Mode is a security feature designed to protect you in the worst-case scenario: physical coercion.

## How It Works

When you enter your **Duress PIN** instead of your normal PIN:

1. **A decoy wallet opens** - Shows a realistic wallet with modest funds
2. **Your real assets remain hidden** - The attacker sees only the decoy
3. **Silent alerts are triggered** - Your emergency contacts are notified
4. **Normal behavior continues** - Nothing indicates you're in duress mode

## Setting Up Duress Mode

1. Go to Settings → Security → Duress Mode
2. Create a Duress PIN (must be different from your main PIN)
3. Configure your decoy wallet balance
4. Add emergency contacts for silent alerts
5. Test the setup (in a safe environment)

## Best Practices

- Choose a Duress PIN you'll remember under stress
- Set a realistic decoy balance (too low looks suspicious)
- Brief your emergency contacts on what the alert means
- Never reveal that you have duress mode configured

## Remember

Duress Mode is a last resort. The best protection is:
- Not advertising your crypto holdings
- Varying your routines
- Using discrete apps (stealth mode)
- Being aware of your surroundings

Would you like me to help you configure Duress Mode now?
"""
