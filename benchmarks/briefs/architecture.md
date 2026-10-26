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
* **elements:** 45
* **connections:** 54
* **groups:** Edge Fleet Perimeter, Ingestion Bridge Zone, Real-Time Compute Mesh, Analytics Data Lake

### Brief

The telematics infrastructure coordinates forty-five components across Edge Fleet Perimeter, Ingestion Bridge Zone, Real-Time Compute Mesh, and Analytics Data Lake.
In Edge Fleet Perimeter, AutonomousVehiclePod streams sensor frames from LidarSensorArray, RadarSensorArray, and CameraSensorCluster into OnboardPerceptionEngine. OnboardPerceptionEngine feeds VehicleSafetyController, which communicates externally with EdgeGatewayBroker inside Ingestion Bridge Zone.
EdgeGatewayBroker passes sensor feeds to EdgeMqttIngress and high-throughput streams to WebSocketIngress. SecurityAuthenticator validates certificates against VaultSecretStore.
EdgeMqttIngress passes valid streams to StreamDistributionRouter in Real-Time Compute Mesh. StreamDistributionRouter fans out four ways: sending point clouds to PerceptionFeatureExtractor, safety triggers to AnomalyDetectionWorker, temporal metrics to TimeSeriesAggregator, and raw blobs directly to S3ColdStorageArchive in Analytics Data Lake.
PerceptionFeatureExtractor queries ModelInferenceCluster, which pulls weights from MlflowRegistryStore. AnomalyDetectionWorker flags critical alerts directly to SafetyOperationsDashboard, skipping stream pipelines. TimeSeriesAggregator streams aggregated events into KafkaEventBackbone.
FlinkStreamAnalytics consumes KafkaEventBackbone and updates RedisSpatialCache. GeospatialIndexingWorker consumes KafkaEventBackbone and writes spatial coordinates into ScyllaDbCluster. DriveDiagnosticsService processes vehicle health events, saving diagnostic snapshots into CassandraHealthStore.
BatchEtlService extracts daily logs from ScyllaDbCluster and loads transformed records into SnowflakeDataWarehouse. TrinoQueryEngine queries SnowflakeDataWarehouse, serving analytical feeds to GrafanaVisualizationHub.
Two feedback loops preserve synchronization: CalibrationLoop sends sensor correction offsets from AnomalyDetectionWorker through EdgeGatewayBroker back to OnboardPerceptionEngine; FirmwareLoop delivers OTA updates from S3ColdStorageArchive through EdgeGatewayBroker to AutonomousVehiclePod.

### Must show

* Four enterprise zones: Edge Fleet Perimeter, Ingestion Bridge Zone, Real-Time Compute Mesh, and Analytics Data Lake.
* StreamDistributionRouter fanning out four concurrent streams to PerceptionFeatureExtractor, AnomalyDetectionWorker, TimeSeriesAggregator, and S3ColdStorageArchive.
* AnomalyDetectionWorker bypassing pipeline layers to link directly to SafetyOperationsDashboard.
* Two feedback cycles: CalibrationLoop and FirmwareLoop traversing from deep cloud processing back to vehicle hardware.

### Traps

* Complex bidirectional feedback channels bridging deep cloud analytical nodes back to mobile physical edge devices force layout engines to route reverse edges around nested containment boxes.

### Sources

* Waymo Engineering Blog: "Real-time Telemetry and Large-scale Off-board Sensor Analytics Infrastructure".
* Tesla AI Day: Fleet learning infrastructure, raw video ingestion pipelines, and distributed feature store design.

### Uncertain

* none
