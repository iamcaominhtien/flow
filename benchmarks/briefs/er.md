# Briefs: ER

Three briefs at levels A, B and C. See [README](README.md) for the format and how to run them.

---

## er-A-01 — Public Library Circulation and Catalog Schema

* **type:** er
* **level:** A
* **elements:** 9
* **connections:** 10
* **groups:** none

### Brief

The schema specifies relational structures for library cataloging and circulation operations. Patron maintains a one-to-one relationship with LibraryCard. Patron possesses a one-to-many relationship with LoanRecord, tracking borrowed materials. Patron also possesses a one-to-many relationship with ReservationHold for queueing unavailable items. When overdue penalties occur, LoanRecord generates a one-to-many relationship with FineRecord.
Catalog metadata starts with Publisher, which possesses a one-to-many relationship with BookTitle. BookTitle possesses a many-to-many relationship with Author through TitleAuthorLink. BookTitle maintains a one-to-many relationship with PhysicalCopy, representing inventory stock. PhysicalCopy maintains a one-to-many relationship with LoanRecord when circulating, and a one-to-many relationship with ReservationHold when fulfilling holds.

### Must show

* Cardinality integrity: 1-to-1 between Patron and LibraryCard, and 1-to-many between Patron and LoanRecord.
* Associative entity TitleAuthorLink resolving the many-to-many relationship between BookTitle and Author.
* PhysicalCopy connecting simultaneously as a foreign key target to both LoanRecord and ReservationHold.

### Traps

* Dual multi-entity convergences on LoanRecord and ReservationHold cause intersecting relationship lines if entity positioning is forced into rigid planar rows.

### Sources

* Modern Database Management (13th Edition), Hoffer, Venkataraman, Topi — Chapter 2: Modeling Data in the Organization (Library Schema Pattern).

### Uncertain

* none

---

## er-B-01 — Multi-Tenant SaaS Metered Subscription and Billing Schema

* **type:** er
* **level:** B
* **elements:** 22
* **connections:** 26
* **groups:** Tenancy Boundary, Subscription Billing, Metering Analytics

### Brief

The architecture organizes enterprise multitenant SaaS subscription accounts across twenty-two relational entities. In Tenancy Boundary, Organization possesses a one-to-many relationship with TenantDomain, and a one-to-many relationship with UserAccount. UserAccount links one-to-many to UserRole, which maps many-to-many to PermissionEntitlement via RolePermissionMapping. UserAccount maintains a one-to-many relationship with AuditActivityLog.
In Subscription Billing, Organization maintains a one-to-many relationship with BillingCustomerProfile. BillingCustomerProfile maintains a one-to-many relationship with PaymentMethodToken, and a one-to-many relationship with SubscriptionContract. SubscriptionPlan maintains a one-to-many relationship with SubscriptionContract, and a one-to-many relationship with PlanTierFeature. SubscriptionContract maintains a one-to-many relationship with SubscriptionInvoice.
SubscriptionInvoice possesses a one-to-many relationship with InvoiceLineItem, and a one-to-many relationship with PaymentTransactionRecord. When disputes arise, PaymentTransactionRecord links one-to-many to RefundChargebackEvent.
In Metering Analytics, TenantDomain links one-to-many to MeteredUsageEvent. MeteredResource links one-to-many to MeteredUsageEvent, and one-to-many to PlanTierFeature. MeteredUsageEvent aggregates into AggregatedDailyUsage, which maintains a one-to-many relationship with InvoiceLineItem. Furthermore, SubscriptionContract maintains a cyclic self-referencing relationship, ParentContractRenewal, modeling upgrade transitions. Finally, TenantDomain maintains a one-to-many relationship with SubscriptionContract.

### Must show

* Domain grouping across Tenancy Boundary, Subscription Billing, and Metering Analytics.
* Self-referential recursive relationship on SubscriptionContract for ParentContractRenewal.
* MeteredUsageEvent aggregating into AggregatedDailyUsage and linking to InvoiceLineItem across domain boundaries.

### Traps

* AggregatedDailyUsage connects usage metering back into financial invoice items, creating cross-boundary edge crossings between analytics and billing tables.

### Sources

* https://stripe.com/docs/billing — Stripe Billing Object Architecture and metered multi-tier enterprise models.

### Uncertain

* none

---

## er-C-01 — Global Multi-Echelon Logistics and Inventory Schema

* **type:** er
* **level:** C
* **elements:** 41
* **connections:** 50
* **groups:** Procurement Core, Facility Topology, Inventory Tracking, Fulfillment Fleet

### Brief

The model has 41 entities in 4 groups: Procurement Core, Facility Topology, Inventory Tracking, Fulfillment Fleet. Every name below is one entity to draw, and every sentence describes connections to draw.

In Procurement Core: GlobalVendor links one-to-many to MasterVendorContract, one-to-many to PurchaseOrderRecord, and one-to-many to SupplierQualityScorecard. MasterVendorContract links one-to-many to ContractPriceTier. PurchaseOrderRecord links one-to-many to PurchaseOrderLineItem, one-to-many to GoodsReceiptNote, and one-to-one to ShippingDispatchManifest. GoodsReceiptNote links one-to-many to PutawayTask. ProductMasterSKU links one-to-many to PurchaseOrderLineItem, one-to-many to ProductBillOfMaterials, one-to-many to ContractPriceTier, one-to-many to StorageBinAllocation, one-to-many to StockKeepingUnitBatch, many-to-many to TariffClassificationCode, one-to-many to ReplenishmentRule, one-to-many to DemandForecastPlan, and one-to-many to SalesOrderFulfillmentLine.

In Facility Topology: DistributionCenter links one-to-many to WarehouseBuilding, one-to-many to StockTransferOrder, and one-to-many to ShippingDispatchManifest. WarehouseBuilding links one-to-many to FacilityStorageZone. FacilityStorageZone links one-to-many to StorageAisle. StorageAisle links one-to-many to RackBay. RackBay links one-to-many to StorageBinLocation. StorageBinLocation links one-to-many to PutawayTask, one-to-many to SerializedUnitInventory, and one-to-many to StorageBinAllocation.

In Inventory Tracking: StorageBinAllocation links one-to-many to InternalBayTransfer. InternalBayTransfer links one-to-many to PalletUnitConsolidation. PalletUnitConsolidation links one-to-many to StorageBinAllocation. StockKeepingUnitBatch links one-to-many to SerializedUnitInventory, and one-to-many to QualityInspectionLot. SerializedUnitInventory links one-to-many to CycleCountAuditRecord, and one-to-many to PackingConsignmentContainer. CycleCountAuditRecord links one-to-many to StockDiscrepancyLog. StockDiscrepancyLog links one-to-many to SerializedUnitInventory. StockTransferOrder links one-to-many to InternalBayTransfer.

In Fulfillment Fleet: ShippingDispatchManifest links one-to-many to CustomsDeclaration. PackingConsignmentContainer links one-to-many to ShippingDispatchManifest. SalesOrderFulfillmentLine links one-to-many to WarehouseWavePickingTask. WarehouseWavePickingTask links one-to-many to PackingConsignmentContainer. CustomerSalesOrder links one-to-many to SalesOrderFulfillmentLine, and one-to-many to ReturnAuthorization. ReturnAuthorization links one-to-many to ReturnInspectionRecord. ReturnInspectionRecord links one-to-many to SerializedUnitInventory. FreightLogisticsCarrier links one-to-many to ShippingDispatchManifest, one-to-many to FleetTransportVehicle, and one-to-many to CarrierRateCard. FleetTransportVehicle links one-to-many to DriverDeliveryAssignment. DriverDeliveryAssignment links one-to-many to ProofOfDeliveryRecord.

### Must show

* The 4 groups (Procurement Core, Facility Topology, Inventory Tracking, Fulfillment Fleet) contain exactly the elements listed under Structure.
* Fan-out of three or more: ProductMasterSKU (9), GlobalVendor (3), PurchaseOrderRecord (3), DistributionCenter (3), StorageBinLocation (3).
* 2 connections return to an earlier element: PalletUnitConsolidation to StorageBinAllocation, StockDiscrepancyLog to SerializedUnitInventory.
* 14 connections cross between groups, for example GoodsReceiptNote to PutawayTask, ProductMasterSKU to StorageBinAllocation, ProductMasterSKU to StockKeepingUnitBatch.

### Traps

* Two three-entity cycles (audit and consolidation) inside a deep six-tier facility hierarchy.
* ProductMasterSKU is referenced from five groups, so its relationships cross every other group.

### Structure

**Elements**

- Procurement Core: GlobalVendor, MasterVendorContract, ContractPriceTier, PurchaseOrderRecord, PurchaseOrderLineItem, GoodsReceiptNote, SupplierQualityScorecard, ProductMasterSKU, ProductBillOfMaterials
- Facility Topology: PutawayTask, DistributionCenter, WarehouseBuilding, FacilityStorageZone, StorageAisle, RackBay, StorageBinLocation
- Inventory Tracking: StorageBinAllocation, InternalBayTransfer, PalletUnitConsolidation, StockKeepingUnitBatch, SerializedUnitInventory, CycleCountAuditRecord, StockDiscrepancyLog, QualityInspectionLot, TariffClassificationCode, ReplenishmentRule, DemandForecastPlan, StockTransferOrder
- Fulfillment Fleet: ShippingDispatchManifest, CustomsDeclaration, PackingConsignmentContainer, SalesOrderFulfillmentLine, WarehouseWavePickingTask, CustomerSalesOrder, ReturnAuthorization, ReturnInspectionRecord, FreightLogisticsCarrier, FleetTransportVehicle, DriverDeliveryAssignment, ProofOfDeliveryRecord, CarrierRateCard

**Connections**

- GlobalVendor -> MasterVendorContract
- GlobalVendor -> PurchaseOrderRecord
- GlobalVendor -> SupplierQualityScorecard
- MasterVendorContract -> ContractPriceTier
- PurchaseOrderRecord -> PurchaseOrderLineItem
- PurchaseOrderRecord -> GoodsReceiptNote
- ProductMasterSKU -> PurchaseOrderLineItem
- ProductMasterSKU -> ProductBillOfMaterials
- ProductMasterSKU -> ContractPriceTier
- GoodsReceiptNote -> PutawayTask
- DistributionCenter -> WarehouseBuilding
- WarehouseBuilding -> FacilityStorageZone
- FacilityStorageZone -> StorageAisle
- StorageAisle -> RackBay
- RackBay -> StorageBinLocation
- StorageBinLocation -> PutawayTask
- ProductMasterSKU -> StorageBinAllocation
- ProductMasterSKU -> StockKeepingUnitBatch
- ProductMasterSKU -> TariffClassificationCode (many-to-many)
- ProductMasterSKU -> ReplenishmentRule
- ProductMasterSKU -> DemandForecastPlan
- StockKeepingUnitBatch -> SerializedUnitInventory
- StockKeepingUnitBatch -> QualityInspectionLot
- StorageBinLocation -> SerializedUnitInventory
- StorageBinLocation -> StorageBinAllocation
- SerializedUnitInventory -> CycleCountAuditRecord
- CycleCountAuditRecord -> StockDiscrepancyLog
- StockDiscrepancyLog -> SerializedUnitInventory
- StorageBinAllocation -> InternalBayTransfer
- InternalBayTransfer -> PalletUnitConsolidation
- PalletUnitConsolidation -> StorageBinAllocation
- DistributionCenter -> StockTransferOrder
- StockTransferOrder -> InternalBayTransfer
- CustomerSalesOrder -> SalesOrderFulfillmentLine
- ProductMasterSKU -> SalesOrderFulfillmentLine
- SalesOrderFulfillmentLine -> WarehouseWavePickingTask
- WarehouseWavePickingTask -> PackingConsignmentContainer
- PackingConsignmentContainer -> ShippingDispatchManifest
- FreightLogisticsCarrier -> ShippingDispatchManifest
- FreightLogisticsCarrier -> FleetTransportVehicle
- FreightLogisticsCarrier -> CarrierRateCard
- FleetTransportVehicle -> DriverDeliveryAssignment
- DriverDeliveryAssignment -> ProofOfDeliveryRecord
- ShippingDispatchManifest -> CustomsDeclaration
- CustomerSalesOrder -> ReturnAuthorization
- ReturnAuthorization -> ReturnInspectionRecord
- ReturnInspectionRecord -> SerializedUnitInventory
- PurchaseOrderRecord -> ShippingDispatchManifest (one-to-one)
- DistributionCenter -> ShippingDispatchManifest
- SerializedUnitInventory -> PackingConsignmentContainer

### Sources

* SAP S/4HANA Extended Warehouse Management Technical Reference Architecture — Master data structures for storage topologies, serial handling, and wave fulfillment.
* Oracle Warehouse Management Cloud Data Model — Logistics data structures for inbound receipts, bin locations, and carrier dispatching.

### Uncertain

* The domain details were written to give the diagram a realistic shape; they were not checked against the cited sources.
