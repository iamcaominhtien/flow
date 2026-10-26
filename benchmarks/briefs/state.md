# Briefs: State

Three briefs at levels A, B and C. See [README](README.md) for the format and how to run them.

---

## state-A-01 — Kubernetes Pod Container Lifecycle and Phase Transition Model

* **type:** state
* **level:** A
* **elements:** 9
* **connections:** 11
* **groups:** none

### Brief

The state model represents execution phases of a Kubernetes pod.
Execution initiates when the API server creates a manifest, placing the pod into PendingState. When worker node resources are scheduled, PendingState transitions via imagePullSuccess to ContainerCreatingState. If image pulling fails, PendingState transitions via pullError to ImagePullBackOffState. From ImagePullBackOffState, retryTimerExpiry loops back into ContainerCreatingState.
Once containers initialize successfully, ContainerCreatingState advances via containerStart to RunningState. When all foreground processes exit with exit code zero, RunningState transitions via zeroExitCode to SucceededState. If any container crashes with non-zero exit codes, RunningState transitions via nonZeroExitCode to CrashLoopBackOffState. From CrashLoopBackOffState, backoffTimerExpiry loops back into RunningState.
If cluster administrators trigger pod eviction, RunningState transitions via administrativeEvict to FailedState. During node drainage or API deletion, RunningState transitions via gracePeriodExpired to TerminatingState. SucceededState, FailedState, and TerminatingState terminate into PodGarbageCollected.

### Must show

* The central operational hub centered on RunningState.
* Two distinct error mitigation loops: retryTimerExpiry entering ContainerCreatingState, and backoffTimerExpiry entering RunningState.
* PodGarbageCollected acting as the definitive terminal state.

### Traps

* Dual recovery loops entering ContainerCreatingState and RunningState from opposite backoff nodes complicate planar state machine layout.

### Sources

* https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ — Pod phases, container restart policies, and probing conditions.

### Uncertain

* none

---

## state-B-01 — Distributed E-Commerce Order Fulfillment and Settlement Engine

* **type:** state
* **level:** B
* **elements:** 22
* **connections:** 27
* **groups:** Checkout Processing, Warehouse Fulfillment, Post-Delivery Servicing

### Brief

The state machine models order states across Checkout Processing, Warehouse Fulfillment, and Post-Delivery Servicing.
Lifecycle begins at OrderSubmittedState in Checkout Processing. The system evaluates authorization via PaymentAuthorizationPending. If authorization times out, PaymentAuthorizationPending transitions to PaymentFailedState, which loops via paymentRetryEvent back to PaymentAuthorizationPending. If authorization succeeds, it transitions to FraudScreeningReview. If fraud scoring fails, it transitions to OrderRejectedState.
If approved, it advances to InventoryReservationPending. If items are out of stock, it transitions to BackorderHoldState. When inventory restocks, restockEvent transitions BackorderHoldState back to InventoryReservationPending.
Upon successful stock reservation, the order advances to PickListGenerated in Warehouse Fulfillment. From PickListGenerated, it enters ItemsPickingInProgress, followed by PackingVerificationPending, and reaches PackageStagedForCarrier.
Carrier pickup moves the order to TransitCarrierHandover, which transitions to InTransitOutForDelivery. If delivery fails due to incorrect address, InTransitOutForDelivery transitions to DeliveryAttemptFailed, which loops via reattemptDispatchEvent back to InTransitOutForDelivery.
Successful delivery moves the order into PackageDeliveredCustomer within Post-Delivery Servicing. From PackageDeliveredCustomer, customer return triggers ReturnInitiatedState. ReturnInitiatedState advances to ReturnInspectedWarehouse. If goods are damaged, it transitions to DisputeArbitrationState. If goods pass inspection, it transitions to RefundProcessedState, which concludes at OrderArchivedClosed. In parallel, if no return occurs within warranty limits, PackageDeliveredCustomer transitions via warrantyPeriodElapsed directly to OrderArchivedClosed.

### Must show

* Grouping across Checkout Processing, Warehouse Fulfillment, and Post-Delivery Servicing.
* Three error recovery loops: paymentRetryEvent, restockEvent, and reattemptDispatchEvent.
* Direct skip: warrantyPeriodElapsed transitioning PackageDeliveredCustomer directly to OrderArchivedClosed without entering return processing.

### Traps

* High density of sequential fulfillment states combined with peripheral return/dispute loops causes horizontal elongation and overlapping reverse transition arcs.

### Sources

* Enterprise Integration Patterns (Gregor Hohpe) — Composed message processor and order broker lifecycle states.
* Shopify Engineering: "Order Management System Architecture and Lifecycle State Graphs".

### Uncertain

* none

---

## state-C-01 — Autonomous Spacecraft Rendezvous and Proximity Docking System

* **type:** state
* **level:** C
* **elements:** 44
* **connections:** 56
* **groups:** Far-Field Rendezvous, Proximity Operations Zone, Terminal Docking Corridor, Contingency Abort Safe-Mode

### Brief

The state machine governs an autonomous spacecraft docking sequence across Far-Field Rendezvous, Proximity Operations Zone, Terminal Docking Corridor, and Contingency Abort Safe-Mode.
The flight sequence starts at OrbitalInsertionPhase inside Far-Field Rendezvous. OrbitalInsertionPhase transitions via orbitConfirmed to GroundTrackingAcquisition, which transitions via ephemerisUpload to HohmannTransferPhase. HohmannTransferPhase transitions via burnComplete to CoEllipticPhasingOrbit. From CoEllipticPhasingOrbit, sensor lock advances to RelativeGpsNavigationAcquired. If GPS integrity degrades, RelativeGpsNavigationAcquired enters FilterDriftHold, which loops via gnssRelock back to RelativeGpsNavigationAcquired.
When relative navigation converges, the spacecraft enters ApproachCorridorGate in Proximity Operations Zone. ApproachCorridorGate transitions via rangeBelow5km to LidarAcquisitionMode, which advances to OpticalPoseEstimationActive. OpticalPoseEstimationActive transitions to StationKeepingHold1km. From StationKeepingHold1km, circumnavigationCommand transitions to FlyAroundInspectionPhase, which loops via inspectionPassComplete back to StationKeepingHold1km.
When inspection validates target status, StationKeepingHold1km advances to ApproachInitiationAxis in Terminal Docking Corridor. ApproachInitiationAxis passes through RangeHold200m to CrossTrackAlignmentMode, and reaches RangeHold50m. RangeHold50m advances to LaserRetroreflectorTracking, then to ContactProbeExtensionMode.
From ContactProbeExtensionMode, AlignmentSensorEvaluator fans out three ways: transitioning to CaptureLatchEngagement upon alignment; to ThrusterPlumeHold upon thruster backpressure; and directly to CollisionAvoidanceManeuverAbort within Contingency Abort Safe-Mode upon trajectory violation, skipping intermediate stages.
CaptureLatchEngagement leads to HardCaptureRingMotorDrive, then to UmbilicalInterfaceMating, concluding at SecureDockingAchieved.
From ThrusterPlumeHold, settleTimerExpired loops back to RangeHold50m. If sensor telemetry fails at any point, OpticalPoseEstimationActive, ApproachInitiationAxis, and LaserRetroreflectorTracking execute abort transitions to CollisionAvoidanceManeuverAbort.
CollisionAvoidanceManeuverAbort transitions to RetroBurnExecution, followed by AutonomousSeparationVector, entering SafeDriftTrajectory. From SafeDriftTrajectory, recoveryVerification transitions to SunPointingAttitudeAcquired, which concludes at MissionAbortSafeHold.

### Must show

* Four architectural phases: Far-Field Rendezvous, Proximity Operations Zone, Terminal Docking Corridor, and Contingency Abort Safe-Mode.
* AlignmentSensorEvaluator branching three ways: to CaptureLatchEngagement, ThrusterPlumeHold, and CollisionAvoidanceManeuverAbort.
* CollisionAvoidanceManeuverAbort acting as a global abort sink receiving skip connections from three prior operational phases.
* Two operational loops: FilterDriftHold returning to RelativeGpsNavigationAcquired, and FlyAroundInspectionPhase returning to StationKeepingHold1km.

### Traps

* Multiple convergence transitions from distant outer-loop operational phases into a single emergency abort sink create high crossing counts across composite state boundaries.

### Sources

* NASA SP-2010-579: "Autonomous Rendezvous and Docking Technology Assessment".
* ESA ECSS-E-ST-60-20C: "Space Engineering: Star and optical navigation sensor operational modes and state machines".

### Uncertain

* none
