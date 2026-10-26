# Briefs: Org chart

Three briefs at levels A, B and C. See [README](README.md) for the format and how to run them.

---

## orgchart-A-01 — Academic University College of Engineering Governance Hierarchy

* **type:** org chart
* **level:** A
* **elements:** 11
* **connections:** 10
* **groups:** none

### Brief

The organizational structure outlines administrative leadership for an engineering faculty.
UniversityProvost serves as the institutional executive. DeanOfEngineering reports directly to UniversityProvost.
Three associate deans report to DeanOfEngineering: AssociateDeanAcademicAffairs, AssociateDeanResearch, and AssociateDeanStudentSuccess.
Two academic department heads report to AssociateDeanAcademicAffairs: HeadMechanicalEngineering and HeadElectricalEngineering.
Two research center directors report to AssociateDeanResearch: DirectorNanotechnologyLab and DirectorAdvancedRoboticsCenter.
Two student support officers report to AssociateDeanStudentSuccess: ChiefUndergraduateAdvisor and DirectorCareerPlacement.

### Must show

* Hierarchical tree layout rooted at UniversityProvost.
* DeanOfEngineering supervising three distinct administrative associate deans.
* Symmetrical two-node reporting branches under each associate dean.

### Traps

* Over-widening of sibling nodes across the bottom row if the layout engine cannot balance horizontal tree spans.

### Sources

* Standard American University Academic Senate Governance Frameworks (e.g., UC Berkeley College of Engineering Administrative Organization).

### Uncertain

* none

---

## orgchart-B-01 — Wikimedia Foundation Operational Directorate Hierarchy

* **type:** org chart
* **level:** B
* **elements:** 24
* **connections:** 23
* **groups:** Governance Board, Executive Officers, Departmental Leadership

### Brief

The organizational hierarchy models executive reporting lines at the Wikimedia Foundation.
Inside Governance Board, BoardOfTrustees sits at the root. BoardOfTrustees exercises supervisory oversight over ChiefExecutiveOfficer in Executive Officers.
Reporting directly to ChiefExecutiveOfficer are ChiefTechnologyOfficer, ChiefProductOfficer, ChiefFinancialOfficer, ChiefLegalOfficer, ChiefAdvocacyOfficer, and ChiefPeopleOfficer.
Within Departmental Leadership, ChiefTechnologyOfficer supervises VicePresidentCorePlatform, VicePresidentSecurityEngineering, and VicePresidentSiteReliability. Under VicePresidentSiteReliability report DataCenterOperationsLead and CloudServicesDirector.
ChiefProductOfficer supervises VicePresidentCommunityGrowth and VicePresidentDesignAccessibility.
ChiefFinancialOfficer supervises DirectorFinancialPlanning and DirectorGlobalAccounting.
ChiefLegalOfficer supervises GeneralCounselLitigation and DirectorIntellectualProperty.
ChiefAdvocacyOfficer supervises GlobalPolicyDirector and HumanRightsLead.
ChiefPeopleOfficer supervises TalentAcquisitionDirector and CultureDiversityDirector.

### Must show

* Three administrative tiers: Governance Board, Executive Officers, and Departmental Leadership.
* ChiefExecutiveOfficer managing six functional C-level executives.
* Asymmetric tree depth beneath ChiefTechnologyOfficer extending through site reliability to operational leads.

### Traps

* Wide single-parent fan-out from ChiefExecutiveOfficer (6 immediate direct reports) coupled with deep sub-branching under ChiefTechnologyOfficer produces asymmetric tree imbalances.

### Sources

* https://wikimediafoundation.org/about/org-chart/ — Wikimedia Foundation executive leadership structure, operational departments, and Board reporting channels.

### Uncertain

* none

---

## orgchart-C-01 — CERN European Organization for Nuclear Research Governance Structure

* **type:** org chart
* **level:** C
* **elements:** 44
* **connections:** 43
* **groups:** Council Governance, Executive Directorate, Operational Departments

### Brief

The organizational structure outlines CERN's governing and research hierarchy.
CernCouncil sits at the governance root. CernCouncil oversees three advisory councils: ScientificPolicyCommittee, FinanceCommittee, and TripartiteEmploymentForum.
CernCouncil appoints and supervises DirectorGeneral. DirectorGeneral oversees legal and administrative units: LegalServicesOffice, InternalAuditService, and OmbudsOffice.
DirectorGeneral directs four executive directors: DirectorResearchComputing, DirectorAcceleratorsTechnology, DirectorFinanceHumanResources, and DirectorInternationalRelations.
Under DirectorResearchComputing report ExperimentalPhysicsDepartment, TheoreticalPhysicsDepartment, and InformationTechnologyDepartment. ExperimentalPhysicsDepartment coordinates large LHC experiments: AtlasSpokesperson, CmsSpokesperson, AliceSpokesperson, and LhcbSpokesperson. InformationTechnologyDepartment directs HighPerformanceComputingGroup, GridInfrastructureGroup, and DataStorageGroup.
Under DirectorAcceleratorsTechnology report BeamsDepartment, TechnologyDepartment, and EngineeringDepartment. BeamsDepartment oversees BeamInstrumentationGroup and RadioFrequencyGroup. TechnologyDepartment oversees SuperconductingMagnetsGroup and CryogenicsSystemsGroup. EngineeringDepartment oversees MechanicalEngineeringGroup and CoolingVentilationGroup.
Under DirectorFinanceHumanResources report FinanceDepartment, HumanResourcesDepartment, and SiteManagementDepartment. FinanceDepartment oversees ProcurementGroup and AccountingGroup. HumanResourcesDepartment oversees TalentAcquisitionGroup and PersonnelAdministrationGroup. SiteManagementDepartment oversees InfrastructureMaintenanceGroup and LogisticsServicesGroup.
Under DirectorInternationalRelations report MemberStatesRelationsOffice, NonMemberStatesRelationsOffice, ProtocolOffice, and ScienceCommunicationEducationGroup.

### Must show

* Three governance tiers: Council Governance, Executive Directorate, and Operational Departments.
* CernCouncil supervising three advisory committees alongside DirectorGeneral.
* ExperimentalPhysicsDepartment supervising four distinct LHC experimental collaborations (ATLAS, CMS, ALICE, LHCb).
* Four directorates spanning research, accelerators, finance, and international relations.

### Traps

* Extreme vertical depth combined with broad horizontal branch density (e.g., across Experimental Physics and Accelerator Technology) causes layout overlap if subtree bounding boxes are not calculated dynamically.

### Structure

**Elements**

- Council Governance: CernCouncil, ScientificPolicyCommittee, FinanceCommittee, TripartiteEmploymentForum, DirectorGeneral
- Executive Directorate: LegalServicesOffice, InternalAuditService, OmbudsOffice, DirectorResearchComputing, DirectorAcceleratorsTechnology, DirectorFinanceHumanResources, DirectorInternationalRelations, MemberStatesRelationsOffice, NonMemberStatesRelationsOffice, ProtocolOffice, ScienceCommunicationEducationGroup
- Operational Departments: ExperimentalPhysicsDepartment, TheoreticalPhysicsDepartment, InformationTechnologyDepartment, AtlasSpokesperson, CmsSpokesperson, AliceSpokesperson, LhcbSpokesperson, HighPerformanceComputingGroup, GridInfrastructureGroup, DataStorageGroup, BeamsDepartment, TechnologyDepartment, EngineeringDepartment, BeamInstrumentationGroup, RadioFrequencyGroup, SuperconductingMagnetsGroup, CryogenicsSystemsGroup, MechanicalEngineeringGroup, CoolingVentilationGroup, FinanceDepartment, HumanResourcesDepartment, SiteManagementDepartment, ProcurementGroup, AccountingGroup, TalentAcquisitionGroup, PersonnelAdministrationGroup, InfrastructureMaintenanceGroup, LogisticsServicesGroup

**Connections**

- CernCouncil -> ScientificPolicyCommittee
- CernCouncil -> FinanceCommittee
- CernCouncil -> TripartiteEmploymentForum
- CernCouncil -> DirectorGeneral
- DirectorGeneral -> LegalServicesOffice
- DirectorGeneral -> InternalAuditService
- DirectorGeneral -> OmbudsOffice
- DirectorGeneral -> DirectorResearchComputing
- DirectorGeneral -> DirectorAcceleratorsTechnology
- DirectorGeneral -> DirectorFinanceHumanResources
- DirectorGeneral -> DirectorInternationalRelations
- DirectorResearchComputing -> ExperimentalPhysicsDepartment
- DirectorResearchComputing -> TheoreticalPhysicsDepartment
- DirectorResearchComputing -> InformationTechnologyDepartment
- ExperimentalPhysicsDepartment -> AtlasSpokesperson
- ExperimentalPhysicsDepartment -> CmsSpokesperson
- ExperimentalPhysicsDepartment -> AliceSpokesperson
- ExperimentalPhysicsDepartment -> LhcbSpokesperson
- InformationTechnologyDepartment -> HighPerformanceComputingGroup
- InformationTechnologyDepartment -> GridInfrastructureGroup
- InformationTechnologyDepartment -> DataStorageGroup
- DirectorAcceleratorsTechnology -> BeamsDepartment
- DirectorAcceleratorsTechnology -> TechnologyDepartment
- DirectorAcceleratorsTechnology -> EngineeringDepartment
- BeamsDepartment -> BeamInstrumentationGroup
- BeamsDepartment -> RadioFrequencyGroup
- TechnologyDepartment -> SuperconductingMagnetsGroup
- TechnologyDepartment -> CryogenicsSystemsGroup
- EngineeringDepartment -> MechanicalEngineeringGroup
- EngineeringDepartment -> CoolingVentilationGroup
- DirectorFinanceHumanResources -> FinanceDepartment
- DirectorFinanceHumanResources -> HumanResourcesDepartment
- DirectorFinanceHumanResources -> SiteManagementDepartment
- FinanceDepartment -> ProcurementGroup
- FinanceDepartment -> AccountingGroup
- HumanResourcesDepartment -> TalentAcquisitionGroup
- HumanResourcesDepartment -> PersonnelAdministrationGroup
- SiteManagementDepartment -> InfrastructureMaintenanceGroup
- SiteManagementDepartment -> LogisticsServicesGroup
- DirectorInternationalRelations -> MemberStatesRelationsOffice
- DirectorInternationalRelations -> NonMemberStatesRelationsOffice
- DirectorInternationalRelations -> ProtocolOffice
- DirectorInternationalRelations -> ScienceCommunicationEducationGroup

### Sources

* https://home.cern/about/who-we-are/our-governance — CERN Council, scientific committees, and directorate governance model.
* CERN Annual Report: Governance and Directorate Organizational Charts (CERN-HR-ORGANIGRAM).

### Uncertain

* none
