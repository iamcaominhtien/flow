# Briefs: BPMN

Four briefs: levels A, B and C, and a second level C. See [README](README.md) for the format and how to run them.

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
* **elements:** 41
* **connections:** 48
* **groups:** Clinical Trial Site, Safety Management CRO, Data Safety Monitoring Board, Regulatory Oversight Authority

### Brief

The model has 41 elements in 4 groups: Clinical Trial Site, Safety Management CRO, Data Safety Monitoring Board, Regulatory Oversight Authority. Every name below is one element to draw, and every sentence describes connections to draw.

In Clinical Trial Site: AdverseEventDetected flows to DocumentAdverseEventTask. DocumentAdverseEventTask flows to SafetyNarrativeDraftingTask. SafetyNarrativeDraftingTask flows to AssessSeriousnessTask. AssessSeriousnessTask flows to SeriousAdverseEventGateway. SeriousAdverseEventGateway flows to LogStandardRegistryTask if the event is not serious; flows to TransmitE2BReportTask if the event is serious. LogStandardRegistryTask flows to RoutineCaseArchivedEnd. TransmitE2BReportTask sends a message to IngestionValidationTask (sends the safety report). SiteFollowUpVisitTask flows to FollowUpDeadlineTimer. FollowUpDeadlineTimer sends a message to SafetyReviewJoinGateway (the follow-up deadline passes). IssueInvestigationalSiteHoldTask flows to NotifyEthicsCommitteeTask. NotifyEthicsCommitteeTask flows to SiteFollowUpVisitTask.

In Safety Management CRO: IngestionValidationTask flows to TriagingGateway. TriagingGateway flows to ClarificationRequestTask if the data has errors; flows to MeddraCodingTask if the data is valid. ClarificationRequestTask sends a message to DocumentAdverseEventTask (requests a corrected report). MeddraCodingTask flows to SignalDetectionTask. SignalDetectionTask flows to LiteratureReviewTask. LiteratureReviewTask flows to MedicalCausalityAssessmentTask. MedicalCausalityAssessmentTask flows to CausalityEvaluationGateway. CausalityEvaluationGateway flows to StandardSafetyDatabaseTask if causality is unconfirmed; flows to SuspectedUnexpectedReactionGateway if causality is confirmed. StandardSafetyDatabaseTask flows to PeriodicSafetyUpdateReportTask. PeriodicSafetyUpdateReportTask flows to PeriodicReportLoggedEnd. SuspectedUnexpectedReactionGateway sends a message to FastTrackSafetyNoticeTask (the event is life-threatening); sends a message to ConveneEmergencySessionTask (standard track); flows to UnblindTrialArmTask if standard track; sends a message to IssueInvestigationalSiteHoldTask (standard track). SafetyReviewJoinGateway flows to AdjudicateBenefitRiskTask. UnblindTrialArmTask sends a message to ReviewUnblindedDataTask (delivers unblinded data).

In Data Safety Monitoring Board: AdjudicateBenefitRiskTask flows to BenefitRiskGateway. BenefitRiskGateway sends a message to MedicalCausalityAssessmentTask (further inquiry is demanded); flows to ExtendedReviewTimer if the board needs more time; flows to RecommendationIssuedEvent if the safety ratio is acceptable. ExtendedReviewTimer flows to AdjudicateBenefitRiskTask if the review period ends. RecommendationIssuedEvent sends a message to DraftRegulatorySubmissionTask (sends the recommendation). ConveneEmergencySessionTask flows to ReviewUnblindedDataTask. ReviewUnblindedDataTask flows to MinutesApprovalTask. MinutesApprovalTask flows to SafetyReviewJoinGateway.

In Regulatory Oversight Authority: FastTrackSafetyNoticeTask flows to AcknowledgeNoticeTask. AcknowledgeNoticeTask flows to DraftRegulatorySubmissionTask. DraftRegulatorySubmissionTask flows to FinalComplianceValidationTask. FinalComplianceValidationTask flows to SubmitSafetyAdvisoryTask; flows to SubmissionRejectedErrorEvent if validation fails. SubmitSafetyAdvisoryTask flows to PublishEudraVigilanceAlertTask. PublishEudraVigilanceAlertTask flows to RegulatoryTrialInterventionEnd; sends a message to SiteFollowUpVisitTask (informs the site of the alert). SubmissionRejectedErrorEvent flows to DraftRegulatorySubmissionTask if the draft is reworked.

### Must show

* The 4 groups (Clinical Trial Site, Safety Management CRO, Data Safety Monitoring Board, Regulatory Oversight Authority) contain exactly the elements listed under Structure.
* Fan-out of three or more: SuspectedUnexpectedReactionGateway (4), BenefitRiskGateway (3).
* 5 connections return to an earlier element: ClarificationRequestTask to DocumentAdverseEventTask, BenefitRiskGateway to MedicalCausalityAssessmentTask, ExtendedReviewTimer to AdjudicateBenefitRiskTask, RecommendationIssuedEvent to DraftRegulatorySubmissionTask, SubmissionRejectedErrorEvent to DraftRegulatorySubmissionTask.
* 12 connections cross between groups, for example TransmitE2BReportTask to IngestionValidationTask, ClarificationRequestTask to DocumentAdverseEventTask, SuspectedUnexpectedReactionGateway to FastTrackSafetyNoticeTask.

### Traps

* Message flows return to tasks in other pools, creating cycles that cross pool boundaries.
* A timer loop, an error loop and a clarification loop all sit near one join gateway.

### Structure

**Elements**

- Clinical Trial Site: AdverseEventDetected, DocumentAdverseEventTask, SafetyNarrativeDraftingTask, AssessSeriousnessTask, SeriousAdverseEventGateway, LogStandardRegistryTask, RoutineCaseArchivedEnd, TransmitE2BReportTask, SiteFollowUpVisitTask, FollowUpDeadlineTimer, IssueInvestigationalSiteHoldTask, NotifyEthicsCommitteeTask
- Safety Management CRO: IngestionValidationTask, TriagingGateway, ClarificationRequestTask, MeddraCodingTask, SignalDetectionTask, LiteratureReviewTask, MedicalCausalityAssessmentTask, CausalityEvaluationGateway, StandardSafetyDatabaseTask, PeriodicSafetyUpdateReportTask, PeriodicReportLoggedEnd, SuspectedUnexpectedReactionGateway, SafetyReviewJoinGateway, UnblindTrialArmTask
- Data Safety Monitoring Board: AdjudicateBenefitRiskTask, BenefitRiskGateway, ExtendedReviewTimer, RecommendationIssuedEvent, ConveneEmergencySessionTask, ReviewUnblindedDataTask, MinutesApprovalTask
- Regulatory Oversight Authority: FastTrackSafetyNoticeTask, AcknowledgeNoticeTask, DraftRegulatorySubmissionTask, FinalComplianceValidationTask, SubmitSafetyAdvisoryTask, PublishEudraVigilanceAlertTask, RegulatoryTrialInterventionEnd, SubmissionRejectedErrorEvent

**Connections**

- AdverseEventDetected -> DocumentAdverseEventTask
- DocumentAdverseEventTask -> SafetyNarrativeDraftingTask
- SafetyNarrativeDraftingTask -> AssessSeriousnessTask
- AssessSeriousnessTask -> SeriousAdverseEventGateway
- SeriousAdverseEventGateway -> LogStandardRegistryTask (the event is not serious)
- LogStandardRegistryTask -> RoutineCaseArchivedEnd
- SeriousAdverseEventGateway -> TransmitE2BReportTask (the event is serious)
- TransmitE2BReportTask -> IngestionValidationTask (sends the safety report; message)
- IngestionValidationTask -> TriagingGateway
- TriagingGateway -> ClarificationRequestTask (the data has errors)
- ClarificationRequestTask -> DocumentAdverseEventTask (requests a corrected report; message)
- TriagingGateway -> MeddraCodingTask (the data is valid)
- MeddraCodingTask -> SignalDetectionTask
- SignalDetectionTask -> LiteratureReviewTask
- LiteratureReviewTask -> MedicalCausalityAssessmentTask
- MedicalCausalityAssessmentTask -> CausalityEvaluationGateway
- CausalityEvaluationGateway -> StandardSafetyDatabaseTask (causality is unconfirmed)
- StandardSafetyDatabaseTask -> PeriodicSafetyUpdateReportTask
- PeriodicSafetyUpdateReportTask -> PeriodicReportLoggedEnd
- CausalityEvaluationGateway -> SuspectedUnexpectedReactionGateway (causality is confirmed)
- SuspectedUnexpectedReactionGateway -> FastTrackSafetyNoticeTask (the event is life-threatening; message)
- FastTrackSafetyNoticeTask -> AcknowledgeNoticeTask
- AcknowledgeNoticeTask -> DraftRegulatorySubmissionTask
- SuspectedUnexpectedReactionGateway -> ConveneEmergencySessionTask (standard track; message)
- SuspectedUnexpectedReactionGateway -> UnblindTrialArmTask (standard track)
- SuspectedUnexpectedReactionGateway -> IssueInvestigationalSiteHoldTask (standard track; message)
- IssueInvestigationalSiteHoldTask -> NotifyEthicsCommitteeTask
- NotifyEthicsCommitteeTask -> SiteFollowUpVisitTask
- SiteFollowUpVisitTask -> FollowUpDeadlineTimer
- FollowUpDeadlineTimer -> SafetyReviewJoinGateway (the follow-up deadline passes; message)
- ConveneEmergencySessionTask -> ReviewUnblindedDataTask
- UnblindTrialArmTask -> ReviewUnblindedDataTask (delivers unblinded data; message)
- ReviewUnblindedDataTask -> MinutesApprovalTask
- MinutesApprovalTask -> SafetyReviewJoinGateway
- SafetyReviewJoinGateway -> AdjudicateBenefitRiskTask
- AdjudicateBenefitRiskTask -> BenefitRiskGateway
- BenefitRiskGateway -> MedicalCausalityAssessmentTask (further inquiry is demanded; message)
- BenefitRiskGateway -> ExtendedReviewTimer (the board needs more time)
- ExtendedReviewTimer -> AdjudicateBenefitRiskTask (the review period ends)
- BenefitRiskGateway -> RecommendationIssuedEvent (the safety ratio is acceptable)
- RecommendationIssuedEvent -> DraftRegulatorySubmissionTask (sends the recommendation; message)
- DraftRegulatorySubmissionTask -> FinalComplianceValidationTask
- FinalComplianceValidationTask -> SubmitSafetyAdvisoryTask
- FinalComplianceValidationTask -> SubmissionRejectedErrorEvent (validation fails)
- SubmissionRejectedErrorEvent -> DraftRegulatorySubmissionTask (the draft is reworked)
- SubmitSafetyAdvisoryTask -> PublishEudraVigilanceAlertTask
- PublishEudraVigilanceAlertTask -> RegulatoryTrialInterventionEnd
- PublishEudraVigilanceAlertTask -> SiteFollowUpVisitTask (informs the site of the alert; message)

### Sources

* ICH E2A Clinical Safety Data Management: Definitions and Standards for Expedited Reporting (FDA / EMA harmonized standard).
* European Medicines Agency Guideline on Good Pharmacovigilance Practices (GVP) Module VI.

### Uncertain

* The domain details were written to give the diagram a realistic shape; they were not checked against the cited sources.

---

## bpmn-C-02 — Cross-Border E-Commerce Order Fulfilment with Fraud Review, Customs and Returns

* **type:** bpmn
* **level:** C
* **elements:** 46
* **connections:** 55
* **groups:** Customer, Online Shop, Payment and Fraud Service, Logistics Carrier

### Brief

The model has 46 elements in 4 groups: Customer, Online Shop, Payment and Fraud Service, Logistics Carrier. Every name below is one element to draw, and every sentence describes connections to draw.

In Customer: OrderIntentStarted flows to PlaceOrderTask. PlaceOrderTask sends a message to ValidateOrderTask (sends the order). ProvideVerificationTask sends a message to ManualReviewTask (sends identity documents). ReceiveParcelTask flows to SatisfiedGateway. SatisfiedGateway flows to OrderCompletedEnd if the customer is satisfied; flows to RequestReturnTask if the customer is not satisfied. RequestReturnTask sends a message to InspectReturnTask (asks to return the item).

In Online Shop: ValidateOrderTask flows to StockCheckGateway. StockCheckGateway flows to BackorderNoticeTask if the item is out of stock; flows to ReserveStockTask if the item is in stock. BackorderNoticeTask flows to CancelOrderTask. ReserveStockTask flows to RequestPaymentTask. RequestPaymentTask sends a message to AuthorizePaymentTask (asks for authorization). ParallelPrepGateway flows to PickAndPackTask; flows to GenerateInvoiceTask; flows to CustomsDeclarationTask. PickAndPackTask flows to PrepJoinGateway. GenerateInvoiceTask flows to PrepJoinGateway. CustomsDeclarationTask flows to PrepJoinGateway. PrepJoinGateway flows to HandoverToCarrierTask. HandoverToCarrierTask sends a message to ScheduleCollectionTask (books the pickup). InspectReturnTask flows to RefundGateway. RefundGateway flows to IssueRefundTask if the item is accepted; flows to ReturnRejectedEnd if the item is rejected. IssueRefundTask sends a message to ProcessRefundTask (asks for the refund); flows to RestockItemTask. RestockItemTask flows to RestockedEnd. CancelOrderTask flows to OrderCancelledEnd.

In Payment and Fraud Service: AuthorizePaymentTask flows to FraudScoreTask. FraudScoreTask flows to FraudGateway. FraudGateway flows to CapturePaymentTask if the risk is low; flows to ManualReviewTask if the risk is medium; flows to PaymentDeclinedErrorEvent if the risk is high. ManualReviewTask sends a message to ProvideVerificationTask (asks for documents); flows to VerificationTimer. VerificationTimer flows to ReviewOutcomeGateway if the waiting period ends. ReviewOutcomeGateway flows to CapturePaymentTask if the customer is verified; flows to PaymentDeclinedErrorEvent if the customer is not verified; flows to ManualReviewTask if more evidence is needed. CapturePaymentTask sends a message to ParallelPrepGateway (the payment is captured). PaymentDeclinedErrorEvent sends a message to CancelOrderTask (the payment is declined). ProcessRefundTask flows to RefundSettledEnd.

In Logistics Carrier: ScheduleCollectionTask flows to CollectParcelTask. CollectParcelTask flows to CustomsClearanceTask. CustomsClearanceTask flows to CustomsGateway. CustomsGateway flows to LineHaulTransportTask if the parcel is cleared; flows to HoldParcelTask if the parcel is held for inspection. HoldParcelTask flows to CustomsClearanceTask if the inspection is finished. LineHaulTransportTask flows to LastMileDeliveryTask. LastMileDeliveryTask flows to DeliveryAttemptGateway. DeliveryAttemptGateway sends a message to ReceiveParcelTask (the parcel is delivered); flows to LastMileDeliveryTask if the next attempt is scheduled; flows to ReturnToSenderTask if three attempts failed. ReturnToSenderTask flows to ReturnToSenderEnd; sends a message to InspectReturnTask (the parcel is back at the shop).

### Must show

* The 4 groups (Customer, Online Shop, Payment and Fraud Service, Logistics Carrier) contain exactly the elements listed under Structure.
* A parallel split into three tasks (ParallelPrepGateway) and its join (PrepJoinGateway).
* Fan-out of three: FraudGateway, ParallelPrepGateway, DeliveryAttemptGateway, ReviewOutcomeGateway.
* 4 loops: ReviewOutcomeGateway to ManualReviewTask, HoldParcelTask to CustomsClearanceTask, DeliveryAttemptGateway to LastMileDeliveryTask, and the verification exchange between ManualReviewTask and ProvideVerificationTask.
* 11 connections cross between groups; 11 of them are message flows.

### Traps

* Three message flows meet in the Online Shop pool from three other pools (CapturePaymentTask, PaymentDeclinedErrorEvent, ReturnToSenderTask or RequestReturnTask), so lines converge on a few elements.
* The customer pool is small but receives messages from two pools and sends to two.
* A returned parcel starts a second process (inspection and refund) inside the same pools.

### Structure

**Elements**

- Customer: OrderIntentStarted, PlaceOrderTask, ProvideVerificationTask, ReceiveParcelTask, SatisfiedGateway, RequestReturnTask, OrderCompletedEnd
- Online Shop: ValidateOrderTask, StockCheckGateway, BackorderNoticeTask, ReserveStockTask, RequestPaymentTask, ParallelPrepGateway, PickAndPackTask, GenerateInvoiceTask, CustomsDeclarationTask, PrepJoinGateway, HandoverToCarrierTask, InspectReturnTask, RefundGateway, IssueRefundTask, RestockItemTask, RestockedEnd, CancelOrderTask, OrderCancelledEnd, ReturnRejectedEnd
- Payment and Fraud Service: AuthorizePaymentTask, FraudScoreTask, FraudGateway, ManualReviewTask, VerificationTimer, ReviewOutcomeGateway, CapturePaymentTask, PaymentDeclinedErrorEvent, ProcessRefundTask, RefundSettledEnd
- Logistics Carrier: ScheduleCollectionTask, CollectParcelTask, CustomsClearanceTask, CustomsGateway, HoldParcelTask, LineHaulTransportTask, LastMileDeliveryTask, DeliveryAttemptGateway, ReturnToSenderTask, ReturnToSenderEnd

**Connections**

- OrderIntentStarted -> PlaceOrderTask
- PlaceOrderTask -> ValidateOrderTask (sends the order; message)
- ProvideVerificationTask -> ManualReviewTask (sends identity documents; message)
- ReceiveParcelTask -> SatisfiedGateway
- SatisfiedGateway -> OrderCompletedEnd (the customer is satisfied)
- SatisfiedGateway -> RequestReturnTask (the customer is not satisfied)
- RequestReturnTask -> InspectReturnTask (asks to return the item; message)
- ValidateOrderTask -> StockCheckGateway
- StockCheckGateway -> BackorderNoticeTask (the item is out of stock)
- BackorderNoticeTask -> CancelOrderTask
- StockCheckGateway -> ReserveStockTask (the item is in stock)
- ReserveStockTask -> RequestPaymentTask
- RequestPaymentTask -> AuthorizePaymentTask (asks for authorization; message)
- ParallelPrepGateway -> PickAndPackTask
- ParallelPrepGateway -> GenerateInvoiceTask
- ParallelPrepGateway -> CustomsDeclarationTask
- PickAndPackTask -> PrepJoinGateway
- GenerateInvoiceTask -> PrepJoinGateway
- CustomsDeclarationTask -> PrepJoinGateway
- PrepJoinGateway -> HandoverToCarrierTask
- HandoverToCarrierTask -> ScheduleCollectionTask (books the pickup; message)
- InspectReturnTask -> RefundGateway
- RefundGateway -> IssueRefundTask (the item is accepted)
- RefundGateway -> ReturnRejectedEnd (the item is rejected)
- IssueRefundTask -> ProcessRefundTask (asks for the refund; message)
- IssueRefundTask -> RestockItemTask
- RestockItemTask -> RestockedEnd
- CancelOrderTask -> OrderCancelledEnd
- AuthorizePaymentTask -> FraudScoreTask
- FraudScoreTask -> FraudGateway
- FraudGateway -> CapturePaymentTask (the risk is low)
- FraudGateway -> ManualReviewTask (the risk is medium)
- FraudGateway -> PaymentDeclinedErrorEvent (the risk is high)
- ManualReviewTask -> ProvideVerificationTask (asks for documents; message)
- ManualReviewTask -> VerificationTimer
- VerificationTimer -> ReviewOutcomeGateway (the waiting period ends)
- ReviewOutcomeGateway -> CapturePaymentTask (the customer is verified)
- ReviewOutcomeGateway -> PaymentDeclinedErrorEvent (the customer is not verified)
- ReviewOutcomeGateway -> ManualReviewTask (more evidence is needed)
- CapturePaymentTask -> ParallelPrepGateway (the payment is captured; message)
- PaymentDeclinedErrorEvent -> CancelOrderTask (the payment is declined; message)
- ProcessRefundTask -> RefundSettledEnd
- ScheduleCollectionTask -> CollectParcelTask
- CollectParcelTask -> CustomsClearanceTask
- CustomsClearanceTask -> CustomsGateway
- CustomsGateway -> LineHaulTransportTask (the parcel is cleared)
- CustomsGateway -> HoldParcelTask (the parcel is held for inspection)
- HoldParcelTask -> CustomsClearanceTask (the inspection is finished)
- LineHaulTransportTask -> LastMileDeliveryTask
- LastMileDeliveryTask -> DeliveryAttemptGateway
- DeliveryAttemptGateway -> ReceiveParcelTask (the parcel is delivered; message)
- DeliveryAttemptGateway -> LastMileDeliveryTask (the next attempt is scheduled)
- DeliveryAttemptGateway -> ReturnToSenderTask (three attempts failed)
- ReturnToSenderTask -> ReturnToSenderEnd
- ReturnToSenderTask -> InspectReturnTask (the parcel is back at the shop; message)

### Sources

* OMG Business Process Model and Notation 2.0 specification (event, gateway and message flow semantics): https://www.omg.org/spec/BPMN/2.0/

### Uncertain

* The domain details were written to give the diagram a realistic shape; they were not checked against real fulfilment or card-network rules.
