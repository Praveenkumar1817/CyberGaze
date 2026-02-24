"""
mining_engine.py - FP-Growth Pattern Mining Engine
====================================================
Implements the FP-Growth frequent itemset mining algorithm
for discovering attack patterns in forensic log data.

FP-Growth is ideal for DFIR because:
- Efficient on sparse transaction data (log events per IP)
- No candidate generation (unlike Apriori) — faster on large logs
- Discovers "If A then B" patterns (e.g., "Failed Login -> Brute Force")

Pipeline:
    1. Load raw log DataFrame
    2. Group events by source_ip to form "transactions"
    3. One-hot encode the event types
    4. Run FP-Growth to find frequent itemsets
    5. Generate association rules with confidence scores
    6. Return human-readable threat patterns
"""

import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules
from mlxtend.preprocessing import TransactionEncoder
from typing import List, Dict, Any


def build_transactions(df: pd.DataFrame) -> List[List[str]]:
    """
    Transform raw log DataFrame into transaction format for FP-Growth.

    Each "transaction" = all unique events seen from a single source_ip.
    We append status to event_type to differentiate success vs failure
    (e.g., "Failed Login:Fail" vs "Login:Success").

    Args:
        df: Raw forensic log DataFrame with columns
            [timestamp, source_ip, event_type, status, description]

    Returns:
        List of transactions (each = list of event strings per IP)
    """
    transactions = []

    for ip, group in df.groupby("source_ip"):
        # Combine event_type + status for richer pattern items
        # e.g., "Brute Force:Fail", "Login:Success"
        items = list(set(
            f"{row['event_type']}:{row['status']}"
            for _, row in group.iterrows()
        ))
        if items:
            transactions.append(items)

    return transactions


def run_fpgrowth(
    df: pd.DataFrame,
    min_support: float = 0.1,
    min_confidence: float = 0.5,
) -> Dict[str, Any]:
    """
    Execute FP-Growth algorithm on the forensic log data.

    Args:
        df: Forensic logs DataFrame
        min_support: Minimum fraction of IPs that must show the pattern
                     (0.1 = pattern appears in 10%+ of source IPs)
        min_confidence: Minimum confidence for association rules
                       (0.5 = antecedent is followed by consequent 50%+ of time)

    Returns:
        Dict with:
            - "frequent_itemsets": List of discovered patterns with support
            - "association_rules": List of IF->THEN threat rules
            - "summary": Human-readable threat summary
    """
    # Step 1: Build transactions from logs
    transactions = build_transactions(df)

    if not transactions:
        return {"error": "No transactions found in log data."}

    # Step 2: One-hot encode using TransactionEncoder
    te = TransactionEncoder()
    te_array = te.fit_transform(transactions)
    encoded_df = pd.DataFrame(te_array, columns=te.columns_)

    # Step 3: Run FP-Growth to find frequent itemsets
    # use_colnames=True returns readable item names instead of indices
    frequent_itemsets = fpgrowth(
        encoded_df,
        min_support=min_support,
        use_colnames=True,
    )

    if frequent_itemsets.empty:
        return {
            "frequent_itemsets": [],
            "association_rules": [],
            "summary": "No frequent patterns found. Try lowering min_support.",
        }

    # Step 4: Generate association rules (IF antecedent THEN consequent)
    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=min_confidence,
    )

    # Step 5: Format results for API response
    itemsets_output = []
    for _, row in frequent_itemsets.iterrows():
        itemsets_output.append({
            "pattern": list(row["itemsets"]),
            "support": round(float(row["support"]), 4),
            "support_pct": f"{round(float(row['support']) * 100, 1)}% of IPs",
        })

    rules_output = []
    for _, row in rules.iterrows():
        antecedent = list(row["antecedents"])
        consequent = list(row["consequents"])
        rules_output.append({
            "rule": f"IF [{', '.join(antecedent)}] THEN [{', '.join(consequent)}]",
            "antecedent": antecedent,
            "consequent": consequent,
            "support": round(float(row["support"]), 4),
            "confidence": round(float(row["confidence"]), 4),
            "lift": round(float(row["lift"]), 4),
            "threat_label": _classify_threat(antecedent, consequent),
        })

    # Sort rules by confidence (most reliable patterns first)
    rules_output.sort(key=lambda x: x["confidence"], reverse=True)

    return {
        "transaction_count": len(transactions),
        "frequent_itemsets": itemsets_output,
        "association_rules": rules_output,
        "summary": _generate_summary(rules_output),
    }


def _classify_threat(antecedent: List[str], consequent: List[str]) -> str:
    """
    Map discovered patterns to MITRE ATT&CK-inspired threat labels.

    Args:
        antecedent: List of "IF" items
        consequent: List of "THEN" items

    Returns:
        Human-readable threat classification string
    """
    all_items = " ".join(antecedent + consequent).lower()

    if "brute force" in all_items or "failed login" in all_items:
        return "🔴 CREDENTIAL ATTACK - Possible Brute Force / Credential Stuffing"
    elif "lateral movement" in all_items:
        return "🟠 LATERAL MOVEMENT - Attacker traversing internal network"
    elif "privilege escalation" in all_items:
        return "🟠 PRIVILEGE ESCALATION - Attempt to gain elevated access"
    elif "data exfiltration" in all_items:
        return "🔴 DATA EXFILTRATION - Sensitive data leaving environment"
    elif "malware" in all_items:
        return "🔴 MALWARE EXECUTION - Malicious code detected"
    elif "port scan" in all_items:
        return "🟡 RECONNAISSANCE - Network scanning activity"
    elif "file access" in all_items:
        return "🟡 SUSPICIOUS FILE ACCESS - Potential data staging"
    else:
        return "🔵 ANOMALOUS BEHAVIOR - Investigate further"


def _generate_summary(rules: List[Dict]) -> str:
    """
    Generate a plain-English threat summary from discovered rules.

    Args:
        rules: List of association rule dicts

    Returns:
        Formatted summary string for analysts
    """
    if not rules:
        return "No significant attack patterns discovered."

    top_rules = rules[:3]
    summary_lines = [
        f"🔍 FP-Growth discovered {len(rules)} threat pattern(s).",
        "",
        "Top Patterns Identified:",
    ]

    for i, rule in enumerate(top_rules, 1):
        summary_lines.append(
            f"  {i}. {rule['rule']}"
            f" (Confidence: {rule['confidence']*100:.0f}%, "
            f"Lift: {rule['lift']:.2f}x)"
        )
        summary_lines.append(f"     → {rule['threat_label']}")

    return "\n".join(summary_lines)
