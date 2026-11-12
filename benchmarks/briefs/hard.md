# Briefs: hard set, one per diagram type

One hard brief for each of the 21 diagram types of the plugin. Written for this repository (not by the research tool) to stress each type's layout: many elements, hubs, loops, long names, and Vietnamese text in four of them. It is **not** read by `check_briefs.py`. The counts in `Must show` were written by hand with the brief and were not recounted by a script. No domain detail was checked against a source.

First run: [`../results/2026-11-12-hard-set-sonnet.md`](../results/2026-11-12-hard-set-sonnet.md).

Faults in these briefs, found by the first run. The brief text is left as it was run; fix it before a second run.

- **org-chart:** says 62 positions; the text lists 58 (3 + 7 + 22 + 19 + 7). `Must show` counts the store managers twice.
- **architecture:** says 34 components; the lists add up to 38.
- **er:** says 26 tables; the text lists 27.
- **gantt:** four dependencies contradict the dates (the later task starts before the earlier one ends): Target architecture and Data model mapping after Current-state analysis, Security design after Target architecture, System integration test after Integration layer build. The build refuses them. There are 41 tasks and 6 milestones, 47 rows, not 46.
- **roadmap:** 39 items (40 bars), not 40; 7 dependency sentences, 8 arrows.
- **mind-map:** the agent counted 83 nodes; `Must show` says about 95. Not recounted.
- **usecase:** the agent counted 31 use cases; `Must show` says 16 and 14. Says "three system actors" and lists four.
- **dfd:** the agent counted 56 flows; `Must show` says 55. Not recounted.

How to run: give a fresh agent only the text under `Brief` and the skill of the type, as in the [README](README.md). `Must show` is for the reviewer.

---

## hard-flowchart — Tiếp nhận cấp cứu (swimlanes, Vietnamese)

### Brief

Vẽ lưu đồ có làn bơi (swimlane) cho quy trình tiếp nhận cấp cứu của một bệnh viện. Toàn bộ chữ trong sơ đồ viết bằng tiếng Việt có dấu. Có 5 làn: Bệnh nhân, Điều dưỡng phân loại, Bác sĩ cấp cứu, Xét nghiệm và Chẩn đoán hình ảnh, Thu ngân và Bảo hiểm.

Bệnh nhân đến khoa cấp cứu. Điều dưỡng đo sinh hiệu rồi phân loại mức độ theo 3 mức: Đỏ (nguy kịch), Vàng (khẩn cấp), Xanh (không khẩn cấp). Mức Đỏ: chuyển thẳng vào phòng hồi sức, bác sĩ hồi sức ngay. Mức Vàng: xếp giường theo dõi, bác sĩ khám trong 15 phút. Mức Xanh: bệnh nhân lấy số chờ, ngồi phòng chờ; cứ 30 phút điều dưỡng đánh giá lại, nếu nặng lên thì quay lại bước phân loại, nếu không thì chờ tiếp đến lượt khám.

Sau khi khám, bác sĩ quyết định có cần cận lâm sàng không. Nếu có, hai việc chạy song song: lấy máu xét nghiệm và chụp X-quang hoặc CT; chỉ khi cả hai có kết quả thì bác sĩ mới đọc kết quả. Nếu mẫu máu bị vỡ hồng cầu thì phải lấy máu lại (quay lại bước lấy máu). Sau khi đọc kết quả, bác sĩ chọn một trong bốn hướng: nhập viện nội trú, chuyển mổ cấp cứu, chuyển tuyến trên, hoặc cho về kèm đơn thuốc.

Song song với việc khám, thu ngân kiểm tra thẻ bảo hiểm y tế: thẻ hợp lệ thì tính đồng chi trả, thẻ không hợp lệ hoặc không có thẻ thì thu tạm ứng; nếu bệnh nhân không đủ tiền tạm ứng thì báo công tác xã hội rồi vẫn tiếp tục điều trị. Trước khi cho về, bệnh nhân phải thanh toán; nếu thanh toán thất bại thì quay lại quầy thu ngân thử lại. Kết thúc: Đã nhập viện, Đã chuyển mổ, Đã chuyển tuyến, Đã ra về. Đường quan trọng nhất là Vàng → khám → cận lâm sàng → đọc kết quả → cho về.

### Must show

* 5 lanes with the Vietnamese names; every step sits in one lane.
* A three-way exit from the triage decision (Đỏ, Vàng, Xanh) and a four-way exit after the results are read.
* A parallel split and join around blood test and imaging.
* At least 4 lines that return to an earlier step: reassessment to triage, wait loop, haemolysed sample to blood draw, failed payment to the cashier.
* 4 distinct end states. Vietnamese diacritics are not clipped by their boxes.

---

## hard-sequence — Checkout with 3-D Secure and a saga rollback

### Brief

Draw a sequence diagram of a web checkout. Participants, in this order: Shopper, Browser SPA, API Gateway, Auth Service, Order Service, Inventory Service, Payment Service, Card Network / Issuer ACS, Message Broker, Notification Service.

1. Shopper clicks Pay in the Browser. The Browser sends POST /checkout with a bearer token to the Gateway. The Gateway asks Auth to validate the token; Auth checks its own cache (a message to itself) and answers 200 with the claims.
2. Optional part, only if the token has expired: Gateway answers 401, Browser posts the refresh token to Auth, Auth returns a new token, Browser sends the checkout again.
3. Gateway forwards to Order Service. Order Service creates the order as PENDING (message to itself), then in parallel: (a) asks Inventory to reserve the 3 lines and (b) asks Payment to create a payment intent. Both answer.
4. Alternatives on the card: [frictionless] Payment authorises with the Card Network and gets an approval. [challenge required] Payment returns a 3-D Secure redirect all the way back through Order Service and Gateway to the Browser; the Browser shows the issuer page; the Shopper types the one-time code; the Browser posts the result to the Issuer ACS; the ACS calls the Payment Service webhook; Payment authorises and gets an approval.
5. Loop, up to 3 times with back-off: Payment sends capture to the Card Network; on a timeout it retries.
6. Alternatives on the outcome: [captured] Payment tells Order Service; Order Service marks the order PAID and publishes OrderPaid to the Broker (asynchronous); the Broker delivers it to Notification Service and to Inventory (commit the reservation), asynchronously; Notification sends the email to the Shopper. [capture failed after 3 tries] Payment tells Order Service; Order Service asks Inventory to release the reservation, asks Payment to void the authorisation, marks the order CANCELLED and publishes OrderCancelled; Notification tells the Shopper.
7. In both outcomes the Order Service answers the Gateway, and the Gateway answers the Browser (201 or 402), and the Browser shows the result to the Shopper.

Show synchronous calls, their returns and asynchronous messages differently, and show when each service is active.

### Must show

* 10 participants in the given order; about 45 messages in time order.
* Fragments: one opt (refresh), one par (reserve and intent), two alt (3-D Secure; outcome) and one loop (capture retry). The frames nest without cutting through messages they do not own.
* At least 2 self messages (cache check, create PENDING).
* Asynchronous messages through the Broker look different from calls and returns.
* The long 3-D Secure return path crosses four lifelines and its label is readable.

---

## hard-er — Multi-tenant marketplace schema

### Brief

Draw an ER diagram for a multi-tenant marketplace database with these 26 tables. Show primary keys, foreign keys and at least the listed columns.

Tenancy and identity: `tenants` (id, slug, plan, created_at); `users` (id, tenant_id, email, password_hash, status); `roles` (id, tenant_id, name); `user_roles` (user_id, role_id; composite primary key); `api_keys` (id, user_id, hash, last_used_at); `audit_log` (id, tenant_id, actor_user_id, entity_type, entity_id, action, at), where entity_type plus entity_id point to any table.

Catalogue: `sellers` (id, tenant_id, owner_user_id, legal_name); `categories` (id, tenant_id, parent_id pointing to categories, name); `products` (id, seller_id, category_id, title, status); `product_variants` (id, product_id, sku unique, price_cents, currency); `product_images` (id, product_id, url, position); `tags` (id, tenant_id, label); `product_tags` (product_id, tag_id; composite primary key); `warehouses` (id, seller_id, country); `stock_levels` (variant_id, warehouse_id, on_hand, reserved; composite primary key).

Orders: `customers` (id, tenant_id, user_id nullable, email); `addresses` (id, customer_id, kind, line1, city, country); `carts` (id, customer_id, updated_at); `cart_items` (cart_id, variant_id, qty; composite primary key); `orders` (id, customer_id, shipping_address_id, billing_address_id, status, total_cents, placed_at); `order_items` (id, order_id, variant_id, seller_id, qty, unit_price_cents); `shipments` (id, order_id, warehouse_id, carrier, tracking_no); `shipment_items` (shipment_id, order_item_id, qty; composite primary key).

Money: `payments` (id, order_id, provider, amount_cents, status); `refunds` (id, payment_id, order_item_id nullable, amount_cents, reason); `payouts` (id, seller_id, period_start, period_end, amount_cents); `reviews` (id, product_id, customer_id, order_item_id unique, rating, body).

Every table with a tenant_id belongs to one tenant. An order has two different links to addresses. Mark which side of each relation is "one" and which is "many", and which are optional. Group the tables by the four domains.

### Must show

* 27 tables are named in the text (the brief says 26: `reviews` makes 27). The agent should draw all 27 or say that the count is off.
* Composite primary keys on the 5 junction tables.
* The self-reference on `categories.parent_id`.
* Two separate relations from `orders` to `addresses`.
* `tenants` is a hub with 8 relations; the lines do not hide the tables.
* The four domains are visible as groups; optional sides (`customers.user_id`, `refunds.order_item_id`) are marked.

---

## hard-architecture — Event-driven ride platform

### Brief

Draw the architecture of a ride-hailing platform, 34 components in 7 zones.

Clients: Rider app (iOS/Android), Driver app, Ops web console, Partner API clients.
Edge: CDN, WAF, API Gateway, WebSocket Gateway.
Core services: Identity, Rider profile, Driver profile, Trip, Matching, Pricing, Routing/ETA, Payments, Promotions, Notifications, Support.
Async backbone: Kafka (topics trip-events, location-stream, payment-events), Schema Registry, Stream processor (Flink), Dead-letter queue.
Data: Postgres (trips, payments), Redis (geo index, sessions), Cassandra (location history), Elasticsearch (support search), S3 data lake, Snowflake warehouse.
Platform: Kubernetes, Service mesh, Vault, Observability (Prometheus, Loki, Tempo), Feature flags.
External: Card processor, Maps provider, SMS/Push provider, Identity verification (KYC).

Calls. All four clients go through CDN then WAF then API Gateway; the two apps also keep a WebSocket to the WebSocket Gateway. The API Gateway calls Identity on every request and routes to Rider profile, Driver profile, Trip, Payments, Promotions and Support. Trip calls Matching, Pricing and Routing/ETA synchronously. Matching reads the Redis geo index. Routing calls the Maps provider. Pricing calls Promotions. Payments calls the Card processor. Driver profile calls KYC. Notifications calls the SMS/Push provider.

Events. The Driver app sends locations through the WebSocket Gateway to the Kafka location-stream; Flink reads it and writes the Redis geo index and Cassandra. Trip, Payments and Matching publish to Kafka; Notifications, Support, Payments and the Stream processor consume. Failed messages go to the Dead-letter queue. Every producer checks the Schema Registry. Kafka is sunk to the S3 data lake, and the lake loads Snowflake nightly. Trip and Payments own Postgres; Identity keeps sessions in Redis; Support indexes into Elasticsearch.

The main path to highlight: Rider app → Gateway → Trip → Matching → Kafka → Notifications → Push provider → Driver app. Draw synchronous calls and event streams differently. The Platform zone supports everything: do not draw a line from it to every service.

### Must show

* 7 zones with their names; the components listed above inside the right zone.
* Kafka is a hub with at least 9 lines that can still be followed one by one.
* Synchronous calls and event streams look different; one highlighted main path that ends back at the Driver app.
* The API Gateway fan-out to 7 services is readable.
* Platform is drawn as a supporting zone without a line to each service.

---

## hard-bpmn — Motor insurance claim across three pools

### Brief

Draw a BPMN diagram of a motor insurance claim with three pools: Policyholder (one lane), Insurer (lanes: Claims intake, Claims adjuster, Fraud unit, Finance) and Repair garage (one lane).

Policyholder: the accident happens (start), they submit a claim form with photos (message to the Insurer), wait for a decision, and then either receive a rejection letter (end), or bring the car to the garage, collect the repaired car and confirm satisfaction (end).

Insurer, Claims intake: a message start event receives the claim; register the claim; check the policy is active (exclusive gateway). Not active: send the rejection letter and end. Active: a parallel gateway starts three things: the adjuster assesses the damage; the Fraud unit runs an automated fraud score (service task); intake requests the police report. The police report request has a timer boundary event of 10 days: if it fires, send a reminder and wait again. All three join.

After the join, an exclusive gateway on the fraud score: low goes on; high goes to a manual investigation subprocess (collapsed) in the Fraud unit, which can end in an error end event "Fraud confirmed" (the claim is rejected and reported) or go on. Then the adjuster decides: total loss, repairable, or below the excess (rejection). Total loss: Finance calculates the market value, the offer is sent to the Policyholder, and an event-based gateway waits for either the acceptance message or a 14-day timer (then escalate to a call and wait again). On acceptance Finance pays the settlement and the claim is closed.

Repairable: the Insurer sends a repair authorisation to the garage. Garage: receive the authorisation, inspect the car, send a quote back. The adjuster approves the quote, or asks for a revised quote (loop back to the garage, at most twice). The garage repairs the car (a looping task while parts are missing), sends the invoice, and hands the car over. Finance pays the garage, minus the excess, which the Policyholder pays to the garage directly. The claim is closed (end).

Show message flows between pools differently from sequence flows inside a pool.

### Must show

* 3 pools; the Insurer pool has 4 lanes.
* Gateways of three kinds: exclusive, parallel (split and join of three branches) and event-based.
* A timer boundary event on the police report task, a timer after the event-based gateway, and an error end event.
* A collapsed subprocess and a looping task.
* At least 8 message flows between pools, drawn differently from sequence flows, and none running along a pool border.
* The quote revision loop returns to the garage pool.

---

## hard-state — Trip state machine with composite and parallel states

### Brief

Draw a UML state diagram for a ride trip. The initial state leads to Requested.

Requested: on entry, start the search timer. `driverAccepted` goes to Assigned. `timeout [after 60 s]` goes to NoDriver. `riderCancelled` goes to Cancelled. NoDriver: `retry [attempts < 3]` goes back to Requested; `retry [attempts >= 3]` or `giveUp` goes to Cancelled.

Assigned is a composite state with the substates EnRoute (initial), Arrived and Waiting. EnRoute: `gpsUpdate` is a transition to itself that recalculates the ETA; `reachedPickup` goes to Arrived. Arrived: `after 2 min` goes to Waiting, which charges a waiting fee per minute as an activity. From Arrived or Waiting, `riderOnBoard` leaves the composite state to InProgress. From any substate of Assigned: `driverCancelled` goes back to Requested (re-match); `riderCancelled [before arrival]` goes to Cancelled without a fee; `riderCancelled [after arrival]` goes to CancelledWithFee; `noShow [waited 5 min]` goes to CancelledWithFee.

InProgress is a composite state with two parallel regions. Region Movement: Driving (initial), Paused (`stopRequested` / `resume`), Rerouting (`destinationChanged`, and back to Driving on `routeReady`). Region Safety: Normal (initial), SosActive (`sosPressed`), Monitored (`supportJoined`), and back to Normal on `resolved`. `arrivedAtDestination` leaves InProgress to Completing. `emergencyStop` from SosActive ends the trip in Aborted. If the app loses connection, InProgress goes to Suspended, and `reconnected` returns to the substate it was in (history).

Completing: Fare is calculated, then a choice: `[card on file]` goes to Charging, `[cash]` goes to AwaitingCash. Charging: `approved` goes to Paid; `declined [retries < 2]` goes back to Charging; `declined [retries >= 2]` goes to PaymentDue. AwaitingCash: `driverConfirmsCash` goes to Paid. PaymentDue: `paidLater` goes to Paid; `after 7 days` goes to WrittenOff. Paid: `rated` or `after 24 h` goes to Closed. Final states: Closed, Cancelled, CancelledWithFee, Aborted, WrittenOff. From Paid, `disputeOpened` goes to Disputed; `resolvedForRider` goes to Refunded then Closed; `resolvedForDriver` goes to Closed.

### Must show

* Two composite states: Assigned with 3 substates, InProgress with two parallel regions of 3 states each.
* A history return from Suspended into InProgress.
* A choice point after the fare; self transitions on EnRoute and Charging.
* Guards in square brackets are readable on the lines; transitions that leave a composite state start at its border.
* 5 final states, and about 45 transitions.

---

## hard-org-chart — Tập đoàn bán lẻ (Vietnamese, 62 positions)

### Brief

Vẽ sơ đồ tổ chức của một tập đoàn bán lẻ, chữ tiếng Việt có dấu, gồm 62 vị trí, 5 cấp.

Cấp 1: Tổng Giám đốc Nguyễn Thị Minh Khuê. Trợ lý Tổng Giám đốc Phạm Quỳnh Anh và Chánh Văn phòng Hội đồng quản trị Đỗ Hữu Nghĩa là vị trí tham mưu, vẽ lệch sang bên, không nằm trong tuyến quản lý.

Cấp 2 (báo cáo Tổng Giám đốc), 7 người: Giám đốc Tài chính Trần Quốc Bảo; Giám đốc Vận hành Lê Hoàng Phúc; Giám đốc Công nghệ Vũ Thanh Tùng; Giám đốc Nhân sự Đặng Ngọc Ánh; Giám đốc Kinh doanh Bùi Gia Huy; Giám đốc Marketing Hoàng Thị Thu Hằng; Giám đốc Pháp chế và Tuân thủ Phan Đình Trọng Nghĩa.

Cấp 3. Tài chính: Kế toán trưởng, Trưởng phòng Ngân quỹ, Trưởng phòng Kế hoạch tài chính, Trưởng phòng Thuế. Vận hành: Giám đốc Chuỗi cung ứng, Giám đốc Vùng Miền Bắc, Giám đốc Vùng Miền Trung, Giám đốc Vùng Miền Nam, Trưởng phòng Chất lượng. Công nghệ: Trưởng phòng Hạ tầng, Trưởng phòng Phát triển sản phẩm số, Trưởng phòng Dữ liệu và Trí tuệ nhân tạo, Trưởng phòng An toàn thông tin. Nhân sự: Trưởng phòng Tuyển dụng, Trưởng phòng Đào tạo, Trưởng phòng Lương thưởng và Phúc lợi. Kinh doanh: Trưởng phòng Bán lẻ, Trưởng phòng Thương mại điện tử, Trưởng phòng Khách hàng doanh nghiệp. Marketing: Trưởng phòng Thương hiệu, Trưởng phòng Truyền thông số. Pháp chế: Trưởng phòng Hợp đồng (đang tuyển, vị trí trống).

Cấp 4. Dưới Giám đốc Chuỗi cung ứng: Trưởng kho Hà Nội, Trưởng kho Đà Nẵng, Trưởng kho TP. Hồ Chí Minh, Trưởng bộ phận Vận tải, Trưởng bộ phận Mua hàng. Dưới mỗi Giám đốc Vùng: 3 Quản lý khu vực (ví dụ Miền Bắc: Hà Nội, Hải Phòng, Quảng Ninh; Miền Trung: Đà Nẵng, Huế, Nha Trang; Miền Nam: TP. Hồ Chí Minh, Cần Thơ, Bình Dương). Dưới Trưởng phòng Phát triển sản phẩm số: Trưởng nhóm Ứng dụng di động, Trưởng nhóm Web, Trưởng nhóm Thiết kế trải nghiệm. Dưới Trưởng phòng Dữ liệu: Trưởng nhóm Kỹ thuật dữ liệu, Trưởng nhóm Phân tích.

Cấp 5. Dưới Quản lý khu vực Hà Nội: 4 Cửa hàng trưởng (Cầu Giấy, Hoàn Kiếm, Long Biên, Hà Đông). Dưới Trưởng nhóm Ứng dụng di động: 3 kỹ sư.

Quan hệ đường chấm (báo cáo chức năng, không phải quản lý trực tiếp): Trưởng phòng An toàn thông tin báo cáo chức năng cho Giám đốc Pháp chế; Trưởng phòng Thương mại điện tử báo cáo chức năng cho Giám đốc Công nghệ; ba Giám đốc Vùng báo cáo chức năng cho Giám đốc Kinh doanh. Các vị trí cấp 3 trở xuống không cần tên người, chỉ cần chức danh. Tô màu theo khối.

### Must show

* 62 positions: 1 + 2 staff + 7 + 22 + 19 + 7 + the 4 store managers (the brief's own total; the reviewer recounts).
* The two staff positions sit beside the chief, off the management line.
* One vacant position is marked as vacant.
* 5 dotted functional reports are drawn differently from solid reports and do not run through boxes.
* Long Vietnamese titles ("Trưởng phòng Dữ liệu và Trí tuệ nhân tạo") fit their boxes.
* The uneven tree (the Operations branch is far wider and deeper) stays readable.

---

## hard-gantt — Core banking migration, 46 tasks over 52 weeks

### Brief

Draw a Gantt chart for a core banking migration that starts on Monday 4 January 2027 and runs 52 weeks. Weeks are numbered from 1. `W5-W8` means start of week 5 to end of week 8. Owners are in brackets. `→` after a task lists the tasks that must finish before it starts.

Phase 1, Mobilise: Business case W1-W3 (PMO), done. Vendor selection W2-W7 (Procurement), done. Contract signature, milestone end of W8 → Vendor selection. Team onboarding W8-W10 (HR), 80%. Programme governance W1-W52 (PMO), runs the whole year, 25%.

Phase 2, Design: Current-state analysis W6-W12 (Architecture), 60%. Target architecture W10-W17 (Architecture) → Current-state analysis. Data model mapping W12-W20 (Data) → Current-state analysis. Integration inventory W10-W14 (Integration). Security design W14-W19 (Security) → Target architecture. Design sign-off, milestone end of W20 → Target architecture, Data model mapping, Security design.

Phase 3, Build: Environment setup W15-W18 (Platform). Core configuration W21-W32 (Vendor) → Design sign-off. Product catalogue setup W23-W30 (Product). Integration layer build W21-W34 (Integration) → Design sign-off, Integration inventory. Payments adapters W24-W33 (Payments). Card system adapter W26-W33 (Cards). Reporting rebuild W27-W36 (Data). Access management W22-W27 (Security). Batch scheduler W28-W32 (Platform). Build complete, milestone end of W36.

Phase 4, Data migration: Extract scripts W21-W26 (Data) → Data model mapping. Cleansing rules W22-W28 (Data). Mock migration 1 W29-W30 → Extract scripts, Cleansing rules. Reconciliation 1 W31. Mock migration 2 W34-W35 → Reconciliation 1. Reconciliation 2 W36. Dress rehearsal W44-W45 → Reconciliation 2, UAT cycle 2. Final migration W49 (a weekend, show it as one week) → Go/No-go.

Phase 5, Test: Test strategy W18-W20 (QA). System integration test W33-W38 (QA) → Core configuration, Integration layer build. Performance test W37-W40 (Platform). Security penetration test W38-W40 (Security). UAT cycle 1 W39-W41 (Business) → System integration test. Defect fixing W39-W44 (Vendor). UAT cycle 2 W42-W43 (Business) → UAT cycle 1. Regulatory parallel run W40-W47 (Finance). Test exit, milestone end of W47.

Phase 6, Cutover and hypercare: Training material W30-W36 (Change). Branch staff training W37-W46 (Change) → Training material. Customer communications W40-W48 (Marketing). Cutover runbook W38-W44 (PMO). Go/No-go, milestone end of W48 → Test exit, Dress rehearsal. Go-live, milestone end of W49 → Final migration. Hypercare W50-W52 (Vendor, PMO). Legacy decommission planning W46-W52 (Architecture). Lessons learned W52 (PMO).

Mark today at the start of week 11. Mark a change freeze over weeks 46-49 as a shaded band. Show the critical path: Vendor selection → Contract → … → Design sign-off → Core configuration → System integration test → UAT 1 → UAT 2 → Dress rehearsal → Go/No-go → Final migration → Go-live.

### Must show

* 6 phases; 46 rows, of which 6 are milestones drawn as diamonds.
* A 52-week axis with months or weeks readable; a today marker at week 11; a shaded freeze band over weeks 46-49.
* Progress on the tasks that give one (100%, 80%, 60%, 25%).
* At least 20 dependency arrows, several across phases, that can be followed.
* The critical path stands out. The year-long Programme governance bar spans the full axis.
* One-week tasks (Reconciliation 1, Lessons learned) are still visible and labelled.

---

## hard-mind-map — Chuyển đổi số doanh nghiệp (Vietnamese, 4 levels)

### Brief

Vẽ sơ đồ tư duy bằng tiếng Việt có dấu với ý trung tâm "Chuyển đổi số doanh nghiệp vừa và nhỏ". Có 7 nhánh chính, không đều nhau:

1. Chiến lược: Tầm nhìn 3 năm; Lộ trình theo quý; Ngân sách (Vốn tự có; Vay ưu đãi; Hỗ trợ của nhà nước); Chỉ số đo lường (Doanh thu số; Tỷ lệ khách quay lại; Thời gian xử lý đơn).
2. Con người: Lãnh đạo cam kết; Đào tạo lại (Kỹ năng số cơ bản; Phân tích dữ liệu; An toàn thông tin); Tuyển dụng (Kỹ sư dữ liệu; Quản lý sản phẩm); Văn hoá thử nghiệm; Quản trị thay đổi (Truyền thông nội bộ; Đại sứ thay đổi; Khen thưởng).
3. Quy trình: Số hoá chứng từ; Tự động hoá (Kế toán; Kho vận (Quét mã vạch; Kiểm kê tự động; Dự báo tồn kho); Chăm sóc khách hàng); Chuẩn hoá dữ liệu; Phê duyệt điện tử.
4. Công nghệ: Hạ tầng đám mây (Công cộng; Riêng; Lai); Phần mềm lõi (ERP; CRM; Quản lý kho; Kế toán); Tích hợp (API; Trao đổi dữ liệu điện tử); Trí tuệ nhân tạo (Trợ lý ảo; Gợi ý sản phẩm; Phát hiện gian lận); Thiết bị (Máy bán hàng; Cảm biến kho).
5. Khách hàng: Kênh bán (Cửa hàng; Website; Sàn thương mại điện tử; Mạng xã hội); Trải nghiệm đa kênh; Chương trình khách hàng thân thiết; Thanh toán (Mã QR; Ví điện tử; Trả góp).
6. Dữ liệu: Thu thập; Kho dữ liệu; Báo cáo quản trị; Bảo vệ dữ liệu cá nhân (Nghị định 13/2023/NĐ-CP).
7. Rủi ro: An ninh mạng (Mã độc tống tiền; Lừa đảo qua thư); Phụ thuộc nhà cung cấp; Vượt ngân sách; Nhân viên phản đối.

Dấu ngoặc là các ý con. Ngoài ra vẽ ba liên kết chéo giữa các nhánh: "An toàn thông tin" (Con người) với "An ninh mạng" (Rủi ro); "Dự báo tồn kho" (Quy trình) với "Trí tuệ nhân tạo" (Công nghệ); "Ngân sách" (Chiến lược) với "Vượt ngân sách" (Rủi ro). Mỗi nhánh chính một màu.

### Must show

* The centre and 7 main branches, each in its own colour; about 95 nodes in all.
* Four levels below the centre exist in one place (Quy trình → Tự động hoá → Kho vận → 3 leaves).
* The unbalanced map (Công nghệ has 19 descendants, Dữ liệu 5) has no overlapping labels.
* 3 cross links are drawn, or the report says the type does not support them.
* Long Vietnamese labels wrap and are not clipped.

---

## hard-class — Plugin-based document editor

### Brief

Draw a UML class diagram for a document editor. Show attributes and methods with visibility (+, -, #), types, and mark static and abstract members.

Interfaces: `Serializable` (+serialize(): bytes, +deserialize(data: bytes): void); `Observable<T>` (+subscribe(o: Observer<T>): Subscription, +notify(event: T): void); `Observer<T>` (+onEvent(event: T): void); `Command` (+execute(): void, +undo(): void, +canMerge(other: Command): bool); `Plugin` (+id: string, +activate(ctx: EditorContext): void, +deactivate(): void); `Renderer` (+render(node: Node, surface: Surface): void).

Abstract classes: `Node` (#id: UUID, #parent: Node?, +children: List<Node>, +accept(v: NodeVisitor): void abstract, +clone(): Node) implements Serializable; `BlockNode` and `InlineNode` extend Node; `BaseCommand` (#doc: Document, #timestamp: Instant) implements Command.

Concrete nodes: `Paragraph`, `Heading` (+level: int), `ListBlock` (+ordered: bool), `Table` (+rows: int, +cols: int), `CodeBlock` (+language: string) extend BlockNode; `TextRun` (+text: string, +marks: Set<Mark>), `Link` (+href: URL), `ImageInline` (+src: URL, +alt: string) extend InlineNode. `TableCell` extends BlockNode; a Table is composed of 1..* TableCell. `Mark` is an enumeration: BOLD, ITALIC, CODE, STRIKE.

Core: `Document` (-root: BlockNode, -version: long, +apply(c: Command): void, +snapshot(): Snapshot) implements Observable<ChangeEvent> and Serializable; it is composed of exactly one root Node. `Snapshot` (+version: long, +data: bytes). `ChangeEvent` (+kind: ChangeKind, +path: List<int>). `ChangeKind` enumeration: INSERT, DELETE, UPDATE, MOVE. `History` (-undoStack: Deque<Command>, -redoStack: Deque<Command>, +push(c: Command): void, +undo(): void, +redo(): void) aggregates 0..* Command and belongs to one Document. `InsertTextCommand`, `DeleteRangeCommand`, `FormatCommand`, `MoveNodeCommand` extend BaseCommand. `CompositeCommand` extends BaseCommand and aggregates 1..* Command.

Editor: `Editor` (-document: Document, -selection: Selection, -plugins: Map<string, Plugin>, +static create(config: EditorConfig): Editor, +dispatch(c: Command): void) implements Observer<ChangeEvent>; it has one Document, one History, one Selection, 0..* Plugin, and uses a Renderer. `Selection` (+anchor: Position, +focus: Position, +isCollapsed(): bool). `Position` (+path: List<int>, +offset: int). `EditorContext` (+editor: Editor, +registerCommand(name: string, factory: CommandFactory): void). `EditorConfig` (+readOnly: bool, +plugins: List<Plugin>).

Plugins and rendering: `SpellCheckPlugin`, `CollaborationPlugin` (-socket: WebSocket, -clock: VectorClock), `MarkdownShortcutsPlugin` implement Plugin. CollaborationPlugin also implements Observer<ChangeEvent> and depends on `VectorClock` (+tick(): void, +merge(o: VectorClock): void). `NodeVisitor` is an interface with one visit method per concrete node; `HtmlRenderer` and `CanvasRenderer` implement both Renderer and NodeVisitor. `WordCountVisitor` implements NodeVisitor.

Draw inheritance, interface realisation, composition, aggregation, plain association and dependency with their own line ends, and write the multiplicities.

### Must show

* About 40 classifiers: 7 interfaces (with `NodeVisitor`), 4 abstract classes, 2 enumerations, the rest concrete.
* Six relation kinds, each with its own line end; multiplicities on compositions and aggregations.
* Generic names (`Observable<ChangeEvent>`, `Map<string, Plugin>`) are not broken or clipped.
* The Node hierarchy (2 abstract children, 9 concrete) reads as a tree.
* `Command` is a hub: 1 abstract realisation, History and CompositeCommand aggregate it, Editor dispatches it.
* Static and abstract members are marked.

---

## hard-layers — A request through a seven-layer platform

### Brief

Draw a layers diagram of a SaaS platform with 7 stacked layers and 2 vertical bands that cross all layers.

Layers, top to bottom, with their items:
1. Experience: Web app (React), iOS app, Android app, Public API docs, Admin console, Embeddable widget.
2. Edge and delivery: CDN, WAF, Rate limiter, API Gateway, GraphQL federation router, WebSocket hub.
3. Application services: Accounts, Billing, Workspaces, Documents, Search, Notifications, Automation rules, Reporting.
4. Domain and shared libraries: Auth SDK, Permissions engine, Feature flags, Audit trail, Pricing rules.
5. Integration and messaging: Event bus, Job queue, Webhook dispatcher, Email/SMS adapters, Third-party connectors.
6. Data: PostgreSQL (primary + 2 replicas), Redis, OpenSearch, Object storage, ClickHouse, Backup vault.
7. Infrastructure: Kubernetes, Service mesh, Terraform state, Multi-region network, Hardware security module.

Vertical bands that touch every layer: "Security and compliance (SSO, secrets, SOC 2 controls)" on the left and "Observability (logs, metrics, traces, on-call)" on the right.

Arrows. The main request to highlight: Web app → CDN → WAF → API Gateway → GraphQL federation router → Documents → Permissions engine → PostgreSQL. Also: iOS app and Android app → API Gateway; Embeddable widget → WebSocket hub → Notifications; Documents → Event bus → Search → OpenSearch; Event bus → Automation rules → Job queue → Webhook dispatcher → Third-party connectors; Billing → Pricing rules; Reporting → ClickHouse (this arrow skips two layers); Accounts → Auth SDK → Redis; Notifications → Email/SMS adapters; PostgreSQL → Backup vault (inside one layer); Object storage → CDN (an arrow that goes back up four layers); every Application service runs on Kubernetes (draw this once, not eight times).

### Must show

* 7 layers in the given order with 41 items in the right layer.
* Two vertical bands that span all 7 layers, left and right.
* One highlighted main request with 7 hops.
* Arrows that skip layers (Reporting → ClickHouse), stay inside a layer (PostgreSQL → Backup vault) and go upward (Object storage → CDN) are all drawn and do not run through unrelated items.
* "Runs on Kubernetes" is drawn once for the whole layer.

---

## hard-usecase — University learning platform

### Brief

Draw a UML use case diagram for a university learning platform with two system boundaries side by side: "Learning Platform" and "Assessment Engine".

Actors on the left: Visitor; Student (a Student is a kind of Registered user); Teaching assistant (a kind of Registered user); Lecturer (a kind of Teaching assistant: can do everything a TA can); Registered user (abstract). Actors on the right: Department administrator; and three system actors: Identity Provider (SSO), Plagiarism Checker, Payment Gateway, Student Records System.

Learning Platform use cases: Browse course catalogue (Visitor, Registered user); Sign in (Registered user, Identity Provider); Enrol in course (Student); Pay course fee (Student, Payment Gateway), which extends Enrol in course when the course is paid; Join waiting list, which extends Enrol in course when the course is full; Watch lecture (Student); Download materials (Student); Post in forum (Registered user); Moderate forum (Teaching assistant); Publish course (Lecturer); Upload materials (Lecturer); Schedule live session (Lecturer); Manage enrolments (Department administrator); Approve course (Department administrator); Generate transcript (Student, Student Records System); Configure term calendar (Department administrator). Enrol in course, Post in forum, Watch lecture and Publish course each include Sign in. Publish course includes Approve course.

Assessment Engine use cases: Create assignment (Lecturer); Create quiz (Lecturer); Submit assignment (Student); Take quiz (Student); Check originality (Plagiarism Checker), included by Submit assignment; Grade submission (Teaching assistant); Auto-grade quiz, included by Take quiz; Request regrade (Student), which extends Grade submission; Approve regrade (Lecturer); Publish grades (Lecturer), which includes Sync grades to records (Student Records System); Grant extension (Lecturer), which extends Submit assignment; Proctor exam (Teaching assistant); Report misconduct (Teaching assistant, Department administrator), which extends Check originality and extends Proctor exam; Export analytics (Lecturer, Department administrator).

Draw actor generalisation, include and extend each with its UML notation, and write the extension conditions where given.

### Must show

* Two system boundaries with 16 and 14 use cases.
* 10 actors: 5 on the left with a three-step generalisation chain (Lecturer → Teaching assistant → Registered user ← Student), 5 on the right, of which 4 are systems (the brief says "three system actors" and lists four).
* Include (dashed, towards the included case) and extend (dashed, towards the base case) are labelled and point the right way.
* Sign in is a hub of 4 includes plus 2 actors.
* Associations from right-hand actors do not run through unrelated use cases; a use case in one boundary linked to an actor on the far side stays traceable.

---

## hard-wireframe — Analytics dashboard: desktop, tablet, phone and states

### Brief

Draw wireframes for an analytics dashboard page of a B2B product, as one page with three parts.

Part 1, a responsive set of the same page at three widths: desktop (1440), tablet (834) and phone (390).

Desktop content: a top bar (logo, workspace switcher, global search, notifications bell with a badge, avatar menu); a left sidebar with 8 navigation items in two groups (Overview, Dashboards, Reports, Alerts / Data sources, Team, Billing, Settings) and a collapse control; a page header (breadcrumb, title "Revenue overview", date-range picker, compare toggle, Export button, primary button "New chart"); a filter row of 4 chips plus "Add filter"; a row of 4 KPI cards (value, delta, sparkline); a large line chart (two thirds) next to a donut chart (one third); a data table with 6 columns (checkbox, Customer, Plan, MRR, Change, Last seen), a sortable header, 8 rows, row actions and pagination; a right-side activity feed of 5 items; a footer.

Tablet: the sidebar becomes an icon rail, KPI cards are 2 by 2, the charts stack, the table hides two columns, the activity feed moves under the table. Phone: the sidebar becomes a bottom tab bar of 5 items, the top bar keeps only a menu, the title and the bell; KPI cards become a horizontal carousel; the filters collapse into one "Filters (4)" button; the table becomes a list of cards; the Export and New chart actions go into a floating action button.

Part 2, a state set of the desktop data table alone: loading (skeleton rows), empty (illustration, message and a button), error (banner with Retry), and a state with 3 rows selected that shows a bulk action bar.

Part 3: the phone "New chart" flow as 3 screens in order: choose a metric (searchable list), choose a chart type (grid of 6 tiles), preview and save (chart, name field, Save and Cancel).

Add numbered notes (at least 10) that explain the behaviour: what collapses at each width, the sticky table header, the keyboard shortcut for search, what the badge counts, and the limit of 5 filters.

### Must show

* Three device frames of clearly different widths with the same content rearranged as described.
* The desktop frame holds all 9 regions; the table shows 6 columns and 8 rows.
* A state set of 4 table states.
* A 3-screen phone flow in order.
* At least 10 numbered notes whose numbers appear on the screens and in a legend.
* Dense desktop content does not overflow its frame.

---

## hard-roadmap — Product roadmap, 6 teams by 6 quarters

### Brief

Draw a roadmap for 2027 Q1 to 2028 Q2 (6 quarters) with one row per team. Items are written as `name (quarters) [status]`. Status is one of done, in progress, planned, at risk.

Platform: Kubernetes 1.34 upgrade (27Q1) [done]; Multi-region failover (27Q1-27Q3) [in progress]; Cost dashboards (27Q2) [in progress]; Zero-trust network (27Q3-28Q1) [planned]; Developer portal v2 (27Q4) [planned]; ARM migration (28Q1-28Q2) [planned]; Chaos testing programme (28Q2) [planned].

Payments: PSD3 readiness (27Q1-27Q2) [in progress]; Instant payouts (27Q2-27Q3) [at risk]; Multi-currency wallets (27Q3-27Q4) [planned]; Dispute automation (27Q4) [planned]; Buy now, pay later pilot (28Q1) [planned]; Ledger v3 (27Q1-28Q2) [in progress], which runs across all six quarters.

Growth: Onboarding redesign (27Q1) [done]; Referral programme (27Q2) [in progress]; Pricing experiments (27Q2-27Q3) [in progress]; Localisation: Vietnam, Thailand, Indonesia (27Q3-28Q1) [planned]; Self-serve upgrade (27Q4) [planned]; Lifecycle messaging (28Q1-28Q2) [planned].

Mobile: Offline mode (27Q1-27Q2) [at risk]; Design system 3.0 (27Q1-27Q3) [in progress]; Passkeys (27Q2) [planned]; Tablet layout (27Q3) [planned]; Widgets and live activities (27Q4) [planned]; React Native to native rewrite (27Q4-28Q2) [planned]; Accessibility audit fixes (28Q1) [planned].

Data and AI: Event schema registry (27Q1) [done]; Feature store (27Q1-27Q2) [in progress]; Fraud model v2 (27Q2-27Q3) [in progress]; Assistant for support agents (27Q3-27Q4) [planned]; Forecasting service (27Q4-28Q1) [planned]; Customer-facing assistant (28Q1-28Q2) [planned]; Model governance (27Q2-28Q2) [in progress].

Security and compliance: SOC 2 Type II audit (27Q1-27Q2) [in progress]; Secrets rotation (27Q1) [done]; ISO 27001 certification (27Q3-27Q4) [planned]; Bug bounty launch (27Q3) [planned]; Data residency controls (27Q4-28Q1) [planned]; Penetration test (27Q2, and again 28Q2) [planned].

Dependencies across teams: Instant payouts needs Ledger v3; Multi-currency wallets needs Multi-region failover; Fraud model v2 needs Feature store; Customer-facing assistant needs Assistant for support agents and Model governance; Localisation needs Multi-currency wallets; Passkeys needs Zero-trust network (note: this one points backwards in time, show it as a conflict); Data residency controls needs Multi-region failover.

Milestones on the time axis: Series C close (end of 27Q2), Vietnam launch (end of 27Q4), SOC 2 report issued (end of 27Q2), Annual conference (middle of 28Q1). Mark "today" in the middle of 27Q2.

### Must show

* 6 rows, 6 quarter columns, 40 items (the penetration test appears twice, making 41 bars).
* Items that span quarters have bars of the right length; Ledger v3 spans all six. Rows with overlapping items (Mobile has 3 items in 27Q1-27Q2) stack without overlap.
* Four statuses look different and have a legend.
* 8 cross-team dependencies are drawn; the Passkeys one is marked as a conflict or the report says so.
* 4 milestones and a today marker on the axis; two milestones share the end of 27Q2 and both labels are readable.

---

## hard-explainer — How a contactless card payment works

### Brief

Make an explainer page for people who do not work in payments: "What happens in the two seconds after you tap your card". One page with these parts.

1. A journey through bands. Five bands from top to bottom: "You and the shop" (your card, the shop's card reader), "The shop's bank" (the acquirer, its payment processor), "The card network" (for example Visa or Mastercard: the switch, the token vault, the fraud score), "Your bank" (the issuer: the authorisation system, your account, the risk rules), and "Later that night" (clearing file, settlement between banks, the shop's payout). The journey has 14 numbered steps: 1 tap; 2 the chip makes a one-time code; 3 the reader encrypts and sends; 4 the processor formats the request; 5 the acquirer forwards to the network; 6 the network swaps the token for the real card number; 7 the network scores fraud risk; 8 the network routes to your bank; 9 your bank checks the one-time code; 10 your bank checks balance and risk rules; 11 your bank answers approved or declined; 12 the answer travels all the way back to the reader (one long return through three bands); 13 the reader beeps; and, in the last band, 14 the money actually moves the next day.

2. An analogy beside the journey: "It works like a restaurant order": you = the guest, the reader = the waiter, the network = the kitchen pass, your bank = the chef who decides, settlement = paying the suppliers at the end of the week. Map each of the five to its real part.

3. A comparison of three ways to pay, as columns: Contactless card, Chip and PIN, Phone wallet. Rows: what proves it is you; what the shop sees; limit without a PIN; works offline?; who pays if it is fraud. Fill each cell with a few words.

4. A small tree: "Why a payment gets declined", with the branches Not enough money; Looks like fraud (unusual place, unusual amount, too many taps); Technical (reader offline, bank not answering, expired card); Limits (daily limit, contactless limit reached).

5. Three "numbers to remember" call-outs: about 2 seconds; 4 parties; 1 to 2 days until the money moves.

Use plain words, define each technical term the first time (acquirer, issuer, token), and keep the 14 steps readable in order.

### Must show

* Five bands in order with their items; 14 numbered steps that can be followed from 1 to 14, with the long return (step 12) crossing three bands.
* An analogy block with 5 mappings.
* A comparison with 3 columns and 5 rows, every cell filled.
* A tree with 4 branches and 11 leaves.
* Three call-outs. All four parts are on one page without overlapping.
* The terms acquirer, issuer and token are defined.

---

## hard-c4 — Container diagram of an online bank

### Brief

Draw a C4 container diagram for "Internet Banking System".

People: Retail customer; Business customer; Customer support agent; Fraud analyst; Bank operations engineer.

Containers inside the system boundary (name, technology, responsibility): Web application (React SPA: banking in the browser); Mobile app (Kotlin and Swift: banking on the phone); Backoffice portal (Angular: support and fraud tooling); API Gateway (Kong: authentication, rate limits, routing); Backend for frontend (Node.js GraphQL: shapes data for web and mobile); Accounts service (Java Spring Boot: balances and statements); Payments service (Go: transfers, standing orders, SEPA and SWIFT files); Cards service (Java: card controls, PIN change, tokenisation); Onboarding service (Python FastAPI: KYC and account opening); Fraud detection service (Python: real-time scoring, case management); Notification service (Node.js: email, SMS, push); Event bus (Apache Kafka: domain events); Operational database (PostgreSQL: accounts, payments, cards, one schema per service); Document store (MongoDB: KYC documents metadata); Cache (Redis: sessions and rate limits); Object storage (S3-compatible: statements as PDF, KYC scans); Analytics warehouse (Snowflake: reporting); Batch scheduler (Airflow: end-of-day jobs).

External systems: Core Banking Mainframe (IBM z/OS, the ledger of record); Card processor; SEPA clearing house; SWIFT network; Identity verification provider; Credit bureau; Email and SMS provider; Apple and Google push services; Regulator reporting portal.

Relations (write the protocol on each): both customers use the Web application and the Mobile app (HTTPS); the support agent and the fraud analyst use the Backoffice portal; the operations engineer uses the Batch scheduler UI. Web, Mobile and Backoffice call the API Gateway (HTTPS/JSON); the Gateway reads the Cache and routes to the Backend for frontend (web and mobile) and directly to the services (backoffice). The Backend for frontend calls Accounts, Payments, Cards and Onboarding (gRPC). Accounts, Payments and Cards read and write the Operational database (JDBC/SQL) and call the Core Banking Mainframe (IBM MQ). Payments sends files to the SEPA clearing house (SFTP) and messages to SWIFT (ISO 20022 over MQ). Cards calls the Card processor (ISO 8583). Onboarding calls the Identity verification provider and the Credit bureau (HTTPS), writes the Document store and Object storage. Accounts, Payments, Cards and Onboarding publish events to the Event bus; Fraud detection and Notification consume them; Fraud detection can call Payments and Cards to block (gRPC) and writes its cases to the Operational database. Notification calls the Email and SMS provider and the push services. The Batch scheduler triggers Accounts (statements, written to Object storage) and loads the Analytics warehouse from the Operational database and the Event bus, and sends reports to the Regulator reporting portal (HTTPS).

### Must show

* 5 people, 18 containers inside one system boundary, 9 external systems outside it.
* Each container shows its name, technology and responsibility.
* About 55 relations, each with a protocol label that can be attributed to its line.
* Databases and the event bus have their own shapes; people have the person shape; external systems look different from containers.
* The Event bus (4 publishers, 2 consumers, 1 loader) and the Operational database (5 writers, 1 reader) are hubs whose lines can be followed.

---

## hard-dfd — Level 1 DFD of a hospital pharmacy

### Brief

Draw a level 1 data flow diagram of a hospital pharmacy system.

External entities (8): Prescriber; Nurse; Patient; Wholesaler; Health insurer; Drug regulator; Hospital finance system; Ward dispensing cabinet.

Processes (12): 1 Receive prescription; 2 Check interactions and allergies; 3 Verify by pharmacist; 4 Dispense medication; 5 Label and pack; 6 Record administration; 7 Manage stock; 8 Order from wholesaler; 9 Receive goods; 10 Handle controlled drugs; 11 Bill and claim; 12 Report adverse events and recalls.

Data stores (9): D1 Prescriptions; D2 Patient medication record; D3 Drug formulary; D4 Interaction rules; D5 Stock ledger; D6 Purchase orders; D7 Controlled drugs register; D8 Claims; D9 Audit log.

Flows. Prescriber → 1: prescription; 1 → D1: new prescription; 1 → 2: prescription to check; D2 → 2: allergies and current drugs; D3 → 2: drug details; D4 → 2: interaction rules; 2 → Prescriber: interaction alert; 2 → 3: checked prescription; Prescriber → 3: override reason; 3 → D1: verification status; 3 → 4: approved order; 3 → Prescriber: rejection with reason; D5 → 4: stock availability; 4 → D5: stock decrement; 4 → 5: items to pack; 5 → Nurse: labelled medication; 5 → Ward dispensing cabinet: cabinet refill list; Ward dispensing cabinet → 7: cabinet stock levels; 5 → Patient: discharge medication and leaflet; Nurse → 6: administration scan; 6 → D2: administration record; 6 → Prescriber: missed dose alert; Patient → 6: self-reported reaction; 4 → 10: controlled item request; 10 → D7: register entry; Nurse → 10: witness signature; 10 → 4: release authorisation; 10 → Drug regulator: controlled drugs return; D5 → 7: stock levels; 7 → 8: reorder request; D3 → 8: preferred supplier; 8 → D6: purchase order; 8 → Wholesaler: order; Wholesaler → 9: delivery note and goods data; D6 → 9: expected order; 9 → D5: stock receipt; 9 → 10: controlled drugs received; 9 → Hospital finance system: goods received note; Wholesaler → Hospital finance system is outside the system: do not draw it. 4 → 11: dispensed items; D2 → 11: patient cover details; 11 → D8: claim; 11 → Health insurer: claim; Health insurer → 11: remittance or rejection; 11 → Hospital finance system: charges; 11 → Patient: co-payment invoice; Nurse → 12: adverse event report; 6 → 12: reaction record; Drug regulator → 12: recall notice; 12 → D3: formulary update; 12 → 7: quarantine instruction; 12 → Drug regulator: adverse event submission; 12 → Prescriber: recall alert. Processes 3, 4, 10 and 11 each write to D9 Audit log.

Use standard DFD shapes, number the processes and stores, label every flow, and highlight the main flow: Prescriber → 1 → 2 → 3 → 4 → 5 → Nurse → 6.

### Must show

* 8 external entities, 12 numbered processes, 9 numbered data stores, each with its own DFD shape.
* 55 flows drawn (51 named plus 4 to the audit log), each labelled; the one flow the brief says not to draw is absent.
* No flow runs directly between two stores or between two external entities.
* Process 4 (9 flows) and the Prescriber (7 flows) are hubs whose lines can be followed.
* The main flow is highlighted from the Prescriber to process 6.
* An external entity that is far from some of its flows may be drawn twice and marked as a duplicate.

---

## hard-cloud — Two-region AWS deployment with a hybrid link

### Brief

Draw a cloud infrastructure diagram on AWS for a regulated web application, active in eu-west-1 (Ireland) and on standby in eu-central-1 (Frankfurt), with a link to an on-premises data centre.

Global, outside the regions: Users; Route 53 (failover routing with health checks); CloudFront; AWS WAF; AWS Shield Advanced; ACM certificates; an IAM Identity Center; AWS Organizations with three accounts (Network, Production, Security/Log archive).

Primary region eu-west-1, one VPC 10.0.0.0/16 across three Availability Zones (a, b, c). In each AZ: a public subnet (NAT gateway; the Application Load Balancer spans the three public subnets), a private application subnet (EKS worker nodes in an Auto Scaling group, 2 to 6 per AZ), and an isolated data subnet. Data: Aurora PostgreSQL with the writer in AZ a and readers in AZ b and c; ElastiCache Redis with a primary and two replicas; Amazon MSK with 3 brokers, one per AZ; OpenSearch in two AZs. Regional services not in a subnet: S3 (application assets, with versioning), S3 (audit logs, object lock), ECR, Secrets Manager, KMS, CloudWatch, SQS with a dead-letter queue, Lambda (image processing, triggered by S3), Cognito, API Gateway (private, for partners), EventBridge. VPC endpoints (gateway for S3, interface for ECR, Secrets Manager and CloudWatch) so the private subnets do not need the internet for AWS APIs. An internet gateway. A bastion is not used: access is through Systems Manager Session Manager.

Standby region eu-central-1, VPC 10.1.0.0/16 across two AZs: the same three subnet tiers, EKS at minimum size (pilot light), an Aurora global database secondary cluster, an S3 replica bucket, an ALB, MSK replicated with MirrorMaker 2.

Connectivity: a Transit Gateway in each region, peered; the on-premises data centre (core banking, HSM, Active Directory) joins the eu-west-1 Transit Gateway by Direct Connect (2 links, 2 locations) with a site-to-site VPN as backup. Cross-region: Aurora global replication, S3 cross-region replication, ECR replication, MSK mirroring. Security account: GuardDuty, Security Hub, CloudTrail organisation trail writing to the audit bucket, AWS Config.

Traffic to highlight: Users → Route 53 → CloudFront → WAF → ALB → EKS pods → Aurora writer. Show the failover path to Frankfurt as a dashed alternative. Show replication flows differently from request traffic.

### Must show

* Nesting: region → VPC → Availability Zone → subnet tier, for 3 AZs in Ireland and 2 in Frankfurt; the regional services sit in the region but outside the VPC.
* Resources that span AZs (ALB, Aurora cluster, MSK, Auto Scaling group) are shown as spanning, not repeated without a link.
* Global services outside both regions; the on-premises site with Direct Connect (2 links) and the VPN backup into the Transit Gateway.
* Request traffic highlighted on one path; the failover path dashed; 4 replication flows in a different style.
* About 60 resources; names are readable at full size and subnet CIDRs or tiers are labelled.

---

## hard-kanban — Bảng Kanban của nhóm sản phẩm (Vietnamese, 48 cards)

### Brief

Vẽ bảng Kanban bằng tiếng Việt có dấu cho một nhóm phát triển ứng dụng ngân hàng số. Có 7 cột, giới hạn WIP ghi cạnh tên cột: Tồn đọng (không giới hạn); Sẵn sàng (8); Đang phát triển (5); Chờ xem xét mã (3); Đang kiểm thử (4); Chờ phát hành (6); Hoàn thành tuần này (không giới hạn).

Có 2 làn ngang: "Khẩn cấp" ở trên và "Thông thường" ở dưới.

Mỗi thẻ có: mã (NH-xxx), tiêu đề, loại (Tính năng, Lỗi, Nợ kỹ thuật, Nghiên cứu), người phụ trách, điểm ước lượng, và có thể có nhãn "Bị chặn" kèm lý do, hoặc hạn chót.

Làn Khẩn cấp (4 thẻ): NH-412 "Sửa lỗi chuyển khoản liên ngân hàng bị trừ tiền hai lần" (Lỗi, Trần Minh Đức, 5 điểm, Đang phát triển, hạn 14/11); NH-415 "Cập nhật chứng chỉ SSL sắp hết hạn" (Nợ kỹ thuật, Lê Thị Hồng Nhung, 2, Đang kiểm thử); NH-418 "Khoá tính năng rút tiền không thẻ theo yêu cầu của Ngân hàng Nhà nước" (Tính năng, Phạm Quốc Khánh, 3, Chờ phát hành, hạn 15/11); NH-420 "Ứng dụng treo khi quét mã QR trên Android 15" (Lỗi, Nguyễn Hoàng Yến, 3, Chờ xem xét mã, Bị chặn: chờ thiết bị thử nghiệm).

Làn Thông thường: Tồn đọng 12 thẻ; Sẵn sàng 7 thẻ; Đang phát triển 6 thẻ (vượt giới hạn WIP, phải làm nổi bật cột này); Chờ xem xét mã 3 thẻ; Đang kiểm thử 4 thẻ; Chờ phát hành 5 thẻ; Hoàn thành tuần này 7 thẻ. Hãy tự đặt 44 thẻ thực tế cho một ứng dụng ngân hàng số (ví dụ: "Đăng nhập bằng sinh trắc học", "Mở tài khoản trực tuyến bằng định danh điện tử", "Tiết kiệm tự động theo mục tiêu", "Thanh toán hoá đơn điện nước định kỳ", "Tái cấu trúc mô-đun sổ cái", "Nghiên cứu chuẩn ISO 20022"), chia đủ 4 loại, 6 người phụ trách. Trong đó có 3 thẻ bị chặn có lý do, 5 thẻ có hạn chót, và 2 thẻ có tiêu đề dài hơn 12 từ.

Thêm chú giải cho 4 loại thẻ và một dòng tổng: tổng số thẻ, tổng điểm đang làm dở.

### Must show

* 7 columns with their WIP limits and 2 horizontal lanes.
* 48 cards: 4 in the urgent lane in the stated columns, 44 in the normal lane with the stated count per column.
* The column over its WIP limit (Đang phát triển: 1 urgent + 6 normal against a limit of 5) is highlighted.
* Each card shows code, title, type, owner and points; 4 blocked cards show a reason; due dates are visible.
* Long Vietnamese titles wrap inside the card. A legend for the 4 types and a totals line.

---

## hard-concept — What makes a product observable

### Brief

Draw a concept diagram with the central idea "Observability of a production system".

Around it, 12 parts in four families:
Signals: Logs (structured events with context); Metrics (numbers over time, cheap to keep); Traces (one request across services); Profiles (where CPU and memory go).
Practices: Service level objectives (the promise, in numbers); Alerting on symptoms (page on what users feel); Incident response (roles, timeline, review); Runbooks (what to do at 3 a.m.).
Plumbing: Instrumentation (OpenTelemetry SDKs and auto-instrumentation); Collection pipeline (agents, sampling, routing); Storage and retention (hot, warm, cold tiers).
People: Ownership (every service has a team and a rota).

Each part has two or three sub-points to show as small satellites; for example Traces: "span", "context propagation", "tail sampling"; Service level objectives: "indicator", "error budget", "burn rate"; Collection pipeline: "agent", "sampling", "routing"; write suitable ones for the others.

Links between parts (not through the centre), each with a short label: Logs ↔ Traces "trace id in every log line"; Metrics → Service level objectives "indicators come from metrics"; Service level objectives → Alerting on symptoms "burn rate triggers the page"; Alerting on symptoms → Incident response "opens an incident"; Incident response → Runbooks "follows and improves"; Instrumentation → Logs, Metrics, Traces and Profiles "produces" (four links); Collection pipeline → Storage and retention "writes"; Ownership → Runbooks "maintains"; Traces → Profiles "links a slow span to its profile"; Storage and retention → Metrics "downsamples old data".

Add a one-line analogy under the title: "Like a car dashboard, a black box recorder and a mechanic's manual together." Highlight the path Metrics → Service level objectives → Alerting → Incident response as the main story.

### Must show

* The centre with 12 parts around it, grouped or coloured in 4 families (one family has a single part).
* Two or three satellites per part, about 30 in all, attached to the right part.
* 13 labelled cross links between parts that do not pass through the centre or through other parts.
* Instrumentation fans out to four signals.
* A highlighted 3-hop main story and the analogy line.

---

## hard-screen-flow — Digital bank app: onboarding, transfers, cards and a tablet teller mode

### Brief

Draw a screen flow for a digital bank app. Phone screens unless marked; the Teller group is tablet screens. A name ending in "?" is a decision. Every sentence is one connection.

Entry points: App icon opens Splash. Push "Transfer received" opens Transaction detail. Deep link "Activate card" opens Card activation. QR scan from the camera opens Pay by QR.

Onboarding: Splash, after 1.5 s, goes to Session valid?. [yes] goes to Home. [no] goes to Welcome. Welcome, tap Open account, goes to Phone number. Welcome, tap Sign in, goes to Sign in. Phone number, tap Continue, goes to OTP. OTP, tap Edit number, goes back to Phone number. OTP, code correct, goes to ID capture front. ID capture front, photo taken, goes to ID capture back. ID capture back, photo taken, goes to Selfie liveness. Selfie liveness, check passes, goes to KYC result?. Selfie liveness, check fails three times, goes to Video call booking. [approved] goes to Create PIN. [manual review] goes to Review pending. [rejected] goes to Application rejected. Review pending, push "Approved", goes to Create PIN. Video call booking, tap Confirm, goes to Review pending. Create PIN, PIN saved, goes to Enable biometrics. Enable biometrics, tap Enable or Skip, goes to Home. Sign in, PIN or biometrics accepted, goes to Home. Sign in, tap Forgot PIN, goes to OTP. Sign in, 5 wrong attempts, goes to Account locked.

Home and transfers: Home has tabs Home, Cards, Pay, Savings, Profile. Home, tap an account, goes to Account detail. Account detail, tap a row, goes to Transaction detail. Transaction detail, tap Dispute, goes to Dispute form. Dispute form, tap Submit, goes to Dispute submitted (a bottom sheet over Transaction detail). Home, tap Pay tab, goes to Pay hub. Pay hub, tap Transfer, goes to Choose recipient. Choose recipient, tap New, goes to Add recipient. Add recipient, name check returns, goes to Name matches?. [match] goes to Amount. [no match] goes to Name mismatch warning (a dialog). Name mismatch warning, tap Continue anyway, goes to Amount. Name mismatch warning, tap Edit, goes back to Add recipient. Choose recipient, tap a saved recipient, goes to Amount. Amount, tap Next, goes to Review transfer. Review transfer, tap Confirm, goes to Over limit?. [under limit] goes to Authenticate (PIN sheet). [over limit] goes to Step-up OTP. Step-up OTP, code correct, goes to Authenticate. Authenticate, accepted, goes to Processing. Processing, API answers success, goes to Transfer success. Processing, API answers failure, goes to Transfer failed. Transfer failed, tap Try again, goes back to Review transfer. Transfer success, tap Share receipt, goes to the system share sheet. Transfer success, tap Done, goes to Home. Pay hub, tap Scan, goes to Pay by QR. Pay by QR, code read, goes to Amount.

Cards: Home, tap Cards tab, goes to Card list. Card list, tap a card, goes to Card detail. Card detail, toggle Freeze, goes to Freeze confirm (dialog), and Confirm returns to Card detail. Card detail, tap Show PIN, goes to Authenticate, then to Reveal PIN (closes itself after 10 s back to Card detail). Card detail, tap Limits, goes to Card limits. Card list, tap Order card, goes to Card design picker, then Delivery address, then Order confirmed. Card activation, last 4 digits entered, goes to Create card PIN, then Card detail.

Savings and profile: Home, tap Savings tab, goes to Savings goals. Savings goals, tap New goal, goes to Goal setup, then Auto-save rule, then Savings goals. Home, tap Profile tab, goes to Profile. Profile goes to Personal details, Security settings, Statements, Help centre and Sign out confirm (dialog). Security settings goes to Change PIN and Trusted devices. Help centre goes to Chat with support. Sign out confirm, tap Confirm, goes to Welcome.

Teller (tablet, used by branch staff): Teller sign in goes to Customer lookup. Customer lookup, customer found, goes to Customer 360. Customer 360 goes to Assisted transfer, Card replacement and KYC refresh. Assisted transfer, customer approves on own phone (a push to the phone app), goes to Authenticate on the phone, then Teller receipt on the tablet.

Draw what the person does and what the system does differently. Group the screens by the six areas above.

### Must show

* About 75 items: 4 entry points, 4 decisions, the rest screens, in 6 groups (entry points, onboarding, home and transfers, cards, savings and profile, teller).
* Phone frames for the app and tablet frames for the Teller group; dialogs and bottom sheets (Dispute submitted, Name mismatch warning, Freeze confirm, Sign out confirm, Authenticate) look different from full screens.
* User actions and system events (timers, API answers, pushes) look different.
* Hubs: Home (5 tabs and 5 incoming returns), Authenticate (3 ways in, 3 ways out), Amount (4 ways in).
* The cross-device link from the tablet Assisted transfer to the phone Authenticate and back to the tablet is drawn.
* At least 10 connections return to an earlier screen and are routed outside the frames.
