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
* **elements:** 41
* **connections:** 51
* **groups:** Far-Field Rendezvous, Proximity Operations Zone, Terminal Docking Corridor, Contingency Abort Safe-Mode

### Brief

The model has 41 states in 4 groups: Far-Field Rendezvous, Proximity Operations Zone, Terminal Docking Corridor, Contingency Abort Safe-Mode. Every name below is one state to draw, and every sentence describes connections to draw.

In Far-Field Rendezvous: OrbitalInsertionPhase transitions via orbitConfirmed to GroundTrackingAcquisition. GroundTrackingAcquisition transitions via trackLocked to GroundContactWindow. GroundContactWindow transitions via ephemerisUpload to StarTrackerCalibration. StarTrackerCalibration transitions via attitudeKnown to TransferBurnPlanning. TransferBurnPlanning transitions via burnPlanApproved to HohmannTransferPhase. HohmannTransferPhase transitions via burnComplete to CoEllipticPhasingOrbit. CoEllipticPhasingOrbit transitions via sensorLock to RelativeGpsNavigationAcquired. RelativeGpsNavigationAcquired transitions via gpsIntegrityDegraded to FilterDriftHold, via relativeNavConverged to ApproachCorridorGate. FilterDriftHold transitions via gnssRelock to RelativeGpsNavigationAcquired, via driftExceedsLimit to NavigationFilterReset. NavigationFilterReset transitions via filterReinitialised to CoEllipticPhasingOrbit.

In Proximity Operations Zone: ApproachCorridorGate transitions via rangeBelow5km to LidarAcquisitionMode. LidarAcquisitionMode transitions via targetAcquired to OpticalPoseEstimationActive. OpticalPoseEstimationActive transitions via poseConverged to StationKeepingHold1km, via telemetryLost to CollisionAvoidanceManeuverAbort. StationKeepingHold1km transitions via circumnavigationCommand to FlyAroundInspectionPhase, via inspectionValidated to TargetAttitudeMatching. FlyAroundInspectionPhase transitions via inspectionPassComplete to StationKeepingHold1km, via closeApproachDetected to KeepOutSphereMonitor. KeepOutSphereMonitor transitions via rangeRestored to FlyAroundInspectionPhase, via keepOutSphereBreached to CollisionAvoidanceManeuverAbort. TargetAttitudeMatching transitions via attitudeMatched to DockingPortSelection. DockingPortSelection transitions via portSelected to ApproachInitiationAxis.

In Terminal Docking Corridor: ApproachInitiationAxis transitions via axisAligned to RangeHold200m, via telemetryLost to CollisionAvoidanceManeuverAbort. RangeHold200m transitions via goForDocking to CrossTrackAlignmentMode. CrossTrackAlignmentMode transitions via crossTrackNulled to RangeHold50m. RangeHold50m transitions via rangeBelow50m to LaserRetroreflectorTracking. LaserRetroreflectorTracking transitions via reflectorsLocked to VisualServoControl, via telemetryLost to CollisionAvoidanceManeuverAbort. VisualServoControl transitions via servoConverged to ContactProbeExtensionMode. ContactProbeExtensionMode transitions via probeExtended to AlignmentSensorEvaluator. AlignmentSensorEvaluator transitions via alignmentWithinTolerance to CaptureLatchEngagement, via thrusterBackpressure to ThrusterPlumeHold, via trajectoryViolation to CollisionAvoidanceManeuverAbort. CaptureLatchEngagement transitions via latchesClosed to HardCaptureRingMotorDrive. HardCaptureRingMotorDrive transitions via ringRetracted to CaptureConfirmationHold. CaptureConfirmationHold transitions via captureConfirmed to UmbilicalInterfaceMating, via captureLost to CollisionAvoidanceManeuverAbort. UmbilicalInterfaceMating transitions via umbilicalsMated to PostDockLeakCheck. PostDockLeakCheck transitions via pressureHolds to SecureDockingAchieved. ThrusterPlumeHold transitions via settleTimerExpired to RangeHold50m.

In Contingency Abort Safe-Mode: CollisionAvoidanceManeuverAbort transitions via abortLatched to AbortInhibitDisarm. AbortInhibitDisarm transitions via thrustersArmed to RetroBurnExecution. RetroBurnExecution transitions via burnComplete to AutonomousSeparationVector. AutonomousSeparationVector transitions via separationConfirmed to SafeDriftTrajectory. SafeDriftTrajectory transitions via recoveryVerification to SunPointingAttitudeAcquired. SunPointingAttitudeAcquired transitions via powerPositive to MissionAbortSafeHold. MissionAbortSafeHold transitions via groundCommandReceived to GroundIntervention. GroundIntervention transitions via retryApproved to ApproachCorridorGate.

### Must show

* The 4 groups (Far-Field Rendezvous, Proximity Operations Zone, Terminal Docking Corridor, Contingency Abort Safe-Mode) contain exactly the elements listed under Structure.
* Fan-out of three or more: AlignmentSensorEvaluator (3).
* 6 connections return to an earlier element: FilterDriftHold to RelativeGpsNavigationAcquired, NavigationFilterReset to CoEllipticPhasingOrbit, FlyAroundInspectionPhase to StationKeepingHold1km, KeepOutSphereMonitor to FlyAroundInspectionPhase, GroundIntervention to ApproachCorridorGate, ThrusterPlumeHold to RangeHold50m.
* 9 connections cross between groups, for example RelativeGpsNavigationAcquired to ApproachCorridorGate, DockingPortSelection to ApproachInitiationAxis, AlignmentSensorEvaluator to CollisionAvoidanceManeuverAbort.

### Traps

* Six states send an abort transition to one sink in the last group, from three different groups.
* Four small loops (hold and retry) are nested inside the forward path.

### Structure

**Elements**

- Far-Field Rendezvous: OrbitalInsertionPhase, GroundTrackingAcquisition, GroundContactWindow, StarTrackerCalibration, TransferBurnPlanning, HohmannTransferPhase, CoEllipticPhasingOrbit, RelativeGpsNavigationAcquired, FilterDriftHold, NavigationFilterReset
- Proximity Operations Zone: ApproachCorridorGate, LidarAcquisitionMode, OpticalPoseEstimationActive, StationKeepingHold1km, FlyAroundInspectionPhase, KeepOutSphereMonitor, TargetAttitudeMatching, DockingPortSelection
- Terminal Docking Corridor: ApproachInitiationAxis, RangeHold200m, CrossTrackAlignmentMode, RangeHold50m, LaserRetroreflectorTracking, VisualServoControl, ContactProbeExtensionMode, AlignmentSensorEvaluator, CaptureLatchEngagement, HardCaptureRingMotorDrive, CaptureConfirmationHold, UmbilicalInterfaceMating, PostDockLeakCheck, SecureDockingAchieved, ThrusterPlumeHold
- Contingency Abort Safe-Mode: CollisionAvoidanceManeuverAbort, AbortInhibitDisarm, RetroBurnExecution, AutonomousSeparationVector, SafeDriftTrajectory, SunPointingAttitudeAcquired, MissionAbortSafeHold, GroundIntervention

**Connections**

- OrbitalInsertionPhase -> GroundTrackingAcquisition (orbitConfirmed)
- GroundTrackingAcquisition -> GroundContactWindow (trackLocked)
- GroundContactWindow -> StarTrackerCalibration (ephemerisUpload)
- StarTrackerCalibration -> TransferBurnPlanning (attitudeKnown)
- TransferBurnPlanning -> HohmannTransferPhase (burnPlanApproved)
- HohmannTransferPhase -> CoEllipticPhasingOrbit (burnComplete)
- CoEllipticPhasingOrbit -> RelativeGpsNavigationAcquired (sensorLock)
- RelativeGpsNavigationAcquired -> FilterDriftHold (gpsIntegrityDegraded)
- FilterDriftHold -> RelativeGpsNavigationAcquired (gnssRelock)
- FilterDriftHold -> NavigationFilterReset (driftExceedsLimit)
- NavigationFilterReset -> CoEllipticPhasingOrbit (filterReinitialised)
- RelativeGpsNavigationAcquired -> ApproachCorridorGate (relativeNavConverged)
- ApproachCorridorGate -> LidarAcquisitionMode (rangeBelow5km)
- LidarAcquisitionMode -> OpticalPoseEstimationActive (targetAcquired)
- OpticalPoseEstimationActive -> StationKeepingHold1km (poseConverged)
- StationKeepingHold1km -> FlyAroundInspectionPhase (circumnavigationCommand)
- FlyAroundInspectionPhase -> StationKeepingHold1km (inspectionPassComplete)
- FlyAroundInspectionPhase -> KeepOutSphereMonitor (closeApproachDetected)
- KeepOutSphereMonitor -> FlyAroundInspectionPhase (rangeRestored)
- StationKeepingHold1km -> TargetAttitudeMatching (inspectionValidated)
- TargetAttitudeMatching -> DockingPortSelection (attitudeMatched)
- DockingPortSelection -> ApproachInitiationAxis (portSelected)
- ApproachInitiationAxis -> RangeHold200m (axisAligned)
- RangeHold200m -> CrossTrackAlignmentMode (goForDocking)
- CrossTrackAlignmentMode -> RangeHold50m (crossTrackNulled)
- RangeHold50m -> LaserRetroreflectorTracking (rangeBelow50m)
- LaserRetroreflectorTracking -> VisualServoControl (reflectorsLocked)
- VisualServoControl -> ContactProbeExtensionMode (servoConverged)
- ContactProbeExtensionMode -> AlignmentSensorEvaluator (probeExtended)
- AlignmentSensorEvaluator -> CaptureLatchEngagement (alignmentWithinTolerance)
- AlignmentSensorEvaluator -> ThrusterPlumeHold (thrusterBackpressure)
- AlignmentSensorEvaluator -> CollisionAvoidanceManeuverAbort (trajectoryViolation)
- ThrusterPlumeHold -> RangeHold50m (settleTimerExpired)
- CaptureLatchEngagement -> HardCaptureRingMotorDrive (latchesClosed)
- HardCaptureRingMotorDrive -> CaptureConfirmationHold (ringRetracted)
- CaptureConfirmationHold -> UmbilicalInterfaceMating (captureConfirmed)
- CaptureConfirmationHold -> CollisionAvoidanceManeuverAbort (captureLost)
- UmbilicalInterfaceMating -> PostDockLeakCheck (umbilicalsMated)
- PostDockLeakCheck -> SecureDockingAchieved (pressureHolds)
- OpticalPoseEstimationActive -> CollisionAvoidanceManeuverAbort (telemetryLost)
- ApproachInitiationAxis -> CollisionAvoidanceManeuverAbort (telemetryLost)
- LaserRetroreflectorTracking -> CollisionAvoidanceManeuverAbort (telemetryLost)
- KeepOutSphereMonitor -> CollisionAvoidanceManeuverAbort (keepOutSphereBreached)
- CollisionAvoidanceManeuverAbort -> AbortInhibitDisarm (abortLatched)
- AbortInhibitDisarm -> RetroBurnExecution (thrustersArmed)
- RetroBurnExecution -> AutonomousSeparationVector (burnComplete)
- AutonomousSeparationVector -> SafeDriftTrajectory (separationConfirmed)
- SafeDriftTrajectory -> SunPointingAttitudeAcquired (recoveryVerification)
- SunPointingAttitudeAcquired -> MissionAbortSafeHold (powerPositive)
- MissionAbortSafeHold -> GroundIntervention (groundCommandReceived)
- GroundIntervention -> ApproachCorridorGate (retryApproved)

### Sources

* NASA SP-2010-579: "Autonomous Rendezvous and Docking Technology Assessment".
* ESA ECSS-E-ST-60-20C: "Space Engineering: Star and optical navigation sensor operational modes and state machines".

### Uncertain

* The domain details were written to give the diagram a realistic shape; they were not checked against the cited sources.
