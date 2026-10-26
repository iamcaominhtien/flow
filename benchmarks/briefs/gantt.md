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
* **connections:** 60
* **groups:** Discovery Assessment, Cloud Foundation, Platform Modernization, Cutover Assurance

### Brief

The program has 44 tasks in 4 groups: Discovery Assessment, Cloud Foundation, Platform Modernization, Cutover Assurance. Time is counted in weeks; week 1 is the first week. Each task lists its start week, its length and the tasks it waits for.

In Discovery Assessment: InfrastructureAssetInventory starts in week 1 and lasts 3 weeks, with no predecessor. ApplicationDependencyMapping starts in week 4 and lasts 3 weeks after InfrastructureAssetInventory finishes. TechnicalDebtEvaluation starts in week 7 and lasts 2 weeks after ApplicationDependencyMapping finishes. LicenseConsolidationReview starts in week 9 and lasts 2 weeks after TechnicalDebtEvaluation finishes. MigrationWaveBundlingStrategy starts in week 9 and lasts 2 weeks after SecurityComplianceAudit, TechnicalDebtEvaluation and BusinessImpactAnalysis finish. CloudCostModeling starts in week 9 and lasts 2 weeks after BusinessImpactAnalysis and TechnicalDebtEvaluation finish. SecurityComplianceAudit starts in week 4 and lasts 4 weeks after InfrastructureAssetInventory finishes. BusinessImpactAnalysis starts in week 4 and lasts 3 weeks after InfrastructureAssetInventory finishes.

In Cloud Foundation: DedicatedDirectConnectLinkProvisioning starts in week 11 and lasts 4 weeks after MigrationWaveBundlingStrategy finishes. TransitGatewayRoutingMeshConfiguration starts in week 15 and lasts 3 weeks after SoftwareDefinedVirtualPrivateCloudSetup and DedicatedDirectConnectLinkProvisioning finish. CentralizedLoggingCollectorSetup starts in week 18 and lasts 2 weeks after TransitGatewayRoutingMeshConfiguration finishes. SoftwareDefinedVirtualPrivateCloudSetup starts in week 11 and lasts 3 weeks after MigrationWaveBundlingStrategy finishes. IdentityAccessManagementFederation starts in week 14 and lasts 3 weeks after SoftwareDefinedVirtualPrivateCloudSetup finishes. SecurityKeyVaultDeployment starts in week 17 and lasts 2 weeks after IdentityAccessManagementFederation finishes. LandingZoneGuardrailPolicies starts in week 14 and lasts 3 weeks after SoftwareDefinedVirtualPrivateCloudSetup and CloudCostModeling finish.

In Platform Modernization: ContainerRegistryProvisioning starts in week 20 and lasts 2 weeks after CentralizedLoggingCollectorSetup finishes. ContinuousIntegrationDeliveryPipelineUpdate starts in week 22 and lasts 4 weeks after ContainerRegistryProvisioning finishes. ObservabilityStackRollout starts in week 22 and lasts 3 weeks after ContainerRegistryProvisioning and LandingZoneGuardrailPolicies finish. KubernetesClusterBootstrapping starts in week 22 and lasts 3 weeks after ContainerRegistryProvisioning and SecurityKeyVaultDeployment finish. CoreMicroservicesRefactoring starts in week 25 and lasts 6 weeks after KubernetesClusterBootstrapping finishes. PerformanceBaselineTesting starts in week 31 and lasts 3 weeks after CoreMicroservicesRefactoring and SecurityPenetrationTesting finish. ServiceMeshAdoption starts in week 25 and lasts 3 weeks after KubernetesClusterBootstrapping finishes. SecurityPenetrationTesting starts in week 28 and lasts 3 weeks after ServiceMeshAdoption finishes. DistributedCacheClusterConfiguration starts in week 18 and lasts 2 weeks after TransitGatewayRoutingMeshConfiguration finishes. RelationalDatabaseClusterProvisioning starts in week 19 and lasts 4 weeks after SecurityKeyVaultDeployment and TransitGatewayRoutingMeshConfiguration finish. DatabaseSchemaMigrationConversion starts in week 23 and lasts 4 weeks after RelationalDatabaseClusterProvisioning finishes. ObjectStorageDataReplicationPipeline starts in week 14 and lasts 5 weeks after SoftwareDefinedVirtualPrivateCloudSetup finishes.

In Cutover Assurance: TrainingAndHandoverWorkshops starts in week 34 and lasts 4 weeks after PerformanceBaselineTesting finishes. FormalStakeholderSignoffAcceptance starts in week 50 and lasts 1 week after LegacyServerDecommissioning, DisasterRecoveryTestingVerification, TrainingAndHandoverWorkshops and ComplianceEvidencePackage finish. MockCutoverExecutionDryRun starts in week 31 and lasts 2 weeks after Wave1DryRunDataSynchronization and CoreMicroservicesRefactoring finish. RollbackRunbookRehearsal starts in week 33 and lasts 2 weeks after MockCutoverExecutionDryRun finishes. SecondDryRunRehearsal starts in week 37 and lasts 1 week after RemediationFixRoundOne and RollbackRunbookRehearsal finish. CustomerCommunicationPlan starts in week 38 and lasts 3 weeks after SecondDryRunRehearsal finishes. DnsRoutingCutoverExecution starts in week 41 and lasts 1 week after FinalDeltaDataSynchronization and CustomerCommunicationPlan finish. LiveTrafficVerificationValidation starts in week 42 and lasts 2 weeks after DnsRoutingCutoverExecution finishes. RemediationFixRoundTwo starts in week 44 and lasts 2 weeks after LiveTrafficVerificationValidation finishes. LegacyServerDecommissioning starts in week 46 and lasts 4 weeks after RemediationFixRoundTwo finishes. DisasterRecoveryTestingVerification starts in week 46 and lasts 3 weeks after RemediationFixRoundTwo finishes. ProductionFreezeWindowDeclaration starts in week 38 and lasts 1 week after SecondDryRunRehearsal finishes. FinalDeltaDataSynchronization starts in week 39 and lasts 2 weeks after ProductionFreezeWindowDeclaration finishes. OperationalSmokeTestingValidation starts in week 33 and lasts 2 weeks after MockCutoverExecutionDryRun finishes. ComplianceEvidencePackage starts in week 35 and lasts 3 weeks after OperationalSmokeTestingValidation and SecurityPenetrationTesting finish. RemediationFixRoundOne starts in week 35 and lasts 2 weeks after OperationalSmokeTestingValidation finishes. Wave1DryRunDataSynchronization starts in week 27 and lasts 2 weeks after DatabaseSchemaMigrationConversion and ObjectStorageDataReplicationPipeline finish.

### Must show

* All 44 tasks appear, each in its own group and at its start week and length.
* Every dependency line goes from the end of one task to the start of a later one (60 lines).
* Fan-out of three or more: SoftwareDefinedVirtualPrivateCloudSetup (4), InfrastructureAssetInventory (3), TechnicalDebtEvaluation (3), TransitGatewayRoutingMeshConfiguration (3), ContainerRegistryProvisioning (3).
* 15 dependencies cross between groups, for example MigrationWaveBundlingStrategy to DedicatedDirectConnectLinkProvisioning, MigrationWaveBundlingStrategy to SoftwareDefinedVirtualPrivateCloudSetup, CloudCostModeling to LandingZoneGuardrailPolicies.
* FormalStakeholderSignoffAcceptance waits for four predecessors and is the last task.

### Traps

* Many tasks have two to four predecessors from different groups, so dependency lines cross.
* One task (FormalStakeholderSignoffAcceptance) depends on four tasks that end in different weeks.

### Structure

**Elements**

- Discovery Assessment: InfrastructureAssetInventory@0+3, ApplicationDependencyMapping@3+3, TechnicalDebtEvaluation@6+2, LicenseConsolidationReview@8+2, MigrationWaveBundlingStrategy@8+2, CloudCostModeling@8+2, SecurityComplianceAudit@3+4, BusinessImpactAnalysis@3+3
- Cloud Foundation: DedicatedDirectConnectLinkProvisioning@10+4, TransitGatewayRoutingMeshConfiguration@14+3, CentralizedLoggingCollectorSetup@17+2, SoftwareDefinedVirtualPrivateCloudSetup@10+3, IdentityAccessManagementFederation@13+3, SecurityKeyVaultDeployment@16+2, LandingZoneGuardrailPolicies@13+3
- Platform Modernization: ContainerRegistryProvisioning@19+2, ContinuousIntegrationDeliveryPipelineUpdate@21+4, ObservabilityStackRollout@21+3, KubernetesClusterBootstrapping@21+3, CoreMicroservicesRefactoring@24+6, PerformanceBaselineTesting@30+3, ServiceMeshAdoption@24+3, SecurityPenetrationTesting@27+3, DistributedCacheClusterConfiguration@17+2, RelationalDatabaseClusterProvisioning@18+4, DatabaseSchemaMigrationConversion@22+4, ObjectStorageDataReplicationPipeline@13+5
- Cutover Assurance: TrainingAndHandoverWorkshops@33+4, FormalStakeholderSignoffAcceptance@49+1, MockCutoverExecutionDryRun@30+2, RollbackRunbookRehearsal@32+2, SecondDryRunRehearsal@36+1, CustomerCommunicationPlan@37+3, DnsRoutingCutoverExecution@40+1, LiveTrafficVerificationValidation@41+2, RemediationFixRoundTwo@43+2, LegacyServerDecommissioning@45+4, DisasterRecoveryTestingVerification@45+3, ProductionFreezeWindowDeclaration@37+1, FinalDeltaDataSynchronization@38+2, OperationalSmokeTestingValidation@32+2, ComplianceEvidencePackage@34+3, RemediationFixRoundOne@34+2, Wave1DryRunDataSynchronization@26+2

**Connections**

- InfrastructureAssetInventory -> ApplicationDependencyMapping
- InfrastructureAssetInventory -> SecurityComplianceAudit
- InfrastructureAssetInventory -> BusinessImpactAnalysis
- ApplicationDependencyMapping -> TechnicalDebtEvaluation
- TechnicalDebtEvaluation -> LicenseConsolidationReview
- SecurityComplianceAudit -> MigrationWaveBundlingStrategy
- TechnicalDebtEvaluation -> MigrationWaveBundlingStrategy
- BusinessImpactAnalysis -> MigrationWaveBundlingStrategy
- BusinessImpactAnalysis -> CloudCostModeling
- TechnicalDebtEvaluation -> CloudCostModeling
- MigrationWaveBundlingStrategy -> DedicatedDirectConnectLinkProvisioning
- MigrationWaveBundlingStrategy -> SoftwareDefinedVirtualPrivateCloudSetup
- SoftwareDefinedVirtualPrivateCloudSetup -> IdentityAccessManagementFederation
- SoftwareDefinedVirtualPrivateCloudSetup -> TransitGatewayRoutingMeshConfiguration
- DedicatedDirectConnectLinkProvisioning -> TransitGatewayRoutingMeshConfiguration
- SoftwareDefinedVirtualPrivateCloudSetup -> LandingZoneGuardrailPolicies
- CloudCostModeling -> LandingZoneGuardrailPolicies
- IdentityAccessManagementFederation -> SecurityKeyVaultDeployment
- TransitGatewayRoutingMeshConfiguration -> CentralizedLoggingCollectorSetup
- SoftwareDefinedVirtualPrivateCloudSetup -> ObjectStorageDataReplicationPipeline
- TransitGatewayRoutingMeshConfiguration -> DistributedCacheClusterConfiguration
- SecurityKeyVaultDeployment -> RelationalDatabaseClusterProvisioning
- TransitGatewayRoutingMeshConfiguration -> RelationalDatabaseClusterProvisioning
- CentralizedLoggingCollectorSetup -> ContainerRegistryProvisioning
- ContainerRegistryProvisioning -> ContinuousIntegrationDeliveryPipelineUpdate
- ContainerRegistryProvisioning -> ObservabilityStackRollout
- LandingZoneGuardrailPolicies -> ObservabilityStackRollout
- ContainerRegistryProvisioning -> KubernetesClusterBootstrapping
- SecurityKeyVaultDeployment -> KubernetesClusterBootstrapping
- RelationalDatabaseClusterProvisioning -> DatabaseSchemaMigrationConversion
- KubernetesClusterBootstrapping -> CoreMicroservicesRefactoring
- KubernetesClusterBootstrapping -> ServiceMeshAdoption
- ServiceMeshAdoption -> SecurityPenetrationTesting
- CoreMicroservicesRefactoring -> PerformanceBaselineTesting
- SecurityPenetrationTesting -> PerformanceBaselineTesting
- DatabaseSchemaMigrationConversion -> Wave1DryRunDataSynchronization
- ObjectStorageDataReplicationPipeline -> Wave1DryRunDataSynchronization
- Wave1DryRunDataSynchronization -> MockCutoverExecutionDryRun
- CoreMicroservicesRefactoring -> MockCutoverExecutionDryRun
- MockCutoverExecutionDryRun -> RollbackRunbookRehearsal
- MockCutoverExecutionDryRun -> OperationalSmokeTestingValidation
- PerformanceBaselineTesting -> TrainingAndHandoverWorkshops
- OperationalSmokeTestingValidation -> ComplianceEvidencePackage
- SecurityPenetrationTesting -> ComplianceEvidencePackage
- OperationalSmokeTestingValidation -> RemediationFixRoundOne
- RemediationFixRoundOne -> SecondDryRunRehearsal
- RollbackRunbookRehearsal -> SecondDryRunRehearsal
- SecondDryRunRehearsal -> CustomerCommunicationPlan
- SecondDryRunRehearsal -> ProductionFreezeWindowDeclaration
- ProductionFreezeWindowDeclaration -> FinalDeltaDataSynchronization
- FinalDeltaDataSynchronization -> DnsRoutingCutoverExecution
- CustomerCommunicationPlan -> DnsRoutingCutoverExecution
- DnsRoutingCutoverExecution -> LiveTrafficVerificationValidation
- LiveTrafficVerificationValidation -> RemediationFixRoundTwo
- RemediationFixRoundTwo -> LegacyServerDecommissioning
- RemediationFixRoundTwo -> DisasterRecoveryTestingVerification
- LegacyServerDecommissioning -> FormalStakeholderSignoffAcceptance
- DisasterRecoveryTestingVerification -> FormalStakeholderSignoffAcceptance
- TrainingAndHandoverWorkshops -> FormalStakeholderSignoffAcceptance
- ComplianceEvidencePackage -> FormalStakeholderSignoffAcceptance

### Sources

* AWS Prescriptive Guidance: Large-Scale Migration Framework (7 R's strategy and migration wave planning).
* Google Cloud Architecture Framework: Data Center Migration and Hybrid Cloud Foundation Planning.

### Uncertain

* The domain details were written to give the diagram a realistic shape; they were not checked against the cited sources.
