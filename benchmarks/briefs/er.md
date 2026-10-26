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
* **elements:** 42
* **connections:** 50
* **groups:** Procurement Core, Facility Topology, Inventory Tracking, Fulfillment Fleet

### Brief

The schema coordinates global distribution across forty-two entities grouped into Procurement Core, Facility Topology, Inventory Tracking, and Fulfillment Fleet.
In Procurement Core, GlobalVendor maintains a one-to-many relationship with MasterVendorContract, and a one-to-many relationship with PurchaseOrderRecord. PurchaseOrderRecord links one-to-many to PurchaseOrderLineItem. ProductMasterSKU links one-to-many to PurchaseOrderLineItem, and one-to-many to ProductBillOfMaterials.
In Facility Topology, DistributionCenter links one-to-many to WarehouseBuilding, which links one-to-many to FacilityStorageZone. FacilityStorageZone links one-to-many to StorageAisle, which links one-to-many to RackBay. RackBay links one-to-many to StorageBinLocation.
In Inventory Tracking, ProductMasterSKU fans out four relationships: one-to-many to StorageBinAllocation, one-to-many to StockKeepingUnitBatch, one-to-many to TariffClassificationCode, and one-to-many to ReplenishmentRule. StockKeepingUnitBatch links one-to-many to SerializedUnitInventory, and one-to-many to QualityInspectionLot. StorageBinLocation links one-to-many to SerializedUnitInventory.
Two relational audit loops enforce data integrity: SerializedUnitInventory links one-to-many to CycleCountAuditRecord, which links one-to-many to StockDiscrepancyLog, which links back one-to-many to SerializedUnitInventory. In parallel, StorageBinAllocation links one-to-many to InternalBayTransfer, which links to PalletUnitConsolidation, which links back to StorageBinAllocation.
In Fulfillment Fleet, CustomerSalesOrder links one-to-many to SalesOrderFulfillmentLine. ProductMasterSKU links one-to-many to SalesOrderFulfillmentLine. SalesOrderFulfillmentLine links one-to-many to WarehouseWavePickingTask. WarehouseWavePickingTask links one-to-many to PackingConsignmentContainer. PackingConsignmentContainer links one-to-many to ShippingDispatchManifest.
FreightLogisticsCarrier links one-to-many to ShippingDispatchManifest, and one-to-many to FleetTransportVehicle. FleetTransportVehicle links one-to-many to DriverDeliveryAssignment, which links one-to-many to ProofOfDeliveryRecord.
ExpressEmergencyDrop skips intermediate warehouse picking by linking PurchaseOrderRecord directly to ShippingDispatchManifest. Across groups, DistributionCenter links one-to-many to ShippingDispatchManifest, and SerializedUnitInventory links one-to-many to PackingConsignmentContainer.

### Must show

* Enterprise grouping across Procurement Core, Facility Topology, Inventory Tracking, and Fulfillment Fleet.
* ProductMasterSKU fanning out four distinct relationship links to StorageBinAllocation, StockKeepingUnitBatch, TariffClassificationCode, and ReplenishmentRule.
* The two cyclic relational loops involving CycleCountAuditRecord and InternalBayTransfer.
* ExpressEmergencyDrop jumping from Procurement Core directly to Fulfillment Fleet, skipping inventory and warehouse picking entities.

### Traps

* Combining deep six-tier vertical nesting in Facility Topology with cyclic audit loops and cross-domain order fulfillment links challenges planar relational graph embedding.

### Sources

* SAP S/4HANA Extended Warehouse Management Technical Reference Architecture — Master data structures for storage topologies, serial handling, and wave fulfillment.
* Oracle Warehouse Management Cloud Data Model — Logistics data structures for inbound receipts, bin locations, and carrier dispatching.

### Uncertain

* none
