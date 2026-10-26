# Briefs: Gantt

Three briefs at levels A, B and C. See [README](README.md) for the format and how to run them.

---

## gantt-A-01 — Agile Scrum Iteration Sprint Cycle and Deployment Schedule

* **type:** gantt
* **level:** A
* **elements:** 10
* **connections:** 9
* **groups:** Sprint Inception, Development Iteration, Release Packaging

### Brief

The project schedule models execution of a two-week software engineering sprint across ten tasks.
In Sprint Inception, SprintBacklogRefinement begins on Day 1. SprintPlanningSession starts after SprintBacklogRefinement finishes.
In Development Iteration, ApiEndpointEngineering begins after SprintPlanningSession finishes. DataSchemaMigration runs parallel to API development, starting after SprintPlanningSession finishes. FrontendComponentDevelopment starts after ApiEndpointEngineering finishes. ContinuousIntegrationAutomatedTesting starts after FrontendComponentDevelopment and DataSchemaMigration finish.
In Release Packaging, SprintDemonstrationReview starts after ContinuousIntegrationAutomatedTesting finishes. SprintRetrospectiveInspection starts after SprintDemonstrationReview finishes. ProductionCanaryRollout starts after SprintRetrospectiveInspection finishes. PostDeploymentMonitoring starts after ProductionCanaryRollout finishes.

### Must show

* Groups partitioned across Sprint Inception, Development Iteration, and Release Packaging.
* Parallel development tracks for ApiEndpointEngineering and DataSchemaMigration.
* ContinuousIntegrationAutomatedTesting synchronizing after both API and database tasks complete.

### Traps

* Dual dependency convergence onto ContinuousIntegrationAutomatedTesting requiring clear multi-predecessor link routing without arrow crossing.

### Sources

* The Scrum Guide (Ken Schwaber and Jeff Sutherland) — Scrum events, release increments, and iteration planning sequences.

### Uncertain

* none

---

## gantt-B-01 — Commercial Earth Ground Station Antenna Construction Program

* **type:** gantt
* **level:** B
* **elements:** 23
* **connections:** 26
* **groups:** Civil Works, Antenna Assembly, RF Systems Integration, Telemetry Commissioning

### Brief

The engineering plan outlines installation of a deep-space ground tracking station across four phases.
In Civil Works, SiteBoundarySurveying starts in Month 1. GeotechnicalSoilExcavation starts after SiteBoundarySurveying finishes. ConcretePedestalFoundationPour starts after GeotechnicalSoilExcavation finishes. ConduitTrenchingCableDucting starts after GeotechnicalSoilExcavation finishes. StructuralPadCuringTimer starts after ConcretePedestalFoundationPour finishes.
In Antenna Assembly, CraneSupportRiggingArrival starts after StructuralPadCuringTimer finishes. KingpostAzimuthBearingMounting starts after CraneSupportRiggingArrival finishes. ElevationDriveGimbalAssembly starts after KingpostAzimuthBearingMounting finishes. MainReflectorDishLifting starts after ElevationDriveGimbalAssembly finishes. SubreflectorQuadripodInstallation starts after MainReflectorDishLifting finishes. SurfacePhotogrammetryAlignment starts after SubreflectorQuadripodInstallation finishes.
In RF Systems Integration, CryogenicFeedhornInstallation starts after SurfacePhotogrammetryAlignment finishes. WaveguideFeedlineRouting starts after CryogenicFeedhornInstallation and ConduitTrenchingCableDucting finish. LowNoiseAmplifierIntegration starts after CryogenicFeedhornInstallation finishes. HighPowerAmplifierInstallation starts after WaveguideFeedlineRouting finishes. DownconverterReceiverMounting starts after LowNoiseAmplifierIntegration finishes. FiberOpticBackhaulInterconnect starts after ConduitTrenchingCableDucting finishes.
In Telemetry Commissioning, BasebandProcessorCalibration starts after DownconverterReceiverMounting and FiberOpticBackhaulInterconnect finish. TrackingLoopGainTuning starts after BasebandProcessorCalibration and ElevationDriveGimbalAssembly finish. SatelliteRadioCalibrationBoresighting starts after TrackingLoopGainTuning finishes. RegulatorySpectrumInterferenceAudit starts after SatelliteRadioCalibrationBoresighting finishes. FlightMissionReadinessReview starts after RegulatorySpectrumInterferenceAudit finishes. CommercialOperationsCommencement starts after FlightMissionReadinessReview finishes.

### Must show

* Four sequential engineering phases: Civil Works, Antenna Assembly, RF Systems Integration, and Telemetry Commissioning.
* ConduitTrenchingCableDucting from Civil Works bridging across phases to feed WaveguideFeedlineRouting and FiberOpticBackhaulInterconnect in RF Systems Integration.
* BasebandProcessorCalibration synchronizing two upstream delivery paths.

### Traps

* Inter-phase cross-links jumping past intermediate assembly tasks to connect initial foundation trenching to final integration tasks stress Gantt vertical layout engines.

### Sources

* NASA Deep Space Network 34-Meter Beam Waveguide Antenna Construction & Commissioning Technical Manuals (JPL Publication).

### Uncertain

* none

---

## gantt-C-01 — Enterprise Hybrid Cloud Data Center Migration Program

* **type:** gantt
* **level:** C
* **elements:** 44
* **connections:** 52
* **groups:** Discovery Assessment, Cloud Foundation, Platform Modernization, Cutover Assurance

### Brief

The migration program governs migration of core applications to the cloud across four program phases.
In Discovery Assessment, InfrastructureAssetInventory starts in Month 1. ApplicationDependencyMapping starts after InfrastructureAssetInventory finishes. SecurityComplianceAudit starts after InfrastructureAssetInventory finishes. TechnicalDebtEvaluation starts after ApplicationDependencyMapping finishes. MigrationWaveBundlingStrategy starts after SecurityComplianceAudit and TechnicalDebtEvaluation finish.
In Cloud Foundation, DedicatedDirectConnectLinkProvisioning starts after MigrationWaveBundlingStrategy finishes. SoftwareDefinedVirtualPrivateCloudSetup starts after DedicatedDirectConnectLinkProvisioning finishes. IdentityAccessManagementFederation starts after SoftwareDefinedVirtualPrivateCloudSetup finishes. TransitGatewayRoutingMeshConfiguration starts after SoftwareDefinedVirtualPrivateCloudSetup finishes. SecurityKeyVaultDeployment starts after IdentityAccessManagementFederation finishes. CentralizedLoggingCollectorSetup starts after TransitGatewayRoutingMeshConfiguration finishes.
In Platform Modernization, ContainerRegistryProvisioning starts after CentralizedLoggingCollectorSetup finishes. KubernetesClusterBootstrapping starts after ContainerRegistryProvisioning and SecurityKeyVaultDeployment finish. RelationalDatabaseClusterProvisioning starts after SecurityKeyVaultDeployment and TransitGatewayRoutingMeshConfiguration finish. DistributedCacheClusterConfiguration starts after TransitGatewayRoutingMeshConfiguration finishes. ObjectStorageDataReplicationPipeline starts after SoftwareDefinedVirtualPrivateCloudSetup finishes. CoreMicroservicesRefactoring starts after KubernetesClusterBootstrapping finishes. DatabaseSchemaMigrationConversion starts after RelationalDatabaseClusterProvisioning finishes. ContinuousIntegrationDeliveryPipelineUpdate starts after ContainerRegistryProvisioning finishes.
In Cutover Assurance, Wave1DryRunDataSynchronization starts after DatabaseSchemaMigrationConversion and ObjectStorageDataReplicationPipeline finish. MockCutoverExecutionDryRun starts after Wave1DryRunDataSynchronization and CoreMicroservicesRefactoring finish. OperationalSmokeTestingValidation starts after MockCutoverExecutionDryRun finishes.
RemediationFixCycle1 starts if dry-run errors occur, looping from OperationalSmokeTestingValidation back into Wave1DryRunDataSynchronization.
ProductionFreezeWindowDeclaration starts after OperationalSmokeTestingValidation finishes. FinalDeltaDataSynchronization starts after ProductionFreezeWindowDeclaration finishes. DnsRoutingCutoverExecution starts after FinalDeltaDataSynchronization finishes. LiveTrafficVerificationValidation starts after DnsRoutingCutoverExecution finishes.
RemediationFixCycle2 starts if live discrepancies arise, looping from LiveTrafficVerificationValidation back into FinalDeltaDataSynchronization.
LegacyServerDecommissioning starts after LiveTrafficVerificationValidation finishes. DisasterRecoveryTestingVerification starts after LiveTrafficVerificationValidation finishes. FormalStakeholderSignoffAcceptance starts after LegacyServerDecommissioning and DisasterRecoveryTestingVerification finish.

### Must show

* Four program groups: Discovery Assessment, Cloud Foundation, Platform Modernization, and Cutover Assurance.
* SoftwareDefinedVirtualPrivateCloudSetup fanning out three concurrent dependencies: IdentityAccessManagementFederation, TransitGatewayRoutingMeshConfiguration, and ObjectStorageDataReplicationPipeline.
* Direct-skip dependency: DedicatedDirectConnectLinkProvisioning establishing long-distance dependencies that jump over intermediate tasks to feed Cutover Assurance testing.
* Two iterative remediation cycles: RemediationFixCycle1 and RemediationFixCycle2 modeling mock cutover and live cutover retry loops.

### Traps

* Multi-predecessor dependencies spanning across distant phases combined with iterative rollback-remediation loops can break standard acyclic waterfall Gantt renderers.

### Sources

* AWS Prescriptive Guidance: Large-Scale Migration Framework (7 R's strategy and migration wave planning).
* Google Cloud Architecture Framework: Data Center Migration and Hybrid Cloud Foundation Planning.

### Uncertain

* none
