# Contract Comparison Evaluation Metrics

## Overview
This document outlines the evaluation metrics for the contract-to-policy comparison system.

## Test Dataset Summary
**Total Test Cases:** 8 contracts
- **Compliant Contracts:** 2 (25%)
- **Non-Compliant Contracts:** 6 (75%)

## Test Cases

### 1. Valid Service Agreement ✅
- **Expected:** Compliant
- **Key Features:** Complete terms, clear payment, termination clause, dispute resolution, governing law
- **Expected Violations:** 0

### 2. Missing Consideration ❌
- **Expected:** Non-Compliant
- **Missing:** Payment terms, consideration
- **Expected Violations:** 2

### 3. Vague Termination Clause ❌
- **Expected:** Non-Compliant
- **Missing:** Specific termination notice period
- **Expected Violations:** 2

### 4. No Dispute Resolution ❌
- **Expected:** Non-Compliant
- **Missing:** Dispute resolution mechanism, governing law
- **Expected Violations:** 2

### 5. Incomplete Contract Elements ❌
- **Expected:** Non-Compliant
- **Missing:** Business details, capital contribution, management structure, dissolution terms
- **Expected Violations:** 4

### 6. Good Lease Agreement ✅
- **Expected:** Compliant
- **Key Features:** Complete lease terms, payment details, termination clause, dispute resolution
- **Expected Violations:** 0

### 7. Unenforceable Terms ❌
- **Expected:** Non-Compliant
- **Issues:** One-sided termination, unreasonable restraint clause, no notice period
- **Expected Violations:** 3

### 8. Missing Parties Details ❌
- **Expected:** Non-Compliant
- **Missing:** Party identification, addresses, proper signatures
- **Expected Violations:** 3

## Evaluation Metrics

### 1. **Classification Accuracy**
Measures how well the system correctly classifies contracts as compliant or non-compliant.

**Formula:**
```
Accuracy = (Correct Classifications) / (Total Test Cases)
```

**Expected Range:** 70-85%

### 2. **Precision (Violation Detection)**
Measures the accuracy of detected violations.

**Formula:**
```
Precision = True Positives / (True Positives + False Positives)
```

Where:
- **True Positive:** Correctly identified violation
- **False Positive:** Incorrectly flagged as violation

**Expected Range:** 60-75%

### 3. **Recall (Violation Detection)**
Measures how many actual violations were found.

**Formula:**
```
Recall = True Positives / (True Positives + False Negatives)
```

Where:
- **False Negative:** Missed violation that should have been detected

**Expected Range:** 55-70%

### 4. **F1-Score**
Harmonic mean of precision and recall.

**Formula:**
```
F1-Score = 2 × (Precision × Recall) / (Precision + Recall)
```

**Expected Range:** 58-72%

### 5. **Overall Accuracy**
Total correct predictions (both violations and compliances).

**Formula:**
```
Overall Accuracy = (TP + TN) / (TP + TN + FP + FN)
```

**Expected Range:** 65-80%

## Confusion Matrix Structure

|                    | Predicted Compliant | Predicted Non-Compliant |
|--------------------|---------------------|-------------------------|
| **Actually Compliant** | True Negative (TN)  | False Positive (FP)     |
| **Actually Non-Compliant** | False Negative (FN) | True Positive (TP)      |

## Expected Results (Baseline)

Based on the test dataset with 8 contracts and 16 total expected violations:

### Macro-Averaged Metrics (Per Contract)
- **Precision:** ~65%
- **Recall:** ~60%
- **F1-Score:** ~62%
- **Classification Accuracy:** ~75%

### Micro-Averaged Metrics (Overall)
- **Precision:** ~68%
- **Recall:** ~63%
- **F1-Score:** ~65%

### Confusion Matrix (Expected)
- **True Positives:** ~10 violations correctly identified
- **False Positives:** ~5 incorrect violation flags
- **False Negatives:** ~6 missed violations
- **True Negatives:** ~2 correctly identified compliant contracts

## Performance Benchmarks

### Excellent Performance (>80% F1)
- System reliably detects most violations
- Few false positives
- Strong compliance classification

### Good Performance (60-80% F1)
- System catches majority of violations
- Acceptable false positive rate
- Generally accurate classification

### Needs Improvement (<60% F1)
- Missing significant violations
- High false positive rate
- Poor compliance classification

## Key Performance Indicators

1. **Violation Detection Rate:** % of expected violations found
2. **False Alarm Rate:** % of flagged violations that are incorrect
3. **Compliance Classification Rate:** % of correctly classified contracts
4. **Critical Violation Detection:** % of critical violations (missing consideration, no signatures) found

## Recommendations for Improvement

1. **Improve Precision:**
   - Refine LLM prompts to reduce false positives
   - Add more specific legal clause patterns
   - Implement confidence thresholds

2. **Improve Recall:**
   - Expand test cases with more violation types
   - Enhance FAISS retrieval with lower thresholds
   - Add multi-pass verification

3. **Improve Overall Accuracy:**
   - Fine-tune policy preprocessing
   - Implement weighted violation scoring
   - Add human-in-the-loop validation for edge cases

## How to Run Evaluation

```bash
cd backend
python evaluate_contract_comparison.py
```

**Note:** Requires:
- Initialized policy processor
- Valid Gemini API key
- Preprocessed legal index

## Output Files

- `contract_comparison_evaluation.json` - Detailed results
- Console output with metrics summary

## Interpretation Guide

- **High Precision, Low Recall:** System is conservative, misses violations
- **Low Precision, High Recall:** System is aggressive, many false alarms  
- **Balanced F1-Score:** Good overall performance
- **High Classification Accuracy:** Strong compliant/non-compliant determination
