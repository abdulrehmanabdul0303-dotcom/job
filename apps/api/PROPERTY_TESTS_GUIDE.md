# 🧪 Property-Based Testing Guide

## Overview

This project uses **property-based testing** (PBT) to verify universal correctness properties that must hold for ALL inputs, not just specific examples. We use the `hypothesis` library to generate hundreds of test cases automatically.

## What Are Property-Based Tests?

Instead of writing:
```python
def test_url_hash():
    assert generate_hash("https://example.com/job1") == generate_hash("https://example.com/job1")
```

We write:
```python
@given(url=st.from_regex(r'https?://[a-z0-9\-\.]+\.[a-z]{2,}/jobs/[a-z0-9\-]+'))
@settings(max_examples=100)
def test_property_url_hash_deterministic(url: str):
    """For ANY URL, hashing it multiple times SHALL produce the same result."""
    assert generate_hash(url) == generate_hash(url) == generate_hash(url)
```

Hypothesis generates 100+ different URLs and tests them all automatically!

---

## 📦 Installation

```powershell
# Install hypothesis (already in pyproject.toml dev dependencies)
cd jobpilot-ai/apps/api
pip install -e ".[dev]"
```

---

## 🚀 Running Property Tests

### Run All Property Tests
```powershell
pytest tests/test_job_processing_properties.py tests/test_matching_properties.py -v
```

### Run Specific Property Test File
```powershell
# Job processing properties
pytest tests/test_job_processing_properties.py -v

# Matching properties
pytest tests/test_matching_properties.py -v
```

### Run Specific Property Test
```powershell
pytest tests/test_job_processing_properties.py::TestCompliantSourceEnforcement::test_property_9_non_whitelisted_domains_rejected -v
```

### Run with Coverage
```powershell
pytest tests/test_job_processing_properties.py tests/test_matching_properties.py --cov=app/services --cov-report=html
```

### Run Stateful Tests Only
```powershell
pytest tests/test_job_processing_properties.py::TestJobProcessing -v
pytest tests/test_matching_properties.py::TestMatching -v
```

---

## 📊 Property Test Coverage

### Job Processing Properties (18 tests, 1500+ examples)

#### ✅ Property 9: Compliant Source Enforcement
**Validates: Requirements 4.1, 4.3**

- `test_property_9_non_whitelisted_domains_rejected` - Non-whitelisted domains are rejected
- `test_property_9_whitelisted_domains_accepted` - Whitelisted domains are accepted
- `test_property_9_whitelist_is_deterministic` - Whitelist checking is deterministic

**What it tests**: For ANY URL, the system SHALL only fetch from RSS/API sources or whitelisted domains.

#### ✅ Property 10: Job Deduplication Accuracy
**Validates: Requirements 4.2, 4.5**

- `test_property_10_same_url_same_hash` - Same URL produces same hash (idempotence)
- `test_property_10_query_params_ignored` - Query parameters are ignored
- `test_property_10_case_insensitive` - URL hashing is case-insensitive
- `test_property_10_trailing_slashes_ignored` - Trailing slashes are ignored
- `test_property_10_different_urls_different_hashes` - Different URLs produce different hashes

**What it tests**: For ANY two job URLs, if they normalize to the same URL, they SHALL produce the same hash.

#### ✅ Property 11: Data Normalization Consistency
**Validates: Requirements 4.4, 4.5**

- `test_property_11_parsing_is_deterministic` - Parsing RSS entries is deterministic
- `test_property_11_required_fields_always_present` - Required fields always present
- `test_property_11_url_hash_matches_link` - URL hash matches application URL
- `test_property_11_work_type_extraction_consistent` - Work type extraction is consistent

**What it tests**: For ANY RSS entry, parsing it multiple times SHALL produce the same normalized data.

#### ✅ Property 18: Scheduled Job Reliability
**Validates: Requirements 11.1, 11.5**

- `test_property_18_batch_processing_handles_any_count` - Batch processing handles any count
- `test_property_18_deduplication_in_batch` - Deduplication works in batch processing

**What it tests**: For ANY scheduled job execution, the system SHALL complete successfully or fail gracefully.

---

### Matching Properties (15 tests, 1330+ examples)

#### ✅ Property 12: Match Scoring Explainability
**Validates: Requirements 5.1, 5.2, 5.3**

- `test_property_12_scoring_is_deterministic` - Match scoring is deterministic
- `test_property_12_score_has_required_fields` - Match result has all required fields
- `test_property_12_score_in_valid_range` - Match score is in valid range (0-100)
- `test_property_12_missing_skills_are_accurate` - Missing skills are accurately identified
- `test_property_12_skill_overlap_score_correct` - Skill overlap score is correctly calculated
- `test_property_12_location_bonus_in_range` - Location bonus is in valid range (0-0.2)

**What it tests**: For ANY resume and job description, the match score SHALL be explainable with specific reasons.

#### ✅ Property 13: Match Ranking Accuracy
**Validates: Requirements 5.1, 5.2, 5.3**

- `test_property_13_ranking_is_descending` - Matches are ranked in descending order
- `test_property_13_higher_score_ranks_higher` - Higher scores always rank higher
- `test_property_13_ranking_preserves_all_scores` - Ranking preserves all scores
- `test_property_13_ranking_is_stable` - Ranking is stable (deterministic)
- `test_property_13_filtering_preserves_ranking` - Filtering preserves ranking order

**What it tests**: For ANY set of matches, they SHALL be ranked by score in descending order.

---

## 🎯 Understanding Property Test Output

### Successful Test
```
tests/test_job_processing_properties.py::TestCompliantSourceEnforcement::test_property_9_whitelist_is_deterministic PASSED [100%]
```

This means hypothesis generated 100 different URLs and ALL of them passed the property test!

### Failed Test
```
tests/test_job_processing_properties.py::TestJobDeduplicationAccuracy::test_property_10_same_url_same_hash FAILED

Falsifying example: test_property_10_same_url_same_hash(
    base_url='https://example.com/jobs/test-job'
)
```

When a property test fails, hypothesis shows you the **exact input** that caused the failure. This is incredibly valuable for debugging!

---

## 🔧 Configuring Property Tests

### Adjust Number of Examples
```python
@settings(max_examples=200)  # Generate 200 test cases instead of 100
def test_my_property(...):
    ...
```

### Adjust Deadline
```python
@settings(deadline=None)  # No timeout (useful for slow tests)
def test_my_property(...):
    ...
```

### Suppress Health Checks
```python
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_my_property(...):
    ...
```

---

## 📝 Writing New Property Tests

### Step 1: Identify a Universal Property

Ask: "What should be true for ALL inputs?"

Examples:
- "For ANY URL, hashing it twice should give the same result"
- "For ANY resume and job, the match score should be between 0 and 100"
- "For ANY list of matches, sorting them should preserve all matches"

### Step 2: Write the Property Test

```python
from hypothesis import given, strategies as st, settings

@given(
    url=st.from_regex(r'https?://[a-z0-9\-\.]+\.[a-z]{2,}/jobs/[a-z0-9\-]+', fullmatch=True)
)
@settings(max_examples=100, deadline=None)
def test_property_url_hash_deterministic(url: str):
    """
    Property: URL hashing is deterministic.
    
    **Feature: job-processing, Property X: URL Hashing**
    
    For ANY URL, hashing it multiple times SHALL produce the same result.
    """
    hash1 = generate_url_hash(url)
    hash2 = generate_url_hash(url)
    hash3 = generate_url_hash(url)
    
    assert hash1 == hash2 == hash3, "URL hash must be deterministic"
```

### Step 3: Run and Verify

```powershell
pytest tests/test_my_properties.py::test_property_url_hash_deterministic -v
```

---

## 🐛 Debugging Failed Property Tests

### 1. Hypothesis Shows You the Failing Input

```
Falsifying example: test_property_10_same_url_same_hash(
    base_url='https://example.com/jobs/test-job?utm_source=test'
)
```

### 2. Reproduce the Failure

```python
def test_reproduce_failure():
    """Reproduce the exact failure from hypothesis."""
    url = 'https://example.com/jobs/test-job?utm_source=test'
    hash1 = generate_url_hash(url)
    hash2 = generate_url_hash(url)
    assert hash1 == hash2
```

### 3. Fix the Bug

```python
def generate_url_hash(url: str) -> str:
    # BUG: Not removing query params!
    # FIX: Parse URL and remove query params
    parsed = urlparse(url.lower().strip())
    normalized = f"{parsed.netloc}{parsed.path}".rstrip('/')
    return hashlib.sha256(normalized.encode()).hexdigest()
```

### 4. Verify Fix

```powershell
pytest tests/test_job_processing_properties.py::TestJobDeduplicationAccuracy::test_property_10_same_url_same_hash -v
```

---

## 🎓 Property Test Patterns

### Pattern 1: Idempotence
"Doing something twice = doing it once"

```python
@given(data=st.text())
def test_idempotence(data):
    result1 = process(data)
    result2 = process(result1)
    assert result1 == result2
```

### Pattern 2: Round Trip
"Encode then decode = original"

```python
@given(data=st.dictionaries(st.text(), st.text()))
def test_round_trip(data):
    encoded = json.dumps(data)
    decoded = json.loads(encoded)
    assert decoded == data
```

### Pattern 3: Invariants
"Some property always holds"

```python
@given(items=st.lists(st.integers()))
def test_invariant(items):
    sorted_items = sorted(items)
    assert len(sorted_items) == len(items)  # Length preserved
```

### Pattern 4: Metamorphic
"Relationship between inputs and outputs"

```python
@given(items=st.lists(st.integers()))
def test_metamorphic(items):
    filtered = [x for x in items if x > 0]
    assert len(filtered) <= len(items)  # Filtering reduces or maintains size
```

---

## 📈 Benefits of Property-Based Testing

### 1. **Finds Edge Cases You Didn't Think Of**
Hypothesis generates inputs you would never write manually:
- Empty strings
- Very long strings
- Special characters
- Boundary values
- Combinations you didn't consider

### 2. **Tests Universal Correctness**
Instead of testing specific examples, you test that properties hold for ALL inputs.

### 3. **Automatic Test Case Generation**
Write one property test, get 100+ test cases automatically.

### 4. **Regression Prevention**
Once hypothesis finds a bug, it remembers it and always tests that case.

### 5. **Living Documentation**
Property tests document what MUST be true about your system.

---

## 🚨 Common Pitfalls

### Pitfall 1: Testing Implementation Instead of Properties

❌ **Bad**:
```python
def test_implementation():
    result = compute_hash("test")
    assert result == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
```

✅ **Good**:
```python
@given(text=st.text())
def test_property_hash_deterministic(text):
    assert compute_hash(text) == compute_hash(text)
```

### Pitfall 2: Not Using `assume()` to Filter Invalid Inputs

❌ **Bad**:
```python
@given(url=st.text())
def test_url_parsing(url):
    # Will fail on invalid URLs!
    parsed = parse_url(url)
    assert parsed is not None
```

✅ **Good**:
```python
@given(url=st.from_regex(r'https?://[a-z0-9\-\.]+\.[a-z]{2,}'))
def test_url_parsing(url):
    parsed = parse_url(url)
    assert parsed is not None
```

### Pitfall 3: Flaky Tests Due to Non-Determinism

❌ **Bad**:
```python
@given(data=st.text())
def test_with_random(data):
    result = process_with_random(data)  # Uses random.random()
    assert result == process_with_random(data)  # Will fail!
```

✅ **Good**:
```python
@given(data=st.text(), seed=st.integers())
def test_with_seed(data, seed):
    random.seed(seed)
    result1 = process_with_random(data)
    random.seed(seed)
    result2 = process_with_random(data)
    assert result1 == result2
```

---

## 📚 Further Reading

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing with Hypothesis](https://hypothesis.works/)
- [Introduction to Property-Based Testing](https://fsharpforfunandprofit.com/posts/property-based-testing/)

---

## 🎯 Next Steps

1. **Run the existing property tests**:
   ```powershell
   pytest tests/test_job_processing_properties.py tests/test_matching_properties.py -v
   ```

2. **Check coverage**:
   ```powershell
   pytest tests/test_job_processing_properties.py tests/test_matching_properties.py --cov=app/services --cov-report=html
   ```

3. **Add more properties** as you identify universal correctness requirements

4. **Integrate into CI/CD** to run on every commit

---

**Remember**: Property tests complement unit tests. Use both!
- **Unit tests**: Test specific examples and edge cases
- **Property tests**: Test universal properties across all inputs

Together, they provide comprehensive correctness guarantees! 🚀
