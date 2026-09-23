import re
from typing import Dict, Any, List, Tuple


class GreenwashingScorer:
    """
    Deterministic rule-based evaluation engine for Greenwashing Risk Scoring.
    Calibrated across the 5 IEEE SEPP project dimensions:
      1. Evidence Strength (30% weight)
      2. Claim Specificity (20% weight)
      3. Source Reliability (20% weight)
      4. Contradictory Evidence (20% weight)
      5. Missing Information (10% weight)

    Produces a unified Greenwashing Risk Score (0-100) and structured Explainable AI breakdown.
    """

    # Vague marketing buzzwords that lack empirical or verifiable measurement boundaries
    VAGUE_BUZZWORDS = [
        "100%", "zero impact", "eco-friendly", "pure green", "planet safe",
        "completely green", "all-natural", "cleanest", "fully sustainable",
        "infinitely recyclable", "zero footprint", "nature positive", "guilt-free"
    ]

    # Specificity positive indicators (quantitative, chronological, or standard-aligned)
    SPECIFICITY_MARKERS = [
        r"\b\d+(\.\d+)?%\b",             # Percentages (e.g., "40%", "32.5%")
        r"\b(20[2-5][0-9])\b",            # Target years (e.g., 2030, 2045, 2050)
        r"\bscope\s*[123]\b",             # Scope 1, Scope 2, Scope 3
        r"\b(mtco2e?|metric tons?|tco2e?|mw|gwh|mwh)\b", # Measurable units
        r"\b(sbti|gri|ghg protocol|sebi|brsr|iso\s*\d+)\b", # Standards
        r"\b(baseline|financial year|fy\s*\d{2,4})\b"        # Baselines
    ]

    # Contradiction flag keywords in claims or corporate context
    SUSPECT_OFFSET_TERMS = [
        "carbon offset", "offset credits", "purchased credits", "planting trees", "net-zero today"
    ]

    @classmethod
    def evaluate_claim_specificity(cls, claim_text: str) -> Tuple[float, List[str]]:
        """
        Evaluates how concrete, measurable, and auditable the claim statement is.
        Returns specificity risk (0 = highly specific, 100 = completely vague/fluff).
        """
        text_lower = claim_text.lower()
        reasons = []

        # Check for vague buzzwords
        found_buzzwords = [bw for bw in cls.VAGUE_BUZZWORDS if bw in text_lower]
        # Check for concrete markers
        found_markers = [m for m in cls.SPECIFICITY_MARKERS if re.search(m, text_lower)]

        # Base specificity risk
        risk = 50.0

        if found_buzzwords:
            buzz_penalty = min(len(found_buzzwords) * 20.0, 40.0)
            risk += buzz_penalty
            reasons.append(f"Claim contains unquantified marketing terms: {', '.join(found_buzzwords)}.")

        if found_markers:
            specificity_bonus = min(len(found_markers) * 18.0, 45.0)
            risk -= specificity_bonus
            reasons.append("Claim includes quantitative metrics, standards, or target milestones.")
        else:
            risk += 15.0
            reasons.append("Claim lacks a baseline year or quantitative boundaries (e.g. Scope 1/2 definition).")

        return max(5.0, min(95.0, risk)), reasons

    @classmethod
    def calculate_score(
        cls,
        claim_text: str,
        citations: List[Dict[str, Any]],
        has_audited_source: bool = True,
        has_direct_contradiction: bool = False,
        missing_scope_or_baseline: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates the complete 5-factor risk score matrix and generates explainable verdict.
        """
        text_lower = claim_text.lower()
        summary_reasons: List[str] = []

        # 1. Claim Specificity (20% weight)
        spec_risk, spec_reasons = cls.evaluate_claim_specificity(claim_text)
        summary_reasons.extend(spec_reasons)

        # 2. Evidence Strength (30% weight)
        # Check citations retrieved
        supporting_citations = [c for c in citations if c.get("type") == "Supporting"]
        contradicting_citations = [c for c in citations if c.get("type") == "Contradicting"]

        if has_direct_contradiction or (contradicting_citations and not supporting_citations):
            evidence_risk = 92.0
            summary_reasons.append("Retrieved statutory BRSR disclosures directly refute the operational assertion.")
        elif not citations:
            evidence_risk = 85.0
            summary_reasons.append("No direct supporting evidence found in company BRSR filings.")
        elif supporting_citations and not contradicting_citations:
            avg_rel = sum(c.get("relevance", 0.8) for c in supporting_citations) / len(supporting_citations)
            evidence_risk = max(5.0, (1.0 - avg_rel) * 100.0)
            summary_reasons.append("Audited BRSR filings directly confirm the stated target or achievement.")
        elif supporting_citations and contradicting_citations:
            evidence_risk = 60.0
            summary_reasons.append("Retrieved passages present mixed evidence: disclosures show ongoing transition challenges.")
        else:
            evidence_risk = 88.0
            summary_reasons.append("Retrieved disclosures fail to support the operational claim.")

        # 3. Source Reliability (20% weight)
        if has_direct_contradiction:
            # When disclosures directly contradict the claim, the claim lacks reliable factual substantiation
            source_risk = 80.0
            summary_reasons.append("Claim contradicts audited statutory disclosures, indicating unverified marketing representation.")
        elif has_audited_source:
            # Audited BRSR / SEBI disclosures are high reliability -> low risk
            source_risk = 15.0
        else:
            source_risk = 75.0
            summary_reasons.append("Source relies on unaudited marketing copy rather than statutory BRSR disclosures.")

        # 4. Contradictory Evidence (20% weight)
        if has_direct_contradiction or contradicting_citations:
            contradiction_risk = 92.0
            summary_reasons.append("Contradictory evidence detected in audited data (e.g. substantial current emissions or fossil reliance).")
        elif any(term in text_lower for term in cls.SUSPECT_OFFSET_TERMS):
            contradiction_risk = 65.0
            summary_reasons.append("Claim relies heavily on unbundled carbon offsets rather than direct operational decarbonization.")
        else:
            contradiction_risk = 10.0

        # 5. Missing Information (10% weight)
        if missing_scope_or_baseline:
            missing_risk = 75.0
            summary_reasons.append("Measurement methodology or Scope 3 value-chain impact is omitted.")
        else:
            missing_risk = 20.0

        # Weighted calculation (IEEE SEPP model)
        # Weights: Evidence (30%), Specificity (20%), Source (20%), Contradiction (20%), Missing (10%)
        weighted_score = (
            (evidence_risk * 0.30) +
            (spec_risk * 0.20) +
            (source_risk * 0.20) +
            (contradiction_risk * 0.20) +
            (missing_risk * 0.10)
        )
        risk_score = round(max(0.0, min(100.0, weighted_score)), 1)

        # Verdict status determination based on established thresholds
        if risk_score <= 25.0:
            verdict_status = "Verified"
        elif risk_score <= 50.0:
            verdict_status = "Partially Supported"
        elif risk_score <= 75.0:
            verdict_status = "Unsupported"
        else:
            verdict_status = "High Risk"

        factors = {
            "evidence_strength": round(evidence_risk, 1),
            "claim_specificity": round(spec_risk, 1),
            "source_reliability": round(source_risk, 1),
            "contradictory_evidence": round(contradiction_risk, 1),
            "missing_information": round(missing_risk, 1)
        }

        return {
            "risk_score": risk_score,
            "verdict_status": verdict_status,
            "factors": factors,
            "summary_reasons": summary_reasons
        }
