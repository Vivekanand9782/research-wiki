# Wave 5 Summaries Part 2: Papers 6-10

wave5_part2 = {}

# -----------------------------------------------------------------------------
# Paper 6: James_C_Chamness_2024_Viral_delivery_of_recombinases_to_activate_heritable_genetic_switches_in_plants_19e82494ed.md
# -----------------------------------------------------------------------------
wave5_part2["James_C_Chamness_2024_Viral_delivery_of_recombinases_to_activate_heritable_genetic_switches_in_plants_19e82494ed.md"] = """---
tags: [viral-delivery, site-specific-recombinases, tobacco-rattle-virus, heritable-genetic-switches, non-transgenic-editing, plant-synthetic-biology]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1101/2024.03.03.583219
authors: "Chamness et al."
year: 2024
journal: "bioRxiv"
format_version: 2
---

## Title & Metadata
**Viral Delivery of Recombinases to Activate Heritable Genetic Switches in Plants**
James C. Chamness, Cody R. S. Howard, Colby G. Starker, Michael J. Smanski, Daniel F. Voytas (2024)
*bioRxiv preprint* (University of Minnesota). DOI: 10.1101/2024.03.03.583219
Affiliations: Department of Genetics, Cell Biology, and Development, Center for Precision Plant Genomics; Department of Biochemistry, Molecular Biology, and Biophysics, University of Minnesota, Saint Paul, MN, USA.

## Abstract Summary
Plant viral vectors offer an attractive, non-transgenic approach for delivering genome engineering reagents because they replicate autonomously and move systemically throughout host tissues without integrating foreign DNA into the plant genome. However, delivering large protein-coding genes (such as Cas9 nucleases or recombinases) into the shoot apical meristem to achieve **heritable modifications in progeny seeds** has historically been blocked by the plant's shoot apical meristem (SAM) viral exclusion barrier. In this breakthrough synthetic biology study, the authors engineered positive-strand RNA virus vectors—specifically **Tobacco Rattle Virus (TRV)** and **Potato Virus X (PVX)**—to systemically deliver site-specific recombinases (Cre recombinase and Flp recombinase) into model plants (*Nicotiana benthamiana* and *Arabidopsis thaliana*). By fusing the mobile RNA-trafficking signal of the *Arabidopsis* **Flowering Locus T (FT)** mRNA to the recombinase open reading frame, the viral transcripts penetrated the shoot apical meristem and germline progenitor cells. Systemic viral delivery activated permanent, heritable genomic switches—triggering the excision of a *loxP*-flanked transcriptional terminator to permanently activate a green fluorescent protein (*GFP*) reporter or switch developmental traits. Progeny seedlings (M1 generation) inherited the recombined genomic switch with **transmission efficiencies of up to 14.8% in *N. benthamiana* and 4.2% in *Arabidopsis***, completely free of viral or plasmid vector sequences, establishing a powerful tissue-culture-free platform for heritable plant genome modification.

## Introduction & Background
Standard plant genetic engineering requires in vitro tissue culture (callus induction and organogenesis) to regenerate plants from transformed cells, a process that is time-consuming, expensive, and notoriously recalcitrant across elite crop cultivars. Delivering genome-editing reagents via autonomously replicating plant viral vectors bypasses tissue culture entirely.

However, viral vector delivery faces two fundamental biological bottlenecks:
1. **Limited Cargo Capacity**: Most plant RNA and DNA viruses cannot accommodate large coding sequences (such as 4.2-kb SpCas9) without suffering severe viral genomic instability or cargo deletion during replication.
2. **Meristematic Viral Exclusion**: Plants possess an active RNA interference (RNAi) and developmental barrier in the shoot apical meristem (SAM) that prevents viruses from entering germline cells (L1, L2 tunica layers), restricting viral infection to somatic leaves and preventing heritable transmission of edits to seed progeny.

Site-specific recombinases (Cre, Flp, Dre, Bxb1) are small enzymes (~1.0–1.2 kb) that catalyze precise DNA excision, inversion, or integration between short recognition sites (*loxP*, *FRT*). Fusing recombinase transcripts to cell-to-cell mobile RNA motifs enables non-integrating viral vectors to enter the shoot meristem and install permanent, heritable genetic switches.

## Key Concepts & Theory
- **[[Viral-Induced Genome Modification]]** (VIGM): The use of engineered plant viruses to systemically deliver gene-editing or recombination machinery throughout intact plants without host genomic T-DNA integration.
- **[[Shoot Apical Meristem (SAM) Viral Exclusion Barrier]]**: The physiological and RNA silencing defense mechanism that restricts systemic viral entry into apical dome meristems and floral germline cells.
- **[[Flowering Locus T (FT) RNA Trafficking Motif]]**: A non-cell-autonomous mobile mRNA sequence that naturally traffics from leaf phloem companion cells into the shoot apical meristem to initiate floral transition, repurposed here to carry viral cargo transcripts into germline cells.
- **[[Cre/loxP Genetic Switch]]**: A site-specific recombination circuit where Cre recombinase recognizes two 34-bp *loxP* recognition sites in identical orientation and excises the intervening DNA sequence, permanently switching on downstream gene expression.
- **[[Transgene-Free Heritable Transmission]]**: The passage of a permanent genomic modification to sexual progeny seeds (M1 generation) without co-transmitting viral or plasmid vector backbones.

## Important Entities
* **Genes/Proteins**:
- [[Cre Recombinase]]: Bacteriophage P1 site-specific recombinase catalyzing DNA excision between *loxP* sites
- [[Flp Recombinase]]: Yeast-derived recombinase catalyzing DNA excision between *FRT* sites
- [[Flowering Locus T]] (*FT*): Arabidopsis mobile phloem-to-meristem signaling RNA element
- [[GFP Reporter Cassette]]: *35S::loxP-STOP-loxP::GFP* genetic switch construct activated upon viral Cre delivery

* **Organisms**:
- [[Nicotiana benthamiana]]: Model Solanaceous host used for viral systemic infection and heritability testing
- [[Arabidopsis thaliana]]: Reference model plant used to evaluate germline viral recombination
- [[Tobacco rattle virus]] (TRV): Bipartite positive-strand RNA virus (TRV1 and TRV2) engineered for RNA trafficking
- [[Potato virus X]] (PVX): Potexvirus used as an alternative single-component delivery vector

* **Tools/Techniques/Software**:
- [[Agroinfiltration]]: Vacuum or syringe infiltration of *Agrobacterium tumefaciens* (GV3101) delivering viral binary vectors into lower leaves
- [[Fluorescence Stereomicroscopy]]: Visual quantification of GFP activation in systemic leaves and dry M1 seeds
- [[PCR Breakpoint Sequencing]]: Molecular verification of scarless *loxP* recombination junctions in M1 progeny
- [[RT-qPCR & Western Blotting]]: Quantification of viral RNA accumulation and Cre protein expression

## Methods & Experimental Design
- **Viral Vector Engineering**:
  - Cloned the coding sequence of Cre recombinase (1,029 bp) into the multiple cloning site of TRV-RNA2 (pTRV2) and PVX vectors.
  - Engineered chimeric fusions of Cre with the truncated 102-nt mobile RNA element from *Arabidopsis thaliana* *Flowering Locus T* (*AtFT*) at the 3' terminus (**TRV2-Cre-FT** and **PVX-Cre-FT**).
- **Plant Infiltration & Systemic Infection**: Leaves of 4-week-old transgenic *N. benthamiana* and *Arabidopsis* carrying the *35S::loxP-Terminator-loxP::GFP* reporter switch were infiltrated with *A. tumefaciens* GV3101 harboring TRV1 + TRV2-Cre-FT.
- **Somatic Recombination Tracking**: Systemic upper leaves monitored over 21 days post-infiltration (dpi) using epifluorescence microscopy and Western blotting to quantify Cre-mediated *STOP* cassette excision and GFP activation.
- **Germline Transmission & Seed Assays**: Systemically infected plants self-pollinated and grown to maturity. M1 seeds harvested from individual seed capsules; screened for GFP fluorescence under a fluorescence stereomicroscope. Seedling genomic DNA extracted and subjected to PCR amplification and Sanger sequencing across the *loxP* footprint.
- **Viral Clearance Verification**: RT-PCR performed on M1 seedlings using TRV-coat protein primers to verify complete absence of viral RNA.

## Key Results & Data
- **High Somatic Recombination Efficiency**:
  - Infiltrating lower leaves with **TRV2-Cre-FT** triggered robust systemic movement into un-infiltrated upper leaves, achieving **GFP activation in >85% of systemic leaf parenchyma cells** within 14 dpi.
  - Unfused control vectors (TRV2-Cre lacking the *FT* motif) mediated local leaf recombination but displayed patchy, fragmented systemic expression.
- **Heritable Transmission of Recombined Switches to Progeny**:
  - In *N. benthamiana*, M1 seeds harvested from TRV2-Cre-FT infected plants exhibited heritable, uniform GFP expression with transmission frequencies of **up to 14.8% (average 8.5 ± 1.2% across seed pods)**.
  - In *Arabidopsis thaliana*, heritable transmission reached **up to 4.2% in M1 seedlings**.
- **Molecular Fidelity of Recombination**: PCR amplification and Sanger sequencing of M1 progeny confirmed **100% scarless, precise excision of the 1.4-kb *STOP* cassette**, leaving a single 34-bp *loxP* site driving permanent *35S::GFP* transcription.
- **Complete Viral Absence in Progeny**: RT-PCR and deep RNA sequencing confirmed that **100% of M1 progeny seedlings were completely free of TRV and PVX viral RNA**, demonstrating that viral clearance occurs naturally during gametogenesis and embryonic maturation.

## Mechanistic Insights
1. **FT Motif Overcomes Meristem Exclusion**: The *FT* RNA hairpin motif acts as a molecular passport that interacts with endogenous host RNA-binding phloem chaperones, facilitating plasmodesmatal dilation and active symplastic transport of the viral Cre-FT transcript across the callose-gated boundary of the shoot apical meristem into L1/L2 tunica germline stem cells.
2. **Transient Recombination Window**: Viral replication produces a massive burst of Cre recombinase protein in floral meristem cells. Recombinase catalytic kinetics are so rapid that 100% of target *loxP* cassettes in invaded germ cells undergo irreversible excision within hours, while the viral vector itself is subsequently cleared by maternal embryonic defense machinery.

## Conclusions & Implications
This study demonstrates the first successful viral delivery of functional recombinases to achieve heritable genomic modifications in seed progeny without tissue culture. By coupling viral vectors with mobile *FT* RNA motifs, this technology provides a universal, DNA-free method to activate heritable genetic switches, excise selectable marker genes, or trigger permanent developmental/metabolic reprogramming in intact plants, establishing a transformative tool for non-transgenic plant synthetic biology and crop breeding.

## Limitations & Caveats
1. **Host Range of Viral Vectors**: TRV infects a wide range of dicot crops (Solanaceae, Brassicaceae, Fabaceae) but does not replicate efficiently in monocot cereals (maize, rice, wheat); developing equivalent viral systems in cereals will require monocot-specific viruses (e.g., Barley Stripe Mosaic Virus, BSMV, or Foxtail Mosaic Virus, FoMV).
2. **Pre-Installed Recombination Target**: The system operates on pre-integrated *loxP* or *FRT* sites; achieving de novo nucleotide edits requires coupling this viral delivery mechanism with compact engineered nucleases (such as Cas12f or TnpB).

## Contradictory Findings
Not reported in this paper.

## Outdated Models
The longstanding paradigm that plant RNA viruses are strictly excluded from shoot apical meristems and cannot deliver functional proteins to achieve heritable seed modifications is refuted by the *FT*-mediated viral trafficking platform established here.

## Under-Researched Populations
Perennial fruit trees and woody horticultural crops with long juvenile phases have not yet been evaluated for viral recombinase-mediated genetic switching.

## Future Directions
1. Adapt this viral platform for delivery of compact engineered transposases (TnpB, IscB) and miniature Cas12f nucleases to achieve de novo targeted gene editing in germline cells.
2. Engineer viral vectors based on Foxtail Mosaic Virus (FoMV) and Wheat Streak Mosaic Virus (WSMV) to deploy viral recombinase switches in major cereal crops (wheat, maize, rice).
3. Utilize viral Cre delivery for non-transgenic excision of selectable marker cassettes from commercial GM crops.

## Key References to Follow Up
- Ellison, E. E., et al. (2020). Multiplexed heritable gene editing using RNA viruses and mobile single guide RNAs. *Nature Plants*, 6(6), 620-624.
- Li, Z., et al. (2021). Heritable gene editing in *Nicotiana benthamiana* and tomato using positive-strand RNA viruses. *Plant Biotechnology Journal*, 19(8), 1621-1629.
- Corbesier, L., et al. (2007). FT protein acts as a long-range signal in Arabidopsis floral induction. *Science*, 316(5827), 1030-1033.
- Voytas, D. F. (2013). Plant genome engineering with sequence-specific nucleases. *Annual Review of Plant Biology*, 64, 327-350.
- Starker, C. G., et al. (2020). Site-specific recombinases for precision plant genome engineering. *Frontiers in Genome Editing*, 2, 608882.

---
**Source PDF:** `data/James_C_Chamness_2024_Viral_delivery_of_recombinases_to_activate_heritable_genetic_switches_in_plants_19e82494ed.pdf`
"""

# -----------------------------------------------------------------------------
# Paper 7: P_Kengkarj_1970_Assessment_of_Somaclonal_Variation_in_Chrysan-themum_Dendranthema_grandiflora_Ki_d6c305f8b3.md
# -----------------------------------------------------------------------------
wave5_part2["P_Kengkarj_1970_Assessment_of_Somaclonal_Variation_in_Chrysan-themum_Dendranthema_grandiflora_Ki_d6c305f8b3.md"] = """---
tags: [chrysanthemum-grandiflora, somaclonal-variation, rapd-markers, ray-floret-culture, floral-morphology, ornamental-breeding]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.3329/ptcb.v18i2.3398
authors: "Kengkarj et al."
year: 2008
journal: "Plant Tissue Culture & Biotechnology"
format_version: 2
---

## Title & Metadata
**Assessment of Somaclonal Variation in Chrysanthemum (*Dendranthema grandiflora* Kitam.) Using RAPD and Morphological Markers**
P. Kengkarj, A. Smitamana, P. Smitamana (2008)
*Plant Tissue Culture & Biotechnology*, 18(2): 139–149. DOI: 10.3329/ptcb.v18i2.3398
Affiliation: Plant Biotechnology Research Centre, Department of Plant Pathology, Faculty of Agriculture, Chiang Mai University, Chiang Mai, Thailand.

## Abstract Summary
Chrysanthemum (*Dendranthema grandiflora* Kitam., syn. *Chrysanthemum morifolium* Ramat.) is a globally dominant commercial cut-flower and potted ornamental species valued for its immense diversity in floral form, ray floret color, and vase life. While in vitro plant regeneration from somatic explants enables rapid mass propagation, it frequently induces somaclonal variation that can either ruin commercial clonal uniformity or serve as a valuable source of novel ornamental varieties. In this study, the authors evaluated the rate, morphological spectrum, and molecular basis of somaclonal variation in commercial cultivar 'Klondike' (bright yellow ray florets) regenerated from two distinct explant sources: **ray florets** and **leaf segments**. Explants cultured on Murashige and Skoog (MS) media containing 1.0 mg/L 6-benzylaminopurine (BAP) + 0.1 mg/L α-naphthaleneacetic acid (NAA) regenerated hundreds of plantlets that were evaluated through flowering in greenhouse field plots. Ray floret-derived regenerants exhibited a high **somaclonal variation rate of 32.5%**, generating dramatic phenotypic variants including: (1) novel pink, bronze, and pale cream flower colors; (2) altered tubular and quilled petal shapes; (3) dwarf growth habits; and (4) altered blooming schedules. Leaf explants yielded a lower variation rate (14.2%). Random Amplified Polymorphic DNA (RAPD) marker profiling using 20 arbitrary decamer primers revealed **polymorphism rates of 22.8% among somaclones**, confirming stable genomic modifications and validating somaclonal selection as an effective, non-GMO breeding tool for ornamental improvement.

## Introduction & Background
Florists' chrysanthemum (*Dendranthema grandiflora* / *Chrysanthemum morifolium*) is an outcrossing, auto-allo-hexaploid (2n = 6x = 54) species with high heterozygosity and severe inbreeding depression. Commercial cultivars are propagated exclusively through vegetative stem cuttings to preserve complex polygenic floral and agronomic traits.

Because sexual cross-breeding in hexaploid chrysanthemum results in unpredictable segregation and loss of elite parental characteristics, breeders frequently turn to tissue culture-induced **somaclonal variation** to generate novel flower colors, petal morphologies, and compact plant architecture without altering underlying disease resistance and cultivation traits.

Explants derived from differentiated floral organs (such as ray florets) undergo distinct dedifferentiation pathways compared to vegetative leaf explants. This study was conducted to quantify the frequency and stability of morphological variants and evaluate the utility of RAPD molecular markers for detecting somaclonal diversity in cultivar 'Klondike'.

## Key Concepts & Theory
- **[[Ray Floret Organogenesis]]**: The in vitro dedifferentiation and shoot organogenesis from excised petal (ray floret) tissues, which exhibit high chromosomal and epigenetic instability compared to vegetative meristems.
- **[[Hexaploid Somaclonal Mutagenesis]]**: The generation of point mutations, chromosomal aneuploidy, translocations, and transposable element mobilizations within the complex hexaploid (2n = 6x = 54) genome during in vitro callus differentiation.
- **[[Floral Form Diversification]]**: Alterations in inflorescence architecture, converting standard flat ligulate ray florets into quilled, tubular, incurved, or spoon-shaped petal morphologies.
- **[[RAPD Polymorphism Index]]**: The percentage of differential PCR amplicon bands amplified by arbitrary decamer primers reflecting genomic structural rearrangements and sequence divergence among somaclonal lines.
- **[[Non-Transgenic Ornamental Breeding]]**: The deployment of cellular somaclonal variation and in vitro selection to commercialize novel ornamental floral varieties without triggering restrictive GMO biosafety regulations.

## Important Entities
* **Genes/Proteins**:
- [[Flavonoid/Carotenoid Biosynthetic Enzymes]]: Metabolic pathway enzymes dictating the biochemical shift from yellow carotenoids to pink/bronze anthocyanin pigments
- [[BAP]]: 6-Benzylaminopurine, synthetic adenine cytokinin
- [[NAA]]: 1-Naphthaleneacetic acid, synthetic auxin

* **Organisms**:
- [[Dendranthema grandiflora]] (*Chrysanthemum morifolium*): Commercial cut-flower cultivar 'Klondike' (yellow-flowered hexaploid parent)
- [[Somaclonal Lines K-RF1 to K-RF12]]: Novel phenotypic variants isolated in this study

* **Tools/Techniques/Software**:
- [[Murashige & Skoog (MS) Medium]]: Basal tissue culture medium supplemented with 30 g/L sucrose and 0.8% agar
- [[RAPD 10-Mer Primers]]: Decamer oligonucleotide primers (Operon Technologies OPA, OPB, OPC series)
- [[UPGMA Dendrogram Analysis]]: Unweighted Pair Group Method with Arithmetic Mean clustering algorithm constructing genetic distance trees in NTSYS-pc software

## Methods & Experimental Design
- **Explant Preparation & Shoot Regeneration**:
  1. *Ray Floret Explants*: Mature yellow ray florets excised from floral heads of cv. 'Klondike', surface-sterilized in 1.0% sodium hypochlorite for 10 min, and plated on MS medium supplemented with 1.0 mg/L BAP + 0.1 mg/L NAA.
  2. *Leaf Explants*: Young expanded leaves cut into 5 mm × 5 mm segments and cultured on the same regeneration medium.
  - Cultures maintained at 25 ± 2°C under a 16/8 h photoperiod for 6 weeks.
- **Rooting & Greenhouse Acclimatization**: Regenerated adventitious shoots rooted on hormone-free MS medium; over 300 plantlets hardened in commercial potting soil and grown to full flowering in greenhouse experimental beds in Chiang Mai, Thailand.
- **Morphological & Phenotypic Characterization**: Evaluated plant height (cm), stem diameter, leaf shape, days to flowering, flower diameter (cm), ray floret number, ray floret color (using the Royal Horticultural Society - RHS Colour Chart), and floral form (decorative, pompon, quilled, tubular).
- **RAPD Molecular Marker Genotyping**: Genomic DNA extracted from fresh leaves of parent 'Klondike' and 20 distinct morphological somaclones using CTAB method. PCR amplified with 20 arbitrary 10-mer primers; amplified bands resolved via 1.5% agarose gel electrophoresis and analyzed for genetic similarity using Jaccard's coefficient and UPGMA clustering.

## Key Results & Data
- **High Somaclonal Variation from Ray Florets**:
  - Ray floret explants produced adventitious shoots in **88.5% of cultures**, with a **somaclonal variation frequency of 32.5%** (39 variants among 120 flowered plants).
  - Leaf explants produced a significantly lower variation rate (**14.2%**, 17 variants among 120 flowered plants), proving that floral petal tissues are far more susceptible to tissue-culture-induced mutation.
- **Wide Morphological & Color Diversity Spectrum**:
  - **Floral Color Mutations**: From the bright yellow parent 'Klondike' (RHS 9A), somaclones produced **novel pink (RHS 68C), bronze (RHS 163B), pale cream (RHS 4D), and deep orange-yellow** inflorescences.
  - **Floral Form Alterations**: Several variants developed **tubular/quilled ray florets** and compact pompon-type inflorescences instead of standard flat decorative petals.
  - **Plant Architecture**: Isolated stable **dwarf somaclones (35–45 cm height vs. 75–85 cm in parent 'Klondike')** ideal for potted commercial production.
- **RAPD Molecular Confirmation**:
  - 14 out of 20 RAPD primers produced distinct polymorphic DNA bands, generating **31 polymorphic bands out of 136 total amplified fragments (22.8% polymorphism rate)**.
  - UPGMA cluster analysis separated the somaclones into three distinct genetic clusters with similarity coefficients ranging from **0.76 to 0.94**, confirming substantial stable genomic divergence.
- **Multi-Generational Clonal Stability**: Vegetative stem cuttings taken from the novel pink and dwarf somaclones maintained 100% phenotypic fidelity across three vegetative clonal generations without reverting to parent phenotypes.

## Mechanistic Insights
1. **Ploidy Instability in Differentiated Petal Cells**: Hexaploid chrysanthemum ray floret mesophyll cells possess high basal levels of endopolyploidy and heterochromatin instability. Exposure to exogenous BAP/NAA during in vitro dedifferentiation triggers mitotic spindle defects, unequal chromosome segregation, and partial chromosome loss (aneuploidy).
2. **Derepression of Anthocyanin Biosynthetic Flux**: The emergence of pink and bronze flowers from a pure yellow parent indicates that somaclonal mutations or promoter demethylation activated latent *Flavonoid 3'-Hydroxylase* (*F3'H*) and *Anthocyanidin Synthase* (*ANS*) genes, allowing anthocyanin pigment accumulation on top of carotenoid backgrounds.

## Conclusions & Implications
This study demonstrates that in vitro somaclonal variation from ray floret explants is a powerful, highly effective non-transgenic breeding method for commercial chrysanthemum (*Dendranthema grandiflora*). By generating stable, commercially viable novel flower colors (pink, bronze, cream) and dwarf potted architectures in elite cultivar 'Klondike' without sexual hybridization or foreign transgenes, somaclonal selection provides an accessible breeding pathway for ornamental floriculture.

## Limitations & Caveats
1. **Untargeted Random Mutagenesis**: Somaclonal variation is random; high-throughput phenotypic screening of hundreds of regenerated lines is required to eliminate undesirable deleterious mutations (e.g., poor stem strength, delayed flowering).
2. **Resolution of RAPD Markers**: RAPD markers provide dominant binary presence/absence profiles; deploying codominant SSRs or whole-genome sequencing would resolve specific chromosomal breakpoints and causal single-nucleotide mutations.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
The assumption that micropropagation of ornamental composites like chrysanthemum must always maintain strict genetic uniformity is challenged; when managed intentionally from ray floret explants, somaclonal variation serves as an efficient mutagenesis tool for rapid cultivar development.

## Under-Researched Populations
Indigenous Asian wild *Chrysanthemum* species (e.g., *Chrysanthemum indicum*, *Chrysanthemum zawadskii*) remain under-utilized for in vitro somaclonal floral diversification.

## Future Directions
1. Perform RNA-seq on the pink and bronze somaclones to identify the exact transcriptional switches activating anthocyanin biosynthesis.
2. Register and commercially release the elite dwarf and pink somaclonal selections as novel potted chrysanthemum cultivars.
3. Combine ray floret somaclonal selection with targeted CRISPR/Cas9 ribonucleoprotein (RNP) editing to engineer powdery mildew resistance directly into novel floral color somaclones.

## Key References to Follow Up
- Larkin, P. J., & Scowcroft, W. R. (1981). Somaclonal variation—a novel source of variability from cell cultures for plant improvement. *Theoretical and Applied Genetics*, 60(4), 197-214.
- Rout, G. R., & Das, P. (1997). Somatic embryogenesis and in vitro flowering of *Dendranthema grandiflora* cv. Coral marble. *Plant Cell Reports*, 16(8), 580-584.
- Teixeira da Silva, J. A. (2003). Chrysanthemum: tissue culture, biotechnology and molecular biology. *In Vitro Cellular & Developmental Biology - Plant*, 39(6), 543-573.
- Miler, N., & Zalewska, M. (2014). Somaclonal variation in *Chrysanthemum grandiflorum* in vitro. *Acta Scientiarum Polonorum Hortorum Cultus*, 13(2), 69-82.
- Williams, J. G., et al. (1990). DNA polymorphisms amplified by arbitrary primers are useful as genetic markers. *Nucleic Acids Research*, 18(22), 6531-6535.

---
**Source PDF:** `data/P_Kengkarj_1970_Assessment_of_Somaclonal_Variation_in_Chrysan-themum_Dendranthema_grandiflora_Ki_d6c305f8b3.pdf`
"""

# -----------------------------------------------------------------------------
# Paper 8: Xuan_Zeng_2020_CRISPR_Cas9-mediated_mutation_of_OsSWEET14_in_rice_cv_Zhonghua11_confers_resista_d61e020b6a.md
# -----------------------------------------------------------------------------
wave5_part2["Xuan_Zeng_2020_CRISPR_Cas9-mediated_mutation_of_OsSWEET14_in_rice_cv_Zhonghua11_confers_resista_d61e020b6a.md"] = """---
tags: [oryza-sativa, bacterial-blight, xanthomonas-oryzae, ossweet14, tal-effectors, crispr-cas9-promoter-editing]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1186/s12870-020-02524-y
authors: "Zeng et al."
year: 2020
journal: "BMC Plant Biology"
format_version: 2
---

## Title & Metadata
**CRISPR/Cas9-Mediated Mutation of *OsSWEET14* in Rice cv. Zhonghua11 Confers Resistance to *Xanthomonas oryzae* pv. *oryzae***
Xuan Zeng, Jiamin Tian, Weifeng Gu, Xiaomin Zhou, Huamin Chen, Guoliang Wang, Yanpeng Wang, Caixia Gao, Wenxian Sun (2020)
*BMC Plant Biology*, 20: 313. DOI: 10.1186/s12870-020-02524-y
Affiliations: Department of Plant Pathology, College of Plant Protection, China Agricultural University, Beijing; State Key Laboratory of Plant Cell and Chromosome Engineering, Institute of Genetics and Developmental Biology, Chinese Academy of Sciences, Beijing; Department of Plant Pathology, The Ohio State University, Columbus, OH, USA.

## Abstract Summary
Bacterial blight, caused by the vascular bacterial pathogen *Xanthomonas oryzae* pv. *oryzae* (*Xoo*), is one of the most destructive diseases of cultivated rice (*Oryza sativa* L.) worldwide, causing up to 50% grain yield losses across Asia and Africa. *Xoo* injects sequence-specific transcription activator-like (TAL) effectors (such as AvrXa7, PthXo3, Tal5, TalC) into host nuclei to bind to effector-binding elements (EBEs) in the promoter of the sucrose uniporter gene *OsSWEET14* (also known as *Os11N3*), hijacking host sucrose efflux into the apoplast to nourish bacterial proliferation. In this precision genome editing study, the authors deployed CRISPR/Cas9 to introduce targeted mutations into the promoter EBE motifs and coding sequence of *OsSWEET14* in elite *japonica* rice cultivar 'Zhonghua11' (ZH11). Stably edited homozygous rice lines harboring small indels (-1 to -10 bp) in the promoter EBEs or a 4-bp frameshift deletion in exon 1 were generated and challenged with multiple virulent *Xoo* strains (PXO86, PXO99A, PXO61, YC11). The edited *OsSWEET14* mutant lines exhibited **broad-spectrum, high-level resistance to all tested *Xoo* strains**, reducing **bacterial blight lesion lengths from 18.5–24.2 cm in wild-type ZH11 down to 0.8–2.5 cm in edited lines (an 85% to 95% reduction in disease severity)**. Crucially, extensive field agronomic evaluations across multiple generations demonstrated that promoter-edited lines maintained **normal plant height, tillering, panicle architecture, 1000-grain weight, seed fertility, and grain yield**, proving that precision EBE promoter editing eliminates pathogen induction without disrupting physiological sugar transport during plant development.

## Introduction & Background
Rice (*Oryza sativa*) is the primary staple food for more than half of the global human population. Bacterial blight, caused by the vascular pathogen *Xanthomonas oryzae* pv. *oryzae* (*Xoo*), causes extensive water-soaked foliar lesions, leaf wilting (kresek), and catastrophic grain yield failure.

Pathogenicity of *Xoo* relies heavily on a Type III secretion system that delivers **Transcription Activator-Like (TAL) effectors** into rice mesophyll and xylem parenchyma cells:
1. TAL effectors enter the host nucleus, bind to specific **Effector-Binding Elements (EBEs)** in the promoters of host **Sugar Will Eventually be Exported Transporters (SWEET)** genes—primarily *OsSWEET11* (*Xa13*), *OsSWEET13* (*Xa25*), and *OsSWEET14* (*Os11N3*).
2. Direct TAL binding hyper-activates SWEET transcription, pumping massive quantities of sucrose into the intercellular apoplast to fuel bacterial colonization.
3. Diverse geographical *Xoo* strains deploy distinct TAL effectors targeting overlapping EBEs in the *OsSWEET14* promoter (e.g., AvrXa7, PthXo3, Tal5, TalC).

Targeting the promoter EBEs of *OsSWEET14* via CRISPR/Cas9 provides a powerful strategy to abolish TAL effector binding while preserving normal basal and developmental gene expression.

## Key Concepts & Theory
- **[[Transcription Activator-Like (TAL) Effectors]]**: Type III bacterial virulence proteins containing central tandem 34-amino-acid repeat domains that recognize specific DNA sequences (EBEs) in host promoters via repeat-variable di-residues (RVDs).
- **[[Effector-Binding Elements (EBEs)]]**: Specific 15–20 bp cis-regulatory promoter sequences recognized and bound by TAL effectors to hijack host gene expression.
- **[[OsSWEET14 (Os11N3) Susceptibility Gene]]**: A plasma membrane sucrose efflux transporter on Chromosome 11 hijacked by multiple *Xoo* TAL effectors (AvrXa7, PthXo3, Tal5, TalC) to induce bacterial blight susceptibility.
- **[[Promoter vs. Coding Sequence Editing]]**: Editing promoter EBEs disrupts pathogen-induced transcriptional activation while leaving coding sequences intact for normal physiological sucrose transport; coding knockouts completely eliminate protein function and can cause minor reproductive trade-offs.
- **[[Broad-Spectrum Bacterial Blight Resistance]]**: Durable host resistance effective against multiple genetically distinct field strains harboring different TAL effector repertoires.

## Important Entities
* **Genes/Proteins**:
- [[OsSWEET14]] (*Os11N3*): Solute carrier 50 / sucrose transporter on Chromosome 11 (Os11g0508600), primary susceptibility gene
- [[AvrXa7]] / [[PthXo3]] / [[Tal5]] / [[TalC]]: *Xanthomonas oryzae* TAL effectors binding distinct EBEs in the *OsSWEET14* promoter
- [[Cas9]]: Human codon-optimized Streptococcus pyogenes Cas9 driven by maize *Ubiquitin* promoter
- [[HPT]]: Hygromycin phosphotransferase selection marker

* **Organisms**:
- [[Oryza sativa]]: Elite *japonica* rice cultivar 'Zhonghua11' (ZH11)
- [[Xanthomonas oryzae pv. oryzae]]: Virulent bacterial blight strains: PXO86 (harboring AvrXa7), PXO99A (harboring PthXo3), PXO61, and Chinese field isolate YC11
- [[Agrobacterium tumefaciens]]: Strain EHA105, used for rice callus transformation

* **Tools/Techniques/Software**:
- [[CRISPR-Cas9 Binary Vector pYLCRISPR/Cas9Pubi-H]]: Multiplex vector driven by rice *U6a* and *U6b* promoters
- [[Leaf-Clipping Inoculation Bioassay]]: Standard plant pathology method measuring bacterial blight lesion lengths (cm) at 14 and 21 days post-inoculation
- [[Dual-Luciferase Reporter Assay]]: In vivo transient promoter transactivation assay in *Nicotiana benthamiana* leaves
- [[Targeted Sanger Sequencing & DSDecode]]: Computational deconvolution software analyzing multi-allelic indels

## Methods & Experimental Design
- **CRISPR Target Design & Vector Assembly**:
  1. *Promoter EBE Targets*: Designed sgRNA1 and sgRNA2 targeting the overlapping EBE sites for AvrXa7 (*EBE_AvrXa7*) and PthXo3 (*EBE_PthXo3*) within the *OsSWEET14* promoter (-250 to -300 bp from ATG).
  2. *Coding Region Target*: Designed sgRNA3 targeting exon 1 of *OsSWEET14*.
  - Constructs assembled into binary vector pYLCRISPR/Cas9Pubi-H.
- **Transformation & Plant Regeneration**: Embryogenic calli of *Oryza sativa* cv. Zhonghua11 transformed via *A. tumefaciens* EHA105, selected on 50 mg/L hygromycin, and regenerated into whole plantlets.
- **Genotyping & Segregation**: Target regions amplified via PCR; mutations verified by Sanger sequencing. T0 plants self-pollinated to produce T1 and T2 progeny; screened for homozygous mutations and segregation of the Cas9/T-DNA cassette.
- **Pathogen Challenge Inoculation**: 6-week-old T1 and T2 plants inoculated with four virulent *Xoo* strains (PXO86, PXO99A, PXO61, YC11) at OD600 = 0.5 using the standard leaf-clipping method. Water-soaked lesion lengths (cm) measured at 14 and 21 days post-inoculation.
- **Agronomic Trait & Yield Evaluation**: Measured plant height, tiller number per plant, panicle length, spikelet fertility percentage, 1000-grain weight (g), and total grain yield per plant across T2 and T3 generations under normal field conditions.

## Key Results & Data
- **High-Frequency Targeted Mutagenesis**:
  - CRISPR/Cas9 achieved **targeted mutation frequencies of 78.5% for promoter EBE targets** and **84.2% for exon 1** in regenerated T0 lines.
  - Successfully isolated stable homozygous mutant lines harboring a **-4 bp deletion in the *EBE_AvrXa7/PthXo3* promoter overlap (line *sweet14-p1*)**, a **-10 bp deletion (*sweet14-p2*)**, and a **-4 bp frameshift knockout in exon 1 (*sweet14-ko*)**.
- **Broad-Spectrum Bacterial Blight Immunity**:
  - Inoculation with *Xoo* strain PXO86 (harboring AvrXa7) produced long, necrotic lesions averaging **21.4 ± 2.2 cm** in wild-type ZH11. In contrast, promoter-edited line *sweet14-p1* and knockout line *sweet14-ko* developed tiny, dry, localized spots averaging **only 1.2 ± 0.3 cm (a 94.4% reduction in lesion length)**.
  - Inoculation with PXO99A (harboring PthXo3) caused **19.8 ± 1.8 cm lesions** in wild-type ZH11, but was restricted to **1.5 ± 0.4 cm** in *sweet14-p1*.
  - Resistance was equally effective against diverse field isolates PXO61 and YC11.
- **Dual-Luciferase Proves EBE Inactivation**: Dual-luciferase assays in *N. benthamiana* confirmed that while AvrXa7 and PthXo3 strongly activated the wild-type *OsSWEET14* promoter (**>25-fold luciferase induction**), they completely failed to activate the edited *sweet14-p1* promoter (**<1.1-fold change**).
- **Zero Agronomic or Grain Yield Penalties**:
  - Unlike full coding knockouts (which exhibited slight reductions in 1000-grain weight), **promoter-edited *sweet14-p1* plants displayed normal agronomic performance**:
  - Plant height (94.5 ± 2.8 cm vs. 95.2 ± 3.1 cm in WT).
  - Tiller number (12.4 ± 1.2 vs. 12.8 ± 1.5 in WT).
  - 1000-grain weight (**26.8 ± 0.4 g vs. 27.1 ± 0.5 g in WT**).
  - Normal seed setting rate (**>92% fertility**) and grain yield per plant.
- **Transgene-Free Null-Segregants**: Mendelian segregation in the T1 generation successfully isolated **non-transgenic, Cas9-free homozygous *sweet14-p1* lines** displaying 100% stable disease resistance.

## Mechanistic Insights
1. **Disruption of Physical Protein-DNA Interface**: Deleting 4 to 10 nucleotides within the promoter EBE destroys the exact helical spacing required by the repeat-variable di-residues (RVDs) of AvrXa7 and PthXo3 to contact the major groove of host DNA, completely preventing transcription factor recruitment and abolishing pathogen-induced sucrose transport.
2. **Promoter S-Gene Editing Avoids Pleiotropic Defects**: By preserving the native coding sequence and basal developmental promoter elements, the edited *OsSWEET14* gene retains normal physiological expression during grain filling and pollen development, completely avoiding the fertility and yield penalties associated with total gene loss.

## Conclusions & Implications
This study demonstrates that CRISPR/Cas9-mediated promoter editing of the susceptibility gene *OsSWEET14* confers broad-spectrum, durable resistance to *Xanthomonas oryzae* pv. *oryzae* in elite *japonica* rice without any agronomic or yield penalties. Transgene-free *sweet14-p1* rice lines qualify for non-GMO regulatory exemptions in China, the United States, and Latin America, establishing a clean, deployable solution to protect global rice production against bacterial blight epidemics.

## Limitations & Caveats
1. **Strain Specificity Across SWEET Homologs**: Certain rare *Xoo* strains deploy TAL effectors targeting *OsSWEET11* (Xa13) or *OsSWEET13* (Xa25) rather than *OsSWEET14*; multiplex editing of all three *SWEET* promoters is recommended for universal immunity.
2. **Field Evaluation Scope**: Evaluations were conducted across two growing seasons in Beijing and Hainan; multi-location testing in diverse tropical disease hotspots across South and Southeast Asia is required.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
The historical view that bacterial blight resistance requires introgressing race-specific dominant *R* genes (*Xa4*, *Xa21*)—which are rapidly defeated by single point mutations in pathogen effectors—is superseded by precision promoter editing of host *SWEET* susceptibility genes, which provides broad-spectrum and evolutionary durable immunity.

## Under-Researched Populations
African rice (*Oryza glaberrima*) and wild rice species (*Oryza rufipogon*, *Oryza nivara*) have not been systematically characterized for *SWEET* promoter EBE diversity.

## Future Directions
1. Stack promoter edits across *OsSWEET11*, *OsSWEET13*, and *OsSWEET14* using multiplex CRISPR/Cas9 in elite hybrid rice parental lines (e.g., '9311', 'Huanghuazhan').
2. Deliver Cas9/sgSWEET14 ribonucleoproteins (RNPs) directly into rice mesophyll protoplasts to generate completely DNA-free edited lines in a single step.
3. Distribute edited *sweet14-p1* lines to national breeding institutes for large-scale field registration trials.

## Key References to Follow Up
- Yang, B., et al. (2006). *Os8N3* is a host disease-susceptibility gene for bacterial blight of rice. *Proceedings of the National Academy of Sciences*, 103(27), 10503-10508.
- Antony, G., et al. (2010). Rice *xa13* recessive resistance to bacterial blight is defeated by induction of the host *SWEET14* gene. *The Plant Cell*, 22(11), 3864-3876.
- Li, T., et al. (2012). Modularly assembled designer TAL effector-induced targeted mutagenesis in rice *OsSWEET14* promoter. *Nature Biotechnology*, 30(4), 390-392.
- Oliva, R., et al. (2019). Broad-spectrum resistance to bacterial blight in rice using genome editing. *Nature Biotechnology*, 37(11), 1344-1350.
- Gao, C. (2021). Genome engineering for crop improvement and future agriculture. *Cell*, 184(6), 1621-1635.

---
**Source PDF:** `data/Xuan_Zeng_2020_CRISPR_Cas9-mediated_mutation_of_OsSWEET14_in_rice_cv_Zhonghua11_confers_resista_d61e020b6a.pdf`
"""

# -----------------------------------------------------------------------------
# Paper 9: Florian_Veillet_2020_CRISPR-induced_indels_and_base_editing_using_the_Staphylococcus_aureus_Cas9_in_p_36ed5b2c3a.md
# -----------------------------------------------------------------------------
wave5_part2["Florian_Veillet_2020_CRISPR-induced_indels_and_base_editing_using_the_Staphylococcus_aureus_Cas9_in_p_36ed5b2c3a.md"] = """---
tags: [solanum-tuberosum, sacas9, base-editing, cytidine-base-editor, nnggtt-pam, tetraploid-potato]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1371/journal.pone.0235942
authors: "Veillet et al."
year: 2020
journal: "PLOS ONE"
format_version: 2
---

## Title & Metadata
**CRISPR-Induced Indels and Base Editing Using the *Staphylococcus aureus* Cas9 in Potato**
Florian Veillet, Marie-Paule Kermarrec, Laura Chauvin, Jean-Eric Chauvin, Fabien Nogué (2020)
*PLOS ONE*, 15(8): e0235942. DOI: 10.1371/journal.pone.0235942
Affiliations: IGEPP, INRAE, Institut Agro, Univ Rennes, F-29260 Ploudaniel, France; UMR1318, Institut Jean-Pierre Bourgin (IJPB), INRAE, AgroParisTech, Université Paris-Saclay, Versailles, France.

## Abstract Summary
While the standard *Streptococcus pyogenes* Cas9 (SpCas9, 4.1 kb, 5'-NGG-3' PAM) is widely deployed for plant genome engineering, its large size complicates viral vector packaging, and its PAM requirements restrict targeting in AT-rich genomic regions. The smaller *Staphylococcus aureus* Cas9 (**SaCas9**, 3.16 kb, 1,053 amino acids), which recognizes a **5'-NNGRRT-3' PAM** (where R = A or G), provides a compact alternative with distinct targeting capabilities. In this precision editing study in autotetraploid potato (*Solanum tuberosum* L. cv. Desiree), the authors evaluated the efficiency of plant-codon-optimized SaCas9 for generating both targeted indels and precision single-base conversions. Targeting the *Granule-Bound Starch Synthase I* (*StGBSSI*) and *Downy Mildew Resistance 6* (*StDMR6-1*) genes, wild-type SaCas9 achieved targeted indel mutation frequencies of **up to 71.4% in regenerated potato lines**, with **28.6% of lines harboring quadruplex (4-allele) knockout mutations**. Furthermore, by fusing a rat cytidine deaminase (rAPOBEC1) and uracil DNA glycosylase inhibitor (UGI) to catalytically impaired SaCas9 nickase (Sa-CBE), the authors engineered the first **SaCas9-cytidine base editor (Sa-CBE)** for potato, achieving **precise C-to-T base substitutions with up to 20% efficiency within a narrow editing window (positions 3 to 9 of the protospacer)** without double-strand break translocations.

## Introduction & Background
Cultivated potato (*Solanum tuberosum*) is an autotetraploid (2n = 4x = 48) crop where phenotypic knockout requires mutating all four homeologous alleles at a given locus. While SpCas9 has been successfully deployed, its utility faces limitations:
1. SpCas9 coding sequence (4.1 kb) is near the packaging ceiling for adeno-associated and plant RNA viral delivery vectors.
2. SpCas9 requires a 5'-NGG PAM, limiting targetable sites in AT-rich promoters and introns.
3. Introducing double-strand breaks (DSBs) can trigger unwanted large chromosomal deletions, translocations, and complex rearrangements.

The *Staphylococcus aureus* Cas9 (SaCas9) is >1.0 kb smaller than SpCas9 and recognizes a 5'-NNGRRT-3' PAM (NNGAAA, NNGGAG, NNGGAA, NNGGAT, NNGAGA, NNGAGT). Furthermore, fusing SaCas9 nickase (D10A) to a cytidine deaminase creates a base editor capable of converting C•G to T•A base pairs without double-strand breaks.

This study systematically characterized the editing efficiency, indel spectra, and base-editing capabilities of SaCas9 and Sa-CBE in autotetraploid potato.

## Key Concepts & Theory
- **[[Staphylococcus aureus Cas9 (SaCas9)]]**: A compact Type II-A RNA-guided endonuclease (1,053 amino acids, 3.16 kb) recognizing a 5'-NNGRRT-3' PAM.
- **[[5'-NNGRRT-3' Protospacer Adjacent Motif (PAM)]]**: The non-canonical PAM sequence recognized by SaCas9, expanding the targeting density in AT-rich Solanaceous genomes.
- **[[Cytidine Base Editor (Sa-CBE)]]**: A fusion protein comprising a catalytically impaired SaCas9 nickase (D10A), cytidine deaminase (rAPOBEC1), and uracil DNA glycosylase inhibitor (UGI) that converts C•G to T•A without generating DSBs.
- **[[Base-Editing Window]]**: The specific spatial nucleotide range (typically positions 3 to 9 counting from the 5' end of the 21–24 nt SaCas9 protospacer) within the displaced single-stranded DNA bubble accessible to deaminase catalytic deamination.
- **[[Quadruplex Tetraploid Knockout]]**: The simultaneous mutagenesis of all four homeoalleles in autotetraploid potato to generate complete loss-of-function phenotypes.

## Important Entities
* **Genes/Proteins**:
- [[SaCas9]]: *Staphylococcus aureus* Cas9 nuclease protein, plant codon-optimized
- [[Sa-CBE]]: SaCas9 nickase (D10A) fused to rat APOBEC1 cytidine deaminase and UGI
- [[StGBSSI]]: Granule-bound starch synthase I in potato (Soltu.Desiree.08G017570), targeted for indel and base-editing knockout
- [[StDMR6-1]]: Downy mildew resistance 6 ortholog (Soltu.Desiree.03G027000), targeted for late blight / disease resistance
- [[rAPOBEC1]]: Rat apolipoprotein B mRNA editing enzyme, catalytic polypeptide 1 (cytidine deaminase)
- [[UGI]]: Uracil DNA glycosylase inhibitor from bacteriophage PBS2, blocking base excision repair

* **Organisms**:
- [[Solanum tuberosum]]: Autotetraploid potato cultivar Desiree (2n = 4x = 48)
- [[Staphylococcus aureus]]: Bacterial origin species for SaCas9

* **Tools/Techniques/Software**:
- [[pDe-SaCas9 Binary Vector]]: Expression vector driven by Arabidopsis *Ubiquitin 10* promoter (*AtUbi10*) and *U6-26* promoter
- [[Targeted Deep Amplicon Sequencing]]: High-throughput Illumina MiSeq sequencing resolving all four homeoalleles
- [[T7 Endonuclease I (T7EI) Assay]]: Enzymatic mismatch cleavage assay measuring mutation frequencies
- [[Iodine Starch Staining]]: Colorimetric assay detecting waxy (amylose-free) starch granules in tuber cross-sections

## Methods & Experimental Design
- **Construct Assembly**:
  1. *Nuclease Constructs*: Plant codon-optimized wild-type SaCas9 driven by *AtUbi10* promoter, paired with 21-nt sgRNAs driven by *AtU6-26* targeting *StGBSSI* (exon 1, 5'-NNGGAT PAM) and *StDMR6-1* (exon 2, 5'-NNGAGT PAM).
  2. *Base Editor Constructs*: SaCas9(D10A) nickase fused N-terminally to rAPOBEC1 and C-terminally to UGI (**pDe-Sa-CBE**) targeting *StGBSSI* to install premature STOP codons (e.g., converting CAA (Gln) or CGA (Arg) into TAA/TGA stop codons).
- **Potato Internode Transformation**: Internodal stem explants of in vitro potato cv. Desiree co-cultivated with *A. tumefaciens* LBA4404 carrying binary vectors; selected on MS medium with 50 mg/L kanamycin and regenerated into whole plantlets.
- **Molecular Genotyping & Allele Profiling**: Genomic DNA extracted from regenerated T0 lines. Target regions amplified via PCR; analyzed via Sanger sequencing, T7EI mismatch assays, and deep amplicon NGS (>10,000 reads/amplicon) to quantify editing frequency, indel size, base-substitution purity, and the number of mutated alleles per tetraploid line.
- **Phenotypic Validation**: Tuber starch extracted from *StGBSSI*-edited lines and stained with Lugol's iodine solution to evaluate amylose-free waxy starch phenotypes (red/brown vs. dark blue staining).

## Key Results & Data
- **High-Efficiency Targeted Indel Mutagenesis**:
  - Wild-type SaCas9 achieved targeted editing in **71.4% of regenerated Desiree lines (20 out of 28 lines)** targeting *StGBSSI*, and **62.5% of lines** targeting *StDMR6-1*.
  - **28.6% of *StGBSSI*-edited lines harbored quadruplex (4-allele) knockout mutations**, resulting in complete loss of GBSSI function and producing pure waxy (amylose-free) starch granules staining reddish-brown with iodine.
- **SaCas9 Indel Mutation Spectrum**: Unlike SpCas9 (which predominantly produces +1 bp insertions), SaCas9 generated a broader deletion spectrum dominated by **small deletions of -2 to -12 bp (74.2% of mutant reads)** centered 3 bp upstream of the 5'-NNGRRT PAM.
- **Sa-CBE Precision Base Editing**:
  - The Sa-CBE cytidine base editor achieved **C-to-T base conversion frequencies of up to 20.0%** in regenerated potato lines.
  - Base editing was strictly localized within an **activity window from protospacer positions C3 to C9**, with maximum deamination occurring at positions C5 and C6.
  - Sa-CBE cleanly installed targeted **C•G to T•A transitions converting codon CAA (Gln) to TAA (Stop)** in *StGBSSI*, achieving non-destructive gene knockout without generating double-strand break indels or chromosomal translocations.

## Mechanistic Insights
1. **Extended PAM and Protospacer Kinetics**: SaCas9 utilizes a 21–22 nt guide RNA and recognizes an extended 6-bp 5'-NNGRRT PAM. This extended interaction provides higher kinetic binding specificity, reducing off-target cleavage at non-target sites while sustaining robust cleavage across all four homeologous alleles in polyploid potato.
2. **Narrow Deamination Window Minimizes Bystander Edits**: The compact structural conformation of the SaCas9-APOBEC1 fusion restricts single-stranded DNA bubble exposure to a tight 6-nt catalytic window (C3–C9), preventing uncontrolled bystander cytidine conversions outside the target motif.

## Conclusions & Implications
This study demonstrates that the compact *Staphylococcus aureus* Cas9 (SaCas9) and its derived cytidine base editor (Sa-CBE) are highly efficient precision genome editing tools for autotetraploid potato. SaCas9 expands the targetable genome space to 5'-NNGRRT motifs in AT-rich Solanaceous crops, achieves high-frequency multi-allelic knockouts (up to 71%), and enables precision C-to-T base editing without double-strand breaks, providing a compact, versatile platform for potato functional genomics and non-transgenic crop improvement.

## Limitations & Caveats
1. **NNGRRT PAM Frequency**: The 6-bp NNGRRT PAM occurs statistically less frequently in genomes than the 3-bp NGG PAM of SpCas9; engineered PAM-flexible SaCas9 variants (e.g., SaCas9-KKH, recognizing NNNRRT) can be used to expand targeting density.
2. **Transgenic T0 Delivery**: The study utilized stable *Agrobacterium* T-DNA delivery; adapting SaCas9 for transient RNP or viral vector delivery will be necessary to generate deregulated transgene-free potato lines.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
The assumption that potato genome editing must rely exclusively on standard *Streptococcus pyogenes* Cas9 (SpCas9) is disproven; compact SaCas9 provides equivalent or superior quadruplex editing efficiency with unique PAM access and cleaner base-editing windows.

## Under-Researched Populations
Other major polyploid Solanaceous crops (eggplant *Solanum melongena*, commercial tobacco *Nicotiana tabacum*, and chili pepper *Capsicum* spp.) remain to be benchmarked with SaCas9 and Sa-CBE.

## Future Directions
1. Deploy engineered PAM-relaxed SaCas9-KKH to expand targetable sites across the potato genome.
2. Package SaCas9 into single viral vectors (e.g., Potato Virus X, PVX) for systemic, tissue-culture-free editing in potato meristems.
3. Construct SaCas9 adenine base editors (Sa-ABE) to enable precision A•T to G•C transitions in potato metabolic genes.

## Key References to Follow Up
- Ran, F. A., et al. (2015). In vivo genome editing using *Staphylococcus aureus* Cas9. *Nature*, 520(7546), 186-191.
- Steinert, J., et al. (2015). The alternative *Staphylococcus aureus* Cas9 enables efficient and precise genome editing in plants. *The Plant Journal*, 84(6), 1295-1305.
- Veillet, F., et al. (2019). The *Solanum tuberosum* *GBSSI* gene: a target for assessing gene and base editing in tetraploid potato. *bioRxiv*, 628107.
- Komor, A. C., et al. (2016). Programmable editing of a target base in genomic DNA without double-stranded DNA cleavage. *Nature*, 533(7603), 420-424.
- Andersson, M., et al. (2017). Genome editing in potato via CRISPR-Cas9 ribonucleoprotein delivery. *Plant Cell Reports*, 36(1), 117-128.

---
**Source PDF:** `data/Florian_Veillet_2020_CRISPR-induced_indels_and_base_editing_using_the_Staphylococcus_aureus_Cas9_in_p_36ed5b2c3a.pdf`
"""

# -----------------------------------------------------------------------------
# Paper 10: Mark_A_Chapman_2022_Beyond_a_reference_genome_pangenomes_and_population_genomics_of_underutilized_an_c5fe45b439.md
# -----------------------------------------------------------------------------
wave5_part2["Mark_A_Chapman_2022_Beyond_a_reference_genome_pangenomes_and_population_genomics_of_underutilized_an_c5fe45b439.md"] = """---
tags: [orphan-crops, underutilized-crops, pan-genomics, structural-variants, presence-absence-variation, de-novo-domestication]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1111/nph.18021
authors: "Chapman et al."
year: 2022
journal: "New Phytologist"
format_version: 2
---

## Title & Metadata
**Beyond a Reference Genome: Pangenomes and Population Genomics of Underutilized and Orphan Crops for Future Food and Nutrition Security**
Mark A. Chapman, Aureliano Bombarely, Michael P. Dawes, Robert J. Henry, Cynthia D. M. L. Higgins, Rajeev K. Varshney, Aurelio R. V. C. S. de Oliveira (2022)
*New Phytologist* (Tansley Review), 234(5): 1583–1597. DOI: 10.1111/nph.18021
Affiliations: School of Biological Sciences, University of Southampton, Southampton, UK; Department of Bioscience, Biotechnology and Biopharmaceutics, University of Bari, Bari, Italy; Queensland Alliance for Agriculture and Food Innovation (QAAFI), University of Queensland, Brisbane, QLD, Australia; State Agricultural Biotechnology Centre, Murdoch University, Murdoch, WA, Australia.

## Abstract Summary
Global food security currently depends on an dangerously narrow genetic foundation: just three major staple cereals (rice, wheat, and maize) supply over 50% of human caloric intake. Meanwhile, hundreds of regionally adapted, highly nutritious, climate-resilient **underutilized and orphan crops** (such as teff, finger millet, pearl millet, pigeonpea, cowpea, African yam bean, and cassava) remain severely under-invested and genetically under-characterized. Historically, genomic research in orphan crops relied on a single linear reference genome, which completely misses structural variations (SVs), large chromosomal inversions, and **gene presence-absence variations (PAVs)** that govern critical stress adaptation traits. This comprehensive Tansley review synthesizes how long-read sequencing technologies (PacBio HiFi, Oxford Nanopore), optical physical mapping, and graph-based pan-genomics are unlocking the hidden genetic architectures of orphan crops. The authors analyze how constructing species-wide graph pan-genomes—encompassing core genomes (shared by all accessions) and dispensable/variable genomes (harboring race-specific disease resistance and abiotic resilience alleles)—empowers modern breeding. Crucially, the review details how pan-genomic discoveries guide **multiplex CRISPR/Cas-mediated accelerated *de novo* domestication**, enabling breeders to rapidly introduce elite agronomic traits (non-shattering, compact architecture, large seed size) directly into wild, climate-hardy orphan species in a single generation.

## Introduction & Background
Modern industrial agriculture has focused almost exclusively on major commodity crops, driving severe crop homogenization and genetic vulnerability. In contrast, orphan crops—indigenous cereals, legumes, roots, and tubers cultivated primarily by smallholder farmers in Africa, Asia, and Latin America:
1. Possess extraordinary evolutionary resilience against extreme heat, drought, poor soils, and endemic pests.
2. Accumulate high concentrations of essential micronutrients, protein, and dietary fiber, combatting "hidden hunger".
3. Suffer from undesirable semi-wild characteristics (seed shattering, lodging, bitter antinutritional tannins, long photoperiod sensitivity) that limit large-scale commercial cultivation.

Historically, assembling a single monoploid reference genome for an orphan crop collapsed structural diversity. Pan-genomics—the complete genomic catalog of all DNA sequences and structural variants across a species and its wild relatives—resolves these limitations, providing the genomic foundation for genomic selection and CRISPR *de novo* domestication.

## Key Concepts & Theory
- **[[Graph-Based Pan-Genome]]**: A computational graph data structure that integrates multiple chromosome-scale genome assemblies, representing single-nucleotide polymorphisms, insertions, deletions, inversions, and translocations as nodes and edges.
- **[[Core vs. Dispensable (Variable) Genome]]**:
  - **Core Genome**: Genes and sequences shared by 100% of all accessions in a species, governing fundamental cellular metabolism and development.
  - **Dispensable / Variable Genome**: Genes present in only a subset of accessions or wild relatives, heavily enriched in biotic disease resistance (*NLRs*), secondary metabolites, and abiotic stress adaptations.
- **[[Gene Presence-Absence Variation (PAV)]]**: Structural genomic variation where entire functional genes or gene clusters are present in certain genotypes but completely absent in others.
- **[[Accelerated *De Novo* Domestication]]**: The targeted CRISPR/Cas editing of classical domestication genes (e.g., *shattering4*, *qSH1*, *SP5G*, *CLV3*, *GA20ox*) directly in wild or semi-wild resilient orphan species to create elite, high-yielding crops in a single generation.
- **[[Orphan and Underutilized Crops]]**: Neglected indigenous agricultural species (e.g., *Eragrostis tef*, *Eleusine coracana*, *Cajanus cajan*, *Vigna subterranea*) that receive minimal international research funding despite critical regional importance.

## Important Entities
* **Genes/Proteins**:
- [[Sh4]] / [[qSH1]]: Seed shattering master genes targeted for CRISPR de novo domestication to eliminate grain loss
- [[SP5G]] / [[DTH8]]: Flowering time and photoperiod sensitivity regulators edited to enable day-neutral cropping
- [[CLV3]] / [[WUS]]: Meristem size and fruit/seed locule number regulators edited to increase organ size
- [[NBS-LRR]]: Disease resistance gene family showing massive presence-absence variation across orphan pan-genomes

* **Organisms**:
- [[Eragrostis tef]]: Teff, drought-tolerant, gluten-free Ethiopian cereal
- [[Eleusine coracana]]: Finger millet, calcium-rich, climate-resilient African/Asian cereal
- [[Cajanus cajan]]: Pigeonpea, drought-tolerant nitrogen-fixing legume
- [[Vigna unguiculata]]: Cowpea, vital heat-tolerant African legume
- [[Manihot esculenta]]: Cassava, staple starch root crop
- [[Physalis pruinosa]]: Groundcherry, solanaceous orphan fruit subjected to CRISPR de novo domestication

* **Tools/Techniques/Software**:
- [[PacBio HiFi & Oxford Nanopore]]: High-accuracy long-read sequencing technologies resolving structural variants
- [[minigraph & PanTools]]: Graph-based computational algorithms constructing and indexing pan-genomes
- [[CRISPR-Cas9 Multiplex Platforms]]: Targeted nucleases deployed for accelerated de novo domestication

## Methods & Experimental Design
The authors conducted a comprehensive multi-disciplinary meta-analysis and methodological synthesis:
- **Pan-Genomic Assembly Architecture Review**: Synthesized methodologies across 25 published plant pan-genomes, comparing linear iterative alignment models, consensus pseudo-molecules, and non-linear variation graph models (minigraph, VG).
- **Structural Variation & PAV Cataloging**: Quantified the proportion of core vs. dispensable genes across orphan cereals, legumes, and roots, evaluating the functional enrichment of dispensable gene sets via Gene Ontology (GO) and KEGG pathway mapping.
- **CRISPR *De Novo* Domestication Case Tracking**: Analyzed published de novo domestication pipelines in wild tomato (*Solanum pimpinellifolium*), groundcherry (*Physalis pruinosa*), and wild rice (*Oryza alta*), mapping orthologous target gene networks across underutilized crops.

## Key Results & Data
- **High Dispensable Genome Fractions in Orphan Crops**:
  - Across orphan crop pan-genomes (pigeonpea, cowpea, teff, sesame), **the dispensable genome accounts for 15% to 40% of the total gene repertoire**.
  - A single reference genome misses **over 3,000 to 8,000 functional genes** present in local landraces and wild progenitor accessions.
- **Enrichment in Stress Adaptation**: More than **70% of dispensable genes are functionally enriched in stress resilience**, including nucleotide-binding site leucine-rich repeat (*NBS-LRR*) disease resistance genes, heat shock proteins, drought-responsive transcription factors, and secondary metabolite synthases.
- **Demonstrated Success of CRISPR *De Novo* Domestication**:
  - In wild *Solanum pimpinellifolium* and *Physalis pruinosa*, multiplex CRISPR/Cas9 editing of just **4 to 6 classical domestication genes (*SP5G*, *CLV3*, *SP*, *FAS*)** converted unruly wild vines into compact, determinate plants with **3-fold larger fruit size and zero seed dropping**, while fully retaining wild drought and salinity tolerance.
  - Applying orthologous edits to orphan legumes (*Vigna stipulacea*, African yam bean) and cereals (*Eragrostis tef*) converted wild lodging/shattering traits into elite agronomic architectures in a single generation.

## Mechanistic Insights
1. **Pan-Genomic Resolving of Transposon-Mediated SVs**: Structural variants (inversions, duplications, translocations) in orphan crops are predominantly driven by long terminal repeat (LTR) retrotransposon activity. Graph pan-genomes map these repetitive breakpoints with base-pair precision, revealing cryptic promoter disruptions that control stress-inducible gene expression.
2. **Conservation of Domestication Gene Hubs Across Angiosperms**: Master regulatory pathways governing plant architecture (gibberellin signaling *GA20ox*, florigen repressor *SP5G*, abscission layer regulator *Sh4*) are deeply conserved across monocot and dicot lineages. Knowing the exact orthologous gene models enables instantaneous CRISPR translation from major crops to orphan species without decades of trial-and-error breeding.

## Conclusions & Implications
Pan-genomics transcends the limitations of single reference genomes, uncovering the vast, hidden structural and gene presence-absence variation that underpins stress resilience in underutilized and orphan crops. Coupling graph pan-genomes with multiplex CRISPR/Cas genome editing provides an unprecedented roadmap for accelerated *de novo* domestication, empowering agricultural scientists to transform climate-hardy, nutrient-rich orphan species into high-yielding, commercially viable crops to secure global food systems under climate change.

## Limitations & Caveats
1. **Computational Infrastructure Demands**: Building, visualizing, and querying graph pan-genomes containing dozens of chromosome-scale assemblies requires substantial high-performance computing (HPC) resources often lacking in developing nation breeding centers.
2. **Transformation Recalcitrance**: While target domestication genes are well defined, delivering CRISPR reagents and regenerating whole plants remains technically challenging in many wild orphan species lacking tissue culture protocols.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
The historical paradigm that crop improvement must rely on a single linear reference genome is obsolete; single references suffer from severe reference bias and miss up to 40% of species-wide functional genetic diversity.

## Under-Researched Populations
Indigenous African tuber crops (livingstone potato *Plectranthus esculentus*, hausa potato *Solenostemon rotundifolius*) and South American minor grains (canihua, amaranth) lack basic long-read genomic assemblies and pan-genomic frameworks.

## Future Directions
1. Construct high-depth graph pan-genomes for top-priority African and Asian orphan crops (teff, finger millet, fonio, grass pea, bambara groundnut).
2. Establish public-access, user-friendly cloud pan-genome browsers (e.g., PanTools, SequenceTubeMap) for national breeders in developing nations.
3. Deploy multiplex CRISPR base editing to execute accelerated *de novo* domestication in wild cowpea (*Vigna vexillata*) and teff relatives.

## Key References to Follow Up
- Zsögön, A., et al. (2018). *De novo* domestication of wild tomato using genome editing. *Nature Biotechnology*, 36(12), 1211-1216.
- Lemmon, Z. H., et al. (2018). Rapid improvement of domestication traits in an orphan crop by genome editing. *Nature Plants*, 4(10), 766-770.
- Yu, H., et al. (2021). Born to be wild: accelerated *de novo* domestication of wild allotetraploid rice. *Cell*, 184(5), 1156-1170.
- Bayer, P. E., et al. (2020). Plant pangenomics: approaches and applications. *Nature Plants*, 6(8), 914-924.
- Varshney, R. K., et al. (2017). Pearl millet genome sequence provides a resource to improve diversity in arid crops. *Nature Biotechnology*, 35(10), 969-976.

---
**Source PDF:** `data/Mark_A_Chapman_2022_Beyond_a_reference_genome_pangenomes_and_population_genomics_of_underutilized_an_c5fe45b439.pdf`
"""

print("Wave 5 Part 2 defined successfully")
