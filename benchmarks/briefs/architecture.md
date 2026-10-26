# Briefs: Architecture

Three briefs at levels A, B and C. See [README](README.md) for the format and how to run them.

---

## architecture-A-01 — Scalable Three-Tier Web Application with Read Caching

* **type:** architecture
* **level:** A
* **elements:** 9
* **connections:** 10
* **groups:** none

### Brief

The architecture represents an enterprise web application with high read availability across nine components. EdgeClient transmits external web traffic to Route53Dns. Route53Dns resolves and directs traffic to CloudFrontCdn. CloudFrontCdn forwards static asset cache misses to S3BucketStore, while passing dynamic application requests to ApplicationLoadBalancer.
ApplicationLoadBalancer distributes incoming HTTP requests across AppServerCluster. AppServerCluster queries RedisCacheStore for cached session states and read-heavy object records. If a cache miss occurs, AppServerCluster reads fresh data by querying DatabaseReadReplica.
For all state-mutating transactional writes, AppServerCluster directs operations directly to PrimaryRelationalDatabase. PrimaryRelationalDatabase maintains data consistency by streaming asynchronous replication logs through AsynchronousReplicationLink to DatabaseReadReplica.

### Must show

* Explicit architectural separation between read queries routed to DatabaseReadReplica and write operations routed to PrimaryRelationalDatabase.
* EdgeClient routing through Route53Dns and CloudFrontCdn before reaching ApplicationLoadBalancer.
* Asynchronous replication pipeline linking PrimaryRelationalDatabase to DatabaseReadReplica.

### Traps

* Triangular routing between AppServerCluster, RedisCacheStore, and DatabaseReadReplica generates crossing edges if cache stores are placed inline with databases.

### Sources

* AWS Well-Architected Framework: Reliability Pillar — Multi-tier web architectures with read replication and distributed cache layers.

### Uncertain

* none

---

## architecture-B-01 — Event-Driven Ride-Hailing Real-Time Dispatch Platform

* **type:** architecture
* **level:** B
* **elements:** 24
* **connections:** 28
* **groups:** Ingestion Edge Perimeter, Core Dispatch Mesh, Enterprise Persistence Tier

### Brief

The distributed streaming architecture coordinates twenty-four components across Ingestion Edge Perimeter, Core Dispatch Mesh, and Enterprise Persistence Tier.
PassengerMobileApp and DriverMobileApp in Ingestion Edge Perimeter send telemetry through ApiTrafficGateway. ApiTrafficGateway authenticates clients via SessionTokenAuthorizer and routes driver coordinates to IngestionEventService. IngestionEventService publishes raw telemetry onto ApacheKafkaCluster.
In Core Dispatch Mesh, GeohashSpatialIndexer consumes coordinate streams from ApacheKafkaCluster and updates DriverLocationRegistry in Enterprise Persistence Tier. In parallel, MatchMakingEngine consumes ride requests from ApacheKafkaCluster, queries DriverLocationRegistry for nearby units, and triggers RouteCalculationWorker. RouteCalculationWorker requests distance matrices from ExternalMappingService, and transmits matches to DispatchCoordinator.
DispatchCoordinator pushes ride invitations to NotificationDeliveryWorker, which alerts DriverMobileApp. When accepted, DispatchCoordinator dispatches transactional records to TripExecutionService. TripExecutionService persists active states in CassandraTripStore.
BillingCalculationService consumes completed trips from ApacheKafkaCluster, executes payment settlements against ExternalPaymentGateway, and saves financial logs in PostgreSqlLedger.
Two feedback loops maintain state: TelemetryAdjustmentLoop streams connection keep-alives from DriverMobileApp through ApiTrafficGateway back to IngestionEventService, while StateReconciliationLoop reads CassandraTripStore and reconciles ongoing status back into MatchMakingEngine.

### Must show

* Security zone boundaries separating Ingestion Edge Perimeter, Core Dispatch Mesh, and Enterprise Persistence Tier.
* Central ApacheKafkaCluster decoupling ingestion, trip matching, spatial indexing, and financial billing.
* Two feedback loops: TelemetryAdjustmentLoop and StateReconciliationLoop maintaining system synchronization.

### Traps

* TelemetryAdjustmentLoop and StateReconciliationLoop create cyclic feedback across perimeter and persistence boundaries, disrupting standard left-to-right layered DAG layouts.

### Sources

* Uber Engineering Blog: "Designing Uber's Real-Time Dispatch and Matching Platform with Geohash Hierarchies" (Cherami and H3 architecture reviews).
* https://kafka.apache.org/documentation/ — Event streaming architecture patterns for ride matching and spatial pipelines.

### Uncertain

* none

---

## architecture-C-01 — Autonomous Vehicle Fleet Perception Platform

* **type:** architecture
* **level:** C
* **elements:** 41
* **connections:** 52
* **groups:** Edge Fleet Perimeter, Ingestion Bridge Zone, Real-Time Compute Mesh, Analytics Data Lake

### Brief

The model has 41 components in 4 groups: Edge Fleet Perimeter, Ingestion Bridge Zone, Real-Time Compute Mesh, Analytics Data Lake. Every name below is one component to draw, and every sentence describes connections to draw.

In Edge Fleet Perimeter: OnboardPerceptionEngine calls VehicleSafetyController. VehicleSafetyController calls TlsTerminationProxy (opens a TLS session and sends telemetry). FirmwareUpdateAgent calls AutonomousVehiclePod (installs updates). AutonomousVehiclePod calls LidarSensorArray (powers), RadarSensorArray (powers), and CameraSensorCluster (powers). LidarSensorArray calls OnboardPerceptionEngine (streams point clouds). RadarSensorArray calls OnboardPerceptionEngine (streams radar returns). CameraSensorCluster calls OnboardPerceptionEngine (streams image frames).

In Ingestion Bridge Zone: EdgeGatewayBroker calls RateLimitGuard, OnboardPerceptionEngine (calibration loop: delivers the correction offsets), and FirmwareUpdateAgent (firmware loop: delivers the over-the-air update). RateLimitGuard calls EdgeMqttIngress (forwards sensor feeds), and WebSocketIngress (forwards high-throughput streams). EdgeMqttIngress calls SecurityAuthenticator (asks to validate a device), and StreamDistributionRouter (passes valid streams). SecurityAuthenticator calls DeviceCertificateRegistry (looks up certificates), and VaultSecretStore (reads signing keys). WebSocketIngress calls StreamDistributionRouter (passes valid streams). TlsTerminationProxy calls EdgeGatewayBroker (forwards decrypted traffic).

In Real-Time Compute Mesh: ConfigDistributionService calls EdgeGatewayBroker (pushes fleet configuration), and FleetDirectoryService (reads fleet assignments). StreamDistributionRouter calls PerceptionFeatureExtractor (sends point clouds), AnomalyDetectionWorker (sends safety triggers), TimeSeriesAggregator (sends temporal metrics), S3ColdStorageArchive (writes raw blobs), SchemaRegistry (validates message schemas), and ObservabilityCollector (emits pipeline metrics). PerceptionFeatureExtractor calls ModelInferenceCluster (queries). ModelInferenceCluster calls MlflowRegistryStore (pulls model weights). AnomalyDetectionWorker calls AlertRoutingService (raises critical alerts), and EdgeGatewayBroker (calibration loop: sends sensor correction offsets). AlertRoutingService calls SafetyOperationsDashboard (pushes alerts, skipping the stream pipeline). TimeSeriesAggregator calls KafkaEventBackbone (publishes aggregated events). KafkaEventBackbone calls FlinkStreamAnalytics (feeds), GeospatialIndexingWorker (feeds), DriveDiagnosticsService (feeds), and SchemaRegistry (validates message schemas). FlinkStreamAnalytics calls RedisSpatialCache (updates). RedisSpatialCache calls StreamDistributionRouter (hot cache lookup for routing). GeospatialIndexingWorker calls ScyllaDbCluster (writes spatial coordinates). DriveDiagnosticsService calls CassandraHealthStore (saves diagnostic snapshots). ObservabilityCollector calls GrafanaVisualizationHub (exports metrics).

In Analytics Data Lake: S3ColdStorageArchive calls BatchEtlService (provides raw logs), and FirmwareArtifactRepository (firmware loop: archives release candidates). BatchEtlService calls ScyllaDbCluster (extracts daily logs), CassandraHealthStore (extracts health records), and SnowflakeDataWarehouse (loads transformed records). FirmwareArtifactRepository calls EdgeGatewayBroker (firmware loop: serves signed builds). TrinoQueryEngine calls SnowflakeDataWarehouse (queries), and GrafanaVisualizationHub (serves analytical feeds). DataRetentionScheduler calls S3ColdStorageArchive (expires old objects).

### Must show

* The 4 groups (Edge Fleet Perimeter, Ingestion Bridge Zone, Real-Time Compute Mesh, Analytics Data Lake) contain exactly the elements listed under Structure.
* Fan-out of three or more: StreamDistributionRouter (6), KafkaEventBackbone (4), AutonomousVehiclePod (3), EdgeGatewayBroker (3), BatchEtlService (3).
* 4 connections return to an earlier element: AnomalyDetectionWorker to EdgeGatewayBroker, RedisSpatialCache to StreamDistributionRouter, FirmwareArtifactRepository to EdgeGatewayBroker, TlsTerminationProxy to EdgeGatewayBroker.
* 14 connections cross between groups, for example VehicleSafetyController to TlsTerminationProxy, EdgeMqttIngress to StreamDistributionRouter, WebSocketIngress to StreamDistributionRouter.

### Traps

* Two feedback paths run from the data lake back to the vehicle through the same gateway, against the flow of the layers.
* A bypass (AnomalyDetectionWorker to the dashboard) skips two layers.

### Structure

**Elements**

- Edge Fleet Perimeter: OnboardPerceptionEngine, VehicleSafetyController, FirmwareUpdateAgent, AutonomousVehiclePod, LidarSensorArray, RadarSensorArray, CameraSensorCluster
- Ingestion Bridge Zone: EdgeGatewayBroker, RateLimitGuard, EdgeMqttIngress, SecurityAuthenticator, DeviceCertificateRegistry, VaultSecretStore, WebSocketIngress, TlsTerminationProxy
- Real-Time Compute Mesh: ConfigDistributionService, StreamDistributionRouter, PerceptionFeatureExtractor, ModelInferenceCluster, MlflowRegistryStore, AnomalyDetectionWorker, AlertRoutingService, TimeSeriesAggregator, KafkaEventBackbone, FlinkStreamAnalytics, RedisSpatialCache, GeospatialIndexingWorker, DriveDiagnosticsService, SchemaRegistry, ObservabilityCollector
- Analytics Data Lake: SafetyOperationsDashboard, ScyllaDbCluster, CassandraHealthStore, S3ColdStorageArchive, BatchEtlService, SnowflakeDataWarehouse, FirmwareArtifactRepository, GrafanaVisualizationHub, FleetDirectoryService, TrinoQueryEngine, DataRetentionScheduler

**Connections**

- LidarSensorArray -> OnboardPerceptionEngine (streams point clouds)
- RadarSensorArray -> OnboardPerceptionEngine (streams radar returns)
- CameraSensorCluster -> OnboardPerceptionEngine (streams image frames)
- OnboardPerceptionEngine -> VehicleSafetyController
- AutonomousVehiclePod -> LidarSensorArray (powers)
- AutonomousVehiclePod -> RadarSensorArray (powers)
- AutonomousVehiclePod -> CameraSensorCluster (powers)
- VehicleSafetyController -> TlsTerminationProxy (opens a TLS session and sends telemetry)
- TlsTerminationProxy -> EdgeGatewayBroker (forwards decrypted traffic)
- FirmwareUpdateAgent -> AutonomousVehiclePod (installs updates)
- EdgeGatewayBroker -> RateLimitGuard
- RateLimitGuard -> EdgeMqttIngress (forwards sensor feeds)
- RateLimitGuard -> WebSocketIngress (forwards high-throughput streams)
- SecurityAuthenticator -> DeviceCertificateRegistry (looks up certificates)
- SecurityAuthenticator -> VaultSecretStore (reads signing keys)
- EdgeMqttIngress -> SecurityAuthenticator (asks to validate a device)
- EdgeMqttIngress -> StreamDistributionRouter (passes valid streams)
- WebSocketIngress -> StreamDistributionRouter (passes valid streams)
- StreamDistributionRouter -> PerceptionFeatureExtractor (sends point clouds)
- StreamDistributionRouter -> AnomalyDetectionWorker (sends safety triggers)
- StreamDistributionRouter -> TimeSeriesAggregator (sends temporal metrics)
- StreamDistributionRouter -> S3ColdStorageArchive (writes raw blobs)
- PerceptionFeatureExtractor -> ModelInferenceCluster (queries)
- ModelInferenceCluster -> MlflowRegistryStore (pulls model weights)
- AnomalyDetectionWorker -> AlertRoutingService (raises critical alerts)
- AlertRoutingService -> SafetyOperationsDashboard (pushes alerts, skipping the stream pipeline)
- TimeSeriesAggregator -> KafkaEventBackbone (publishes aggregated events)
- KafkaEventBackbone -> FlinkStreamAnalytics (feeds)
- KafkaEventBackbone -> GeospatialIndexingWorker (feeds)
- KafkaEventBackbone -> DriveDiagnosticsService (feeds)
- FlinkStreamAnalytics -> RedisSpatialCache (updates)
- GeospatialIndexingWorker -> ScyllaDbCluster (writes spatial coordinates)
- DriveDiagnosticsService -> CassandraHealthStore (saves diagnostic snapshots)
- BatchEtlService -> ScyllaDbCluster (extracts daily logs)
- BatchEtlService -> CassandraHealthStore (extracts health records)
- BatchEtlService -> SnowflakeDataWarehouse (loads transformed records)
- S3ColdStorageArchive -> BatchEtlService (provides raw logs)
- TrinoQueryEngine -> SnowflakeDataWarehouse (queries)
- TrinoQueryEngine -> GrafanaVisualizationHub (serves analytical feeds)
- DataRetentionScheduler -> S3ColdStorageArchive (expires old objects)
- AnomalyDetectionWorker -> EdgeGatewayBroker (calibration loop: sends sensor correction offsets)
- EdgeGatewayBroker -> OnboardPerceptionEngine (calibration loop: delivers the correction offsets)
- FirmwareArtifactRepository -> EdgeGatewayBroker (firmware loop: serves signed builds)
- EdgeGatewayBroker -> FirmwareUpdateAgent (firmware loop: delivers the over-the-air update)
- S3ColdStorageArchive -> FirmwareArtifactRepository (firmware loop: archives release candidates)
- RedisSpatialCache -> StreamDistributionRouter (hot cache lookup for routing)
- StreamDistributionRouter -> SchemaRegistry (validates message schemas)
- KafkaEventBackbone -> SchemaRegistry (validates message schemas)
- ConfigDistributionService -> EdgeGatewayBroker (pushes fleet configuration)
- ConfigDistributionService -> FleetDirectoryService (reads fleet assignments)
- StreamDistributionRouter -> ObservabilityCollector (emits pipeline metrics)
- ObservabilityCollector -> GrafanaVisualizationHub (exports metrics)

### Sources

* Waymo Engineering Blog: "Real-time Telemetry and Large-scale Off-board Sensor Analytics Infrastructure".
* Tesla AI Day: Fleet learning infrastructure, raw video ingestion pipelines, and distributed feature store design.

### Uncertain

* The domain details were written to give the diagram a realistic shape; they were not checked against the cited sources.
