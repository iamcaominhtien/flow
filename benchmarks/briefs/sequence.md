# Briefs: Sequence

Three briefs at levels A, B and C. See [README](README.md) for the format and how to run them.

---

## sequence-A-01 — TCP Three-Way Handshake and Teardown

* **type:** sequence
* **level:** A
* **elements:** 10
* **connections:** 9
* **groups:** none

### Brief

The communication sequence models transport layer coordination across ten architectural endpoints. ClientSocket transmits SynMessage to IngressFilter. IngressFilter evaluates security posture and forwards VerifiedSyn to NetworkStack. NetworkStack routes DispatchSyn to ServerDaemon. ServerDaemon issues GenerateSynAck to ResponseQueue. ResponseQueue sends SynAckMessage to ClientSocket.
ClientSocket initiates data transmission by sending AckDataPacket to ServerDaemon, confirming bidirectional synchronization.
Session termination initiates when ClientSocket transmits FinMessage to IngressFilter. IngressFilter passes ProcessFin to ServerDaemon. ServerDaemon returns FinalAckPacket to ClientSocket, completing connection teardown and resetting socket states on both hosts.

### Must show

* The canonical three-step SYN, SYN-ACK, and ACK message sequence pattern.
* The distinct teardown phase separating connection closing from initial handshaking.
* Ten distinct participants handling connection state transitions.

### Traps

* Sequential ping-pong messaging between ten lifelines can cause label collisions if vertical spacing between ACK and subsequent FIN packets is compressed.

### Sources

* https://datatracker.ietf.org/doc/html/rfc9293 — Transmission Control Protocol specification covering state synchronization and connection close mechanisms.

### Uncertain

* none

---

## sequence-B-01 — OAuth 2.0 PKCE Authorization Code Grant (RFC 7636)

* **type:** sequence
* **level:** B
* **elements:** 22
* **connections:** 25
* **groups:** Client Application Tier, Authorization Server Domain, Resource Server Boundary

### Brief

The authentication protocol executes across twenty-two participants distributed over Client Application Tier, Authorization Server Domain, and Resource Server Boundary.
UserAgent triggers UserAuthAction on SinglePageApp. SinglePageApp activates CryptoEngine via GeneratePkceChallenge. CryptoEngine returns ChallengeToken to SinglePageApp. SinglePageApp sends AuthRedirect to BrowserStorage. BrowserStorage transmits GetAuthorize to IngressGateway. IngressGateway routes AuthRequest to AuthController. AuthController calls IdentityDirectory via QueryCredentials. IdentityDirectory returns UserProfile. AuthController renders ConsentForm to UserAgent. UserAgent sends SubmitApproval to AuthController.
AuthController updates SessionStore via WriteSession. AuthController sends IssueAuthCode to UserAgent. UserAgent transmits CodeCallback to SinglePageApp. SinglePageApp sends ExchangeToken to TokenEndpoint. TokenEndpoint invokes VerifierValidator via VerifyPkceCode. If verification fails, VerifierValidator loops back to UserAgent via PromptRetryAuth.
When code verification succeeds, VerifierValidator issues TokenSignRequest to CryptoEngine. CryptoEngine returns SignedJwt to TokenEndpoint. TokenEndpoint delivers AccessToken to SinglePageApp. SinglePageApp issues ApiRequestWithBearer to ResourceGateway. ResourceGateway dispatches IntrospectToken to ScopeValidator. ScopeValidator checks permissions against PolicyEngine via CheckPolicies. PolicyEngine returns ScopeGranted. ResourceGateway routes FetchData to BusinessDataService. Finally, BusinessDataService returns ResourcePayload to SinglePageApp.

### Must show

* Structural separation across Client Application Tier, Authorization Server Domain, and Resource Server Boundary.
* Cryptographic verification sequence validating code verifier against unhashed challenge.
* Error mitigation back-edge looping from VerifierValidator back to UserAgent upon challenge verification failure.

### Traps

* Alternating browser redirect channels and back-channel direct API token exchanges between adjacent lifelines create intersecting visual activations.

### Sources

* https://datatracker.ietf.org/doc/html/rfc7636 — Proof Key for Code Exchange by OAuth Public Clients.
* https://datatracker.ietf.org/doc/html/rfc6749 — The OAuth 2.0 Authorization Framework.

### Uncertain

* none

---

## sequence-C-01 — 3GPP 5G Standalone Initial Access and PDU Session Setup

* **type:** sequence
* **level:** C
* **elements:** 44
* **connections:** 52
* **groups:** Radio Access Network, Core Control Plane, Core User Plane

### Brief

Initial access coordinates forty-four participants across Radio Access Network, Core Control Plane, and Core User Plane.
UserEquipment sends RachPreamble to PhyTransceiver, which notifies MacScheduler. MacScheduler issues RarGrant to UserEquipment. UserEquipment sends RrcSetupRequest to RrcController, which returns RrcSetup. UserEquipment sends RrcSetupComplete with embedded NasRegistrationRequest to GNodeB. If transmission errors occur, GNodeB triggers HarqRetryLoop back to UserEquipment.
GNodeB sends InitialUeMessage to AmfRouter. AmfRouter sends NausfAuthInitiate to AusfServer, which routes NudmAuthGenerate to UdmServer. UdmServer returns VectorData to AusfServer, which sends AuthChallenge to AmfRouter. AmfRouter forwards NasAuthRequest to UserEquipment. UserEquipment returns NasAuthResponse to AmfRouter. If authentication fails, AmfRouter triggers EapRetryLoop back to UserEquipment. If valid, AmfRouter sends AuthConfirm to AusfServer, which returns AuthSuccess.
AmfRouter queries SeirRegistry via CheckImei, receiving DeviceStatus. For immediate emergency routing, AmfRouter sends EmergencyBypass directly to UpfGateway, skipping policy bindings. In standard flow, AmfRouter updates UdmServer via NudmRegister, receiving SubscriptionProfile. AmfRouter issues PolicyControlCreate to PcfServer, receiving PolicyDecision.
AmfRouter fans out three messages simultaneously: PduSessionCreate to SmfController, RegistrationAccept to GNodeB, and AnalyticsLog to NrfDiscovery. SmfController queries UdmServer via NudmSmfData, receiving SmData. SmfController applies policy via NpcfSmfPolicy to PcfServer, receiving SmPolicy. SmfController establishes user plane sessions via N4SessionRequest to UpfGateway, which returns N4SessionResponse. SmfController returns NamfNsmfResponse to AmfRouter.
AmfRouter sends InitialContextSetup to GNodeB, which sends RrcReconfiguration to UserEquipment. UserEquipment returns RrcReconfigurationComplete to GNodeB. GNodeB sends InitialContextSetupResponse to AmfRouter, and establishes GtpuTunnel to UpfGateway. UserEquipment streams DataPacket through UpfGateway to ExternalDataNetwork. Finally, ExternalDataNetwork returns DataAck via UpfGateway to UserEquipment.

### Must show

* Clean domain grouping across Radio Access Network, Core Control Plane, and Core User Plane.
* AmfRouter concurrently dispatching PduSessionCreate, RegistrationAccept, and AnalyticsLog.
* EmergencyBypass skipping intermediate registration stages to connect AmfRouter straight to UpfGateway.
* Two recovery loops: HarqRetryLoop between GNodeB and UserEquipment, and EapRetryLoop between AmfRouter and UserEquipment.

### Traps

* Coordinating forty-four distinct participants across radio and core domains causes severe horizontal crowding and lifeline elongation.

### Sources

* https://www.etsi.org/deliver/etsi_ts/123500_123599/123502/15.02.00_60/ts_123502v150200p.pdf — 3GPP TS 23.502 Procedural flows for 5G System registration and PDU session setup.
* https://www.3gpp.org/technologies/5g-system-overview — 5G Service-Based Architecture interface definitions (N1, N2, N4, SBI).

### Uncertain

* none
