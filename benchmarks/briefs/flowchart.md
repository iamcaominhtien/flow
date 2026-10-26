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
* **elements:** 43
* **connections:** 51
* **groups:** Inbound Route Filter, Policy Decision Pipeline, Rib Installation Engine, Export Pipeline

### Brief

The model has 43 steps in 4 groups: Inbound Route Filter, Policy Decision Pipeline, Rib Installation Engine, Export Pipeline. Every name below is one step to draw, and every sentence describes connections to draw.

In Inbound Route Filter: RouteRefreshRequest routes to AdjRibIn. AdjRibIn splits 2 ways: to FlapFilter; if route refresh is configured, to SoftReconfigStore. FlapFilter splits 2 ways: if flapping exceeds the limit, to DampeningHold; if the route is stable, to PrefixFilter. If decay timers expire, DampeningHold routes to FlapFilter. PrefixFilter routes to AsPathFilter. AsPathFilter routes to CommunityFilter. CommunityFilter routes to NextHopCheck.

In Policy Decision Pipeline: NextHopCheck splits 2 ways: if the next hop is unreachable, to DropUnreachable; if the next hop is reachable, to WeightEvaluator. WeightEvaluator splits 2 ways: if the Cisco weights differ, to LocRibCandidate; if the weights are identical, to LocalPrefCheck. LocalPrefCheck splits 2 ways: if the local preferences differ, to LocRibCandidate; if the local preferences are equal, to LocallyOriginatedCheck. LocallyOriginatedCheck splits 2 ways: if the route was originated locally, to LocRibCandidate; if the route was learned from a peer, to AsPathCheck. AsPathCheck splits 2 ways: if one AS path is shorter, to LocRibCandidate; if the AS path lengths tie, to OriginCheck. If the origin codes tie, OriginCheck routes to MedCheck. If the MED values tie, MedCheck routes to PeerTypeCheck. If the peer types tie, PeerTypeCheck routes to AigpMetricCheck. If the AIGP metrics tie, AigpMetricCheck routes to IgpCostCheck. If the IGP costs tie, IgpCostCheck routes to MultipathGateway. MultipathGateway splits 3 ways: if multipath is enabled, to EcmpGroup; to RouterIdCheck; if one path is clearly best, to LocRibCandidate. EcmpGroup routes to EcmpInstall. EcmpInstall routes to LocRibCandidate. If the router IDs differ, RouterIdCheck routes to OriginatorIdCheck. OriginatorIdCheck routes to ClusterListCheck. ClusterListCheck routes to PeerAddressCheck. PeerAddressCheck routes to LocRibCandidate.

In Rib Installation Engine: LocRibCandidate routes to AdminDistanceCheck. AdminDistanceCheck routes to RibValidation. RibValidation splits 2 ways: if validation fails, to AdjRibIn; if validation succeeds, to RibTableInstall. RibTableInstall splits 4 ways: to ForwardingInformationBase; to BfdMonitor; to ConvergenceTimer; to PrefixExport. If the timer expires before convergence, ConvergenceTimer routes to RibTableInstall.

In Export Pipeline: PrefixExport routes to PolicyOutFilter. PolicyOutFilter routes to CommunityTagging. CommunityTagging routes to AsPathPrepender. AsPathPrepender routes to MedSetter. MedSetter routes to ExportEvaluationGateway. ExportEvaluationGateway splits 2 ways: if the export is rejected, to DropExportRoute; if the export is accepted, to AdjRibOut. AdjRibOut splits 2 ways: to PeerSyncNotification; to AuditLogSink.

### Must show

* The 4 groups (Inbound Route Filter, Policy Decision Pipeline, Rib Installation Engine, Export Pipeline) contain exactly the elements listed under Structure.
* Fan-out of three or more: RibTableInstall (4), MultipathGateway (3).
* 3 connections return to an earlier element: DampeningHold to FlapFilter, RibValidation to AdjRibIn, ConvergenceTimer to RibTableInstall.
* 10 connections cross between groups, for example CommunityFilter to NextHopCheck, WeightEvaluator to LocRibCandidate, LocalPrefCheck to LocRibCandidate.

### Traps

* A long skip edge (WeightEvaluator to LocRibCandidate) passes many ranks, and one validation loop returns across two groups.
* Two small loops sit inside a main path with a four-way fan-out near its end.

### Structure

**Elements**

- Inbound Route Filter: RouteRefreshRequest, AdjRibIn, FlapFilter, DampeningHold, PrefixFilter, AsPathFilter, CommunityFilter, SoftReconfigStore
- Policy Decision Pipeline: NextHopCheck, DropUnreachable, WeightEvaluator, LocalPrefCheck, LocallyOriginatedCheck, AsPathCheck, OriginCheck, MedCheck, PeerTypeCheck, AigpMetricCheck, IgpCostCheck, MultipathGateway, EcmpGroup, EcmpInstall, RouterIdCheck, OriginatorIdCheck, ClusterListCheck, PeerAddressCheck
- Rib Installation Engine: LocRibCandidate, AdminDistanceCheck, RibValidation, RibTableInstall, ForwardingInformationBase, BfdMonitor, ConvergenceTimer
- Export Pipeline: PrefixExport, PolicyOutFilter, CommunityTagging, AsPathPrepender, MedSetter, ExportEvaluationGateway, DropExportRoute, AdjRibOut, PeerSyncNotification, AuditLogSink

**Connections**

- AdjRibIn -> FlapFilter
- AdjRibIn -> SoftReconfigStore (route refresh is configured)
- RouteRefreshRequest -> AdjRibIn
- FlapFilter -> DampeningHold (flapping exceeds the limit)
- DampeningHold -> FlapFilter (decay timers expire)
- FlapFilter -> PrefixFilter (the route is stable)
- PrefixFilter -> AsPathFilter
- AsPathFilter -> CommunityFilter
- CommunityFilter -> NextHopCheck
- NextHopCheck -> DropUnreachable (the next hop is unreachable)
- NextHopCheck -> WeightEvaluator (the next hop is reachable)
- WeightEvaluator -> LocRibCandidate (the Cisco weights differ)
- WeightEvaluator -> LocalPrefCheck (the weights are identical)
- LocalPrefCheck -> LocRibCandidate (the local preferences differ)
- LocalPrefCheck -> LocallyOriginatedCheck (the local preferences are equal)
- LocallyOriginatedCheck -> LocRibCandidate (the route was originated locally)
- LocallyOriginatedCheck -> AsPathCheck (the route was learned from a peer)
- AsPathCheck -> LocRibCandidate (one AS path is shorter)
- AsPathCheck -> OriginCheck (the AS path lengths tie)
- OriginCheck -> MedCheck (the origin codes tie)
- MedCheck -> PeerTypeCheck (the MED values tie)
- PeerTypeCheck -> AigpMetricCheck (the peer types tie)
- AigpMetricCheck -> IgpCostCheck (the AIGP metrics tie)
- IgpCostCheck -> MultipathGateway (the IGP costs tie)
- MultipathGateway -> EcmpGroup (multipath is enabled)
- MultipathGateway -> RouterIdCheck
- MultipathGateway -> LocRibCandidate (one path is clearly best)
- EcmpGroup -> EcmpInstall
- EcmpInstall -> LocRibCandidate
- RouterIdCheck -> OriginatorIdCheck (the router IDs differ)
- OriginatorIdCheck -> ClusterListCheck
- ClusterListCheck -> PeerAddressCheck
- PeerAddressCheck -> LocRibCandidate
- LocRibCandidate -> AdminDistanceCheck
- AdminDistanceCheck -> RibValidation
- RibValidation -> AdjRibIn (validation fails)
- RibValidation -> RibTableInstall (validation succeeds)
- RibTableInstall -> ForwardingInformationBase
- RibTableInstall -> BfdMonitor
- RibTableInstall -> ConvergenceTimer
- RibTableInstall -> PrefixExport
- ConvergenceTimer -> RibTableInstall (the timer expires before convergence)
- PrefixExport -> PolicyOutFilter
- PolicyOutFilter -> CommunityTagging
- CommunityTagging -> AsPathPrepender
- AsPathPrepender -> MedSetter
- MedSetter -> ExportEvaluationGateway
- ExportEvaluationGateway -> DropExportRoute (the export is rejected)
- ExportEvaluationGateway -> AdjRibOut (the export is accepted)
- AdjRibOut -> PeerSyncNotification
- AdjRibOut -> AuditLogSink

### Sources

* https://datatracker.ietf.org/doc/html/rfc4271 — Section 9.1 BGP Route Selection Procedure specifications.
* https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/13753-25.html — Vendor implementation of Weight, AIGP metric integration, and multipath relaxation.

### Uncertain

* The domain details were written to give the diagram a realistic shape; they were not checked against the cited sources.
