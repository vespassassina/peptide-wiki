import Foundation

/// Where a library entry came from. The distinction matters: built-in entries are authored
/// and can be revised by an app update, user entries are owned by the user and must never be
/// overwritten, and agent entries are proposals that carry extra scrutiny.
public enum EntryProvenance: String, Hashable, Sendable, Codable, CaseIterable {
    /// Shipped with the app. Read-only; an update may revise it.
    case builtIn = "built-in"
    /// Authored by the user. Never touched by an update.
    case user
    /// Added by the agent, with the user's confirmation. Editable, but always attributable.
    case agent

    public var isEditable: Bool { self != .builtIn }

    public var label: String {
        switch self {
        case .builtIn: "Built in"
        case .user: "Added by you"
        case .agent: "Added by the assistant"
        }
    }
}

/// A curated reference entry. Eight of these ship with the app (ported from the reference
/// implementation's `database.ts:5-14`), and the user can add their own — directly or by
/// asking the agent to research and draft one.
///
/// Every entry carries an `uncertainty` disclaimer and links out to a source rather than
/// restating claims. That stance is deliberate and applies to user and agent entries too:
/// the app records and organises, it does not advise.
public struct LibraryCatalogEntry: Hashable, Sendable, Codable, Identifiable {
    public let id: String
    public let kind: ItemKind
    public var title: String
    public var summary: String
    public var evidenceTier: EvidenceTier

    /// What the linked sources actually say, in plain sentences, written from those sources
    /// and checked against them. Never carries a dose, an amount or a schedule (D-360).
    ///
    /// Separate from `summary`, which is one line describing what the thing is. `nil` on a
    /// user or agent entry: nobody has checked those against sources.
    public var evidenceSummary: String?

    /// What the studies behind this entry actually did, one line per study (D-362).
    ///
    /// This is reporting, not advice: each protocol names its own source and the population it
    /// was run in, and nothing here is ever averaged into a single number or written into the
    /// user's dose field. It exists so a reader who does not know what to ask their doctor can
    /// see what was tried and go and read it.
    public var researchProtocols: [ResearchProtocol]

    /// The trade-off in a few lines: what the evidence supports, what it warns about, and one
    /// sentence a reader could repeat to their doctor (B-62).
    ///
    /// Nothing new enters the app here. Every line is drawn from this entry's own summary,
    /// protocols and sources, so the section is a shorter reading of checked text rather than a
    /// second opinion. `nil` on a user or agent entry, which nobody has checked.
    public var verdict: Verdict?

    /// What people report doing outside any study, up to three per entry, shown as a reference
    /// only — never prefilled into a schedule or a log (B-72).
    ///
    /// This is explicitly not `researchProtocols`: nobody has checked these, the population is
    /// whoever posted, and a number here is not evidence of anything working. Each one carries
    /// its own source so a reader can judge the source themselves, and the app never averages
    /// or ranks them.
    public var communityProtocols: [CommunityProtocol]

    public var uncertainty: String
    public var officialLinks: [OfficialLink]
    public var provenance: EntryProvenance

    /// Prefill template. Selecting this entry when creating an item copies these values into
    /// the new item's profile, so the user confirms rather than types.
    ///
    /// This is the point of the library: a reference entry is a starting form, not an
    /// encyclopedia page. Values are typical defaults the user is expected to correct —
    /// their vial is not necessarily the concentration on the label.
    public var template: ItemTemplate?

    /// One study's own protocol, as that study reported it.
    ///
    /// The fields are deliberately separate rather than one sentence: the population is what
    /// keeps a number honest ("rats", "24 trained men", "adults with a deficiency"), and a
    /// regimen shown without it reads as a recommendation. Every protocol carries its source,
    /// which is what makes it a report of someone else's work rather than the app's own advice.
    public struct ResearchProtocol: Hashable, Sendable, Codable, Identifiable {
        /// Who or what was studied.
        public let population: String
        /// What was given or done, in the source's own terms.
        public let regimen: String
        /// How long it ran.
        public let duration: String
        /// What the study reported, in one line.
        public let outcome: String
        /// Where this came from. Always present: a protocol without a source is a rumour.
        public let source: OfficialLink

        public var id: String { "\(source.url.absoluteString)|\(regimen)" }

        public init(
            population: String,
            regimen: String,
            duration: String,
            outcome: String,
            source: OfficialLink
        ) {
            self.population = population
            self.regimen = regimen
            self.duration = duration
            self.outcome = outcome
            self.source = source
        }
    }

    /// A source-attributed practice description, separate from intervention-study protocols.
    ///
    /// A checked citation establishes only that a source describes a practice, not its safety
    /// or effectiveness. `description` is plain text, never a recommendation; `source` opens the
    /// account for the reader. Nothing here is copied into a schedule or log.
    public struct CommunityProtocol: Hashable, Sendable, Codable, Identifiable {
        public let description: String
        public let source: OfficialLink

        public var id: String { "\(source.url.absoluteString)|\(description)" }

        public init(description: String, source: OfficialLink) {
            self.description = description
            self.source = source
        }
    }

    public struct OfficialLink: Hashable, Sendable, Codable {
        public let title: String
        public let url: URL

        public init(title: String, url: URL) {
            self.title = title
            self.url = url
        }
    }

    /// A short, grounded reading of the evidence: approval status, benefits, risks, and the
    /// bottom line.
    ///
    /// Approval status is stated once, in its own field, rather than folded into benefits, risks
    /// and the bottom line at once — a regulator's yes-or-no is a single fact, not three. Benefits
    /// and risks are separate lists rather than one balanced paragraph, because the balance is not
    /// equal for every entry: a regulator-approved medicine and a peptide with three rat studies
    /// should not read the same way. Risks are never empty — where the weakness is that nobody has
    /// studied the thing in humans, that is what the list says. Carries no dose, amount or
    /// duration (D-360), and never addresses the reader (D-362).
    public struct Verdict: Hashable, Sendable, Codable {
        /// Whether a regulator has approved it, said in one short line. Not indication detail —
        /// that belongs in `benefits`, since it is a claim about what the thing does, not about
        /// whether an agency signed off on it. `nil` when the entry is not something a regulator
        /// would ever rule on (a practice, a food target, a lifestyle entry).
        public let approvalStatus: String?
        /// What the evidence supports, strength stated in the same line.
        public let benefits: [String]
        /// Harms, unknowns, thin evidence, failed replications.
        public let risks: [String]
        /// One sentence summing the entry up.
        public let bottomLine: String

        public init(benefits: [String], risks: [String], bottomLine: String, approvalStatus: String? = nil) {
            self.approvalStatus = approvalStatus
            self.benefits = benefits
            self.risks = risks
            self.bottomLine = bottomLine
        }
    }

    public init(
        id: String,
        kind: ItemKind,
        title: String,
        summary: String,
        evidenceTier: EvidenceTier,
        evidenceSummary: String? = nil,
        researchProtocols: [ResearchProtocol] = [],
        verdict: Verdict? = nil,
        communityProtocols: [CommunityProtocol] = [],
        uncertainty: String = LibraryCatalog.standardDisclaimer,
        officialLinks: [OfficialLink],
        provenance: EntryProvenance = .builtIn,
        template: ItemTemplate? = nil
    ) {
        self.id = id
        self.kind = kind
        self.title = title
        self.summary = summary
        self.evidenceTier = evidenceTier
        self.evidenceSummary = evidenceSummary
        self.researchProtocols = researchProtocols
        self.verdict = verdict
        self.communityProtocols = communityProtocols
        self.uncertainty = uncertainty
        self.officialLinks = officialLinks
        self.provenance = provenance
        self.template = template
    }

    /// Identifier for a user- or agent-authored entry. The `custom:` prefix keeps these in a
    /// separate namespace from `catalog:`, so a future built-in can never collide with one
    /// the user already made.
    public static func customIdentifier(_ uuid: UUID = UUID()) -> String {
        "custom:\(uuid.uuidString.lowercased())"
    }

    /// Decoding tolerates entries written before provenance existed by assuming built-in,
    /// which is the conservative reading: treat unknown-origin entries as not-user-owned.
    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        kind = try container.decode(ItemKind.self, forKey: .kind)
        title = try container.decode(String.self, forKey: .title)
        summary = try container.decode(String.self, forKey: .summary)
        evidenceTier = try container.decode(EvidenceTier.self, forKey: .evidenceTier)
        evidenceSummary = try container.decodeIfPresent(String.self, forKey: .evidenceSummary)
        researchProtocols = try container
            .decodeIfPresent([ResearchProtocol].self, forKey: .researchProtocols) ?? []
        verdict = try container.decodeIfPresent(Verdict.self, forKey: .verdict)
        communityProtocols = try container
            .decodeIfPresent([CommunityProtocol].self, forKey: .communityProtocols) ?? []
        uncertainty = try container.decodeIfPresent(String.self, forKey: .uncertainty)
            ?? LibraryCatalog.standardDisclaimer
        officialLinks = try container.decodeIfPresent([OfficialLink].self, forKey: .officialLinks) ?? []
        provenance = try container.decodeIfPresent(EntryProvenance.self, forKey: .provenance) ?? .builtIn
        template = try container.decodeIfPresent(ItemTemplate.self, forKey: .template)
    }
}

/// How strong the backing for an entry is. Ordered weakest to strongest is deliberately
/// *not* implied — these are categories, not a scale to average.
public enum EvidenceTier: String, Hashable, Sendable, Codable, CaseIterable {
    case regulatory
    case systematicReview = "systematic-review"
    case clinicalStudy = "clinical-study"
    case preclinical
    case reference

    public var label: String {
        switch self {
        case .regulatory: "Regulator / guideline"
        case .systematicReview: "Systematic review"
        case .clinicalStudy: "Clinical study"
        case .preclinical: "Preclinical"
        case .reference: "Reference only"
        }
    }
}

/// The eight entries that ship with the app, ported from the reference implementation.
///
/// These are seeds, not the whole library: the user's own entries live in the store
/// alongside them. Built-ins stay immutable here so an app update can revise wording or
/// links without touching anything the user wrote.
public enum LibraryCatalog {

    /// Applied to every entry by default. Present on all eight in the reference, so it is
    /// factored out rather than repeated.
    public static let standardDisclaimer = "Reference information only. Not medical advice."

    /// Bump when the built-in entries change, so a seeding pass can tell whether the
    /// shipped set has moved on since the store was last populated.
    public static let version = 7

    /// Identifier prefix for shipped entries. User and agent entries use `custom:`.
    public static let builtInPrefix = "catalog:"

    /// Builds a reference link from a compile-time literal.
    ///
    /// A malformed URL here is a programming error, not a runtime condition. It degrades to
    /// `about:blank` rather than trapping, and `LibraryCatalogTests` walks every shipped entry
    /// so a typo fails the build rather than shipping a dead link.
    private static func link(_ title: String, _ url: String) -> LibraryCatalogEntry.OfficialLink {
        let resolved = URL(string: url) ?? URL(string: "about:blank") ?? URL(fileURLWithPath: "/")
        return LibraryCatalogEntry.OfficialLink(title: title, url: resolved)
    }

    /// The shipped entries, with their checked evidence merged in.
    ///
    /// The evidence lives in a generated file, so the two are written and reviewed apart:
    /// the wording below is authored, the summaries, tiers and links in `evidence` come from
    /// the sources.
    public static let builtInEntries: [LibraryCatalogEntry] = authoredEntries.map { entry in
        guard let found = evidence[entry.id] else { return entry }
        var merged = entry
        merged.evidenceTier = found.tier
        merged.evidenceSummary = found.summary
        merged.officialLinks = found.links
        merged.researchProtocols = found.protocols
        merged.verdict = found.verdict
        merged.communityProtocols = found.community
        return merged
    }

    private static let authoredEntries: [LibraryCatalogEntry] = [

        // MARK: Peptides
        //
        // Templates seed the reconstitution calculator with vial sizes and diluent
        // volumes that are commonly sold. They are starting points, not prescriptions:
        // the user corrects them to match the vial actually in front of them.

        LibraryCatalogEntry(
            id: "catalog:peptide:bpc-157",
            kind: .peptide,
            title: "BPC-157",
            summary: "Synthetic pentadecapeptide studied in animal models for connective tissue and gut healing. No approved human indication.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("PubMed: BPC-157 literature", "https://pubmed.ncbi.nlm.nih.gov/?term=BPC+157"),
                link("ClinicalTrials.gov: BPC-157", "https://clinicaltrials.gov/search?term=BPC-157")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 4, toHours: 6, source: "Preclinical PK; human data limited"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:dsip",
            kind: .peptide,
            title: "DSIP (delta sleep-inducing peptide)",
            summary: "Nonapeptide investigated for sleep architecture. Human evidence is old and thin; no approved indication.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("PubMed: delta sleep-inducing peptide", "https://pubmed.ncbi.nlm.nih.gov/?term=delta+sleep+inducing+peptide")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 0.1, toHours: 0.3, source: "Rapid plasma clearance; preclinical"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:igf-1-lr3",
            kind: .peptide,
            title: "IGF-1 LR3",
            summary: "Long-acting IGF-1 analogue. Research chemical with no human indication; systemic growth signalling carries real risk.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("PubMed: IGF-1 LR3", "https://pubmed.ncbi.nlm.nih.gov/?term=IGF-1+LR3")
            ],
            template: ItemTemplate(
                halfLife: .hours(20, source: "Reduced IGFBP binding extends clearance; preclinical"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 1,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 1,
                storageCondition: .refrigerated
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:kisspeptin-10",
            kind: .peptide,
            title: "Kisspeptin-10",
            summary: "Upstream regulator of GnRH release, studied in reproductive endocrinology.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: kisspeptin-10", "https://pubmed.ncbi.nlm.nih.gov/?term=kisspeptin+10")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 0.3, toHours: 0.7, source: "Human infusion studies"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:kpv",
            kind: .peptide,
            title: "KPV",
            summary: "Alpha-MSH tripeptide fragment studied for anti-inflammatory effects, largely in gut models.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("PubMed: KPV peptide", "https://pubmed.ncbi.nlm.nih.gov/?term=KPV+peptide")
            ],
            template: ItemTemplate(
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                usageNote: "Also used orally for gut-local effect, where systemic exposure is not the goal."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:ll-37",
            kind: .peptide,
            title: "LL-37",
            summary: "Human cathelicidin antimicrobial peptide studied for wound healing and immune modulation.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("PubMed: LL-37 cathelicidin", "https://pubmed.ncbi.nlm.nih.gov/?term=LL-37+cathelicidin")
            ],
            template: ItemTemplate(
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:semax",
            kind: .peptide,
            title: "Semax",
            summary: "ACTH(4-10) analogue developed in Russia as a nootropic. Approved there; not elsewhere.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: Semax", "https://pubmed.ncbi.nlm.nih.gov/?term=Semax")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 0.3, toHours: 0.5, source: "Rapid clearance; intranasal route studied"),
                route: .intranasal,
                dosageForm: .solution,
                storageCondition: .refrigerated
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:selank",
            kind: .peptide,
            title: "Selank",
            summary: "Tuftsin analogue studied for anxiolytic effect. Approved in Russia; not elsewhere.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: Selank", "https://pubmed.ncbi.nlm.nih.gov/?term=Selank")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 0.2, toHours: 0.5, source: "Rapid clearance; intranasal route studied"),
                route: .intranasal,
                dosageForm: .solution,
                storageCondition: .refrigerated
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:tb-500",
            kind: .peptide,
            title: "TB-500 (thymosin beta-4 fragment)",
            summary: "Synthetic fragment of thymosin beta-4 studied preclinically for tissue repair.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("PubMed: thymosin beta-4", "https://pubmed.ncbi.nlm.nih.gov/?term=thymosin+beta+4")
            ],
            template: ItemTemplate(
                halfLife: .days(2, source: "Thymosin beta-4 fragment; preclinical"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                usageNote: "Often run as a loading phase followed by a lower maintenance frequency."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:ipamorelin",
            kind: .peptide,
            title: "Ipamorelin",
            summary: "Growth hormone secretagogue studied for GH release. Selective, with little effect on cortisol or prolactin.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: ipamorelin", "https://pubmed.ncbi.nlm.nih.gov/?term=ipamorelin")
            ],
            template: ItemTemplate(
                halfLife: .hours(2, source: "Ghrelin receptor agonist PK"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                suggestedLabAnalyteIds: ["igf-1", "glucose", "hba1c"],
                usageNote: "Usually taken at night on an empty stomach. IGF-1 is the follow-up marker."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:cjc-1295",
            kind: .peptide,
            title: "CJC-1295 (no DAC)",
            summary: "GHRH analogue studied for amplifying GH pulses. The no-DAC form is short acting and dosed daily.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: CJC-1295", "https://pubmed.ncbi.nlm.nih.gov/?term=CJC-1295")
            ],
            template: ItemTemplate(
                halfLife: .minutes(30, source: "Mod GRF 1-29, no DAC"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                suggestedLabAnalyteIds: ["igf-1"],
                usageNote: "Check whether your product includes DAC — it changes the schedule completely."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:cjc-1295-dac",
            kind: .peptide,
            title: "CJC-1295 with DAC",
            summary: "Long-acting GHRH analogue. The drug affinity complex extends half-life to around a week.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: CJC-1295 DAC", "https://pubmed.ncbi.nlm.nih.gov/?term=CJC-1295+DAC")
            ],
            template: ItemTemplate(
                halfLife: .days(7, source: "DAC albumin binding extends half-life"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                suggestedLabAnalyteIds: ["igf-1"],
                usageNote: "Do not confuse with the no-DAC version."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:cjc-ipamorelin-blend",
            kind: .peptide,
            title: "CJC-1295 / Ipamorelin blend",
            summary: "Common combination vial pairing a GHRH analogue with a GH secretagogue. Sold premixed.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: growth hormone secretagogues", "https://pubmed.ncbi.nlm.nih.gov/?term=growth+hormone+secretagogue")
            ],
            template: ItemTemplate(
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 10,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                blend: Blend(components: [
                    BlendComponent(name: "CJC-1295", amountValue: 5, amountUnit: .milligram, libraryEntryId: "catalog:peptide:cjc-1295"),
                    BlendComponent(name: "Ipamorelin", amountValue: 5, amountUnit: .milligram, libraryEntryId: "catalog:peptide:ipamorelin")
                ]),
                suggestedLabAnalyteIds: ["igf-1", "glucose"],
                usageNote: "One vial, two compounds. The calculator shows what each draw delivers of each."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:semaglutide",
            kind: .peptide,
            title: "Semaglutide",
            summary: "GLP-1 receptor agonist. Approved products follow a stepped titration over months rather than starting at maintenance dose.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("EMA: Ozempic", "https://www.ema.europa.eu/en/medicines/human/EPAR/ozempic"),
                link("EMA: Wegovy", "https://www.ema.europa.eu/en/medicines/human/EPAR/wegovy")
            ],
            template: ItemTemplate(
                halfLife: .days(7, source: "EMA/FDA product information"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                suggestedLabAnalyteIds: ["hba1c", "glucose", "alt", "triglycerides"],
                usageNote: "Record the titration step you are on, not the target dose."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:tirzepatide",
            kind: .peptide,
            title: "Tirzepatide",
            summary: "Dual GIP and GLP-1 receptor agonist. Like semaglutide, follows a stepped titration.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("EMA: Mounjaro", "https://www.ema.europa.eu/en/medicines/human/EPAR/mounjaro")
            ],
            template: ItemTemplate(
                halfLife: .days(5, source: "FDA label, Mounjaro"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                suggestedLabAnalyteIds: ["hba1c", "glucose", "alt", "triglycerides"]
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:retatrutide",
            kind: .peptide,
            title: "Retatrutide",
            summary: "Triple GIP, GLP-1 and glucagon receptor agonist in clinical trials. Not approved.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("ClinicalTrials.gov: retatrutide", "https://clinicaltrials.gov/search?term=retatrutide")
            ],
            template: ItemTemplate(
                halfLife: .days(6, source: "Phase 2 PK, supports weekly dosing"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                suggestedLabAnalyteIds: ["hba1c", "glucose", "alt"],
                usageNote: "Investigational. No approved product information exists."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:tesamorelin",
            kind: .peptide,
            title: "Tesamorelin",
            summary: "GHRH analogue approved for HIV-associated lipodystrophy. Studied for visceral fat reduction.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: tesamorelin", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=tesamorelin")
            ],
            template: ItemTemplate(
                halfLife: .minutes(38, source: "FDA label, Egrifta"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                suggestedLabAnalyteIds: ["igf-1", "glucose"]
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:sermorelin",
            kind: .peptide,
            title: "Sermorelin",
            summary: "GHRH analogue studied for stimulating endogenous growth hormone release.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: sermorelin", "https://pubmed.ncbi.nlm.nih.gov/?term=sermorelin")
            ],
            template: ItemTemplate(
                halfLife: .minutes(12, source: "GHRH 1-29 PK"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                suggestedLabAnalyteIds: ["igf-1"]
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:hexarelin",
            kind: .peptide,
            title: "Hexarelin",
            summary: "Growth hormone secretagogue. More potent than ipamorelin but with greater cortisol and prolactin effect.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("PubMed: hexarelin", "https://pubmed.ncbi.nlm.nih.gov/?term=hexarelin")
            ],
            template: ItemTemplate(
                halfLife: .minutes(70, source: "Published PK"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                suggestedLabAnalyteIds: ["igf-1", "prolactin", "cortisol"]
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:ghrp-2",
            kind: .peptide,
            title: "GHRP-2",
            summary: "Growth hormone releasing peptide studied for GH secretion. Raises appetite via ghrelin signalling.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: GHRP-2", "https://pubmed.ncbi.nlm.nih.gov/?term=GHRP-2")
            ],
            template: ItemTemplate(
                halfLife: .minutes(60, source: "Published PK"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                suggestedLabAnalyteIds: ["igf-1", "prolactin"]
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:ghrp-6",
            kind: .peptide,
            title: "GHRP-6",
            summary: "Growth hormone releasing peptide with a pronounced appetite-stimulating effect.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: GHRP-6", "https://pubmed.ncbi.nlm.nih.gov/?term=GHRP-6")
            ],
            template: ItemTemplate(
                halfLife: .minutes(55, source: "Published PK"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                suggestedLabAnalyteIds: ["igf-1", "prolactin"]
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:mots-c",
            kind: .peptide,
            title: "MOTS-c",
            summary: "Mitochondrial-derived peptide studied preclinically for metabolic regulation.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("PubMed: MOTS-c", "https://pubmed.ncbi.nlm.nih.gov/?term=MOTS-c")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 1, toHours: 3, source: "Mitochondrial peptide; limited human PK"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 10,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                suggestedLabAnalyteIds: ["glucose", "hba1c"]
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:epitalon",
            kind: .peptide,
            title: "Epitalon",
            summary: "Synthetic tetrapeptide studied in Russian literature for telomerase and pineal function. Evidence is limited.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("PubMed: epitalon", "https://pubmed.ncbi.nlm.nih.gov/?term=epitalon")
            ],
            template: ItemTemplate(
                halfLife: .minutes(30, source: "Short tetrapeptide"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 10,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                usageNote: "Typically run in short courses rather than continuously."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:thymosin-alpha-1",
            kind: .peptide,
            title: "Thymosin alpha-1",
            summary: "Immunomodulating peptide approved in some countries for hepatitis B and as a vaccine adjuvant.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: thymosin alpha 1", "https://pubmed.ncbi.nlm.nih.gov/?term=thymosin+alpha+1")
            ],
            template: ItemTemplate(
                halfLife: .hours(2, source: "Zadaxin product information"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:aod-9604",
            kind: .peptide,
            title: "AOD-9604",
            summary: "Modified fragment of hGH studied for fat metabolism without the growth-promoting effects of full hGH.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("PubMed: AOD9604", "https://pubmed.ncbi.nlm.nih.gov/?term=AOD9604")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 0.5, toHours: 1, source: "hGH fragment 176-191"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:pt-141",
            kind: .peptide,
            title: "PT-141 (bremelanotide)",
            summary: "Melanocortin receptor agonist approved for hypoactive sexual desire disorder in premenopausal women.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: bremelanotide", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=bremelanotide")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 2, toHours: 3, source: "FDA label, Vyleesi"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 10,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                usageNote: "Used as needed rather than on a fixed schedule. Nausea is the common dose-limiting effect."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:melanotan-2",
            kind: .peptide,
            title: "Melanotan II",
            summary: "Melanocortin agonist studied for pigmentation. Not approved; sold as a research chemical.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("PubMed: melanotan II", "https://pubmed.ncbi.nlm.nih.gov/?term=melanotan+II")
            ],
            template: ItemTemplate(
                halfLife: .hours(33, source: "Published PK"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 10,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                usageNote: "Moles and pigmented lesions warrant monitoring. Not an approved product."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:ss-31",
            kind: .peptide,
            title: "SS-31 (elamipretide)",
            summary: "Mitochondria-targeting peptide studied in trials for mitochondrial myopathy.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("ClinicalTrials.gov: elamipretide", "https://clinicaltrials.gov/search?term=elamipretide")
            ],
            template: ItemTemplate(
                halfLife: .hours(3, source: "Elamipretide published PK"),
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 10,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:ghk-cu",
            kind: .peptide,
            title: "GHK-Cu",
            summary: "Copper tripeptide studied for skin remodelling and wound repair. Frequently used topically.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("PubMed: GHK-Cu", "https://pubmed.ncbi.nlm.nih.gov/?term=GHK-Cu")
            ],
            template: ItemTemplate(
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 50,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 5,
                storageCondition: .refrigerated,
                usageNote: "Often applied topically rather than injected."
            )
        ),

        // MARK: Hormones — HRT / TRT / hGH / AAS

        LibraryCatalogEntry(
            id: "catalog:hormone:testosterone-cypionate",
            kind: .medicationHormone,
            title: "Testosterone cypionate",
            summary: "Long-acting testosterone ester, half-life around eight days, which is why weekly or twice-weekly injection is typical.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: testosterone cypionate", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=testosterone+cypionate")
            ],
            template: ItemTemplate(
                halfLife: .range(fromDays: 6, toDays: 8, source: "FDA label, Depo-Testosterone"),
                genericName: "testosterone cypionate",
                route: .intramuscular,
                dosageForm: .solution,
                storageCondition: .roomTemperature,
                suggestedLabAnalyteIds: [
                    "testosterone-total", "testosterone-free", "estradiol", "shbg",
                    "haematocrit", "haemoglobin", "lh", "fsh"
                ],
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:testosterone-enanthate",
            kind: .medicationHormone,
            title: "Testosterone enanthate",
            summary: "Long-acting testosterone ester with a half-life close to cypionate. Largely interchangeable for scheduling.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: testosterone enanthate", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=testosterone+enanthate")
            ],
            template: ItemTemplate(
                halfLife: .range(fromDays: 4.5, toDays: 5.5, source: "FDA label"),
                genericName: "testosterone enanthate",
                route: .intramuscular,
                dosageForm: .solution,
                storageCondition: .roomTemperature,
                suggestedLabAnalyteIds: [
                    "testosterone-total", "testosterone-free", "estradiol", "shbg", "haematocrit"
                ]
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:testosterone-propionate",
            kind: .medicationHormone,
            title: "Testosterone propionate",
            summary: "Short-acting testosterone ester, half-life around two to three days, requiring frequent injection.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: testosterone propionate", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=testosterone+propionate")
            ],
            template: ItemTemplate(
                halfLife: .days(0.8, source: "Published ester PK"),
                genericName: "testosterone propionate",
                route: .intramuscular,
                dosageForm: .solution,
                storageCondition: .roomTemperature,
                suggestedLabAnalyteIds: ["testosterone-total", "estradiol", "haematocrit"],
                usageNote: "Short ester. Missing a day moves levels noticeably more than with cypionate."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:testosterone-phenylpropionate",
            kind: .medicationHormone,
            title: "Testosterone phenylpropionate",
            summary: "A mid-length testosterone ester, almost always used as one component of a blend such as Sustanon rather than on its own.",
            evidenceTier: .reference,
            officialLinks: [
                link("Testosterone esters — Wikipedia overview", "https://en.wikipedia.org/wiki/Testosterone_ester")
            ],
            template: ItemTemplate(
                halfLife: .days(8, source: "Compiled clinical-pharmacology reference (Wright & Burgess, Long Acting Injections and Implants, 2012) — depot release duration, not a dedicated single-compound PK trial"),
                genericName: "testosterone phenylpropionate",
                route: .intramuscular,
                dosageForm: .solution,
                storageCondition: .roomTemperature,
                usageNote: "Rarely dosed alone; this is the figure it contributes to a blend's staggered release, not an isolated study."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:testosterone-isocaproate",
            kind: .medicationHormone,
            title: "Testosterone isocaproate",
            summary: "A mid-length testosterone ester that only ever appears as one component of a blend such as Sustanon.",
            evidenceTier: .reference,
            officialLinks: [
                link("Testosterone esters — Wikipedia overview", "https://en.wikipedia.org/wiki/Testosterone_ester")
            ],
            template: ItemTemplate(
                genericName: "testosterone isocaproate",
                route: .intramuscular,
                dosageForm: .solution,
                storageCondition: .roomTemperature,
                usageNote: "No dedicated human half-life has been published for this ester alone — it has only ever been studied mixed with the other Sustanon esters, so no figure is shown here rather than an invented one."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:testosterone-decanoate",
            kind: .medicationHormone,
            title: "Testosterone decanoate",
            summary: "The longest-acting ester in Sustanon, qualitatively between enanthate and undecanoate but never marketed or studied on its own.",
            evidenceTier: .reference,
            officialLinks: [
                link("Testosterone esters — Wikipedia overview", "https://en.wikipedia.org/wiki/Testosterone_ester")
            ],
            template: ItemTemplate(
                genericName: "testosterone decanoate",
                route: .intramuscular,
                dosageForm: .solution,
                storageCondition: .roomTemperature,
                usageNote: "No formal single-compound half-life has been published — it has been studied as a male-contraceptive component, not in isolation, so no figure is shown here rather than a guessed one."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:sustanon-250",
            kind: .medicationHormone,
            title: "Sustanon 250",
            summary: "Blend of four testosterone esters with staggered release, from fast-acting propionate to slow decanoate.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("EMA: product information", "https://www.ema.europa.eu/en/glossary-terms/product-information")
            ],
            template: ItemTemplate(
                halfLife: .range(fromDays: 1, toDays: 21, source: "Four esters; blended release"),
                genericName: "testosterone esters blend",
                brandName: "Sustanon 250",
                route: .intramuscular,
                dosageForm: .solution,
                storageCondition: .roomTemperature,
                blend: Blend(components: [
                    BlendComponent(name: "Testosterone propionate", amountValue: 30, amountUnit: .milligram, libraryEntryId: "catalog:hormone:testosterone-propionate"),
                    BlendComponent(name: "Testosterone phenylpropionate", amountValue: 60, amountUnit: .milligram, libraryEntryId: "catalog:hormone:testosterone-phenylpropionate"),
                    BlendComponent(name: "Testosterone isocaproate", amountValue: 60, amountUnit: .milligram, libraryEntryId: "catalog:hormone:testosterone-isocaproate"),
                    BlendComponent(name: "Testosterone decanoate", amountValue: 100, amountUnit: .milligram, libraryEntryId: "catalog:hormone:testosterone-decanoate")
                ]),
                suggestedLabAnalyteIds: [
                    "testosterone-total", "testosterone-free", "estradiol", "shbg", "haematocrit"
                ],
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:testosterone-gel",
            kind: .medicationHormone,
            title: "Testosterone gel (transdermal)",
            summary: "Daily transdermal testosterone, dosed by pump actuations or sachets rather than injection volume.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: testosterone gel", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=testosterone+gel")
            ],
            template: ItemTemplate(
                halfLife: .hours(2, source: "Transdermal; steady state in 24-48 h"),
                genericName: "testosterone",
                route: .transdermal,
                dosageForm: .gel,
                storageCondition: .roomTemperature,
                suggestedLabAnalyteIds: ["testosterone-total", "estradiol", "haematocrit"],
                usageNote: "Transfer to others by skin contact is the documented risk. Wash hands and cover the site."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:nandrolone-decanoate",
            kind: .medicationHormone,
            title: "Nandrolone decanoate",
            summary: "Long-acting 19-nortestosterone ester. Suppresses natural production and is detectable long after use.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: nandrolone decanoate", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=nandrolone+decanoate")
            ],
            template: ItemTemplate(
                halfLife: .range(fromDays: 6, toDays: 12, source: "FDA label, Deca-Durabolin"),
                genericName: "nandrolone decanoate",
                route: .intramuscular,
                dosageForm: .solution,
                storageCondition: .roomTemperature,
                suggestedLabAnalyteIds: [
                    "testosterone-total", "estradiol", "prolactin", "haematocrit", "ldl", "hdl"
                ],
                usageNote: "Prolactin is worth watching alongside oestradiol on 19-nor compounds."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:hgh",
            kind: .medicationHormone,
            title: "Growth hormone (somatropin)",
            summary: "Recombinant human growth hormone. Dosed in IU or mg depending on the product, which is a common source of error.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("EMA: somatropin", "https://www.ema.europa.eu/en/medicines/human/referrals/somatropin")
            ],
            template: ItemTemplate(
                halfLife: .hours(3, source: "FDA label, Genotropin: SC half-life 3.0 h in GHD adults (vs 0.4 h IV — slow SC absorption dominates)"),
                genericName: "somatropin",
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 10,
                vialContentsUnit: .internationalUnit,
                typicalDiluentMillilitres: 1,
                storageCondition: .refrigerated,
                suggestedLabAnalyteIds: ["igf-1", "glucose", "hba1c", "free-t4"],
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:hcg",
            kind: .medicationHormone,
            title: "hCG (chorionic gonadotropin)",
            summary: "Gonadotropin used to maintain testicular function during testosterone therapy, and in fertility protocols.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: chorionic gonadotropin", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=chorionic+gonadotropin")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 24, toHours: 36, source: "Biphasic; terminal phase"),
                genericName: "chorionic gonadotropin",
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5000,
                vialContentsUnit: .internationalUnit,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                suggestedLabAnalyteIds: ["testosterone-total", "estradiol", "lh", "fsh"]
            )
        ),
        // MARK: Household medications
        //
        // The things people actually have in a drawer. Included because they confound
        // everything else: an NSAID week flattens inflammatory markers and blunts training
        // soreness, and a course of antibiotics reorders the gut for months. Untracked, those
        // show up as an unexplained dip in whatever else is being measured.
        //
        // Doses shown are the common over-the-counter adult figures from the regulatory
        // labels. They are prefill defaults for a tracker, not a recommendation — anything
        // prescribed follows the prescription.
        LibraryCatalogEntry(
            id: "catalog:medication:ibuprofen",
            kind: .medicationHormone,
            title: "Ibuprofen",
            summary: "NSAID. Regular use around training suppresses the inflammatory signal that drives adaptation, so a week of it is worth seeing next to your training log.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: ibuprofen", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=ibuprofen"),
                link("EMA: ibuprofen", "https://www.ema.europa.eu/en/medicines/human/referrals/ibuprofen-dexibuprofen-containing-medicines")
            ],
            template: ItemTemplate(
                halfLife: .hours(2, source: "FDA label; 1.8-2 h"),
                genericName: "ibuprofen",
                route: .oral,
                dosageForm: .tablet,
                storageCondition: .roomTemperature,
                usageNote: "Taken as needed, with food. Note it alongside training: NSAIDs blunt the inflammatory response that drives adaptation."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:paracetamol",
            kind: .medicationHormone,
            title: "Paracetamol (acetaminophen)",
            summary: "Analgesic and antipyretic, not an anti-inflammatory. The usual choice when you want pain or fever relief without suppressing inflammation.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: acetaminophen", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=acetaminophen"),
                link("EMA: paracetamol", "https://www.ema.europa.eu/en/medicines/human/referrals/paracetamol-containing-medicinal-products")
            ],
            template: ItemTemplate(
                halfLife: .hours(2, source: "FDA label; 1.25-3 h"),
                genericName: "paracetamol",
                route: .oral,
                dosageForm: .tablet,
                storageCondition: .roomTemperature,
                usageNote: "The most common accidental overdose, usually from combination cold remedies that also contain it."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:aspirin",
            kind: .medicationHormone,
            title: "Aspirin",
            summary: "NSAID, and an irreversible platelet inhibitor. The antiplatelet effect lasts the life of the platelet, roughly a week, long after the drug itself has cleared.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: aspirin", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=aspirin")
            ],
            template: ItemTemplate(
                halfLife: .hours(3, source: "FDA label, salicylate; dose-dependent"),
                genericName: "acetylsalicylic acid",
                route: .oral,
                dosageForm: .tablet,
                storageCondition: .roomTemperature,
                usageNote: "Half-life describes the drug, not the effect. Platelet inhibition persists about a week, which is why it matters before any procedure."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:naproxen",
            kind: .medicationHormone,
            title: "Naproxen",
            summary: "Longer-acting NSAID, typically twice daily rather than every few hours.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: naproxen", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=naproxen")
            ],
            template: ItemTemplate(
                halfLife: .hours(14, source: "FDA label; 12-17 h"),
                genericName: "naproxen",
                route: .oral,
                dosageForm: .tablet,
                storageCondition: .roomTemperature,
                usageNote: "Same caveat as ibuprofen around training, and it lingers longer."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:diclofenac-topical",
            kind: .medicationHormone,
            title: "Diclofenac gel (topical)",
            summary: "Topical NSAID for a specific joint or muscle. Systemic exposure is a fraction of oral, which is the point.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: diclofenac topical", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=diclofenac+sodium+topical")
            ],
            template: ItemTemplate(
                genericName: "diclofenac sodium",
                route: .topical,
                dosageForm: .gel,
                storageCondition: .roomTemperature,
                usageNote: "Log the site. Where it went is the useful part of the record."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:antibiotic-course",
            kind: .medicationHormone,
            title: "Antibiotic course (generic)",
            summary: "A placeholder for whatever you were prescribed, so the course is on the timeline without needing a catalogue entry per drug. Rename it to the actual antibiotic.",
            evidenceTier: .regulatory,
            uncertainty: "Deliberately generic. Dose, interval and duration come from your prescription, not from here — they vary by drug, indication and body weight.",
            officialLinks: [
                link("DailyMed: search by drug name", "https://dailymed.nlm.nih.gov/dailymed/"),
                link("WHO: antibiotic resistance", "https://www.who.int/news-room/fact-sheets/detail/antibiotic-resistance")
            ],
            template: ItemTemplate(
                genericName: "antibiotic",
                route: .oral,
                dosageForm: .capsule,
                storageCondition: .roomTemperature,
                usageNote: "Finish the course as prescribed. Worth keeping on the timeline for months afterwards: gut flora take a long time to settle, and digestion or mood changes in that window are not a mystery if the course is visible."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:antihistamine",
            kind: .medicationHormone,
            title: "Antihistamine (non-drowsy)",
            summary: "Cetirizine, loratadine and similar. Seasonal use is worth logging — allergy load itself affects sleep and training quality.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: cetirizine", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=cetirizine")
            ],
            template: ItemTemplate(
                halfLife: .hours(8, source: "FDA label, cetirizine"),
                genericName: "cetirizine",
                route: .oral,
                dosageForm: .tablet,
                storageCondition: .roomTemperature
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:antacid",
            kind: .medicationHormone,
            title: "Antacid / PPI",
            summary: "Omeprazole and similar. Relevant beyond the symptom: sustained acid suppression reduces absorption of magnesium, B12 and iron.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: omeprazole", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=omeprazole")
            ],
            template: ItemTemplate(
                halfLife: .hours(1, source: "FDA label, omeprazole; effect outlasts plasma level"),
                genericName: "omeprazole",
                route: .oral,
                dosageForm: .capsule,
                storageCondition: .roomTemperature,
                usageNote: "If you take this regularly, it belongs next to your magnesium and B12 markers."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:oral-rehydration",
            kind: .medicationHormone,
            title: "Oral rehydration salts",
            summary: "Electrolyte replacement for illness, heat or heavy sweating.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("WHO: oral rehydration salts", "https://www.who.int/publications/i/item/WHO-FCH-CAH-06.1")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .powder,
                storageCondition: .roomTemperature,
                usageNote: "Worth logging during illness — dehydration explains a lot of what otherwise looks like a bad recovery week."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:levothyroxine",
            kind: .medicationHormone,
            title: "Levothyroxine (T4)",
            summary: "Synthetic T4. Absorption is materially reduced by calcium, iron and magnesium, so timing separation is part of the protocol.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("EMA: levothyroxine", "https://www.ema.europa.eu/en/medicines/human/referrals/levothyroxine-containing-medicinal-products")
            ],
            template: ItemTemplate(
                halfLife: .days(7, source: "FDA label, Synthroid"),
                genericName: "levothyroxine sodium",
                route: .oral,
                dosageForm: .tablet,
                storageCondition: .roomTemperature,
                suggestedLabAnalyteIds: ["tsh", "free-t4", "free-t3"],
                usageNote: "Usually taken fasted. Separate from calcium, iron and magnesium by about four hours."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:liothyronine",
            kind: .medicationHormone,
            title: "Liothyronine (T3)",
            summary: "Synthetic T3. Short half-life, so it is often split across the day rather than taken once.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: liothyronine", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=liothyronine")
            ],
            template: ItemTemplate(
                halfLife: .days(2.5, source: "FDA label, Cytomel: biological half-life about 2 1/2 days"),
                genericName: "liothyronine sodium",
                route: .oral,
                dosageForm: .tablet,
                storageCondition: .roomTemperature,
                suggestedLabAnalyteIds: ["tsh", "free-t3", "free-t4"]
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:anastrozole",
            kind: .medicationHormone,
            title: "Anastrozole",
            summary: "Aromatase inhibitor, recorded alongside testosterone protocols where oestradiol management is part of the plan.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: anastrozole", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=anastrozole")
            ],
            template: ItemTemplate(
                halfLife: .hours(50, source: "FDA label, Arimidex"),
                genericName: "anastrozole",
                route: .oral,
                dosageForm: .tablet,
                storageCondition: .roomTemperature,
                suggestedLabAnalyteIds: ["estradiol", "testosterone-total"],
                usageNote: "Over-suppressing oestradiol causes its own problems. Dose against symptoms and labs together."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:estradiol",
            kind: .medicationHormone,
            title: "Oestradiol",
            summary: "Oestrogen used in feminising HRT and menopausal HRT. Available as tablets, patches, gel and injectable esters.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("EMA: product information", "https://www.ema.europa.eu/en/glossary-terms/product-information")
            ],
            template: ItemTemplate(
                genericName: "estradiol",
                route: .transdermal,
                dosageForm: .patch,
                storageCondition: .roomTemperature,
                suggestedLabAnalyteIds: ["estradiol", "testosterone-total", "shbg", "prolactin"],
                usageNote: "No half-life is shown: it varies enormously by form (oral, patch or injectable ester), and no single reliable figure covers them all. Log the specific product's own label if you need one."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:progesterone",
            kind: .medicationHormone,
            title: "Progesterone (micronised)",
            summary: "Bioidentical progesterone used in HRT. Oral dosing is sedating, which is why it is usually taken at night.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: progesterone", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=progesterone")
            ],
            template: ItemTemplate(
                genericName: "progesterone",
                route: .oral,
                dosageForm: .capsule,
                storageCondition: .roomTemperature,
                usageNote: "No half-life is shown: the Prometrium FDA label reports Cmax/Tmax but not an elimination half-life, and oral vs intramuscular kinetics differ substantially.",
            )
        ),

        // MARK: Supplements

        LibraryCatalogEntry(
            id: "catalog:supplement:creatine",
            kind: .supplement,
            title: "Creatine monohydrate",
            summary: "Among the most studied sports supplements. Daily consistency matters far more than timing.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("ISSN position stand: creatine", "https://jissn.biomedcentral.com/articles/10.1186/s12970-017-0173-z")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .powder,
                typicalDoseValue: 5,
                typicalDoseUnit: .gram,
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["creatinine"],
                usageNote: "No half-life is shown: creatine is stored in muscle and depleted over weeks, not cleared on a first-order pharmacokinetic curve. Raises serum creatinine without indicating kidney injury. Worth noting before a blood panel."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:taurine",
            kind: .supplement,
            title: "Taurine",
            summary: "Conditionally essential amino acid studied for cardiovascular and exercise outcomes.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: taurine supplementation", "https://pubmed.ncbi.nlm.nih.gov/?term=taurine+supplementation")
            ],
            template: ItemTemplate(
                halfLife: .hours(1, source: "Ghandforoush-Sattari et al. 2010, J Amino Acids, PMID 22331937 — oral 4g dose, healthy adults; rapid clearance reflects efficient renal handling and tissue uptake, not first-order elimination in the pharmacokinetic sense"),
                route: .oral,
                dosageForm: .powder,
                typicalDoseValue: 2,
                typicalDoseUnit: .gram,
                typicalRecurrence: .daily
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:glycine",
            kind: .supplement,
            title: "Glycine",
            summary: "Amino acid studied for sleep quality and as a glutathione precursor.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: glycine sleep", "https://pubmed.ncbi.nlm.nih.gov/?term=glycine+sleep")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .powder,
                typicalDoseValue: 3,
                typicalDoseUnit: .gram,
                typicalRecurrence: .daily,
                usageNote: "No half-life is shown: glycine is a nonessential amino acid handled by the same whole-body pools used for protein synthesis and collagen production, not cleared by classical first-order kinetics. Commonly taken before bed. Often paired with magnesium."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:bcaa",
            kind: .supplement,
            title: "BCAAs",
            summary: "Branched-chain amino acids. Largely redundant when total protein intake is adequate.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: BCAA supplementation", "https://pubmed.ncbi.nlm.nih.gov/?term=branched+chain+amino+acid+supplementation")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .powder,
                typicalDoseValue: 5,
                typicalDoseUnit: .gram,
                typicalRecurrence: .daily,
                usageNote: "No half-life is shown: BCAAs are described by whole-body flux/turnover rates, not a classical elimination half-life, since they are continuously exchanged with the free amino acid pool and muscle protein. Complete protein sources supply these already."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:whey-protein",
            kind: .supplement,
            title: "Whey protein",
            summary: "Fast-absorbing complete dairy protein with a high leucine content.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("ISSN position stand: protein and exercise", "https://jissn.biomedcentral.com/articles/10.1186/s12970-017-0177-8")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .powder,
                typicalDoseValue: 25,
                typicalDoseUnit: .gram,
                typicalRecurrence: .daily,
                servingSize: "1 scoop (~30 g)",
                usageNote: "No half-life is shown: whey is a mixture of proteins digested into constituent amino acids over hours, not a single compound with one clearance rate. Record grams of protein, not grams of powder — they differ."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:casein-protein",
            kind: .supplement,
            title: "Casein protein",
            summary: "Slow-digesting dairy protein, often taken before sleep for prolonged amino acid release.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: casein protein overnight", "https://pubmed.ncbi.nlm.nih.gov/?term=casein+protein+overnight+muscle")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .powder,
                typicalDoseValue: 30,
                typicalDoseUnit: .gram,
                typicalRecurrence: .daily,
                servingSize: "1 scoop (~35 g)",
                usageNote: "No half-life is shown: casein clots in the stomach and releases amino acids over several hours, but this digestion curve is not a first-order elimination half-life."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:plant-protein",
            kind: .supplement,
            title: "Plant protein blend",
            summary: "Pea, rice or soy protein blend. Blending improves the amino acid profile over single sources.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: plant protein muscle", "https://pubmed.ncbi.nlm.nih.gov/?term=plant+protein+muscle+protein+synthesis")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .powder,
                typicalDoseValue: 30,
                typicalDoseUnit: .gram,
                typicalRecurrence: .daily,
                servingSize: "1 scoop (~35 g)",
                usageNote: "No half-life is shown: like other protein blends, this is digested into amino acids over hours rather than cleared as a single compound."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:collagen",
            kind: .supplement,
            title: "Collagen peptides",
            summary: "Hydrolysed collagen studied for connective tissue and skin. Not a complete protein.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: collagen peptides tendon", "https://pubmed.ncbi.nlm.nih.gov/?term=collagen+peptide+tendon")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .powder,
                typicalDoseValue: 15,
                typicalDoseUnit: .gram,
                typicalRecurrence: .daily,
                usageNote: "No half-life is shown: a recent tracer study reports a collagen-peptide clearance figure, but its PMID carries a 2026 publication date the research could not confirm as genuine, so it is held back pending manual verification. Often taken with vitamin C before training."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:magnesium",
            kind: .supplement,
            title: "Magnesium",
            summary: "Mineral supplement. Glycinate and citrate are the commonly used forms; oxide is poorly absorbed.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("NIH ODS: Magnesium", "https://ods.od.nih.gov/factsheets/Magnesium-HealthProfessional/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                typicalDoseValue: 200,
                typicalDoseUnit: .milligram,
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["magnesium"],
                usageNote: "No half-life is shown: magnesium is an essential mineral under homeostatic renal and bone-store regulation, not first-order pharmacokinetic clearance. Often taken in the evening. Separate from levothyroxine by about four hours."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:vitamin-a",
            kind: .supplement,
            title: "Vitamin A (retinol)",
            summary: "Fat-soluble vitamin. Has a genuine upper limit — accumulates rather than clearing.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("NIH ODS: Vitamin A", "https://ods.od.nih.gov/factsheets/VitaminA-HealthProfessional/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .softgel,
                typicalDoseValue: 900,
                typicalDoseUnit: .microgram,
                typicalRecurrence: .daily,
                usageNote: "No half-life is shown: retinol is stored for months in the liver rather than cleared on a first-order curve, so no single elimination figure applies. Fat soluble and cumulative. Upper limits matter here more than with water-soluble vitamins."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:vitamin-b-complex",
            kind: .supplement,
            title: "Vitamin B complex",
            summary: "Combined B vitamins. High-dose biotin within these can interfere with some lab immunoassays.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("NIH ODS: B vitamins", "https://ods.od.nih.gov/factsheets/list-VitaminsMinerals/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                typicalDoseValue: 1,
                typicalDoseUnit: .gram,
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["vitamin-b12"],
                usageNote: "Biotin can skew thyroid and troponin assays. Pause several days before testing."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:vitamin-b12",
            kind: .supplement,
            title: "Vitamin B12 (cobalamin)",
            summary: "Water-soluble vitamin. Methylcobalamin and cyanocobalamin are the common forms.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("NIH ODS: Vitamin B12", "https://ods.od.nih.gov/factsheets/VitaminB12-HealthProfessional/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                typicalDoseValue: 1000,
                typicalDoseUnit: .microgram,
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["vitamin-b12"],
                usageNote: "No half-life is shown: plasma clearance (roughly a week) and liver-store depletion (roughly a year) are two very different processes, and only a compiled, not independently verified, figure exists for either."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:vitamin-c",
            kind: .supplement,
            title: "Vitamin C (ascorbic acid)",
            summary: "Water-soluble antioxidant vitamin. Absorption saturates, so split dosing beats one large dose.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("NIH ODS: Vitamin C", "https://ods.od.nih.gov/factsheets/VitaminC-HealthProfessional/")
            ],
            template: ItemTemplate(
                halfLife: .hours(2, source: "Dhotre et al. 2025, Pharmaceutics, PMID 41304796 — acute plasma disappearance; the separate, slower body-pool depletion kinetics relevant to scurvy risk operate over weeks and are a different process"),
                route: .oral,
                dosageForm: .capsule,
                typicalDoseValue: 500,
                typicalDoseUnit: .milligram,
                typicalRecurrence: .daily,
                usageNote: "High doses around training may blunt some adaptation signalling."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:vitamin-d3",
            kind: .supplement,
            title: "Vitamin D3 (cholecalciferol)",
            summary: "Fat-soluble vitamin dosed in international units. Frequently paired with K2.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("NIH ODS: Vitamin D", "https://ods.od.nih.gov/factsheets/VitaminD-HealthProfessional/")
            ],
            template: ItemTemplate(
                halfLife: .days(15, source: "25-OH-D circulating half-life"),
                route: .oral,
                dosageForm: .softgel,
                typicalDoseValue: 2000,
                typicalDoseUnit: .internationalUnit,
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["vitamin-d-25oh"],
                usageNote: "Absorbed better with a fat-containing meal."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:vitamin-e",
            kind: .supplement,
            title: "Vitamin E (tocopherol)",
            summary: "Fat-soluble antioxidant. Mixed tocopherols are closer to the dietary form than alpha alone.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("NIH ODS: Vitamin E", "https://ods.od.nih.gov/factsheets/VitaminE-HealthProfessional/")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 42, toHours: 48, source: "Traber, Ramakrishnan & Kayden 1994, Proc Natl Acad Sci, PMID 7937827 — natural RRR-alpha-tocopherol; the synthetic SRR stereoisomer clears far faster (about 14 hours) due to selective hepatic retention of the natural form"),
                route: .oral,
                dosageForm: .softgel,
                typicalDoseValue: 15,
                typicalDoseUnit: .milligram,
                typicalRecurrence: .daily
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:vitamin-k2",
            kind: .supplement,
            title: "Vitamin K2 (MK-7)",
            summary: "Fat-soluble vitamin involved in calcium handling. Often paired with vitamin D3.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("NIH ODS: Vitamin K", "https://ods.od.nih.gov/factsheets/VitaminK-HealthProfessional/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .softgel,
                typicalDoseValue: 100,
                typicalDoseUnit: .microgram,
                typicalRecurrence: .daily,
                usageNote: "No half-life is shown: MK-7 is known to persist for days (detectable 48-72h post-dose, Sato et al. 2012, PMID 23140417), but the specific hour figure often quoted elsewhere could not be traced to a verifiable primary source. Interacts with warfarin. Relevant if anticoagulants are in play."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:zinc",
            kind: .supplement,
            title: "Zinc",
            summary: "Essential mineral. Long-term high doses induce copper deficiency.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("NIH ODS: Zinc", "https://ods.od.nih.gov/factsheets/Zinc-HealthProfessional/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                typicalDoseValue: 15,
                typicalDoseUnit: .milligram,
                typicalRecurrence: .daily,
                usageNote: "No half-life is shown: zinc is an essential mineral under homeostatic regulation (absorption and excretion adjust to status), not first-order clearance. Competes with copper absorption. Avoid sustained high doses without cause."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:boron",
            kind: .supplement,
            title: "Boron",
            summary: "Trace mineral studied for effects on SHBG and free testosterone at modest doses.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: boron testosterone", "https://pubmed.ncbi.nlm.nih.gov/?term=boron+testosterone")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                typicalDoseValue: 6,
                typicalDoseUnit: .milligram,
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["testosterone-total", "shbg", "estradiol"],
                usageNote: "No half-life is shown: no peer-reviewed human study reporting a reliable elimination figure for supplemental boron was found."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:tongkat-ali",
            kind: .supplement,
            title: "Tongkat ali (Eurycoma longifolia)",
            summary: "Herbal extract studied for testosterone and stress markers. Extract ratios vary widely between products.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: Eurycoma longifolia", "https://pubmed.ncbi.nlm.nih.gov/?term=Eurycoma+longifolia")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                typicalDoseValue: 400,
                typicalDoseUnit: .milligram,
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["testosterone-total", "cortisol", "shbg"],
                usageNote: "No half-life is shown: this is a multi-constituent extract, and no single marker compound (e.g. eurycomanone) has verified human PK data. Record the extract ratio — a 200:1 extract is not comparable to raw root powder."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:fenugreek",
            kind: .supplement,
            title: "Fenugreek",
            summary: "Herbal extract studied for libido and testosterone markers. Results across trials are inconsistent.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: fenugreek testosterone", "https://pubmed.ncbi.nlm.nih.gov/?term=fenugreek+testosterone")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                typicalDoseValue: 500,
                typicalDoseUnit: .milligram,
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["testosterone-total", "estradiol"],
                usageNote: "No half-life is shown: this is a multi-constituent extract, and no single marker compound has verified human PK data."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:ashwagandha",
            kind: .supplement,
            title: "Ashwagandha (Withania somnifera)",
            summary: "Adaptogenic herb studied for cortisol and stress. Standardised by withanolide content.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: ashwagandha cortisol", "https://pubmed.ncbi.nlm.nih.gov/?term=ashwagandha+cortisol")
            ],
            template: ItemTemplate(
                halfLife: .hours(6, source: "Withanolide PK; limited data"),
                route: .oral,
                dosageForm: .capsule,
                typicalDoseValue: 600,
                typicalDoseUnit: .milligram,
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["cortisol", "testosterone-total", "free-t4"],
                usageNote: "Record the withanolide percentage. Occasional thyroid effects are reported."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:omega-3",
            kind: .supplement,
            title: "Omega-3 (EPA/DHA)",
            summary: "Marine fatty acids. Label totals and actual EPA/DHA content frequently differ.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("NIH ODS: Omega-3", "https://ods.od.nih.gov/factsheets/Omega3FattyAcids-HealthProfessional/")
            ],
            template: ItemTemplate(
                halfLife: .days(2, source: "EPA/DHA plasma; tissue incorporation is slower"),
                route: .oral,
                dosageForm: .softgel,
                typicalDoseValue: 1,
                typicalDoseUnit: .gram,
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["triglycerides"],
                usageNote: "Record EPA and DHA separately, not just total fish oil."
            )
        ),

        // MARK: Feeding and fasting protocols

        LibraryCatalogEntry(
            id: "catalog:food-protocol:16-8",
            kind: .foodProtocol,
            title: "16:8 time-restricted eating",
            summary: "Sixteen-hour daily fast with an eight-hour eating window. Tracked by window adherence rather than food content.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: time-restricted eating", "https://pubmed.ncbi.nlm.nih.gov/?term=time+restricted+eating")
            ],
            template: ItemTemplate(
                typicalRecurrence: .daily,
                usageNote: "Log whether the window held. Drifting the start time is the usual adherence failure."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:18-6",
            kind: .foodProtocol,
            title: "18:6 time-restricted eating",
            summary: "Eighteen-hour fast with a six-hour eating window. A tighter variant of 16:8.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: time-restricted eating", "https://pubmed.ncbi.nlm.nih.gov/?term=time+restricted+eating")
            ],
            template: ItemTemplate(typicalRecurrence: .daily)
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:omad",
            kind: .foodProtocol,
            title: "OMAD (one meal a day)",
            summary: "A single daily eating occasion, effectively a 23:1 window. Hitting protein and micronutrient targets in one sitting is the practical difficulty.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: one meal a day", "https://pubmed.ncbi.nlm.nih.gov/?term=one+meal+a+day+fasting")
            ],
            template: ItemTemplate(typicalRecurrence: .daily)
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:5-2",
            kind: .foodProtocol,
            title: "5:2 intermittent fasting",
            summary: "Normal eating five days a week with two non-consecutive restricted days of roughly 500–600 kcal.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: intermittent fasting 5:2", "https://pubmed.ncbi.nlm.nih.gov/?term=5%3A2+intermittent+fasting")
            ],
            template: ItemTemplate(
                typicalRecurrence: .weekdays([1, 4]),
                usageNote: "Schedule the two restricted days. The other five need no logging."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:adf",
            kind: .foodProtocol,
            title: "Alternate-day fasting",
            summary: "Alternating fast days and normal eating days.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: alternate day fasting", "https://pubmed.ncbi.nlm.nih.gov/?term=alternate+day+fasting")
            ],
            template: ItemTemplate(typicalRecurrence: .everyNDays(2))
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:extended-fast",
            kind: .foodProtocol,
            title: "Extended fast",
            summary: "A fast beyond 24 hours. Electrolytes and refeeding become the practical concerns as duration grows.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: prolonged fasting", "https://pubmed.ncbi.nlm.nih.gov/?term=prolonged+fasting")
            ],
            template: ItemTemplate(
                usageNote: "Record start and end instants. Longer fasts warrant medical supervision."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:full-day-fast",
            kind: .foodProtocol,
            title: "24-hour fast",
            summary: "A full calendar day with no food, logged as one entry per day rather than a start and end time.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: 24-hour fasting RCT (Templeman et al. 2021)", "https://pubmed.ncbi.nlm.nih.gov/34135111/")
            ],
            template: ItemTemplate(
                usageNote: "Log one entry for each day fasted in full."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:keto",
            kind: .foodProtocol,
            title: "Ketogenic diet",
            summary: "Very low carbohydrate intake, typically under 50 g daily, to sustain nutritional ketosis.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: ketogenic diet", "https://pubmed.ncbi.nlm.nih.gov/?term=ketogenic+diet")
            ],
            template: ItemTemplate(
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["glucose", "hba1c", "ldl", "hdl", "triglycerides"],
                usageNote: "Blood ketones give the clearest adherence signal. LDL response varies considerably between people."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:low-carb",
            kind: .foodProtocol,
            title: "Low carbohydrate",
            summary: "Reduced carbohydrate intake without necessarily reaching ketosis, commonly 50–130 g daily.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: low carbohydrate diet", "https://pubmed.ncbi.nlm.nih.gov/?term=low+carbohydrate+diet")
            ],
            template: ItemTemplate(
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["glucose", "hba1c", "triglycerides"]
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:carnivore",
            kind: .foodProtocol,
            title: "Carnivore / zero carb",
            summary: "Animal foods only, with carbohydrate intake close to zero. Fibre and micronutrient coverage are the open questions.",
            evidenceTier: .reference,
            officialLinks: [
                link("PubMed: carnivore diet", "https://pubmed.ncbi.nlm.nih.gov/?term=carnivore+diet")
            ],
            template: ItemTemplate(
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["ldl", "hdl", "triglycerides", "crp-hs", "vitamin-d-25oh"]
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:paleo",
            kind: .foodProtocol,
            title: "Paleo",
            summary: "Excludes grains, legumes, dairy and refined foods. Carbohydrate intake is unrestricted from whole-food sources.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: paleolithic diet", "https://pubmed.ncbi.nlm.nih.gov/?term=paleolithic+diet")
            ],
            template: ItemTemplate(typicalRecurrence: .daily)
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:vegan",
            kind: .foodProtocol,
            title: "Vegan",
            summary: "Excludes all animal products. B12 supplementation is required; iron, zinc, omega-3 and iodine warrant attention.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("NIH ODS: Vitamin B12", "https://ods.od.nih.gov/factsheets/VitaminB12-HealthProfessional/")
            ],
            template: ItemTemplate(
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["vitamin-b12", "ferritin", "vitamin-d-25oh"],
                usageNote: "B12 is not optional on a fully plant-based diet."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:vegetarian",
            kind: .foodProtocol,
            title: "Vegetarian",
            summary: "Excludes meat and fish while retaining dairy and eggs.",
            evidenceTier: .reference,
            officialLinks: [
                link("PubMed: vegetarian diet", "https://pubmed.ncbi.nlm.nih.gov/?term=vegetarian+diet")
            ],
            template: ItemTemplate(
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["vitamin-b12", "ferritin"]
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:mediterranean",
            kind: .foodProtocol,
            title: "Mediterranean",
            summary: "Pattern emphasising olive oil, fish, vegetables, legumes and whole grains. Among the best-evidenced dietary patterns.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: Mediterranean diet", "https://pubmed.ncbi.nlm.nih.gov/?term=mediterranean+diet")
            ],
            template: ItemTemplate(
                typicalRecurrence: .daily,
                suggestedLabAnalyteIds: ["ldl", "hdl", "triglycerides", "crp-hs"]
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:carb-cycling",
            kind: .foodProtocol,
            title: "Carb cycling",
            summary: "Carbohydrate intake varied across the week, commonly aligned to training days.",
            evidenceTier: .reference,
            officialLinks: [
                link("PubMed: carbohydrate periodisation", "https://pubmed.ncbi.nlm.nih.gov/?term=carbohydrate+periodization")
            ],
            template: ItemTemplate(
                typicalRecurrence: .daily,
                usageNote: "Record whether each day was high, low or refeed."
            )
        ),

        // MARK: Training

        LibraryCatalogEntry(
            id: "catalog:exercise:resistance-session",
            kind: .exercisePlan,
            title: "Resistance training session",
            summary: "A training day recorded at session level: body part or split, duration, and perceived effort.",
            evidenceTier: .reference,
            officialLinks: [
                link("ACSM: Guidelines for Exercise Testing and Prescription", "https://acsm.org/education-resources/books/guidelines-exercise-testing-prescription/")
            ],
            template: ItemTemplate(
                typicalRecurrence: .weekdays([1, 3, 5]),
                usageNote: "Schedule the split, for example Monday shoulders and triceps, heavy. One tap to log."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:cardio-zone2",
            kind: .exercisePlan,
            title: "Zone 2 cardio",
            summary: "Sustained low-intensity aerobic work, conversational pace, for aerobic base.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: zone 2 training", "https://pubmed.ncbi.nlm.nih.gov/?term=aerobic+base+training+intensity")
            ],
            template: ItemTemplate(
                typicalRecurrence: .weekdays([2, 6]),
                usageNote: "Record duration and average heart rate."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:hiit",
            kind: .exercisePlan,
            title: "HIIT session",
            summary: "High-intensity intervals. Recorded by session duration and effort rather than by interval structure.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: high intensity interval training", "https://pubmed.ncbi.nlm.nih.gov/?term=high+intensity+interval+training")
            ],
            template: ItemTemplate(typicalRecurrence: .weekdays([2, 5]))
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:bodyweight",
            kind: .exercisePlan,
            title: "Bodyweight session",
            summary: "Resistance training using body mass alone. Recorded by session, not by exercise.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: bodyweight session", "https://pubmed.ncbi.nlm.nih.gov/?term=bodyweight+resistance+training")
            ],
            template: ItemTemplate(typicalRecurrence: .weekdays([1, 3, 5]))
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:calisthenics",
            kind: .exercisePlan,
            title: "Calisthenics",
            summary: "Skill-based bodyweight training. Recorded by session duration and effort.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: calisthenics", "https://pubmed.ncbi.nlm.nih.gov/?term=calisthenics")
            ]
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:running",
            kind: .exercisePlan,
            title: "Running",
            summary: "Recorded by distance, duration and effort. Pace belongs in the note, not the schedule.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: running", "https://pubmed.ncbi.nlm.nih.gov/?term=running+exercise+health")
            ],
            template: ItemTemplate(typicalRecurrence: .weekdays([2, 4, 6]))
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:cycling",
            kind: .exercisePlan,
            title: "Cycling",
            summary: "Indoor or outdoor. Recorded by duration and effort rather than route.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: cycling", "https://pubmed.ncbi.nlm.nih.gov/?term=cycling+exercise+health")
            ]
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:swimming",
            kind: .exercisePlan,
            title: "Swimming",
            summary: "Recorded by duration and effort. Stroke and distance belong in the note.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: swimming", "https://pubmed.ncbi.nlm.nih.gov/?term=swimming+exercise+health")
            ]
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:walking",
            kind: .exercisePlan,
            title: "Walking",
            summary: "Low-intensity steady movement, the most frequently logged and least often planned.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: walking", "https://pubmed.ncbi.nlm.nih.gov/?term=walking+exercise+health")
            ],
            template: ItemTemplate(typicalRecurrence: .daily)
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:rowing",
            kind: .exercisePlan,
            title: "Rowing",
            summary: "Machine or water. Full-body conditioning recorded by duration and effort.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: rowing", "https://pubmed.ncbi.nlm.nih.gov/?term=rowing+exercise+health")
            ]
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:hiking",
            kind: .exercisePlan,
            title: "Hiking",
            summary: "Extended low-intensity effort, usually irregular. Recorded by duration.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: hiking", "https://pubmed.ncbi.nlm.nih.gov/?term=hiking+exercise+health")
            ]
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:functional-fitness",
            kind: .exercisePlan,
            title: "Functional fitness",
            summary: "Mixed-modal conditioning. Recorded by session rather than by movement.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: functional fitness", "https://pubmed.ncbi.nlm.nih.gov/?term=functional+fitness+training")
            ]
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:martial-arts",
            kind: .exercisePlan,
            title: "Martial arts",
            summary: "Class or sparring. Recorded by session duration and effort.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: martial arts", "https://pubmed.ncbi.nlm.nih.gov/?term=martial+arts+training+health")
            ]
        ),

        // MARK: Recovery

        LibraryCatalogEntry(
            id: "catalog:recovery:sauna",
            kind: .recoveryPractice,
            title: "Sauna session",
            summary: "Heat exposure recorded by temperature, duration and session count.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: sauna bathing", "https://pubmed.ncbi.nlm.nih.gov/?term=sauna+bathing")
            ],
            template: ItemTemplate(
                typicalRecurrence: .weekdays([2, 5]),
                usageNote: "Record temperature and total time. Consistency matters more than any single session."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:cold-exposure",
            kind: .recoveryPractice,
            title: "Cold exposure",
            summary: "Cold water immersion or shower, recorded by temperature and duration.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: cold water immersion", "https://pubmed.ncbi.nlm.nih.gov/?term=cold+water+immersion")
            ],
            template: ItemTemplate(
                typicalRecurrence: .daily,
                usageNote: "Cold straight after resistance training may blunt hypertrophy. Timing is worth recording."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:red-light",
            kind: .recoveryPractice,
            title: "Red light therapy",
            summary: "Photobiomodulation. Wavelength, distance and duration determine the delivered dose.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: photobiomodulation", "https://pubmed.ncbi.nlm.nih.gov/?term=photobiomodulation")
            ],
            template: ItemTemplate(
                typicalRecurrence: .daily,
                usageNote: "Record wavelength and distance — dose depends on both."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:breathwork",
            kind: .recoveryPractice,
            title: "Breathwork",
            summary: "Structured breathing practice, recorded by protocol and duration.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("PubMed: breathwork", "https://pubmed.ncbi.nlm.nih.gov/?term=breathing+exercises+stress")
            ],
            template: ItemTemplate(typicalRecurrence: .daily)
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:meditation",
            kind: .recoveryPractice,
            title: "Meditation",
            summary: "Seated or guided practice — mindfulness, transcendental, loving-kindness, body scan or open awareness. Recorded by duration and style, since they are not interchangeable.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: mindfulness meditation", "https://pubmed.ncbi.nlm.nih.gov/?term=mindfulness+meditation")
            ],
            template: ItemTemplate(typicalRecurrence: .daily)
        ),

        LibraryCatalogEntry(
            id: "catalog:recovery:yoga",
            kind: .recoveryPractice,
            title: "Yoga",
            summary: "Movement and breath practice. Sits between training and recovery depending on the style, so log the intensity rather than assuming.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("NCCIH: yoga", "https://www.nccih.nih.gov/health/yoga-what-you-need-to-know"),
                link("PubMed: yoga", "https://pubmed.ncbi.nlm.nih.gov/?term=yoga+randomized+controlled+trial")
            ],
            template: ItemTemplate(typicalRecurrence: .weekdays([1, 3, 5]))
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:stretching",
            kind: .recoveryPractice,
            title: "Stretching / mobility",
            summary: "Targeted mobility work, usually short and frequent rather than long and occasional.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: stretching and range of motion", "https://pubmed.ncbi.nlm.nih.gov/?term=stretching+range+of+motion+meta-analysis")
            ],
            template: ItemTemplate(typicalRecurrence: .daily)
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:massage",
            kind: .recoveryPractice,
            title: "Massage / soft tissue work",
            summary: "Sports massage, foam rolling or manual therapy.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: massage and recovery", "https://pubmed.ncbi.nlm.nih.gov/?term=massage+muscle+recovery+meta-analysis")
            ],
            template: ItemTemplate()
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:nap",
            kind: .recoveryPractice,
            title: "Nap",
            summary: "Daytime sleep. Worth logging separately from night sleep — a long late nap explains a bad night that otherwise looks unprovoked.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: napping and alertness", "https://pubmed.ncbi.nlm.nih.gov/?term=napping+cognitive+performance")
            ],
            template: ItemTemplate()
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:sunlight",
            kind: .recoveryPractice,
            title: "Morning sunlight",
            summary: "Outdoor light exposure early in the day, for circadian timing.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: light exposure and circadian rhythm", "https://pubmed.ncbi.nlm.nih.gov/?term=morning+light+exposure+circadian")
            ],
            template: ItemTemplate(typicalRecurrence: .daily)
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:journaling",
            kind: .recoveryPractice,
            title: "Journaling",
            summary: "Written reflection. Distinct from the app's own check-in: this is the practice, the check-in is the measurement.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("PubMed: expressive writing", "https://pubmed.ncbi.nlm.nih.gov/?term=expressive+writing+health+outcomes")
            ],
            template: ItemTemplate(typicalRecurrence: .daily)
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:float-tank",
            kind: .recoveryPractice,
            title: "Float tank",
            summary: "Sensory reduction in a flotation tank.",
            evidenceTier: .clinicalStudy,
            uncertainty: "Small trials, mostly on anxiety and stress. Not a well-replicated literature.",
            officialLinks: [
                link("PubMed: flotation REST", "https://pubmed.ncbi.nlm.nih.gov/?term=flotation+REST+anxiety")
            ],
            template: ItemTemplate()
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:compression",
            kind: .recoveryPractice,
            title: "Compression / pneumatic boots",
            summary: "Intermittent pneumatic compression for perceived recovery.",
            evidenceTier: .systematicReview,
            uncertainty: "Consistently improves perceived soreness; effects on actual performance recovery are much weaker.",
            officialLinks: [
                link("PubMed: intermittent pneumatic compression recovery", "https://pubmed.ncbi.nlm.nih.gov/?term=intermittent+pneumatic+compression+recovery")
            ],
            template: ItemTemplate()
        ),

        // MARK: Context and labs

        LibraryCatalogEntry(
            id: "catalog:context:routine",
            kind: .context,
            title: "Context or routine",
            summary: "Records situational context — travel, illness, high stress, a diet change — as timing information rather than a causal claim.",
            evidenceTier: .reference,
            officialLinks: [
                link("CDC: Healthy living", "https://www.cdc.gov/healthy-living/about/index.html")
            ],
            template: ItemTemplate(
                usageNote: "Useful for explaining why a stretch of data looks unusual in hindsight."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:lab-marker:panel",
            kind: .labMarker,
            title: "Blood panel",
            summary: "Records lab-provided values with units, reference ranges and collection context. No interpretation is applied.",
            evidenceTier: .reference,
            officialLinks: [
                link("MedlinePlus: Understanding laboratory tests", "https://medlineplus.gov/lab-tests/")
            ],
            template: ItemTemplate(
                typicalRecurrence: .everyNDays(90),
                suggestedLabAnalyteIds: [
                    "testosterone-total", "estradiol", "shbg", "haematocrit",
                    "alt", "ast", "ldl", "hdl", "triglycerides", "glucose", "hba1c"
                ],
                usageNote: "Collection time matters for testosterone and cortisol. Record whether you were fasted."
            )
        ),

        // MARK: Peptides, hormones, AAS and medications (compound-name research, no vendor pricing or contact data)

        LibraryCatalogEntry(
            id: "catalog:hormone:oxandrolone",
            kind: .medicationHormone,
            title: "Oxandrolone (Anavar)",
            summary: "An anabolic steroid FDA-approved for protein catabolism secondary to corticosteroids and osteoporosis-related bone pain.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("Label: OXANDROLONE tablet - DailyMed", "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=a6f42739-5bfc-4b76-8795-e93fa58f3d29"),
                link("StatPearls - Oxandrolone", "https://www.ncbi.nlm.nih.gov/books/NBK557608/")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 9.4, toHours: 10.4, source: "Miller & Btaiche 2009, Pharmacotherapy 29(2):213-226, PMID 19170590"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:stanozolol",
            kind: .medicationHormone,
            title: "Stanozolol (Winstrol)",
            summary: "A synthetic anabolic steroid that was FDA-approved for hereditary angioedema but is now discontinued.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("Drugs@FDA: Winstrol (stanozolol) NDA 012885", "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo=012885"),
                link("NCATS Inxight Drugs — Stanozolol", "https://drugs.ncats.io/drug/4R1VB9P8V3"),
                link("Winstrol (Stanozolol) for Hereditary Angioedema", "https://angioedemanews.com/winstrol-hereditary-angioedema-therapy-prevents-swelling-flare-ups/")
            ],
            template: ItemTemplate(
                halfLife: .hours(9, source: "Ruiz & Strain (eds.), Lowinson and Ruiz's Substance Abuse (2011), p.358 — oral tablet; the IM aqueous suspension form runs closer to 24 h"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:boldenone-undecylenate",
            kind: .medicationHormone,
            title: "Boldenone Undecylenate (Equipoise)",
            summary: "An anabolic steroid developed for veterinary use that was never FDA-approved for human medicine.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("Boldenone Undecylenate - Wikipedia", "https://en.wikipedia.org/wiki/Boldenone_undecylenate"),
                link("Boldenone - ScienceDirect Overview", "https://www.sciencedirect.com/topics/pharmacology-toxicology-and-pharmaceutical-science/boldenone")
            ],
            template: ItemTemplate(
                halfLife: .days(14, source: "Westreich, in Ruiz & Strain, Lowinson and Ruiz's Substance Abuse (2011), p.358 — compiled reference, no controlled human PK trial; boldenone is primarily a veterinary compound"),
                route: .intramuscular,
                dosageForm: .solution
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:drostanolone",
            kind: .medicationHormone,
            title: "Drostanolone (Masteron)",
            summary: "An anabolic steroid approved for palliative treatment of advanced breast cancer in postmenopausal women.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("Drugs@FDA: Drolban (drostanolone) NDA 012936", "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo=012936"),
                link("Drostanolone - Wikipedia", "https://en.wikipedia.org/wiki/Drostanolone"),
                link("Drostanolone Propionate - DrugBank", "https://go.drugbank.com/drugs/DB14655")
            ],
            template: ItemTemplate(
                halfLife: .days(2, source: "Llewellyn, Anabolics (Molecular Nutrition LLC, 2011), p.517 — compiled pharmacology reference; historically used clinically as Drolban/Masteril, no modern dedicated PK trial"),
                route: .intramuscular,
                dosageForm: .solution
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:trenbolone",
            kind: .medicationHormone,
            title: "Trenbolone",
            summary: "A synthetic anabolic steroid with no approved human indication and extensive reports of severe adverse effects.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("Adverse Effects of Trenbolone - ResearchGate", "https://www.researchgate.net/publication/390366632_ADVERSE_EFFECTS_OF_TRENBOLONE_A_STRUCTURED_REVIEW_OF_CASE_REPORTS_IN_HUMANS"),
                link("Trenbolone and Psychological Distress - ScienceDirect", "https://www.sciencedirect.com/science/article/pii/S0955395924003207")
            ],
            template: ItemTemplate(
                halfLife: .days(3, source: "Ruiz & Strain (eds.), Lowinson and Ruiz's Substance Abuse (2011), p.358 — compiled reference, no human clinical PK trial; a veterinary/livestock compound (as Finaplix)"),
                route: .intramuscular,
                dosageForm: .solution
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:methandienone",
            kind: .medicationHormone,
            title: "Methandienone (Dianabol)",
            summary: "An anabolic steroid whose FDA approval was revoked in 1985 and is no longer approved for human use.",
            evidenceTier: .reference,
            officialLinks: [
                link("NCATS Inxight Drugs — Methandrostenolone", "https://drugs.ncats.io/drug/COZ1R7EOCC"),
                link("Metandienone - Wikipedia", "https://en.wikipedia.org/wiki/Metandienone")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 3, toHours: 6, source: "Llewellyn, Anabolics (2011); Ruiz & Strain, Lowinson and Ruiz's Substance Abuse (2011), p.358 — compiled pharmacology references"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:oxymetholone",
            kind: .medicationHormone,
            title: "Oxymetholone (Anadrol)",
            summary: "An FDA-approved anabolic steroid used to treat anemias caused by deficient red-cell production.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("ANADROL-50 (oxymetholone) Label - FDA", "https://www.accessdata.fda.gov/drugsatfda_docs/label/2004/16848s021lbl.pdf"),
                link("Review of Oxymetholone - PubMed", "https://pubmed.ncbi.nlm.nih.gov/11440282/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:mesterolone",
            kind: .medicationHormone,
            title: "Mesterolone (Proviron)",
            summary: "An anabolic steroid used clinically to treat male hypogonadism and low testosterone.",
            evidenceTier: .reference,
            officialLinks: [
                link("Mesterolone - DrugBank", "https://go.drugbank.com/drugs/DB13587"),
                link("Mesterolone on Cardiac Remodelling - PubMed Central", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2613982/")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 12, toHours: 13, source: "DrugBank clinical-pharmacology monograph"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:methenolone",
            kind: .medicationHormone,
            title: "Methenolone (Primobolan)",
            summary: "An anabolic steroid with limited clinical use and documented risks of androgenic and hepatic toxicity.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("Studies on Anabolic Steroids—Methenolone Acetate Metabolites - PubMed", "https://pubmed.ncbi.nlm.nih.gov/2242348/"),
                link("Methenolone (PIM 907) - INCHEM", "https://www.inchem.org/documents/pims/pharm/pim907.htm")
            ],
            template: ItemTemplate(
                halfLife: .days(10.5, source: "Westreich, in Ruiz & Strain, Lowinson and Ruiz's Substance Abuse (2011), p.358 — enanthate ester (Primobolan Depot)"),
                route: .intramuscular,
                dosageForm: .solution
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:turinabol",
            kind: .medicationHormone,
            title: "Turinabol (Chlorodehydromethyltestosterone)",
            summary: "An anabolic steroid with historical use in East German doping programs and no modern approved indication.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("Controlled Administration of Dehydrochloromethyltestosterone - bioRxiv", "https://www.biorxiv.org/content/10.1101/2021.08.02.454719.full.pdf"),
                link("Chlorodehydromethyltestosterone - Wikipedia", "https://en.wikipedia.org/wiki/Chlorodehydromethyltestosterone")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:trestolone",
            kind: .medicationHormone,
            title: "Trestolone (MENT)",
            summary: "A research compound investigated for male contraception that never received FDA approval.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("Investigations Into Human Metabolism of Trestolone - PubMed Central", "https://pmc.ncbi.nlm.nih.gov/articles/PMC12983052/"),
                link("Trestolone - Wikipedia", "https://en.wikipedia.org/wiki/Trestolone")
            ],
            template: ItemTemplate(
                route: .subcutaneous,
                dosageForm: .solution
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:gonadorelin",
            kind: .peptide,
            title: "Gonadorelin",
            summary: "A GnRH peptide that was FDA-approved for diagnostic pituitary testing but is no longer commercially available.",
            evidenceTier: .reference,
            officialLinks: [
                link("Gonadorelin: GnRH Peptide Overview - Superpower", "https://superpower.com/guides/gonadorelin"),
                link("Gonadorelin Peptide - Peptides Institute", "https://www.peptidesinstitute.org/peptides/gonadorelin")
            ],
            template: ItemTemplate(
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 2,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:clomiphene-citrate",
            kind: .medicationHormone,
            title: "Clomiphene Citrate",
            summary: "An FDA-approved selective estrogen receptor modulator used to induce ovulation in women with infertility.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("Clomid (clomiphene citrate) Label - FDA", "https://www.accessdata.fda.gov/drugsatfda_docs/label/2012/016131s026lbl.pdf"),
                link("Clomiphene - StatPearls", "https://www.ncbi.nlm.nih.gov/books/NBK559292/"),
                link("Clomiphene citrate at 50: the dawning of assisted reproduction", "https://www.fertstert.org/article/S0015-0282(17)31697-7/fulltext")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .tablet,
                usageNote: "No half-life is shown: clomiphene citrate is a mixture of two isomers (enclomiphene and zuclomiphene) with very different clearance, and no single reliable figure covers both. Zuclomiphene is detectable for over a month; enclomiphene clears much faster."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:enclomiphene",
            kind: .medicationHormone,
            title: "Enclomiphene",
            summary: "The active isomer of clomiphene with potential for raising testosterone while preserving fertility, but not FDA-approved.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("Clomiphene or Enclomiphene for Male Hypogonadism - PubMed Central", "https://pmc.ncbi.nlm.nih.gov/articles/PMC12510335/"),
                link("Enclomiphene and Fertility - Good Health by Hims", "https://www.hims.com/blog/enclomiphene-and-fertility"),
                link("Efficacy of Clomiphene Citrate Versus Enclomiphene Citrate - PubMed Central", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10404117/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .tablet,
                usageNote: "No half-life is shown: it was never FDA-approved as a standalone product, so no label figure exists, and the published pharmacodynamic studies report clinical persistence rather than a stated elimination half-life."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:letrozole",
            kind: .medicationHormone,
            title: "Letrozole",
            summary: "An FDA-approved aromatase inhibitor used to treat hormone receptor-positive breast cancer.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: letrozole", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=letrozole"),
                link("FDA Approves Femara as First-Line Therapy", "https://www.cancernetwork.com/view/fda-approves-femara-first-line-therapy"),
                link("Letrozole in Breast Cancer Treatment - PubMed", "https://pubmed.ncbi.nlm.nih.gov/11895893/")
            ],
            template: ItemTemplate(
                halfLife: .days(2, source: "FDA label, Femara: terminal elimination half-life about 2 days"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:tamoxifen",
            kind: .medicationHormone,
            title: "Tamoxifen",
            summary: "An FDA-approved selective estrogen receptor modulator used to treat hormone receptor-positive breast cancer.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: tamoxifen", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=tamoxifen"),
                link("Use of SERMs for Adjuvant Therapy - Johns Hopkins University", "https://pure.johnshopkins.edu/en/publications/use-of-serms-for-the-adjuvant-therapy-of-early-stage-breast-cance-6/"),
                link("Tamoxifen - StatPearls", "https://www.ncbi.nlm.nih.gov/books/NBK532905/"),
                link("Treating ER-positive breast cancer: SERMs and SERDs review", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12018393/")
            ],
            template: ItemTemplate(
                halfLife: .range(fromDays: 5, toDays: 7, source: "FDA label, tamoxifen citrate: terminal elimination half-life 5 to 7 days"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:exemestane",
            kind: .medicationHormone,
            title: "Exemestane",
            summary: "An FDA-approved steroidal aromatase inhibitor used to treat hormone receptor-positive breast cancer.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: exemestane", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=exemestane"),
                link("Exemestane Hormonal Therapy - LBBC", "https://www.lbbc.org/about-breast-cancer/treatments/hormonal-therapy/aromatase-inhibitors/exemestane"),
                link("Endocrinological Evaluation of Exemestane - PubMed Central", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2034036/")
            ],
            template: ItemTemplate(
                halfLife: .hours(24, source: "FDA label, Aromasin: mean terminal half-life about 24 hours"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:cabergoline",
            kind: .medicationHormone,
            title: "Cabergoline",
            summary: "An FDA-approved dopamine agonist used to treat hyperprolactinemic disorders.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DOSTINEX (cabergoline) Label - FDA", "https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/020664s016lbl.pdf"),
                link("Cabergoline - Drugs.com Monograph", "https://www.drugs.com/monograph/cabergoline.html")
            ],
            template: ItemTemplate(
                halfLife: .hours(66, source: "FDA label, Dostinex: elimination half-life estimated from urinary data, 63 to 69 hours (midpoint shown — the range rounds to the same day count)"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:finasteride",
            kind: .medicationHormone,
            title: "Finasteride",
            summary: "An FDA-approved 5-alpha reductase inhibitor used to treat benign prostatic hyperplasia.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("PROSCAR (finasteride) Label - FDA", "https://www.accessdata.fda.gov/drugsatfda_docs/label/2021/020180s049lbl.pdf"),
                link("Finasteride - Drugs.com", "https://www.drugs.com/finasteride.html")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 3, toHours: 16, source: "FDA label, Proscar: single-dose half-life 3-16 hours in men 45-60y (6-15h in men over 70y)"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:dutasteride",
            kind: .medicationHormone,
            title: "Dutasteride",
            summary: "An FDA-approved 5-alpha reductase inhibitor for benign prostatic hyperplasia, used off-label for hair loss.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: dutasteride", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=dutasteride"),
                link("Dutasteride (Avodart) - American Hair Loss Association", "https://www.americanhairloss.org/hair-loss-treatment/drug-therapy/dutasteride-avodart/"),
                link("Avodart Regulatory Status Global - HealthRX", "https://healthrx.com/dutasteride/regulatory-status-global")
            ],
            template: ItemTemplate(
                halfLife: .days(35, source: "FDA label, Avodart: terminal half-life about 5 weeks at steady state with daily dosing (single-dose values range 170-300 h depending on age)"),
                route: .oral,
                dosageForm: .softgel
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:sildenafil",
            kind: .medicationHormone,
            title: "Sildenafil",
            summary: "An FDA-approved phosphodiesterase-5 inhibitor used to treat erectile dysfunction and pulmonary arterial hypertension.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("Label: SILDENAFIL CITRATE tablet - DailyMed", "https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=49a95b25-08b3-4cfe-a60b-c5132c280be2"),
                link("Sildenafil - StatPearls", "https://www.ncbi.nlm.nih.gov/books/NBK558978/"),
                link("FDA Approves Impotence Pill, Viagra - ScienceDaily", "https://www.sciencedaily.com/releases/1998/04/980401074901.htm")
            ],
            template: ItemTemplate(
                halfLife: .hours(4, source: "FDA label, Viagra: parent and active N-desmethyl metabolite half-life about 4 hours"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:tadalafil",
            kind: .medicationHormone,
            title: "Tadalafil",
            summary: "An FDA-approved phosphodiesterase-5 inhibitor used to treat erectile dysfunction, benign prostatic hyperplasia, and pulmonary hypertension.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("CIALIS (tadalafil) Label - FDA", "https://www.accessdata.fda.gov/drugsatfda_docs/label/2011/021368s20s21lbl.pdf"),
                link("Tadalafil - StatPearls", "https://www.ncbi.nlm.nih.gov/books/NBK603743/")
            ],
            template: ItemTemplate(
                halfLife: .hours(17.5, source: "FDA label, Cialis: mean terminal half-life 17.5 hours"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:lgd-4033",
            kind: .medicationHormone,
            title: "LGD-4033 (Ligandrol)",
            summary: "A selective androgen receptor modulator investigated in clinical trials but not FDA-approved for human use.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("Basaria et al. 2013, J Gerontol A Biol Sci Med Sci - PubMed", "https://pubmed.ncbi.nlm.nih.gov/22459616/"),
                link("LGD-4033 SARM Research - Ligand Pharmaceuticals", "https://investor.ligand.com/news-and-events/press-releases/news-details/2009/Ligand-Initiates-Clinical-Trial-with-the-Selective-Androgen-Receptor-Modulator-LGD-4033-a-Potential-Treatment-of-Muscle-and-Bone-Disorders-06-17-2009/default.aspx"),
                link("LGD-4033 - Wikipedia", "https://en.wikipedia.org/wiki/LGD-4033")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 24, toHours: 36, source: "Basaria et al. 2013, J Gerontol A Biol Sci Med Sci 68(1):87-95, PMID 22459616 — Phase 1 human PK trial"),
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:rad140",
            kind: .medicationHormone,
            title: "RAD140 (Testolone)",
            summary: "A selective androgen receptor modulator with preclinical promise but limited human data and reported serious adverse effects.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("Preclinical Assessment of RAD140 - PubMed Central", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12274021/"),
                link("Human In Vivo Metabolism of RAD140 - PubMed Central", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9325264/")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 45, toHours: 60, source: "LoRusso et al. 2022, Clin Breast Cancer 22(1):67-77, PMID 34565686 — Phase 1 human PK trial"),
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:mk-2866",
            kind: .medicationHormone,
            title: "MK-2866 (Ostarine)",
            summary: "A selective androgen receptor modulator tested in over 1,700 subjects that failed FDA approval for muscle wasting.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("Ostarine (MK-2866) Clinical Trials - MorePlatesMoreDates", "https://moreplatesmoredates.com/ostarine-results/"),
                link("Enobosarm - Wikipedia", "https://en.wikipedia.org/wiki/Enobosarm")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 14, toHours: 24, source: "Human clinical PK data (Dalton JT group trials; Jones et al. 2013 metabolite study, PMID 27105861) — most rigorously human-studied SARM on this list"),
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:andarine",
            kind: .medicationHormone,
            title: "Andarine (S4)",
            summary: "A selective androgen receptor modulator whose development was abandoned due to vision side effects.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("S4 (Andarine) SARM - MorePlatesMoreDates", "https://moreplatesmoredates.com/andarine-s4/"),
                link("Selective Androgen Receptor Modulator for Prostate - ClinicalTrials.gov", "https://cdn.clinicaltrials.gov/large-docs/97/NCT02499497/Prot_SAP_000.pdf")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 3, toHours: 6, source: "Gao, Kim & Dalton 2006, Pharm Res 23(8):1641-1658, PMID 16841196 — rats and dogs only, no human PK trial exists"),
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:gw-501516",
            kind: .medicationHormone,
            title: "GW-501516 (Cardarine)",
            summary: "A peroxisome proliferator-activated receptor agonist that was never approved for human use.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("GW501516 - DrugBank", "https://go.drugbank.com/drugs/DB05416"),
                link("Metabolomic Study of GW501516 - PubMed Central", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4421799/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:yk-11",
            kind: .medicationHormone,
            title: "YK-11",
            summary: "An experimental selective androgen receptor modulator with myostatin-inhibiting properties and documented neurological risks.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("YK11 Hippocampal Function - PubMed Central", "https://pubmed.ncbi.nlm.nih.gov/38521455/"),
                link("YK-11 and Myostatin Inhibition - ChemicalBook", "https://www.chemicalbook.com/article/side-effects-of-yk-11.htm")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:sr9009",
            kind: .medicationHormone,
            title: "SR9009 (Stenabolic)",
            summary: "A REV-ERB agonist research compound with significant off-target effects that is not FDA-approved.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("SR9009 REV-ERB Agonist - MedKoo", "https://www.medkoo.com/products/14012"),
                link("In Vitro Metabolic Studies of SR9009 - PubMed Central", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5085709/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:mk-677",
            kind: .medicationHormone,
            title: "MK-677 (Ibutamoren)",
            summary: "A growth hormone secretagogue that was investigated for various conditions but never received FDA approval.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("MK-677 Metabolism in Human Urine - Journal of Analytical Chemistry", "https://link.springer.com/article/10.1134/S1061934824020072"),
                link("MK-677 in Alzheimer Disease - PubMed", "https://pubmed.ncbi.nlm.nih.gov/19015485/"),
                link("Effects of Oral GH Secretagogue on Body Composition - ClinicalTrials.gov", "https://clinicaltrials.gov/study/NCT00474279")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 4, toHours: 6, source: "Chapman et al. 1996, J Clin Endocrinol Metab 81(12):4249-4257, PMID 8954023; Copinschi et al. 1996, J Clin Endocrinol Metab 81(8):2776-2782, PMID 8768828 — human clinical PK trials"),
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:cerebrolysin",
            kind: .peptide,
            title: "Cerebrolysin",
            summary: "A peptide extract from porcine brain studied for neurological recovery in stroke and Alzheimer's disease.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Safety and efficacy of Cerebrolysin in early post-stroke recovery: a meta-analysis of nine randomized clinical trials", "https://pubmed.ncbi.nlm.nih.gov/29248999/"),
                link("Safety and Efficacy of Cerebrolysin for Neurorecovery After Acute Ischemic Stroke: A Systematic Review and Meta-Analysis of 14 Randomized Controlled Trials", "https://pubmed.ncbi.nlm.nih.gov/41018475/"),
                link("Efficacy and safety of Cerebrolysin in moderate to moderately severe Alzheimer's disease: results of a randomized, double-blind, controlled trial investigating three dosages of Cerebrolysin", "https://pubmed.ncbi.nlm.nih.gov/20500802/")
            ],
            template: ItemTemplate(
                route: .intramuscular,
                dosageForm: .solution
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:vip",
            kind: .peptide,
            title: "Vasoactive Intestinal Peptide (VIP)",
            summary: "An endogenous neuropeptide with vasodilatory and anti-inflammatory properties studied only in preclinical models.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("Prospect of vasoactive intestinal peptide therapy for COPD/PAH and asthma: a review", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3090995/"),
                link("Therapeutic potential of vasoactive intestinal peptide and its receptors in neurological disorders", "https://pubmed.ncbi.nlm.nih.gov/20632962/"),
                link("Structure-activity relationship of vasoactive intestinal peptide (VIP): potent agonists and potential clinical applications", "https://pubmed.ncbi.nlm.nih.gov/18172612/")
            ],
            template: ItemTemplate(
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:thymalin",
            kind: .peptide,
            title: "Thymalin",
            summary: "A thymic peptide extract used in Eastern Europe for immune dysfunction, with limited evidence outside Russian clinical practice.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Peptide Drug Thymalin Regulates Immune Status in Severe COVID-19 Older Patients", "https://link.springer.com/article/10.1134/S2079057021040068"),
                link("A nonrandomized phase 2 trial of oral thymic peptides in hospitalized patients with Covid-19", "https://www.medrxiv.org/content/10.1101/2021.12.05.21267318.full.pdf"),
                link("Thymalfasin therapy accelerates COVID-19 pneumonia rehabilitation through anti-inflammatory mechanisms", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10518946/")
            ],
            template: ItemTemplate(
                route: .intramuscular,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 10,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:humanin",
            kind: .peptide,
            title: "Humanin",
            summary: "A mitochondrial peptide associated with longevity in centenarians, studied only in cell and animal models.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("Humanin and Its Pathophysiological Roles in Aging: A Systematic Review", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10135985/"),
                link("IGF-I regulates the age-dependent signaling peptide humanin", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4172517/"),
                link("Humanin and Humanin Analogs", "https://www.alzdiscovery.org/uploads/cognitive_vitality_media/Humanin-and-humanin-analogs.pdf")
            ],
            template: ItemTemplate(
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:teriparatide",
            kind: .medicationHormone,
            title: "Teriparatide",
            summary: "An FDA-approved recombinant parathyroid hormone used for osteoporosis to stimulate bone formation.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: teriparatide", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=teriparatide"),
                link("FDA approved new indication for teriparatide to treat osteoporosis", "https://www.healio.com/news/endocrinology/20120331/fda-approved-new-indication-for-teriparatide-to-treat-osteoporosis"),
                link("Indications and adverse events of teriparatide: based on FDA adverse event reporting system (FAERS)", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11335658/"),
                link("Teriparatide - StatPearls", "https://www.ncbi.nlm.nih.gov/books/NBK559248/")
            ],
            template: ItemTemplate(
                halfLife: .hours(1, source: "FDA label, Forteo: serum half-life about 1 hour"),
                route: .subcutaneous,
                dosageForm: .prefilledPen
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:oxytocin",
            kind: .medicationHormone,
            title: "Oxytocin",
            summary: "An endogenous neuropeptide available as intranasal spray, studied in clinical trials for psychiatric and behavioral conditions with mixed results.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("A Double-Blind Randomized Controlled Trial of Oxytocin Nasal Spray and Social Cognition Training for Young People With Early Psychosis", "https://pmc.ncbi.nlm.nih.gov/articles/PMC4332939/"),
                link("The effect of oxytocin nasal spray on social interaction in young children with autism: a randomized clinical trial", "https://www.nature.com/articles/s41380-022-01845-8"),
                link("Intranasal oxytocin", "https://www.alzforum.org/therapeutics/intranasal-oxytocin")
            ],
            template: ItemTemplate(
                route: .intranasal,
                dosageForm: .spray,
                usageNote: "No half-life is shown: intranasal oxytocin has no FDA-approved label and the literature disputes whether it even reaches the brain in a way that a plasma half-life would describe. The injectable form (IV/IM/SC) clears in minutes, but that figure does not apply to this route."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:aicar",
            kind: .supplement,
            title: "AICAR",
            summary: "A naturally produced AMPK activator with limited clinical use due to poor oral bioavailability and requirement for intravenous administration.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("What Athletes Should Know About AICAR and Others", "https://www.usada.org/spirit-of-sport/aicar-and-other-prohibited-amp-activated-protein-kinase-activators/"),
                link("AICAr, a Widely Used AMPK Activator with Important AMPK-Independent Effects: A Systematic Review", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8147799/"),
                link("AICAR inhibits NFκB DNA binding independently of AMPK to attenuate LPS-triggered inflammatory responses in human macrophages", "https://www.nature.com/articles/s41598-018-26102-3")
            ],
            template: ItemTemplate(
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 500,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated,
                usageNote: "No half-life is shown: the one human IV study found (Sabina et al. 1985, PMID 4054274) reports intact acadesine as only briefly detectable (roughly 2 hours, no exact figure given) against a slower ~1-week clearance of total radiolabeled material — the two numbers describe different things, and neither is a clean single half-life for the compound."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:5-amino-1mq",
            kind: .supplement,
            title: "5-Amino-1MQ",
            summary: "An experimental NNMT inhibitor showing weight loss effects in mice, with no completed human trials.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("5-Amino-1MQ: NNMT Inhibitor Research — Superpower", "https://superpower.com/guides/peptides/5-amino-1mq"),
                link("Quinoline derived small molecule inhibitors of nicotinamide N-methyltransferase (NNMT) and uses thereof", "https://image-ppubs.julius.com/dirsearch-public/print/downloadPdf/12071409"),
                link("5-Amino-1MQ Human Clinical Trial: What the Evidence Actually Shows", "https://formblends.com/articles/peptide-hub/directory-5-amino-1mq-human-clinical-trial")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                usageNote: "No half-life is shown: there are no completed human trials, so no human pharmacokinetic data exists at all."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:adipotide",
            kind: .peptide,
            title: "Adipotide (FTPP)",
            summary: "A targeted peptide that showed weight loss in animal models but development was halted due to kidney toxicity in human trials.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("Adipotide (FTPP): Research, Safety, and Status — Superpower", "https://superpower.com/guides/peptides/adipotide"),
                link("Prohibitin-targeting peptide 1", "https://en.wikipedia.org/wiki/Prohibitin-targeting_peptide_1"),
                link("Phase 1 trial of ADI-PEG 20 and liposomal doxorubicin in patients with metastatic solid tumors", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8729058/")
            ],
            template: ItemTemplate(
                route: .subcutaneous,
                dosageForm: .lyophilisedPowder,
                vialContentsValue: 5,
                vialContentsUnit: .milligram,
                typicalDiluentMillilitres: 2,
                storageCondition: .refrigerated
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:peptide:dihexa",
            kind: .peptide,
            title: "Dihexa",
            summary: "A neuropeptide showing regenerative effects in animal models of Alzheimer's and neurological injury, with no human trials.",
            evidenceTier: .preclinical,
            officialLinks: [
                link("Dihexa", "https://www.alzdiscovery.org/uploads/cognitive_vitality_media/Dihexa_1.pdf"),
                link("Dihexa Peptide: Unlocking Brain Repair, Focus, and Memory", "https://revolutionhealth.org/blogs/news/peptide-therapy-dihexa"),
                link("Hepatocyte growth factor mimics as therapeutic agents", "https://image-ppubs.julius.com/dirsearch-public/print/downloadPdf/9051351")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:aniracetam",
            kind: .supplement,
            title: "Aniracetam",
            summary: "A nootropic compound showing cognitive improvements in Alzheimer's disease trials but not in healthy individuals.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Clinical Efficacy of Aniracetam, Either as Monotherapy or Combined with Cholinesterase Inhibitors, in Patients with Cognitive Impairment: A Comparative Open Study", "https://pubmed.ncbi.nlm.nih.gov/22070796/"),
                link("Aniracetam Does Not Alter Cognitive and Affective Behavior in Adult C57BL/6J Mice", "https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0104443"),
                link("Aniracetam | Drugs & Aging", "https://link.springer.com/article/10.2165/00002512-199404030-00007")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                usageNote: "No half-life is shown: the retrieved human and animal studies report cognitive outcomes, not pharmacokinetic clearance, and no reliable elimination half-life for aniracetam could be found."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:tesofensine",
            kind: .medicationHormone,
            title: "Tesofensine",
            summary: "A neurotransmitter reuptake inhibitor showing significant weight loss in Phase II and III trials.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Effect of tesofensine on bodyweight loss, body composition, and quality of life in obese patients: a randomised, double-blind, placebo-controlled trial", "https://www.sciencedirect.com/science/article/abs/pii/S0140673608615251"),
                link("Tesofensine - Saniona", "https://saniona.com/pipeline/tesofensine/"),
                link("Tesofensine Anti-Obesity Medication - Clinical Trials Arena", "https://www.clinicaltrialsarena.com/projects/tesofensine/")
            ],
            template: ItemTemplate(
                halfLife: .hours(234, source: "Lehr et al. 2007, Br J Clin Pharmacol, PMID 17324246 — human PK study; active metabolite M1 half-life is even longer, about 374 hours"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:pentosan-polysulfate",
            kind: .medicationHormone,
            title: "Pentosan Polysulfate",
            summary: "An FDA-approved medication for interstitial cystitis that restores bladder protective layer, with risk of vision changes from long-term use.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: pentosan polysulfate", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=pentosan+polysulfate"),
                link("Pentosan Polysulfate: A Novel Therapy for the Mucopolysaccharidoses", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3554761/"),
                link("Post-marketing safety of pentosan polysulfate sodium: a 21-year pharmacovigilance analysis of the FAERS database", "https://pmc.ncbi.nlm.nih.gov/articles/PMC12872569/"),
                link("Pentosan polysulfate: a review of its use in the relief of bladder pain or discomfort in interstitial cystitis", "https://pubmed.ncbi.nlm.nih.gov/16706553/")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 20, toHours: 27, source: "FDA label, Elmiron: plasma radioactivity half-life about 20-27 hours across the 300/450 mg dose range (reflects total drug-related material, not necessarily unchanged parent)"),
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:methylene-blue",
            kind: .supplement,
            title: "Methylene Blue",
            summary: "A redox compound showing acute memory effects in healthy volunteers, but unclear benefit in dementia trials.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Methylene Blue Shows Promise for Improving Short-Term Memory", "https://www.rsna.org/media/press/i/1888"),
                link("Effects of Methylene Blue in Healthy Aging, Mild Cognitive Impairment and Alzheimer's Disease", "https://cdn.clinicaltrials.gov/large-docs/73/NCT02380573/Prot_SAP_000.pdf"),
                link("Clinical effectiveness and prospects of methylene blue", "https://www.pfmjournal.org/m/journal/view.php?number=132")
            ],
            template: ItemTemplate(
                halfLife: .hours(5.25, source: "Peter, Hongwan, Kupfer & Lauterburg 2000, Eur J Clin Pharmacol, PMID 11214785 — oral/IV crossover in healthy volunteers; the IV and oral arms gave consistent results, unusual for this compound's other pharmacokinetic parameters"),
                route: .oral,
                dosageForm: .solution,
                usageNote: "Not FDA-approved as a supplement; this is an off-label compounded use. MAOI interactions and serotonin syndrome risk apply."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:nad-plus",
            kind: .supplement,
            title: "NAD+ (Nicotinamide Adenine Dinucleotide)",
            summary: "A cellular cofactor with levels that decline with age; supplemental precursors and intravenous forms studied for aging-related benefits.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Intravenous infusion of nicotinamide adenine dinucleotide (NAD+) versus nicotinamide riboside (NR): a retrospective tolerability pilot study in a real-world setting", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12907335/"),
                link("Towards personalized nicotinamide mononucleotide (NMN) supplementation: nicotinamide adenine dinucleotide (NAD) concentration", "https://www.medrxiv.org/content/10.1101/2024.02.19.24303025.full.pdf"),
                link("Chronic nicotinamide mononucleotide supplementation elevates blood nicotinamide adenine dinucleotide levels and alters muscle function in healthy older men", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9158788/")
            ],
            template: ItemTemplate(
                route: .other,
                dosageForm: .solution,
                usageNote: "No half-life is shown: no human pharmacokinetic study for intact IV NAD+ was found — the retrieved studies measure downstream blood NAD levels over days, not the infused molecule's own clearance."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:minoxidil",
            kind: .medicationHormone,
            title: "Minoxidil",
            summary: "An FDA-approved topical medication for pattern hair loss that extends the hair growth phase and increases follicle size.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("DailyMed: minoxidil", "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query=minoxidil"),
                link("Male and Female Pattern Hair Loss: A Guide to Treatment", "https://consultqd.clevelandclinic.org/male-and-female-pattern-hair-loss-a-guide-to-treatment"),
                link("Minoxidil: a comprehensive review", "https://pubmed.ncbi.nlm.nih.gov/34159872/"),
                link("Minoxidil: Formulation, Dosage & Side-Effects", "https://ishrs.org/patients/treatments-for-hair-loss/medications/minoxidil/")
            ],
            template: ItemTemplate(
                route: .topical,
                dosageForm: .solution,
                usageNote: "No half-life is shown: this is the topical form, whose systemic absorption is minimal (about 1.4%), so the oral tablet's ~4.2-hour plasma half-life does not describe it and no dedicated topical PK figure exists."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:cagrilintide",
            kind: .medicationHormone,
            title: "Cagrilintide",
            summary: "An amylin analog combined with GLP-1 agonist showing substantial weight loss in Phase III trials, pending approval.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("REDEFINE 1 Trial Finds Cagrilintide–Semaglutide Combo Delivers Over 20% Weight Loss in Majority of Patients", "https://www.appliedclinicaltrialsonline.com/view/cagrilintide-semaglutide-weight-loss"),
                link("Once-weekly cagrilintide for weight management in people with overweight and obesity: a multicentre, randomised, double-blind, placebo-controlled and active-controlled, dose-finding phase 2 trial", "https://www.sciencedirect.com/science/article/abs/pii/S0140673621017517"),
                link("Cagrilintide lowers bodyweight through brain amylin receptors 1 and 3", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12270663/")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 159, toHours: 195, source: "Enebo et al. 2021, Lancet, PMID 33894838 — phase 1b trial, co-administered with semaglutide 2.4 mg"),
                route: .subcutaneous,
                dosageForm: .prefilledPen
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:liraglutide",
            kind: .medicationHormone,
            title: "Liraglutide",
            summary: "An FDA-approved GLP-1 receptor agonist for weight management in adults and adolescents, administered by once-daily injection.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("Label: VICTOZA (liraglutide) - DailyMed", "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=5a9ef4ea-c76a-4d34-a604-27c5b505f5a4"),
                link("FDA approves weight management drug for patients aged 12 and older", "https://www.fda.gov/drugs/news-events-human-drugs/fda-approves-weight-management-drug-patients-aged-12-and-older"),
                link("Saxenda (liraglutide) FDA Approval History", "https://www.drugs.com/history/saxenda.html"),
                link("Liraglutide for Type 2 diabetes and obesity: a 2015 update", "https://pubmed.ncbi.nlm.nih.gov/26106933/")
            ],
            template: ItemTemplate(
                halfLife: .hours(13, source: "FDA label, Victoza: elimination half-life approximately 13 hours"),
                route: .subcutaneous,
                dosageForm: .prefilledPen
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:survodutide",
            kind: .medicationHormone,
            title: "Survodutide",
            summary: "A dual glucagon and GLP-1 receptor agonist showing 16.6% weight loss in Phase III trials, pending regulatory approval.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Survodutide for treatment of obesity: Baseline characteristics of participants in a randomized, double-blind, placebo-controlled, phase 3 trial (SYNCHRONIZE™-1)", "https://pmc.ncbi.nlm.nih.gov/articles/PMC12673442/"),
                link("Glucagon and GLP-1 receptor dual agonist survodutide for obesity: a randomised, double-blind, placebo-controlled, dose-finding phase 2 trial", "https://pubmed.ncbi.nlm.nih.gov/38330987/"),
                link("Survodutide Once Weekly for the Treatment of Adults with Obesity", "https://www.nejm.org/doi/abs/10.1056/NEJMoa2600751")
            ],
            template: ItemTemplate(
                route: .subcutaneous,
                dosageForm: .solution,
                usageNote: "No half-life is shown: several human PK trials exist, but none of the retrievable published results state an explicit elimination half-life figure. Dosed once weekly."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:mazdutide",
            kind: .medicationHormone,
            title: "Mazdutide",
            summary: "A dual GLP-1/glucagon agonist approved in China for obesity and type 2 diabetes, showing over 20% weight loss in trials.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("With China approval, Lilly and Innovent's mazdutide breaks into new class for GLP-1 obesity drugs", "https://www.fiercepharma.com/pharma/china-approval-lilly-and-innovents-mazdutide-breaks-new-class-glp-1-obesity-drugs"),
                link("A phase 2 randomised controlled trial of mazdutide in Chinese overweight adults or adults with obesity", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10719339/"),
                link("Innovent Announces Mazdutide, First Dual GCG/GLP-1 Receptor Agonist, Received Approval from China's NMPA for Chronic Weight Management", "https://www.prnewswire.com/news-releases/innovent-announces-mazdutide-first-dual-gcgglp-1-receptor-agonist-received-approval-from-chinas-nmpa-for-chronic-weight-management-302493152.html")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 150.9, toHours: 403.5, source: "Ji et al. 2021, EClinicalMedicine, PMID 34430840 — phase 1b ascending-dose study, Chinese adults, range reflects the 3.0/4.5/6.0 mg dose cohorts"),
                route: .subcutaneous,
                dosageForm: .solution
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:orforglipron",
            kind: .medicationHormone,
            title: "Orforglipron",
            summary: "An oral small-molecule GLP-1 receptor agonist showing 10-11% weight loss in Phase III trials, pending regulatory approval in 2026.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Lilly's oral GLP-1, orforglipron, delivers weight loss of up to an average of 27.3 lbs in first of two pivotal Phase 3 trials in adults with obesity", "https://hfsa.org/lillys-oral-glp-1-orforglipron-delivers-weight-loss-average-273-lbs-first-two-pivotal-phase-3"),
                link("Lilly's oral GLP-1, orforglipron, is successful in third Phase 3 trial, triggering global regulatory submissions this year for the treatment of obesity", "https://investor.lilly.com/news-releases/news-release-details/lillys-oral-glp-1-orforglipron-successful-third-phase-3-trial"),
                link("Orforglipron, an oral small-molecule GLP-1 receptor agonist, for the treatment of obesity in people with type 2 diabetes (ATTAIN-2): a phase 3, double-blind, randomised, multicentre, placebo-controlled trial", "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(25)02165-8/abstract")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 51.8, toHours: 76.1, source: "Ohwaki et al. 2026, J Diabetes Investig, PMID 41325139 — phase 1 ascending-dose study in Japanese participants, week-12 mean terminal half-life"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        // MARK: Everyday supplements (B-70 item 1 — evidence and templates in scripts/evidence/evidence.json)
        LibraryCatalogEntry(
            id: "catalog:supplement:caffeine",
            kind: .supplement,
            title: "Caffeine",
            summary: "A widely studied stimulant taken for alertness and physical performance.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("A review of caffeine's effects on cognitive, physical and occupational performance - PubMed", "https://pubmed.ncbi.nlm.nih.gov/27612937/")
            ],
            template: ItemTemplate(
                halfLife: .hours(5, source: "Kaplan et al. 1997, J Clin Pharmacol, PMID 9378841; Bonati et al. 1982, Clin Pharmacol Ther, PMID 7083737 — adult reference value, nonlinear/dose-dependent, ranges 3.5-10.5h depending on smoking, pregnancy and CYP1A2 genotype"),
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:melatonin",
            kind: .supplement,
            title: "Melatonin",
            summary: "A circadian-clock hormone taken most often for jet lag and sleep timing.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Melatonin for preventing and treating jet lag - Cochrane Database of Systematic Reviews (PubMed)", "https://pubmed.ncbi.nlm.nih.gov/11279722/"),
                link("Melatonin: What You Need To Know - NCCIH", "https://www.nccih.nih.gov/health/melatonin-what-you-need-to-know")
            ],
            template: ItemTemplate(
                halfLife: .minutes(54, source: "Andersen et al. 2016, BMC Pharmacol Toxicol, PMID 26893170 — immediate-release oral, 10 mg dose; ranges 40-104 min depending on formulation and physiological state"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:l-theanine",
            kind: .supplement,
            title: "L-Theanine",
            summary: "A green-tea amino acid studied for stress and relaxation.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("The Effects of Green Tea Amino Acid L-Theanine Consumption on the Ability to Manage Stress and Anxiety Levels: a Systematic Review - PubMed", "https://pubmed.ncbi.nlm.nih.gov/31758301/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                usageNote: "No half-life is shown: the only published human study (Scheid et al. 2012, PMID 23096008) measured absorption/Tmax, not elimination — the commonly repeated \"60-90 min\" figure could not be traced to a primary source."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:nac",
            kind: .supplement,
            title: "N-Acetylcysteine (NAC)",
            summary: "An amino-acid derivative and glutathione precursor studied for exercise and antioxidant effects.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Performance and Side Effects of Supplementation with N-Acetylcysteine: A Systematic Review and Meta-Analysis - PubMed", "https://pubmed.ncbi.nlm.nih.gov/28102488/")
            ],
            template: ItemTemplate(
                halfLife: .hours(2.27, source: "Borgstrom et al. 1986, Eur J Clin Pharmacol, PMID 3803419 — oral/IV crossover; oral bioavailability only 6-10%. The FDA's IV label (Acetadote) quotes 5.6 hours over a longer total-acetylcysteine sampling window"),
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:curcumin",
            kind: .supplement,
            title: "Curcumin",
            summary: "The main active compound in turmeric, studied for inflammation and metabolic markers.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("The effect of curcumin supplementation on weight loss and anthropometric indices: an umbrella review and updated meta-analyses of randomized controlled trials - PubMed", "https://pubmed.ncbi.nlm.nih.gov/36898635/")
            ],
            template: ItemTemplate(
                halfLife: .hours(6.77, source: "Vareed et al. 2008, Cancer Epidemiol Biomarkers Prev, PMID 18559556 — total-conjugate model at very high (10-12 g) doses; free curcumin was undetectable in 11 of 12 subjects, reflecting its famously poor oral bioavailability"),
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:berberine",
            kind: .supplement,
            title: "Berberine",
            summary: "A plant alkaloid studied for blood sugar and lipid control in type 2 diabetes.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("The Effect of Berberine on Metabolic Profiles in Type 2 Diabetic Patients: A Systematic Review and Meta-Analysis of Randomized Controlled Trials - PubMed", "https://pubmed.ncbi.nlm.nih.gov/34956436/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                usageNote: "No half-life is shown: oral bioavailability is under 1%, and the resulting plasma levels are too low and variable for a reliable human half-life to have been calculated (Ai et al. 2021, PMID 35370628)."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:coenzyme-q10",
            kind: .supplement,
            title: "Coenzyme Q10",
            summary: "An antioxidant compound studied for heart failure and mitochondrial support.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("The Effect of Coenzyme Q10 on Morbidity and Mortality in Chronic Heart Failure: Results From Q-SYMBIO - PubMed", "https://pubmed.ncbi.nlm.nih.gov/25282031/"),
                link("Coenzyme Q10 - StatPearls - NCBI Bookshelf", "https://www.ncbi.nlm.nih.gov/books/NBK531491/")
            ],
            template: ItemTemplate(
                halfLife: .hours(30.2, source: "Mei et al. 2026, Clin Pharmacol Drug Dev, PMID 41789786 — single 240 mg oral dose, crossover; median 36.3h, range 6.8-52.6h, reflecting lipophilicity and enterohepatic recycling"),
                route: .oral,
                dosageForm: .softgel
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:beta-alanine",
            kind: .supplement,
            title: "Beta-Alanine",
            summary: "An amino acid studied for buffering fatigue during short, high-intensity exercise.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Effects of β-alanine supplementation on exercise performance: a meta-analysis - PubMed", "https://pubmed.ncbi.nlm.nih.gov/22270875/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .powder,
                usageNote: "No half-life is shown: no peer-reviewed human study has calculated an elimination rate constant. Plasma levels return to baseline within about 2 hours of oral dosing (Harris et al. 2006, PMID 16554972)."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:citrulline",
            kind: .supplement,
            title: "L-Citrulline",
            summary: "An amino acid studied for blood flow and exercise performance.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Effects of Citrulline Supplementation on Different Aerobic Exercise Performance Outcomes: A Systematic Review and Meta-Analysis - PubMed", "https://pubmed.ncbi.nlm.nih.gov/36079738/"),
                link("Citrulline: Research Breakdown - Examine", "https://examine.com/supplements/citrulline/research/")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 0.65, toHours: 1.14, source: "Moinard et al. 2008, Br J Nutr, PMID 17953788 — dose-dependent (2-15 g oral); citrulline converts to arginine, but the authors could not compute a reliable arginine half-life from the resulting decay curves"),
                route: .oral,
                dosageForm: .powder
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:l-carnitine",
            kind: .supplement,
            title: "L-Carnitine",
            summary: "An amino-acid derivative studied for body composition and exercise recovery.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Effects of l-carnitine supplementation on weight loss and body composition: A systematic review and meta-analysis - PubMed", "https://pubmed.ncbi.nlm.nih.gov/32359762/"),
                link("The Effect of L-Carnitine Supplementation on Exercise-Induced Muscle Damage: A Systematic Review and Meta-Analysis - PubMed", "https://pubmed.ncbi.nlm.nih.gov/32154768/"),
                link("L-Carnitine: Research Breakdown - Examine", "https://examine.com/supplements/carnitine/research/")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 3.9, toHours: 6.5, source: "Harper et al. 1988, Eur J Clin Pharmacol, PMID 3234464 — oral, dose-dependent (2-6 g). The FDA's IV label (Carnitor) quotes 17.4 hours, but that figure is uncorrected for endogenous carnitine background and reflects the IV route"),
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:alpha-gpc",
            kind: .supplement,
            title: "Alpha-GPC",
            summary: "A choline compound studied mainly in stroke and vascular-dementia recovery.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("alpha-Glycerophosphocholine in the mental recovery of cerebral ischemic attacks. An Italian multicenter clinical trial - PubMed", "https://pubmed.ncbi.nlm.nih.gov/8030842/"),
                link("A multicentre trial to evaluate the efficacy and tolerability of alpha-glycerylphosphorylcholine versus cytosine diphosphocholine in patients with vascular dementia - PubMed", "https://pubmed.ncbi.nlm.nih.gov/1916007/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                usageNote: "No half-life is shown: alpha-GPC is metabolized into choline and glycerophosphate, and no reliable elimination half-life for the parent compound was found."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:inositol",
            kind: .supplement,
            title: "Inositol",
            summary: "A sugar alcohol studied mainly for metabolic and reproductive outcomes in PCOS.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Inositol for Polycystic Ovary Syndrome: A Systematic Review and Meta-analysis to Inform the 2023 Update of the International Evidence-based PCOS Guidelines - PubMed", "https://pubmed.ncbi.nlm.nih.gov/38163998/"),
                link("Inositol: Benefits, Dosage, and Side Effects - Examine", "https://examine.com/supplements/inositol/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .powder,
                usageNote: "No half-life is shown: inositol is an endogenously produced sugar alcohol handled by whole-body pools, not classical first-order clearance."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:probiotic",
            kind: .supplement,
            title: "Probiotic (Multi-Strain)",
            summary: "Live microorganisms studied for gut and digestive outcomes, effects varying by strain.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Systematic review and meta-analysis: Multi-strain probiotics as adjunct therapy for Helicobacter pylori eradication and prevention of adverse events - PubMed", "https://pubmed.ncbi.nlm.nih.gov/27536365/"),
                link("Probiotics: Benefits, Dosage, and Side Effects - Examine", "https://examine.com/supplements/probiotics/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                usageNote: "No half-life is shown: probiotics are live organisms that act locally in the gut and are not absorbed into circulation, so a pharmacokinetic half-life does not apply."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:psyllium",
            kind: .supplement,
            title: "Psyllium Husk",
            summary: "A soluble fiber studied for cholesterol and digestive regularity.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Effect of psyllium (Plantago ovata) fiber on LDL cholesterol and alternative lipid targets, non-HDL cholesterol and apolipoprotein B - PubMed", "https://pubmed.ncbi.nlm.nih.gov/30239559/"),
                link("Psyllium: Benefits, Dosage, and Side Effects - Examine", "https://examine.com/supplements/psyllium/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .powder,
                usageNote: "No half-life is shown: psyllium is a non-absorbed fiber acting locally in the gut, so a pharmacokinetic half-life does not apply."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:selenium",
            kind: .supplement,
            title: "Selenium",
            summary: "An essential trace mineral studied for thyroid antibody levels.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Selenium - Health Professional Fact Sheet - NIH Office of Dietary Supplements", "https://ods.od.nih.gov/factsheets/Selenium-HealthProfessional/"),
                link("Selenium Supplementation in Patients with Hashimoto Thyroiditis: A Systematic Review and Meta-Analysis of Randomized Clinical Trials - PubMed", "https://pubmed.ncbi.nlm.nih.gov/38243784/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .tablet,
                usageNote: "No half-life is shown: selenium is an essential trace mineral under homeostatic regulation, and the plasma half-life figures found in tertiary sources could not be traced to a verifiable primary study."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:potassium",
            kind: .supplement,
            title: "Potassium",
            summary: "An essential mineral studied for blood pressure, requiring caution with kidney disease or certain medications.",
            evidenceTier: .reference,
            officialLinks: [
                link("Potassium - Health Professional Fact Sheet (NIH Office of Dietary Supplements)", "https://ods.od.nih.gov/factsheets/Potassium-HealthProfessional/"),
                link("Potassium - Consumer Fact Sheet (NIH Office of Dietary Supplements)", "https://ods.od.nih.gov/factsheets/Potassium-Consumer/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .tablet,
                usageNote: "No half-life is shown: potassium is tightly homeostatically regulated by the kidneys, not cleared on a first-order curve, and the NIH fact sheets checked directly do not state an elimination figure."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:5-htp",
            kind: .supplement,
            title: "5-HTP",
            summary: "A serotonin precursor studied for mood, with a thin base of quality trial evidence.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Tryptophan and 5-hydroxytryptophan for depression - PubMed (Cochrane review)", "https://pubmed.ncbi.nlm.nih.gov/11869656/"),
                link("Tryptophan and 5-Hydroxytryptophan for depression | Cochrane", "https://www.cochrane.org/evidence/CD003198_tryptophan-and-5-hydroxytryptophan-depression")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 2.2, toHours: 7.4, source: "Neurotransmitter precursor pharmacokinetics reviewed in the Cochrane background; range spans dose and formulation differences across the small human PK literature"),
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:nmn",
            kind: .supplement,
            title: "NMN (Nicotinamide Mononucleotide)",
            summary: "An NAD+ precursor studied in an early human dose-finding trial.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("The efficacy and safety of β-nicotinamide mononucleotide (NMN) supplementation in healthy middle-aged adults - PubMed", "https://pubmed.ncbi.nlm.nih.gov/36482258/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                usageNote: "No half-life is shown: NMN is rapidly converted to nicotinamide riboside and other metabolites before absorption, and no human PK study for the intact molecule was found — only downstream catabolite and blood-NAD levels have been measured."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:resveratrol",
            kind: .supplement,
            title: "Resveratrol",
            summary: "A plant polyphenol studied widely, with evidence still short of a clinical recommendation.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Resveratrol for the Management of Human Health: How Far Have We Come? A Systematic Review of Resveratrol Clinical Trials", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10815776/"),
                link("Resveratrol supplementation efficiently improves endothelial health: A systematic review and meta-analysis - PubMed", "https://pubmed.ncbi.nlm.nih.gov/35833325/")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 1, toHours: 5, source: "Walle et al. 2004, Drug Metab Dispos, PMID 14977870 — human oral PK; rapid and extensive metabolism to glucuronide/sulfate conjugates limits free resveratrol exposure"),
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:tart-cherry",
            kind: .supplement,
            title: "Tart Cherry",
            summary: "A fruit extract studied for exercise-induced muscle soreness.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Efficacy of tart cherry juice in reducing muscle pain during running: a randomized controlled trial", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2874510/"),
                link("No Effect of Tart Cherry Juice or Pomegranate Juice on Recovery from Exercise-Induced Muscle Damage in Non-Resistance Trained Men", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6683053/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .softgel,
                usageNote: "No half-life is shown: this is a multi-constituent extract (anthocyanins, melatonin and others), and no single marker compound has verified human PK data for this product."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:saw-palmetto",
            kind: .supplement,
            title: "Saw Palmetto",
            summary: "A plant extract studied for urinary symptoms of benign prostatic hyperplasia.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Serenoa repens for benign prostatic hyperplasia | Cochrane", "https://www.cochrane.org/evidence/CD001423_serenoa-repens-benign-prostatic-hyperplasia"),
                link("Saw Palmetto for the Treatment of Lower Urinary Tract Symptoms Due to Benign Prostatic Hyperplasia - PubMed", "https://pubmed.ncbi.nlm.nih.gov/38804752/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .softgel,
                usageNote: "No half-life is shown: this is a multi-constituent fatty-acid and sterol extract, and no single marker compound has verified human PK data."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:supplement:beetroot",
            kind: .supplement,
            title: "Beetroot / Dietary Nitrate",
            summary: "A dietary nitrate source studied for blood pressure and exercise performance.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Inorganic nitrate and beetroot juice supplementation reduces blood pressure in adults: a systematic review and meta-analysis - PubMed", "https://pubmed.ncbi.nlm.nih.gov/23596162/"),
                link("The Effect of Beetroot Ingestion on High-Intensity Interval Training: A Systematic Review and Meta-Analysis", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8618171/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .solution,
                usageNote: "No half-life is shown: a commonly cited nitrate half-life figure (van Velzen et al. 2008) could not be independently verified from a retrievable primary source, so it is left out rather than repeated unverified."
            )
        ),
        // MARK: B-70 items 2 & 3 — hormones and medications (evidence and templates in scripts/evidence/evidence.json)
        LibraryCatalogEntry(
            id: "catalog:hormone:testosterone-undecanoate",
            kind: .medicationHormone,
            title: "Testosterone undecanoate",
            summary: "A long-acting testosterone ester, given as an intramuscular depot or an oral capsule, for confirmed male hypogonadism.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("Nebido 1000 mg/4 ml Summary of Product Characteristics (EMC/UK)", "https://www.medicines.org.uk/emc/product/14631/smpc"),
                link("JATENZO (testosterone undecanoate) capsule label — DailyMed", "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=ed7b5d41-7475-4c10-99b9-b62b3434ae60")
            ],
            template: ItemTemplate(
                halfLife: .range(fromDays: 20.9, toDays: 33.9, source: "Nieschlag & Behre, Andrology (Springer, 2010) pp.441-446; Saad et al. 2007, Asian J Androl, PMID 17486268 — range reflects tea-seed-oil vs castor-oil vehicle"),
                route: .intramuscular,
                dosageForm: .solution
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:dhea",
            kind: .medicationHormone,
            title: "DHEA",
            summary: "An adrenal steroid precursor to estrogens and androgens, sold over the counter and studied separately in a prescription vaginal form.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("INTRAROSA (prasterone) vaginal insert label — DailyMed", "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=df731acd-7276-4fef-b037-bc7f30c112cb"),
                link("Long-term DHEA replacement in primary adrenal insufficiency: a randomized, controlled trial — PubMed", "https://pubmed.ncbi.nlm.nih.gov/18000094/")
            ],
            template: ItemTemplate(
                halfLife: .hours(20, source: "Legrain et al. 2000, J Clin Endocrinol Metab, PMID 10999810: apparent terminal half-life of blood DHEA is more than 20 hours after oral dosing"),
                route: .oral,
                dosageForm: .capsule
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:hormone:pregnenolone",
            kind: .medicationHormone,
            title: "Pregnenolone",
            summary: "A cholesterol-derived steroid precursor to progesterone and DHEA, sold as an unregulated supplement.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("A randomized, double-blind, placebo-controlled trial of pregnenolone for bipolar depression — PubMed", "https://pubmed.ncbi.nlm.nih.gov/24917198/"),
                link("Proof-of-concept trial with the neurosteroid pregnenolone targeting cognitive and negative symptoms in schizophrenia — PubMed", "https://pubmed.ncbi.nlm.nih.gov/19339966/")
            ],
            template: ItemTemplate(
                route: .oral,
                dosageForm: .capsule,
                usageNote: "No half-life is shown: no dedicated human elimination-kinetics study for oral pregnenolone was found, and its precursor relationship to DHEA and progesterone does not license borrowing either one's figure."
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:insulin",
            kind: .medicationHormone,
            title: "Insulin glargine",
            summary: "A long-acting basal insulin analogue for once-daily use in type 1 and type 2 diabetes.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("LANTUS (insulin glargine) injection label — DailyMed", "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=b861fdd9-e134-436e-8c0c-a60dd0006dd3"),
                link("LANTUS full prescribing information — FDA AccessData", "https://www.accessdata.fda.gov/drugsatfda_docs/label/2022/021081s076lbl.pdf")
            ],
            template: ItemTemplate(
                halfLife: .hours(12, source: "Bolli et al. 2026, Diabetes Obes Metab, PMID 42046184 — modeled literature estimate, not a figure stated in the FDA label, which describes only a flat 24-hour release profile qualitatively"),
                route: .subcutaneous,
                dosageForm: .prefilledPen
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:metformin",
            kind: .medicationHormone,
            title: "Metformin",
            summary: "A biguanide that lowers blood glucose by reducing hepatic glucose output, first-line for type 2 diabetes.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("Metformin hydrochloride tablet label — DailyMed", "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=56d13a1c-b289-4528-b23c-60f5427b4552")
            ],
            template: ItemTemplate(
                halfLife: .hours(6.2, source: "FDA label, Glumetza: plasma half-life about 6.2 hours (whole-blood/erythrocyte half-life is longer, about 17.6 hours, due to red-cell partitioning)"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        LibraryCatalogEntry(
            id: "catalog:medication:atorvastatin",
            kind: .medicationHormone,
            title: "Atorvastatin",
            summary: "A statin that lowers LDL cholesterol by blocking an early step of hepatic cholesterol synthesis.",
            evidenceTier: .regulatory,
            officialLinks: [
                link("LIPITOR (atorvastatin calcium) tablet label — DailyMed", "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=a60cc18b-0631-4cf0-b021-9f52224ece65"),
                link("LIPITOR full prescribing information — FDA AccessData", "https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/020702s081lbl.pdf")
            ],
            template: ItemTemplate(
                halfLife: .range(fromHours: 20, toHours: 30, source: "FDA label, Lipitor: parent-drug half-life is about 14 hours, but HMG-CoA reductase inhibitory activity (parent plus active metabolites) has a half-life of 20-30 hours, which is the figure usually quoted for dosing purposes"),
                route: .oral,
                dosageForm: .tablet
            )
        ),
        // MARK: B-70 items 4 & 5 — logged, not taken, and practices (evidence in scripts/evidence/evidence.json)
        LibraryCatalogEntry(
            id: "catalog:context:sleep",
            kind: .context,
            title: "Sleep",
            summary: "Sleep duration and quality as an entry in its own right, tracked across nights rather than pulled from a single device reading.",
            evidenceTier: .reference,
            officialLinks: [
                link("Recommended Amount of Sleep for a Healthy Adult: A Joint Consensus Statement of the American Academy of Sleep Medicine and Sleep Research Society", "https://pubmed.ncbi.nlm.nih.gov/26039963/"),
                link("Recommended Amount of Sleep for a Healthy Adult (full text, PMC)", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4434546/")
            ],
            template: ItemTemplate()
        ),
        LibraryCatalogEntry(
            id: "catalog:context:alcohol",
            kind: .context,
            title: "Alcohol",
            summary: "Each drinking occasion recorded as its own entry, separate from any protocol.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Alcohol use and burden for 195 countries and territories, 1990-2016: a systematic analysis for the Global Burden of Disease Study 2016", "https://pubmed.ncbi.nlm.nih.gov/30146330/")
            ],
            template: ItemTemplate()
        ),
        LibraryCatalogEntry(
            id: "catalog:context:nicotine",
            kind: .context,
            title: "Nicotine",
            summary: "Nicotine or tobacco use recorded as an occurrence, separate from any protocol.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Association of Long-term, Low-Intensity Smoking With All-Cause and Cause-Specific Mortality in the National Institutes of Health-AARP Diet and Health Study", "https://pubmed.ncbi.nlm.nih.gov/27918784/"),
                link("Low-intensity cigarette smoking and mortality risks: a pooled analysis of prospective cohort studies in Japan", "https://pubmed.ncbi.nlm.nih.gov/34718588/")
            ],
            template: ItemTemplate()
        ),
        LibraryCatalogEntry(
            id: "catalog:context:alcohol-free-day",
            kind: .context,
            title: "Alcohol-free day",
            summary: "A day with no alcohol, logged as its own positive entry rather than left as an absence.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Voluntary temporary abstinence from alcohol during \"Dry January\" and subsequent alcohol use", "https://pubmed.ncbi.nlm.nih.gov/26690637/"),
                link("Short- and Longer-Term Benefits of Temporary Alcohol Abstinence During 'Dry January' Are Not Also Observed Among Adult Drinkers in the General Population: Prospective Cohort Study", "https://pubmed.ncbi.nlm.nih.gov/32391879/")
            ],
            template: ItemTemplate(usageNote: "Logged as its own entry, not just the absence of an alcohol entry.")
        ),
        LibraryCatalogEntry(
            id: "catalog:food-protocol:calorie-protein-target",
            kind: .foodProtocol,
            title: "Calorie or protein target",
            summary: "A daily calorie or protein target, tracked by adherence rather than by the food itself.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Self-monitoring in weight loss: a systematic review of the literature", "https://pubmed.ncbi.nlm.nih.gov/21185970/"),
                link("A systematic review, meta-analysis and meta-regression of the effect of protein supplementation on resistance training-induced gains in muscle mass and strength in healthy adults", "https://pubmed.ncbi.nlm.nih.gov/28698222/")
            ],
            template: ItemTemplate(usageNote: "Logs adherence to the target you set yourself; the app does not set it for you.")
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:pilates",
            kind: .exercisePlan,
            title: "Pilates",
            summary: "Mat or reformer work focused on core control and alignment.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Pilates for low back pain", "https://pubmed.ncbi.nlm.nih.gov/26133923/"),
                link("Pilates for Low Back Pain: Complete Republication of a Cochrane Review", "https://pubmed.ncbi.nlm.nih.gov/26679894/")
            ],
            template: ItemTemplate()
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:climbing",
            kind: .exercisePlan,
            title: "Climbing",
            summary: "Indoor or outdoor climbing, bouldering or roped, recorded by session.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Indoor rock climbing (bouldering) as a new treatment for depression: study design of a waitlist-controlled randomized group pilot study and the first results", "https://pubmed.ncbi.nlm.nih.gov/26302900/")
            ],
            template: ItemTemplate()
        ),
        LibraryCatalogEntry(
            id: "catalog:exercise:team-sport",
            kind: .exercisePlan,
            title: "Team sport",
            summary: "Football, basketball and the like — recorded by session rather than by drill.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Association between physical exercise and mental health in 1·2 million individuals in the USA between 2011 and 2015: a cross-sectional study", "https://pubmed.ncbi.nlm.nih.gov/30099000/")
            ],
            template: ItemTemplate()
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:acupuncture",
            kind: .recoveryPractice,
            title: "Acupuncture",
            summary: "Needling therapy delivered by a practitioner.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Acupuncture for Chronic Pain: Update of an Individual Patient Data Meta-Analysis", "https://pubmed.ncbi.nlm.nih.gov/29198932/")
            ],
            template: ItemTemplate()
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:hyperbaric-oxygen",
            kind: .recoveryPractice,
            title: "Hyperbaric oxygen therapy",
            summary: "Breathing supplemental oxygen at above-normal pressure in a chamber.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Hyperbaric oxygen therapy can diminish fibromyalgia syndrome--prospective clinical trial", "https://pubmed.ncbi.nlm.nih.gov/26010952/")
            ],
            template: ItemTemplate()
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:gratitude-therapy",
            kind: .recoveryPractice,
            title: "Gratitude practice or therapy session",
            summary: "A written gratitude practice or a talk-therapy session, logged as its own entry.",
            evidenceTier: .clinicalStudy,
            officialLinks: [
                link("Counting blessings versus burdens: an experimental investigation of gratitude and subjective well-being in daily life", "https://pubmed.ncbi.nlm.nih.gov/12585811/")
            ],
            template: ItemTemplate()
        ),
        LibraryCatalogEntry(
            id: "catalog:recovery:screen-curfew",
            kind: .recoveryPractice,
            title: "Screen curfew",
            summary: "A cutoff time for screens before bed, tracked by whether it held.",
            evidenceTier: .systematicReview,
            officialLinks: [
                link("Bedtime, shuteye time and electronic media: sleep displacement is a two-step process", "https://pubmed.ncbi.nlm.nih.gov/28271575/"),
                link("Interventions to control children's screen use and their effect on sleep: A systematic review and meta-analysis", "https://pubmed.ncbi.nlm.nih.gov/32567219/")
            ],
            template: ItemTemplate(usageNote: "Logs whether the cutoff time held, not a recommended cutoff.")
        ),
    ]

    public static func builtInEntry(id: String) -> LibraryCatalogEntry? {
        builtInEntries.first { $0.id == id }
    }

    public static func builtInEntries(for kind: ItemKind) -> [LibraryCatalogEntry] {
        builtInEntries.filter { $0.kind == kind }
    }

    public static func isBuiltIn(id: String) -> Bool {
        id.hasPrefix(builtInPrefix)
    }

    /// Validates an entry the user or agent is trying to save.
    ///
    /// Deliberately permissive about content — this is the user's own reference library and
    /// they may record whatever they find useful. It only enforces what keeps the library
    /// trustworthy: attribution, a title, and no editing of shipped entries.
    public static func validate(_ entry: LibraryCatalogEntry) throws {
        guard entry.provenance.isEditable else {
            throw ValidationFailure.builtInIsReadOnly(entry.id)
        }
        guard !entry.title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw ValidationFailure.titleRequired
        }
        guard !isBuiltIn(id: entry.id) else {
            throw ValidationFailure.reservedIdentifier(entry.id)
        }
        guard !entry.uncertainty.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw ValidationFailure.uncertaintyRequired
        }
    }

    public enum ValidationFailure: Error, Equatable {
        /// Shipped entries cannot be edited. Copy one to a custom entry instead.
        case builtInIsReadOnly(String)
        case titleRequired
        /// The `catalog:` namespace belongs to the app.
        case reservedIdentifier(String)
        /// Every entry states its own limits, including ones the user wrote.
        case uncertaintyRequired
    }
}
