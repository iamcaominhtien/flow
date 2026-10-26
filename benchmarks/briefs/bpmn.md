# Briefs: BPMN

Three briefs at levels A, B and C. See [README](README.md) for the format and how to run them.

---

## bpmn-A-01 — Enterprise Expense Reimbursement and Auditing Process

* **type:** bpmn
* **level:** A
* **elements:** 10
* **connections:** 11
* **groups:** Employee Lane, Finance Lane

### Brief

The reimbursement process coordinates across Employee Lane and Finance Lane.
The workflow starts at ExpenseSubmissionInitiated within Employee Lane. An employee submits expense records via SubmitExpenseReportTask, which transfers to ReceiptVerificationGateway in Finance Lane. ReceiptVerificationGateway examines whether valid payment receipts are attached. If receipts are missing, ReceiptVerificationGateway routes back to RequestReceiptCorrectionTask in Employee Lane, which loops directly back into SubmitExpenseReportTask.
If receipts are verified, ReceiptVerificationGateway advances to ManagerApprovalTask. ManagerApprovalTask leads into ApprovalDecisionGateway. If rejected, ApprovalDecisionGateway passes to SendRejectionNoticeTask, which terminates at ExpenseRejectedEnd. If approved, ApprovalDecisionGateway routes to ProcessDisbursementTask.
ProcessDisbursementTask issues funds and passes to IssueBankTransferTask, which concludes the business workflow at ExpenseReimbursedEnd.

### Must show

* Clear swimlane partitioning separating Employee Lane and Finance Lane.
* A cross-lane feedback cycle between ReceiptVerificationGateway, RequestReceiptCorrectionTask, and SubmitExpenseReportTask.
* Distinct final states: ExpenseRejectedEnd and ExpenseReimbursedEnd.

### Traps

* Cross-lane cyclic routing back to an upstream task in the initial lane requires clear boundary crossings without clipping intermediate task labels.

### Sources

* BPMN 2.0 by Example (OMG Specification) — Standard expense claim, travel approval, and disbursement model patterns.

### Uncertain

* none

---

## bpmn-B-01 — Commercial Real Estate Mortgage Underwriting and Syndication

* **type:** bpmn
* **level:** B
* **elements:** 24
* **connections:** 28
* **groups:** Borrower Entity, Loan Origination Lane, Credit Risk Committee

### Brief

The lending workflow operates across Borrower Entity, Loan Origination Lane, and Credit Risk Committee.
Borrower Entity triggers LoanApplicationStarted and transmits documentation via CompleteApplicationTask to Loan Origination Lane. IntakeSpecialistReviewTask checks document completeness and routes to DocumentIntegrityGateway. If documents are missing, DocumentIntegrityGateway routes back to RequestSupplementaryDocumentsTask, which loops back to CompleteApplicationTask.
If documents are complete, DocumentIntegrityGateway routes to InitiateUnderwritingTask. InitiateUnderwritingTask routes into ParallelUnderwritingGateway, splitting into two concurrent analysis tasks: OrderPropertyAppraisalTask and ConductEnvironmentalAssessmentTask.
Both tasks merge at UnderwritingMergeGateway and pass to PerformFinancialStressTestTask in Credit Risk Committee. PerformFinancialStressTestTask routes to RiskScoreAssessmentGateway. If the calculated risk is unacceptably high, RiskScoreAssessmentGateway directs to IssueDeclineNoticeTask, terminating at MortgageRejectedEnd.
If acceptable, RiskScoreAssessmentGateway routes to StructureCreditFacilityTask. StructureCreditFacilityTask leads into UnderwriterAuditGateway. If loan covenant discrepancies arise, UnderwriterAuditGateway loops back to InitiateUnderwritingTask.
If covenants pass audit, UnderwriterAuditGateway advances to PrepareSyndicationProspectusTask. PrepareSyndicationProspectusTask triggers DistributeToInstitutionalLendersTask, followed by FinalLoanExecutionTask, which completes the business process at LoanSyndicatedEnd.

### Must show

* Swimlane division among Borrower Entity, Loan Origination Lane, and Credit Risk Committee.
* ParallelUnderwritingGateway and UnderwritingMergeGateway fork-and-join pair running property appraisal and environmental review concurrently.
* Two cyclic loops: document remediation looping to CompleteApplicationTask, and UnderwriterAuditGateway looping back to InitiateUnderwritingTask.

### Traps

* Coordinating parallel fork-join branching that spans across lane transitions while maintaining upstream feedback edges challenges conventional grid-based routing engines.

### Sources

* Mortgage Bankers Association Commercial / Multifamily Underwriting Guidelines — Standard loan origination, environmental review, and underwriting workflows.

### Uncertain

* none

---

## bpmn-C-01 — Multinational Clinical Trial Pharmacovigilance Safety Protocol

* **type:** bpmn
* **level:** C
* **elements:** 46
* **connections:** 55
* **groups:** Clinical Trial Site, Safety Management CRO, Data Safety Monitoring Board, Regulatory Oversight Authority

### Brief

The safety protocol manages drug event monitoring across Clinical Trial Site, Safety Management CRO, Data Safety Monitoring Board, and Regulatory Oversight Authority.
The protocol triggers at AdverseEventDetected inside Clinical Trial Site. The site physician enters case details via DocumentAdverseEventTask and passes to AssessSeriousnessTask. AssessSeriousnessTask routes to SeriousAdverseEventGateway. If non-serious, SeriousAdverseEventGateway routes to LogStandardRegistryTask, terminating at RoutineCaseArchivedEnd.
If serious, SeriousAdverseEventGateway routes to TransmitE2BReportTask, which crosses into Safety Management CRO. IngestionValidationTask reviews transmission formatting and advances to TriagingTriageGateway. If data errors exist, TriagingTriageGateway routes back to ClarificationRequestTask, which loops back to DocumentAdverseEventTask.
If data is valid, TriagingTriageGateway advances to MedicalCausalityAssessmentTask, which routes to CausalityEvaluationGateway. If causality is unconfirmed, CausalityEvaluationGateway routes to StandardSafetyDatabaseTask, leading to PeriodicSafetyUpdateReportTask and terminating at PeriodicReportLoggedEnd.
If causality is confirmed, CausalityEvaluationGateway evaluates event novelty at SuspectedUnexpectedReactionGateway. For life-threatening emergencies, SuspectedUnexpectedReactionGateway activates FastTrackSafetyNoticeTask, skipping intermediate committee deliberations to notify Regulatory Oversight Authority directly.
In standard tracks, SuspectedUnexpectedReactionGateway splits three ways: into ConveneEmergencySessionTask in Data Safety Monitoring Board, UnblindTrialArmTask in Safety Management CRO, and IssueInvestigationalSiteHoldTask in Clinical Trial Site. ConveneEmergencySessionTask and UnblindTrialArmTask synchronize at SafetyReviewConsensusGateway, which leads to AdjudicateBenefitRiskRatioTask.
AdjudicateBenefitRiskRatioTask passes to BenefitRiskGateway. If further inquiry is demanded, BenefitRiskGateway loops back to MedicalCausalityAssessmentTask. If the safety ratio is acceptable, BenefitRiskGateway advances to DraftRegulatorySubmissionTask in Regulatory Oversight Authority.
DraftRegulatorySubmissionTask triggers FinalComplianceValidationTask, which leads to SubmitSafetyAdvisoryTask. SubmitSafetyAdvisoryTask advances to PublishEudraVigilanceAlertTask, concluding at RegulatoryTrialInterventionEnd.

### Must show

* Four distinct organizational pools: Clinical Trial Site, Safety Management CRO, Data Safety Monitoring Board, and Regulatory Oversight Authority.
* SuspectedUnexpectedReactionGateway fanning out three concurrent paths across three different pools.
* FastTrackSafetyNoticeTask skipping internal review stages to jump directly to Regulatory Oversight Authority.
* Two feedback loops: ClarificationRequestTask returning to DocumentAdverseEventTask, and BenefitRiskGateway returning to MedicalCausalityAssessmentTask.

### Traps

* Concurrently routing message and sequence flows across four interactive swimlanes while maintaining a multi-step emergency bypass creates complex edge routing constraints.

### Sources

* ICH E2A Clinical Safety Data Management: Definitions and Standards for Expedited Reporting (FDA / EMA harmonized standard).
* European Medicines Agency Guideline on Good Pharmacovigilance Practices (GVP) Module VI.

### Uncertain

* none
