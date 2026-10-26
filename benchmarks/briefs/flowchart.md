# Briefs: Flowchart

Three briefs at levels A, B and C. See [README](README.md) for the format and how to run them.

---

## flowchart-A-01 — Git Feature Branch Integration Workflow

* **type:** flowchart
* **level:** A
* **elements:** 10
* **connections:** 10
* **groups:** none

### Brief

The workflow starts at WorkspaceEdit. A developer makes local modifications and passes them from WorkspaceEdit to StagingIndex using git add. From StagingIndex, the flow proceeds to CommitDecision to evaluate whether staged modifications are complete. If changes are incomplete, CommitDecision routes back to WorkspaceEdit. If changes are complete, CommitDecision advances to LocalCommit. From LocalCommit, the flow triggers RemoteFetch to inspect the tracking branch. RemoteFetch routes directly into ConflictDecision. If upstream conflicts exist, ConflictDecision directs to MergeAbort. If no conflicts exist, ConflictDecision proceeds to FastForwardMerge. From FastForwardMerge, the process runs PushRemote to synchronize commits with origin. PushRemote terminates successfully at CompletedState, while MergeAbort terminates the branch flow at TerminalAbort.

### Must show

* FastForwardMerge is reached only when ConflictDecision evaluates to no conflicts.
* A backward loop connects CommitDecision back to WorkspaceEdit when changes require revision.
* TerminalAbort and CompletedState serve as the two terminal endpoints.

### Traps

* The backward loop from CommitDecision to WorkspaceEdit introduces a cyclic dependency that can invert linear topological rank sorting.

### Sources

* https://git-scm.com/docs/git-merge — Technical rules governing fast-forward merges, upstream fetches, and conflict abort conditions.

### Uncertain

* none

---

## flowchart-B-01 — Emergency Severity Index Hospital Triage Protocol

* **type:** flowchart
* **level:** B
* **elements:** 21
* **connections:** 28
* **groups:** Immediate Resuscitation, Acuity Assessment, Treatment Allocation

### Brief

Patient flow begins at TriageEntry inside Acuity Assessment. From TriageEntry, the flow evaluates UnstableCheck. If life threat is present, UnstableCheck transfers to ResuscitationBay within Immediate Resuscitation. ResuscitationBay advances to ResuscitationReview, which routes to EmergentCare. If stable, UnstableCheck leads to HighRiskCheck. If high risk is identified, HighRiskCheck directs to EmergentCare. EmergentCare moves to ObservationWard, which routes into DischargeLounge.
If negative, HighRiskCheck advances to ResourceEvaluation inside Treatment Allocation. ResourceEvaluation branches based on predicted hospital interventions: zero resources routes to NonUrgentCare; one resource routes to LessUrgentCare; two or more resources directs to VitalSignCheck. VitalSignCheck evaluates systemic physiological indicators: abnormal vitals escalate to UrgentCare; normal vitals progress to PediatricFeverCheck. If pediatric criteria trigger, PediatricFeverCheck sends the patient to InfantSpecialist; otherwise, PediatricFeverCheck directs to UrgentCare.
Patients in UrgentCare undergo LabTesting, which leads to ImagingOrder, followed by IVHydration. After stabilization, IVHydration routes to ClinicalHold. If decompensation occurs, ClinicalHold loops back to VitalSignCheck. From ClinicalHold, patients advance to SecondaryTriage. If additional complications arise, SecondaryTriage loops back to ResourceEvaluation. Otherwise, SecondaryTriage routes to DischargeLounge. Finally, NonUrgentCare, LessUrgentCare, and InfantSpecialist merge into DischargeLounge, terminating at TriageExit.

### Must show

* Multi-lane partitioning across Immediate Resuscitation, Acuity Assessment, and Treatment Allocation.
* Three distinct forward branches leaving ResourceEvaluation based on resource counts.
* Two cycle loops: ClinicalHold returning to VitalSignCheck, and SecondaryTriage returning to ResourceEvaluation.

### Traps

* Multi-tier diamond splits followed by reconvergent lanes into a single discharge corridor create wide layout bloat if edge ranks are not constrained.

### Sources

* https://www.ahrq.gov/patient-safety/settings/emergency-dept/esi.html — Five-level clinical triage decision tree, vital-sign parameter thresholds, and resource allocation logic.

### Uncertain

* none

---

## flowchart-C-01 — BGP-4 Best Path Decision Engine (RFC 4271)

* **type:** flowchart
* **level:** C
* **elements:** 42
* **connections:** 48
* **groups:** Inbound Route Filter, Policy Decision Pipeline, Rib Installation Engine

### Brief

The engine initiates at AdjRibIn within Inbound Route Filter. AdjRibIn sends candidate routes to FlapFilter. If route flapping exceeds limits, FlapFilter routes to DampeningHold, which loops back to FlapFilter once decay timers expire. If accepted, FlapFilter advances to PrefixFilter, which routes to AsPathFilter, followed by CommunityFilter. CommunityFilter advances to NextHopCheck inside Policy Decision Pipeline. If the next hop is unreachable, NextHopCheck drops to DropUnreachable. If reachable, NextHopCheck advances to WeightEvaluator.
If Cisco weight differs, WeightEvaluator skips subsequent policies and transfers directly to LocRibCandidate within Rib Installation Engine. If weights are identical, WeightEvaluator advances to LocalPrefCheck. If local preferences differ, LocalPrefCheck resolves to LocRibCandidate; otherwise, it proceeds to LocallyOriginatedCheck. LocallyOriginatedCheck resolves local generation to LocRibCandidate, or proceeds to AsPathCheck. AsPathCheck routes shortest AS sequences to LocRibCandidate, or advances to OriginCheck. OriginCheck prioritizes IGP over EGP and passes ties to MedCheck. MedCheck evaluates Multi-Exit Discriminators, passing ties to PeerTypeCheck. PeerTypeCheck prefers external eBGP over internal iBGP, passing unresolved ties to IgpCostCheck.
IgpCostCheck prefers the lowest interior gateway metric to next hop, passing ties to MultipathGateway. MultipathGateway splits three ways: into EcmpGroup for parallel forwarding, into RouterIdCheck for deterministic tie-breaking, and directly into LocRibCandidate. RouterIdCheck routes lowest ID to ClusterListCheck, which resolves shortest cluster lists to PeerAddressCheck. PeerAddressCheck routes lowest IP to LocRibCandidate. EcmpGroup routes to EcmpInstall, which advances to LocRibCandidate.
LocRibCandidate initiates RibValidation. If validation fails, RibValidation loops back to AdjRibIn. If validation succeeds, RibValidation advances to RibTableInstall, leading to ForwardingInformationBase, BfdMonitor, and PrefixExport. PrefixExport routes to PolicyOutFilter, CommunityTagging, AsPathPrepender, and MedSetter. MedSetter routes to ExportEvaluationGateway. If rejected, ExportEvaluationGateway drops to DropExportRoute. If accepted, ExportEvaluationGateway routes to AdjRibOut, which notifies PeerSyncNotification and AuditLogSink.

### Must show

* Cisco weight skipping intermediate policy decision nodes to leap directly from Policy Decision Pipeline to LocRibCandidate.
* MultipathGateway fanning out three distinct branches to EcmpGroup, RouterIdCheck, and LocRibCandidate.
* Two cyclic back-edges: DampeningHold looping back to FlapFilter, and RibValidation looping back across groups to AdjRibIn.
* Clean containment of logical routing tables across Inbound Route Filter, Policy Decision Pipeline, and Rib Installation Engine.

### Traps

* The long transitive skip from WeightEvaluator to LocRibCandidate spans across 6 sequential decision ranks, causing severe edge overlap if not routed around intermediate nodes.

### Sources

* https://datatracker.ietf.org/doc/html/rfc4271 — Section 9.1 BGP Route Selection Procedure specifications.
* https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/13753-25.html — Vendor implementation of Weight, AIGP metric integration, and multipath relaxation.

### Uncertain

* none
