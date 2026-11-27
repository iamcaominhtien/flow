# How does an insurance claim move from the first report to payout or rejection?

Reader: a claims operations lead
Medium: screen

Actors: claimant, intake agent, adjuster, fraud team, payments. Each node names the actor who does it, so a hand-off is any connection between nodes of different actors. Kinds: start, end, fail, step, decision, item (a member of a set). A set is a titled list of members that all apply together; each set says whether it is ordered. `S1 -> x` means the flow leaves the whole set. `x -> S1` means the flow enters the whole set. A parallel block means the branches named in its heading run at the same time and all must finish before the next node.

Node format: `id | text | kind | actor`

## Stage A: The claimant reports the loss

Nodes
- a01 | Loss occurs | start | claimant
- a02 | Find policy number | step | claimant
- a03 | Emergency present? | decision | claimant
- a04 | Call emergency services | step | claimant
- a05 | Choose report channel? | decision | claimant
- a06 | Phone intake call | step | intake agent
- a07 | Submit web form | step | claimant
- a08 | Submit app report | step | claimant
- a09 | Create claim record | step | intake agent
- a10 | Assign claim number | step | intake agent
- a11 | Send acknowledgement | step | intake agent
- a12 | Receive acknowledgement | step | claimant

Connections
- a01 -> a02
- a02 -> a03
- a03 -> a04 : yes
- a03 -> a05 : no
- a04 -> a05
- a05 -> a06 : phone
- a05 -> a07 : web
- a05 -> a08 : app
- a06 -> a09
- a07 -> a09
- a08 -> a09
- a09 -> a10
- a10 -> a11
- a11 -> a12
- a12 -> b01

## Stage B: Identity, policy and coverage checks

Retry loop 1: a failed identity check sends the claimant back to resubmit, up to the attempt limit.

Nodes
- b01 | Verify identity | step | intake agent
- b02 | Identity verified? | decision | intake agent
- b03 | Attempts left? | decision | intake agent
- b04 | Resubmit ID | step | claimant
- b05 | Closed unverified | fail | intake agent
- b06 | Look up policy | step | intake agent
- b07 | Policy active? | decision | intake agent
- b08 | Check grace period | step | intake agent
- b09 | Within grace period? | decision | intake agent
- b10 | Loss type covered? | decision | intake agent
- b11 | Check exclusions | step | intake agent
- b12 | Exclusion applies? | decision | intake agent
- b13 | Draft denial letter | step | intake agent
- b14 | Send denial letter | step | intake agent
- b15 | Claim denied | fail | intake agent
- b16 | Record coverage confirmed | step | intake agent
- b17 | Duplicate claim exists? | decision | intake agent
- b18 | Link to existing claim | step | intake agent

Connections
- b01 -> b02
- b02 -> b06 : yes
- b02 -> b03 : no
- b03 -> b04 : yes
- b03 -> b05 : no
- b04 -> b01 : retry
- b06 -> b07
- b07 -> b10 : yes
- b07 -> b08 : no
- b08 -> b09
- b09 -> b10 : yes
- b09 -> b13 : no
- b10 -> b11 : yes
- b10 -> b13 : no
- b11 -> b12
- b12 -> b13 : yes
- b12 -> b16 : no
- b13 -> b14
- b14 -> b15
- b16 -> b17
- b17 -> b18 : yes
- b17 -> c01 : no
- b18 -> c01

## Stage C: Documents, triage and hand-off to the adjuster

Retry loop 2: missing documents trigger a reminder and a new upload, up to the reminder limit.

Nodes
- c01 | Collect documents | step | intake agent
- c03 | Upload documents | step | claimant
- c04 | All documents received? | decision | intake agent
- c05 | Send reminder | step | intake agent
- c06 | Reminders left? | decision | intake agent
- c07 | Closed as withdrawn | end | intake agent
- c08 | Triage claim severity | step | intake agent
- c09 | Severity level? | decision | intake agent
- c10 | Fast-track minor claim | step | intake agent
- c11 | Standard handling | step | intake agent
- c12 | Open total loss file | step | intake agent
- c13 | Hand claim to adjuster | step | intake agent

Set S1: Intake documents (unordered, all are required together)
- c20 | Claim form | item | claimant
- c21 | Photo ID | item | claimant
- c22 | Policy schedule | item | claimant
- c23 | Proof of ownership | item | claimant
- c24 | Loss photos | item | claimant
- c25 | Repair estimate | item | claimant
- c26 | Police report | item | claimant
- c27 | Witness statements | item | claimant
- c28 | Medical report | item | claimant
- c29 | Bank details | item | claimant
- c30 | Signed declaration | item | claimant
- c31 | Prior claims history | item | claimant

Connections
- c01 -> S1
- S1 -> c03
- c03 -> c04
- c04 -> c08 : yes
- c04 -> c06 : no
- c06 -> c05 : yes
- c06 -> c07 : no
- c05 -> c03 : retry
- c08 -> c09
- c09 -> c10 : minor
- c09 -> c11 : moderate
- c09 -> c12 : total loss
- c10 -> c13
- c11 -> c13
- c12 -> c13
- c13 -> d01

## Stage D: Investigation (parallel block 1)

Parallel block 1 has three branches that run at once: damage inspection (adjuster), recorded statement (adjuster, claimant, intake agent), and fraud screening (adjuster, fraud team). They all finish at d12.

Nodes
- d01 | Accept claim file | step | adjuster
- d13 | Set initial reserve | step | adjuster
- d14 | Reserve above limit? | decision | adjuster
- d15 | Request reserve approval | step | adjuster
- d02 | Start parallel work | step | adjuster
- d03 | Schedule inspection | step | adjuster
- d04 | Inspect damage | step | adjuster
- d05 | Write damage report | step | adjuster
- d06 | Request statement | step | adjuster
- d07 | Give statement | step | claimant
- d08 | Transcribe statement | step | intake agent
- d09 | Send screening request | step | adjuster
- d10 | Run screening checks | step | fraud team
- d11 | Score fraud risk | step | fraud team
- d12 | Wait for all branches | step | adjuster

Set S2: Fraud screening checks (unordered, all run together on every claim)
- d30 | Duplicate claim check | item | fraud team
- d31 | Claim timing | item | fraud team
- d32 | Policy age | item | fraud team
- d33 | Prior claim count | item | fraud team
- d34 | Address mismatch | item | fraud team
- d35 | Phone watchlist | item | fraud team
- d36 | Bank account link | item | fraud team
- d37 | Photo metadata | item | fraud team
- d38 | Repair shop blacklist | item | fraud team
- d39 | Social media check | item | fraud team
- d40 | Loss location check | item | fraud team
- d41 | Value versus market | item | fraud team
- d42 | Witness overlap | item | fraud team
- d43 | Medical provider flag | item | fraud team

Connections
- d01 -> d13
- d13 -> d14
- d14 -> d15 : yes
- d14 -> d02 : no
- d15 -> d02
- d02 -> d03 : branch 1
- d02 -> d06 : branch 2
- d02 -> d09 : branch 3
- d03 -> d04
- d04 -> d05
- d05 -> d12
- d06 -> d07
- d07 -> d08
- d08 -> d12
- d09 -> d10
- d10 -> S2
- S2 -> d11
- d11 -> d12
- d12 -> e01

## Stage E: Fraud decision

Nodes
- e01 | Fraud risk level? | decision | adjuster
- e02 | Continue normal handling | step | adjuster
- e03 | Request extra evidence | step | fraud team
- e04 | Evidence satisfactory? | decision | fraud team
- e05 | Open fraud case | step | fraud team
- e06 | Interview claimant | step | fraud team
- e07 | Review financial records | step | fraud team
- e08 | Fraud confirmed? | decision | fraud team
- e09 | Refer to authorities | step | fraud team
- e12 | Flag claimant record | step | fraud team
- e10 | Claim rejected for fraud | fail | fraud team
- e11 | Notify adjuster of clearance | step | fraud team

Connections
- e01 -> e02 : low
- e01 -> e03 : medium
- e01 -> e05 : high
- e03 -> e04
- e04 -> e11 : yes
- e04 -> e05 : no
- e05 -> e06
- e06 -> e07
- e07 -> e08
- e08 -> e09 : yes
- e08 -> e11 : no
- e09 -> e12
- e12 -> e10
- e11 -> e02
- e02 -> f01

## Stage F: Valuation and settlement offer

Nodes
- f01 | Confirm covered amount | step | adjuster
- f18 | Check prior payments | step | adjuster
- f19 | Prior payments found? | decision | adjuster
- f20 | Net prior payments | step | adjuster
- f02 | Compare repair estimates | step | adjuster
- f03 | Estimates agree? | decision | adjuster
- f04 | Negotiate with repairer | step | adjuster
- f05 | Calculate settlement | step | adjuster
- f06 | Apply deductible | step | adjuster
- f07 | Apply policy limit | step | adjuster
- f08 | Amount over authority? | decision | adjuster
- f09 | Request manager approval | step | adjuster
- f10 | Manager approves? | decision | adjuster
- f11 | Revise settlement | step | adjuster
- f12 | Make settlement offer | step | adjuster
- f13 | Offer accepted? | decision | claimant
- f14 | Negotiate revised offer | step | adjuster
- f15 | Revised offer accepted? | decision | claimant
- f16 | Sent to appraisal | end | adjuster
- f17 | Record accepted offer | step | adjuster

Connections
- f01 -> f18
- f18 -> f19
- f19 -> f20 : yes
- f19 -> f02 : no
- f20 -> f02
- f02 -> f03
- f03 -> f05 : yes
- f03 -> f04 : no
- f04 -> f05
- f05 -> f06
- f06 -> f07
- f07 -> f08
- f08 -> f09 : yes
- f08 -> f12 : no
- f09 -> f10
- f10 -> f12 : yes
- f10 -> f11 : no
- f11 -> f12
- f12 -> f13
- f13 -> f17 : yes
- f13 -> f14 : no
- f14 -> f15
- f15 -> f17 : yes
- f15 -> f16 : no
- f17 -> g01

## Stage G: Payment preparation (parallel block 2)

Parallel block 2 has three branches that run at once: funds (payments), compliance (payments), and release and bank details (payments, claimant). They all finish at g12.

Nodes
- g01 | Hand claim to payments | step | adjuster
- g02 | Prepare payment package | step | payments
- g03 | Start parallel preparation | step | payments
- g04 | Reserve funds | step | payments
- g05 | Update ledger | step | payments
- g06 | Run compliance checks | step | payments
- g07 | Compliance cleared? | decision | payments
- g08 | Resolve compliance flag | step | payments
- g09 | Send payout notice | step | payments
- g10 | Return signed release | step | claimant
- g11 | Log signed release | step | payments
- g13 | Confirm bank account | step | payments
- g14 | Account valid? | decision | payments
- g15 | Request new bank details | step | claimant
- g16 | Confirm new account | step | payments
- g12 | Wait for all branches | step | payments

Set S3: Payment compliance checks (unordered, all apply together)
- g30 | Sanctions screening | item | payments
- g31 | Payee name match | item | payments
- g32 | Bank account format | item | payments
- g33 | Tax withholding check | item | payments
- g34 | Deductible applied | item | payments
- g35 | Coverage limit check | item | payments
- g36 | Prior payments netted | item | payments
- g37 | Subrogation hold check | item | payments
- g38 | Authority limit check | item | payments
- g39 | Duplicate payment check | item | payments

Connections
- g01 -> g02
- g02 -> g03
- g03 -> g04 : branch 1
- g03 -> g06 : branch 2
- g03 -> g09 : branch 3
- g04 -> g05
- g05 -> g12
- g06 -> S3
- S3 -> g07
- g07 -> g12 : yes
- g07 -> g08 : no
- g08 -> g12
- g09 -> g10
- g10 -> g11
- g11 -> g13
- g13 -> g14
- g14 -> g12 : yes
- g14 -> g15 : no
- g15 -> g16
- g16 -> g12
- g12 -> h01

## Stage H: Payout settlement (one long sequence, ordered, no branches)

Sequence Q1: h01 to h15 are done strictly in this order, then the claimant receives the money.

Nodes
- h01 | Create payment instruction | step | payments
- h02 | Assign payment reference | step | payments
- h03 | Post ledger debit | step | payments
- h04 | Generate remittance advice | step | payments
- h05 | Obtain first approval | step | payments
- h06 | Obtain second approval | step | payments
- h07 | Compile bank file | step | payments
- h08 | Transmit bank file | step | payments
- h09 | Receive bank acknowledgement | step | payments
- h10 | Mark payment sent | step | payments
- h11 | Post claim payment entry | step | payments
- h12 | Release reserve balance | step | payments
- h13 | Notify adjuster of payment | step | payments
- h14 | Send payment confirmation | step | payments
- h15 | Archive payment record | step | payments
- h16 | Receive payout | step | claimant

Connections
- h01 -> h02
- h02 -> h03
- h03 -> h04
- h04 -> h05
- h05 -> h06
- h06 -> h07
- h07 -> h08
- h08 -> h09
- h09 -> h10
- h10 -> h11
- h11 -> h12
- h12 -> h13
- h13 -> h14
- h14 -> h15
- h15 -> h16
- h16 -> i01

## Stage I: Recovery, survey and closure

Nodes
- i01 | Subrogation possible? | decision | adjuster
- i02 | Identify liable party | step | adjuster
- i03 | Send demand letter | step | adjuster
- i04 | Recovery received? | decision | payments
- i05 | Credit recovery | step | payments
- i06 | Write off recovery | step | adjuster
- i07 | Send satisfaction survey | step | intake agent
- i08 | Complaint raised? | decision | claimant
- i09 | Review complaint | step | adjuster
- i10 | Complaint upheld? | decision | adjuster
- i11 | Issue goodwill payment | step | payments
- i12 | Close claim file | end | adjuster

Connections
- i01 -> i02 : yes
- i01 -> i07 : no
- i02 -> i03
- i03 -> i04
- i04 -> i05 : yes
- i04 -> i06 : no
- i05 -> i07
- i06 -> i07
- i07 -> i08
- i08 -> i09 : yes
- i08 -> i12 : no
- i09 -> i10
- i10 -> i11 : yes
- i10 -> i12 : no
- i11 -> i12

Node count: 169 (133 stage nodes and 36 set members; set titles S1 to S3 are not counted)
