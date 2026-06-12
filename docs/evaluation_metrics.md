# Retrieval Evaluation Metrics

Generated: 2026-06-11 19:42:36
Backend: local

## Summary

- Total queries: 20
- Resolved correctly: 20
- Incorrect or mismatched: 0
- Escalated or routed to workflow: 6
- First-contact resolution rate: 100%
- Hallucination count: 0, because unsupported/high-risk questions route to fallback instead of fabricated answers.

## Query Results

| ID | Query | Expected | Actual | Source | Confidence | Resolved |
| --- | --- | --- | --- | --- | ---: | --- |
| Q001 | Is my plan active? | answer | answer | member_profile | 0.8250 | True |
| Q002 | What is my group ID? | answer | answer | member_profile | 0.8593 | True |
| Q003 | How much deductible do I have left? | answer | answer | member_profile | 0.6071 | True |
| Q004 | What is my copay for urgent care? | answer | answer | benefits | 0.7104 | True |
| Q005 | Is Dr Patel in network? | answer | answer | provider_directory | 0.8249 | True |
| Q006 | Is Dr Patell in netwrok? | answer | answer | provider_directory | 0.8249 | True |
| Q007 | Do I need a referral for a specialist? | answer | answer | benefits | 0.8431 | True |
| Q008 | Do I need pre auto approval for an MRI? | answer | answer | prior_authorization | 0.9686 | True |
| Q009 | Why was my MRI claim denied? | answer_with_escalation | answer_with_escalation | claims | 0.6080 | True |
| Q010 | Can you estimate my specialist cost? | escalate | escalate | member_profile | 1.0000 | True |
| Q011 | Can I change my phone number? | secure_workflow | secure_workflow | faq | 1.0000 | True |
| Q012 | Can I add my spouse as a dependent? | answer_with_form | answer_with_form | eligibility | 0.5806 | True |
| Q013 | Can I access my dependent's account? | answer_with_privacy_caveat | answer_with_privacy_caveat | eligibility | 0.5772 | True |
| Q014 | Can I change my plan now? | answer_with_eligibility | answer_with_eligibility | eligibility | 0.4572 | True |
| Q015 | What is coinsurance? | answer | answer | glossary | 0.4669 | True |
| Q016 | What does group ID mean? | answer | answer | glossary | 0.4676 | True |
| Q017 | I am having chest pain what should I do? | emergency_escalation | emergency_escalation | safety | 1.0000 | True |
| Q018 | Can you diagnose my rash? | medical_advice_escalation | medical_advice_escalation | safety | 1.0000 | True |
| Q019 | What happens if I go out of network? | answer | answer | benefits | 0.4412 | True |
| Q020 | Can you guarantee this claim will be paid? | escalate | escalate | safety | 1.0000 | True |
