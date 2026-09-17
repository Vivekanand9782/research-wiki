"""
Generate Wave 3 Summaries for PHS Tolerance
"""
import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path("/Users/vivekanandsirohi/Desktop/antigravity/research-wiki")
sys.path.insert(0, str(root_dir))

from validation import SummaryValidator
from lint_wiki import validate_source_page
from scripts.resummarize_queue import mark_done

SUMMARIES = {}

# 1. xie_2017_phytochrome_interacting_factors
SUMMARIES["xie_2017_phytochrome_interacting_factors"] = """---
tags: [phytochrome, shade avoidance, microrna, transcription factor, plant development]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: 10.1038/s41467-017-00479-9
authors: "Xie et al."
year: 2017
journal: "Nature Communications"
format_version: 2
---

## Title & Metadata
* **Title:** Phytochrome-interacting factors interact with MIR156 to facilitate the shade-avoidance response in Arabidopsis
* **Authors:** Yonggang Xie, Keqiang Liu, Huichuan Dong, Qingyun Guan, Aizhen Qin, Xiaoguang Meng, Long Li, Ligeng Ma, Haiyang Wang
* **Journal:** Nature Communications (2017) 8:348
* **DOI:** 10.1038/s41467-017-00479-9

## Abstract Summary
Plants adjust architectural morphology to compete for sunlight under canopy shade through the shade avoidance syndrome (SAS), which is triggered by reductions in the red to far-red (R:FR) light ratio detected by phytochrome photoreceptors. This study uncovers an essential molecular pathway linking light quality perception to the conserved miR156-SPL developmental module in *Arabidopsis thaliana*. The authors demonstrate that simulated canopy shade rapidly represses *MIR156* transcription, specifically downregulating primary transcripts *pri-miR156b*, *pri-miR156d*, *pri-miR156f*, and *pri-miR156h*, leading to reduced mature [[miR156]] abundance and subsequent derepression of its target [[SPL]] (SQUAMOSA PROMOTER BINDING PROTEIN-LIKE) genes (notably [[SPL3]], [[SPL9]], [[SPL10]], [[SPL13]], and [[SPL15]]). Phytochrome-interacting factors ([[PIF1]], [[PIF3]], [[PIF4]], and [[PIF5]]) act as direct transcriptional repressors by binding canonical G-box and PBE-box *cis*-regulatory motifs within *MIR156* promoters. Genetic analyses confirm that miR156 overexpression or loss of *SPL* function impairs shade-induced hypocotyl elongation and petiole elongation, establishing that the PIF-miR156-SPL signaling cascade is indispensable for full SAS expression in plants.

## Introduction & Background
* Canopy shade causes a decrease in the ratio of red (R, 660 nm) to far-red (FR, 730 nm) light due to preferential absorption of red light by photosynthetic pigments in upper leaves.
* In response to low R:FR ratios, shade-intolerant plants trigger the shade avoidance syndrome (SAS), characterized by accelerated hypocotyl, stem, and petiole elongation, leaf hyponasty, and early flowering.
* Inactivation of phytochrome B ([[phyB]]) under low R:FR conditions stabilizes basic helix-loop-helix (bHLH) transcription factors known as Phytochrome-Interacting Factors ([[PIF1]], [[PIF3]], [[PIF4]], [[PIF5]], and [[PIF7]]), which directly activate genes involved in auxin biosynthesis (e.g., [[YUC8]], [[YUC9]]), brassinosteroid signaling, and cell wall loosening.
* The microRNA156 ([[miR156]]) family targets [[SPL]] transcription factor genes to regulate juvenile-to-adult vegetative phase change, flowering time, shoot branching, and abiotic stress responses.
* While both PIF signaling and the miR156-SPL module are vital for plant adaptation, how phytochrome signaling directly modulates miR156 biogenesis during shade avoidance remained unresolved prior to this investigation.

## Key Concepts & Theory
- **[[Shade Avoidance Syndrome]]**: An adaptive morphological response wherein shade-intolerant plants elongate hypocotyls and petioles under low red to far-red light ratios to outgrow competing vegetation.
- **[[Phytochrome-Interacting Factors]]**: A class of basic helix-loop-helix (bHLH) transcription factors that accumulate in low red to far-red light and mediate shade-induced growth responses.
- **[[miR156-SPL Module]]**: An evolutionarily conserved microRNA regulatory network where miR156 downregulates SQUAMOSA PROMOTER BINDING PROTEIN-LIKE transcription factors to control plant developmental phase transitions.
- **[[G-box Motif]]**: A hexameric DNA sequence (CACGTG) recognized by bHLH transcription factors to modulate downstream target gene expression.
- **[[Photoreceptor Signaling]]**: The biochemical perception of light quality changes by phytochromes leading to signal transduction that alters transcription and developmental plasticity.

## Important Entities
* **Genes/Proteins**: [[PIF1]], [[PIF3]], [[PIF4]], [[PIF5]], [[PIF7]], [[phyB]], [[phyA]], [[miR156]], [[pri-miR156a]], [[pri-miR156b]], [[pri-miR156c]], [[pri-miR156d]], [[pri-miR156e]], [[pri-miR156f]], [[pri-miR156g]], [[pri-miR156h]], [[pri-miR156i]], [[SPL3]], [[SPL9]], [[SPL10]], [[SPL13]], [[SPL15]], [[MIM156]], [[YUC8]], [[YUC9]], [[IAA19]], [[HAT2]], [[ATHB2]]
* **Organisms**: [[Arabidopsis thaliana]]
* **Tools/Techniques/Software**: [[Chromatin Immunoprecipitation]] (ChIP-qPCR), [[Electrophoretic Mobility Shift Assay]] (EMSA), [[Dual-Luciferase Reporter Assay]], [[Real-Time Quantitative RT-PCR]], [[Stem-Loop RT-qPCR]], [[Yeast One-Hybrid Assay]]

## Methods & Experimental Design
* Plant materials: *Arabidopsis thaliana* wild-type (Col-0, Ws, Ler), mutant lines (*pifq* quadruple mutant [*pif1-1 pif3-3 pif4-2 pif5-3*], *pif4-2*, *pif5-3*, *pif7-1*, *phyB-9*, *spl9-4 spl15-1*, *spl3 spl4 spl5*), and transgenic lines (*35S::miR156a*, *35S::MIM156*, *35S::rSPL9*, *35S::rSPL15*, *pPIF4::PIF4-MYC*, *pPIF5::PIF5-MYC*).
* Light treatments: Seedlings grown under continuous white light (W, R:FR = 6.8) for 6 days were transferred to simulated shade (W + FR, R:FR = 0.05) or maintained in white light.
* Gene expression analysis: Stem-loop RT-qPCR for mature miR156 and standard RT-qPCR for *pri-miR156* transcripts and *SPL* downstream genes.
* DNA-protein interaction assays: Electrophoretic mobility shift assays (EMSA) using recombinant GST-PIF4/5 proteins and biotin-labeled *MIR156* promoter probes; Chromatin immunoprecipitation (ChIP-qPCR) using anti-MYC antibodies in transgenic seedlings; transient dual-luciferase reporter assays in *Nicotiana benthamiana* leaves and Arabidopsis protoplasts.
* Phenotyping: Hypocotyl and petiole length measurements, plant dry weight, and flowering time under high and low R:FR conditions.

## Key Results & Data
* **Shade downregulates miR156**: Low R:FR treatment rapidly reduced mature miR156 levels by >50% within 1 to 4 hours in wild-type Col-0, accompanied by sharp declines in primary transcripts *pri-miR156b*, *pri-miR156d*, *pri-miR156f*, and *pri-miR156h*.
* **Derepression of SPLs under shade**: Transcription levels of *SPL3*, *SPL9*, *SPL10*, *SPL13*, and *SPL15* increased 2- to 4-fold within 2 hours of shade exposure.
* **PIF dependence**: In the *pifq* (*pif1 pif3 pif4 pif5*) mutant, shade-induced downregulation of miR156 and upregulation of *SPL* genes were completely abolished, while *phyB* mutants exhibited constitutively low miR156 levels and high *SPL* expression in white light.
* **Direct binding to G-boxes**: ChIP-qPCR and EMSA confirmed that PIF4 and PIF5 directly bind G-box motifs (CACGTG) within the promoter regions of *MIR156B*, *MIR156D*, *MIR156F*, and *MIR156H*. Dual-luciferase assays demonstrated that PIFs directly repress *pMIR156::LUC* transcription.
* **Phenotypic necessity of miR156-SPL module**: *35S::miR156* plants and *spl* higher-order mutants showed significantly reduced hypocotyl and petiole elongation in response to shade compared to wild-type, whereas *35S::MIM156* and *35S::rSPL9* lines displayed constitutive shade avoidance phenotypes.

## Mechanistic Insights
* Phytochromes (primarily [[phyB]]) act as upstream light sensors; under low R:FR shade, Active Pfr converts to inactive Pr, preventing degradation and promoting accumulation of [[PIF1]], [[PIF3]], [[PIF4]], and [[PIF5]].
* Stabilized PIFs function as transcriptional repressors by directly binding to G-box motifs in *MIR156* promoter regions (*MIR156B/D/F/H*), inhibiting their transcription.
* The resulting decline in [[miR156]] relieves post-transcriptional cleavage and translational repression of [[SPL]] mRNAs.
* Derepressed SPL transcription factors promote downstream growth-promoting target genes that drive cell elongation in hypocotyls and petioles, orchestrating the full shade avoidance response.

## Conclusions & Implications
* This study identifies the PIF-miR156-SPL signaling cascade as a direct transcriptional link connecting light photoreception to microRNA-regulated developmental plasticity in plants.
* The findings demonstrate that PIF transcription factors can act as direct transcriptional repressors, expanding their recognized regulatory repertoire beyond transcriptional activation.
* The integration of environmental light signaling with the miR156-SPL vegetative phase transition module provides a molecular framework for understanding how shade alters plant architecture and crop canopy density.

## Limitations & Caveats
* The study was conducted exclusively in the dicot model plant *Arabidopsis thaliana* under controlled laboratory light chambers, requiring validation in crop monocots like wheat and barley.
* Although PIF7 is a major factor in shade avoidance, its specific contribution to *MIR156* promoter repression was not directly evaluated via ChIP due to lack of suitable tagged lines.

## Contradictory Findings
* Not reported in this paper.

## Outdated Models
* Refutes the assumption that PIF transcription factors act strictly as transcriptional activators of growth genes, proving that PIFs also function as direct sequence-specific transcriptional repressors on microRNA promoters.

## Under-Researched Populations
* Monocot cereal crops (wheat, barley, maize) exhibiting shade avoidance, tillering suppression, and preharvest sprouting dynamics under crowded canopy conditions.

## Future Directions
* Investigate whether the PIF-miR156-SPL pathway is conserved in cereal crops and whether it influences tillering, spike architecture, or seed dormancy during canopy closure.
* Determine the molecular co-repressors that interact with PIFs to mediate chromatin remodeling and transcriptional repression at *MIR156* loci.

## Key References to Follow Up
* **Franklin KA, et al. (2011)** *Phytochrome-interacting factor 4 (PIF4) regulates auxin biosynthesis at high temperature.* Proc. Natl. Acad. Sci. USA 108:20231-20235.
* **Wu G, et al. (2009)** *The sequential action of miR156 and miR172 regulates juvenile-to-adult vegetative phase transition in Arabidopsis.* Cell 138:750-759.
* **de Wit M, et al. (2016)** *Plant development in the shade: integrating light, hormone, and clock signals.* Trends Plant Sci. 21:1059-1073.

---
**Source PDF:** `data/xie_2017_phytochrome_interacting_factors.pdf`
"""

# 2. cao_2016_detection_qtls_traits
SUMMARIES["cao_2016_detection_qtls_traits"] = """---
tags: [seed dormancy, preharvest sprouting, quantitative trait loci, epistasis, triticum aestivum]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: 10.1270/jsbbs.66.260
authors: "Cao et al."
year: 2016
journal: "Breeding Science"
format_version: 2
---

## Title & Metadata
* **Title:** Detection of QTLs for traits associated with preharvest sprouting resistance in bread wheat (Triticum aestivum L.)
* **Authors:** Lianlian Cao, Kazunori Hayashi, Masayuki Tokui, Masahiro Mori, Hitoshi Miura, Kazumitsu Onishi
* **Journal:** Breeding Science (2016) 66:260-270
* **DOI:** 10.1270/jsbbs.66.260

## Abstract Summary
Preharvest sprouting (PHS) in bread wheat (*Triticum aestivum* L.) causes substantial economic losses by degrading end-use flour quality. To dissect the genetic architecture of PHS resistance and associated agronomic traits, a mapping population of 127 recombinant inbred lines (RILs) derived from a cross between the highly dormant, PHS-resistant Japanese red wheat cultivar 'Zenkoujikomugi' and the moderately dormant cultivar 'Chinese Spring' was investigated over two seasons. Quantitative trait locus (QTL) analysis revealed three major QTLs controlling grain dormancy: *QDor-1B* on chromosome 1BL (LOD 4.0, R² = 13.9%, where the Chinese Spring allele increased dormancy), *QDor-3A* on chromosome 3AS (co-localizing with [[TaMFT]], LOD 6.9, R² = 22.3%, Zenkoujikomugi allele conferring dormancy), and *QDor-4A* on chromosome 4AL (LOD 4.3, R² = 14.8%, Zenkoujikomugi allele conferring dormancy). In addition, *QHt-7B* (co-localizing with [[Vrn-B3]], LOD 12.0, R² = 35.6%) controlled heading date and plant height, while *QAwn-4A* (co-locating with [[Hd]] / *Hooded*) and *QAwn-6B* (co-locating with [[B2]] / *wmc397*) controlled awn development. Strong epistatic interactions were detected among *QDor-1B*, *QDor-3A*, and *QDor-4A*, demonstrating that combining dormant alleles across these three distinct loci synergistically optimizes PHS tolerance.

## Introduction & Background
* Preharvest sprouting (PHS) is triggered when mature wheat spikes encounter prolonged rain and high humidity prior to harvest, stimulating alpha-amylase production and starch degradation.
* Seed dormancy (SD) is the primary physiological mechanism protecting wheat grains against PHS, but is genetically complex and influenced by environmental temperature during seed maturation.
* The Japanese cultivar 'Zenkoujikomugi' has long been recognized as a prime genetic donor for high seed dormancy and PHS resistance, possessing the dormant allele of *TaMFT* (*TaPHS1*) on chromosome 3AS.
* Previous studies established that while *TaMFT* is a critical dormancy determinant, additional QTLs on group 1, group 4, and group 7 chromosomes contribute significantly to variation in dormancy and spike morphology traits such as awnedness.
* This study was designed to map QTLs for grain dormancy, heading date, plant height, and awn length, and to analyze their additive and epistatic interactions in the Zenkoujikomugi × Chinese Spring RIL population.

## Key Concepts & Theory
- **[[Seed Dormancy]]**: The temporary failure of an intact viable seed to germinate under favorable environmental conditions, providing protection against preharvest sprouting.
- **[[Preharvest Sprouting]]**: The premature germination of grain on the maternal ear before harvest, leading to enzymatic starch breakdown and degraded breadmaking quality.
- **[[Epistasis]]**: Non-linear genetic interactions between distinct loci where the phenotypic effect of one allele depends on the genotype present at another locus.
- **[[Germination Index]]**: A weighted mathematical index quantifying seed germination speed and depth of dormancy over time.
- **[[Recombinant Inbred Lines]]**: Stable homozygous mapping progeny derived through repeated self-pollination from an initial biparental cross.

## Important Entities
* **Genes/Proteins**: [[TaMFT]], [[Vrn-B3]], [[Hd]], [[B2]], [[R-A1]], [[R-B1]], [[R-D1]]
* **Organisms**: [[Triticum aestivum]] (wheat cv. 'Zenkoujikomugi', cv. 'Chinese Spring')
* **Tools/Techniques/Software**: [[Simple Sequence Repeat]] (SSR markers), [[Composite Interval Mapping]] (CIM), [[WinQTLCartographer]], [[Mapmaker/Exp]], [[Germination Index Assay]]

## Methods & Experimental Design
* Plant population: 127 F8/F9 recombinant inbred lines (RILs) developed by single-seed descent from Zenkoujikomugi × Chinese Spring.
* Field evaluations: Grown in Obihiro, Hokkaido, Japan across two cropping seasons (2012 and 2013) in randomized complete block designs.
* Phenotyping traits: Grain dormancy was evaluated as Germination Index (GI) and Germination Rate (GR) at 15 °C and 20 °C using seeds harvested at physiological maturity (loss of green spike color). Heading date (days from June 1), plant height (cm), and awn length (mm) were recorded.
* Molecular marker genotyping: 218 SSR markers, sequence-tagged site (STS) markers including *UCW99* (*Vrn-B3*), and *TaMFT* promoter cleaved amplified polymorphic sequence (CAPS) markers were mapped across all 21 wheat chromosomes.
* Statistical analysis: Linkage map construction using Mapmaker/Exp v3.0; QTL detection by Composite Interval Mapping (CIM) and Multiple Interval Mapping (MIM) in WinQTLCartographer v2.5; two-way ANOVA for epistatic interactions.

## Key Results & Data
* **Grain dormancy QTLs**:
  * *QDor-3A* (flanked by *barc321-TaMFT* on 3AS): LOD 6.9, explaining 22.3% of phenotypic variance; Zenkoujikomugi allele increased dormancy (reduced GI).
  * *QDor-1B* (flanked by *barc181-wmc406* on 1BL): LOD 4.0, explaining 13.9% of phenotypic variance; Chinese Spring allele increased dormancy.
  * *QDor-4A* (flanked by *cfa2256-wmc48* on 4AL): LOD 4.3, explaining 14.8% of phenotypic variance; Zenkoujikomugi allele increased dormancy.
* **Morphological and developmental QTLs**:
  * *QHt-7B* / *QHeading-7B* (flanked by *UCW99* / *Vrn-B3* on 7BS): LOD 12.0, explaining 35.6% of phenotypic variation for heading date and plant height; Zenkoujikomugi allele conferred earlier heading and reduced plant height.
  * *QAwn-4A* (linked to *cfa2256* near *Hd* locus): LOD 19.3, R² = 50.1% for awn suppression (awnless phenotype from Zenkoujikomugi).
  * *QAwn-6B* (linked to *wmc397* near *B2* locus): LOD 18.7, R² = 49.0% for awn development.
* **Epistatic interactions**: Two-way ANOVA revealed significant epistasis between *QDor-1B* and *QDor-3A* (P < 0.05), and between *QDor-3A* and *QDor-4A*. Lines carrying dormant alleles at all three loci (*QDor-1B_CS*, *QDor-3A_Zen*, *QDor-4A_Zen*) exhibited significantly deeper dormancy than lines with any single resistant allele.

## Mechanistic Insights
* Seed dormancy in Zenkoujikomugi is polygenically governed by a multi-locus regulatory network comprising [[TaMFT]] on 3AS, an independent 4AL locus (*QDor-4A*), and a 1BL locus (*QDor-1B*) contributed by Chinese Spring.
* Co-localization of *QDor-4A* with the awn suppression locus *Hd* suggests either tight genetic linkage or pleiotropic influence of spike morphology genes on grain microenvironment and dormancy.
* The additive and epistatic coordination among 1BL, 3AS, and 4AL loci indicates that dormancy maintenance requires concurrent signaling inputs across distinct homoeologous genomic compartments.

## Conclusions & Implications
* Zenkoujikomugi harbors major dormancy alleles at *QDor-3A* (*TaMFT*) and *QDor-4A*, while Chinese Spring unexpectedly contributes a beneficial dormancy allele at *QDor-1B*.
* Pyramiding the dormant alleles from 1BL, 3AS, and 4AL via marker-assisted selection provides superior PHS tolerance compared to relying solely on *TaMFT*.
* Diagnostic SSR markers (*barc181*, *TaMFT*, *cfa2256*) enable precise multi-locus breeding for enhanced grain dormancy in bread wheat.

## Limitations & Caveats
* The mapping population was evaluated in a single geographical region (Obihiro, Japan), although replicated across two consecutive years.
* Fine mapping was not performed for the 1BL and 4AL intervals, leaving causal genes underlying *QDor-1B* and *QDor-4A* unisolated in this dataset.

## Contradictory Findings
* Not reported in this paper.

## Outdated Models
* Corrects the single-gene assumption that Zenkoujikomugi dormancy is exclusively conferred by *TaMFT* on 3AS, demonstrating indispensable contributions from *QDor-4A* and Chinese Spring-derived *QDor-1B*.

## Under-Researched Populations
* White-grained elite cultivars carrying combinations of group 1, 3, and 4 dormancy alleles under diverse field environments and rainfall conditions.

## Future Directions
* Fine-map *QDor-1B* and *QDor-4A* to isolate the underlying causal genes and determine their functional interaction with *TaMFT*.
* Evaluate the agronomic and breadmaking performance of RILs combining all three dormancy QTLs in commercial breeding backgrounds.

## Key References to Follow Up
* **Nakamura S, et al. (2011)** *A wheat homolog of MOTHER OF FT AND TFL1 acts in the regulation of seed dormancy.* Plant Cell 23:3215-3229.
* **Mori M, et al. (2005)** *Mapping QTLs for grain dormancy on wheat chromosome 3A and the group 4 chromosomes, and their combined effect.* Theor. Appl. Genet. 110:1315-1323.
* **Torada A, et al. (2005)** *A major gene for seed dormancy on wheat chromosome 4A.* Genome 48:143-151.

---
**Source PDF:** `data/cao_2016_detection_qtls_traits.pdf`
"""

# 3. walkersimmons_1987_aba_levels_sensitivity
SUMMARIES["walkersimmons_1987_aba_levels_sensitivity"] = """---
tags: [abscisic acid, seed dormancy, preharvest sprouting, embryo sensitivity, triticum aestivum]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: 10.1104/pp.84.1.61
authors: "Walker-Simmons"
year: 1987
journal: "Plant Physiology"
format_version: 2
---

## Title & Metadata
* **Title:** ABA Levels and Sensitivity in Developing Wheat Embryos of Sprouting Resistant and Susceptible Cultivars
* **Authors:** M. K. Walker-Simmons
* **Journal:** Plant Physiology (1987) 84(1):61-66
* **DOI:** 10.1104/pp.84.1.61

## Abstract Summary
Preharvest sprouting (PHS) in wheat (*Triticum aestivum* L.) results from premature germination of grain before harvest, causing severe downgrading of milling and baking quality. To investigate the physiological and hormonal basis of sprouting resistance, this foundational study compared endogenous abscisic acid ([[ABA]]) concentrations and embryonic ABA responsiveness throughout grain development in two contrasting white wheat cultivars: the sprouting-resistant cv. 'Brevor' and the sprouting-susceptible cv. 'Greer'. Using an indirect enzyme-linked immunosorbent assay (ELISA) with monoclonal antibodies, endogenous ABA levels in developing embryos were determined to be comparable between Brevor and Greer, peaking at 1 to 5 microM (20-30 days post-anthesis [DPA]) and declining during seed desiccation, with Greer exhibiting only ~25% lower peak levels. In stark contrast, dramatic differences were observed in embryo sensitivity to exogenous ABA. Isolated embryos of susceptible 'Greer' lost responsiveness to ABA upon desiccation (>40 DPA), germinating rapidly (80-100%) even in 50 microM ABA. Conversely, embryos of resistant 'Brevor' maintained extreme ABA responsiveness throughout maturation and after desiccation, where 10 microM ABA completely suppressed germination. Washing isolated embryos did not break Brevor dormancy, proving that dormancy in Brevor is governed by sustained embryonic sensitivity to ABA rather than differences in gross ABA content or leachable germination inhibitors.

## Introduction & Background
* Preharvest sprouting is a major hazard in cereal production, occurring when rainfall wets mature spikes, triggering embryonic alpha-amylase synthesis and endosperm starch breakdown.
* Genetic resistance to PHS is predominantly determined by seed dormancy, which prevents precocious germination in moist conditions.
* Abscisic acid ([[ABA]]) is a principal phytohormone involved in embryogenesis, induction of storage protein synthesis, desiccation tolerance, and the prevention of vivipary.
* Historical hypotheses debated whether differences in seed dormancy between sprouting-resistant and susceptible cultivars stem from variations in endogenous ABA concentrations or differences in embryonic tissue responsiveness to ABA.
* Prior to this work, high-resolution monoclonal antibody-based immunoassay quantification of embryonic ABA and systematic developmental time-course assessments of ABA sensitivity had not been conducted in contrasting wheat cultivars.

## Key Concepts & Theory
- **[[Abscisic Acid Sensitivity]]**: The degree of physiological responsiveness of embryonic tissues to ABA-mediated suppression of germination and radicle emergence.
- **[[Seed Dormancy]]**: An internal physiological block within the viable embryo that prevents germination even under optimal hydration and temperature conditions.
- **[[Preharvest Sprouting]]**: In-spike precocious germination of cereal grains during wet harvest conditions, degrading milling and baking quality.
- **[[Embryo Germination Assay]]**: An *in vitro* assay assessing isolated embryo germination and radicle protrusion in the presence or absence of exogenous phytohormones.
- **[[Enzyme-Linked Immunosorbent Assay]]**: A biochemical immunoassay using monoclonal antibodies to achieve highly sensitive and specific quantification of target phytohormones.

## Important Entities
* **Genes/Proteins**: [[ABA 8'-hydroxylase]], [[Alpha-Amylase]]
* **Organisms**: [[Triticum aestivum]] (wheat cv. 'Brevor', cv. 'Greer')
* **Tools/Techniques/Software**: [[Monoclonal Antibody ELISA]], [[High-Performance Liquid Chromatography]] (HPLC), [[Embryo Germination Assay]], [[Phytohormone Extraction]]

## Methods & Experimental Design
* Plant materials: Spring/winter white wheat cultivars 'Brevor' (PHS resistant, dormant) and 'Greer' (PHS susceptible, non-dormant) grown under controlled greenhouse and growth chamber conditions (20 °C day / 15 °C night, 16 h photoperiod).
* Developmental time course: Grains and isolated embryos sampled at 15, 20, 25, 30, 35, 40, 45, 50, and 60 days post-anthesis (DPA), tracking fresh weight, dry weight, and moisture content through physiological maturity and desiccation.
* Endogenous ABA extraction and quantification: Embryos rapidly dissected and frozen in liquid nitrogen, extracted in 80% methanol with BHT antioxidant, partially purified via C18 Sep-Pak cartridges, and quantified by indirect ELISA using anti-ABA monoclonal antibodies (validated against HPLC fractions).
* ABA sensitivity assays: Isolated embryos cultured on agar plates containing 0, 1, 5, 10, and 50 microM (S)-(+)-ABA or (+/-)-ABA in darkness at 20 °C, scoring germination percentages daily for 7 days.
* Leaching/washing experiments: Isolated dormant Brevor embryos imbibed and washed in excess water for 24 h to determine if dormancy could be overcome by removing diffusible inhibitors.

## Key Results & Data
* **Endogenous ABA concentrations**: Embryo ABA levels peaked between 20 and 30 DPA (reaching ~1.5 to 5.0 microM tissue concentration) in both cultivars, followed by a steady decline to low levels (<0.5 microM) at grain maturity (>50 DPA). Greer embryo ABA was only ~25% lower than Brevor at peak stages.
* **Loss of ABA sensitivity in susceptible Greer**: Early in development (20-30 DPA), Greer embryos were sensitive to ABA. However, as grain moisture declined (>40 DPA), Greer embryos completely lost ABA sensitivity; desiccated Greer embryos germinated to >85% within 3 days in the presence of 10 to 50 microM ABA.
* **Maintained ABA sensitivity in resistant Brevor**: Brevor embryos retained profound ABA sensitivity throughout seed maturation and desiccation. At 50-60 DPA, germination of Brevor embryos was 0% in 10 microM ABA and <10% in 5 microM ABA over 7 days of incubation.
* **Embryonic dormancy vs leachable inhibitors**: Intact dormant Brevor embryos germinated poorly in water alone (20-30%), and extensive washing in water failed to accelerate germination, demonstrating that dormancy is an inherent embryonic property rather than the consequence of leachable pericarp inhibitors.

## Mechanistic Insights
* Sprouting resistance in wheat is not primarily driven by absolute quantities of endogenous [[ABA]] during seed development, but rather by the developmental retention of embryonic sensitivity to ABA signaling during grain desiccation.
* Susceptible genotypes like 'Greer' undergo precocious desensitization of embryonic ABA perception and signaling pathways during late maturation (>40 DPA), allowing rapid hydration-triggered germination.
* Resistant genotypes like 'Brevor' maintain functional ABA signaling cascades that suppress embryo cell elongation and alpha-amylase expression upon post-maturation imbibition.

## Conclusions & Implications
* Establishes embryonic ABA sensitivity as the primary physiological determinant distinguishing PHS-resistant from PHS-susceptible wheat cultivars.
* Demonstrates that selection for PHS resistance in breeding programs should target mechanisms regulating ABA responsiveness and signaling rather than gross ABA accumulation.
* Provides the physiological foundation for subsequent cloning and characterization of ABA signaling components, protein phosphatases, and transcription factors governing wheat seed dormancy.

## Limitations & Caveats
* The study focused on two representative white wheat cultivars ('Brevor' and 'Greer'), and findings require verification across genetically diverse red and white wheat backgrounds.
* Conducted under controlled growth chamber temperatures; temperature fluctuations during grain filling can modulate dormancy levels and ABA sensitivity.

## Contradictory Findings
* Not reported in this paper.

## Outdated Models
* Disproves the classical hypothesis that preharvest sprouting susceptibility is caused simply by a deficiency in total endogenous ABA biosynthesis in developing seeds.

## Under-Researched Populations
* Modern hard white winter and spring wheat lines with uncharacterized variations in ABA receptor affinity and downstream phosphatase activity.

## Future Directions
* Characterize the molecular receptors and signaling intermediates (e.g., SnRK2 kinases, PP2C phosphatases, and ABI transcription factors) responsible for maintaining embryo ABA responsiveness in dormant wheat.
* Develop high-throughput biochemical or molecular assays for embryo ABA sensitivity to assist breeding for PHS resistance.

## Key References to Follow Up
* **King RW (1976)** *Abscisic acid in developing wheat grains and its relationship to slow pre-harvest sprouting and germination.* Planta 132:43-51.
* **Quarrie SA (1982)** *Droplet composite technique for radioimmunoassay of abscisic acid in physiological studies.* J. Exp. Bot. 33:1068-1077.
* **Bewley JD, Black M (1982)** *Physiology and Biochemistry of Seeds in Relation to Germination.* Springer-Verlag, Berlin.

---
**Source PDF:** `data/walkersimmons_1987_aba_levels_sensitivity.pdf`
"""

# 4. sano_1994_genetic_studies_speciation
SUMMARIES["sano_1994_genetic_studies_speciation"] = """---
tags: [seed dormancy, preharvest sprouting, grain color, recombinant inbred lines, triticum aestivum]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: null
authors: "Sano"
year: 1994
journal: "Wheat Information Service"
format_version: 2
---

## Title & Metadata
* **Title:** Genetic studies of speciation in cultivated rice and wheat: breaking linkage between red pericarp and seed dormancy
* **Authors:** Y. Sano
* **Journal:** Wheat Information Service (1994) 79:1-8
* **DOI:** Not reported in this paper.

## Abstract Summary
Preharvest sprouting (PHS) is a major constraint in wheat (*Triticum aestivum* L.) production, particularly in white-grained cultivars which traditionally exhibit weak seed dormancy compared to red-grained genotypes. Historically, whether the association between red seed coat color and seed dormancy resulted from pleiotropy of red pigment genes ([[R-1]] loci) or tight genetic linkage remained a fundamental question in cereal genetics. This classical genetic study investigated the inheritance of seed dormancy and pericarp pigmentation in crosses between two deeply dormant, red-grained wheat accessions (8198 and 8207) and the high-yielding, white-grained, PHS-susceptible cultivar 'WL711'. Genetic analysis of F1, F2, and backcross progenies demonstrated that seed dormancy is governed by a major dominant gene that is tightly linked in repulsion phase to the red seed coat color gene on the group 3 chromosomes, rather than being pleiotropic. By advancing selected backcross populations, the author successfully broke this repulsion linkage, isolating five amber/white-grained recombinant BC1F3 lines (designated 90-56-30, 90-56-72, 90-56-159, 90-41-140, and 90-41-147) that exhibit strong seed dormancy and high PHS resistance comparable to the red-grained parental lines.

## Introduction & Background
* In hexaploid bread wheat, red grain color is controlled by duplicate dominant genes located on the long arms of chromosomes 3A ([[R-A1]]), 3B ([[R-B1]]), and 3D ([[R-D1]]).
* White-grained wheats, which lack dominant *R* alleles (homozygous *r-a1 r-b1 r-d1*), are preferred in many global markets for milling and noodle/flatbread production due to higher flour extraction and lack of specks.
* However, white wheats are notoriously susceptible to preharvest sprouting because red pericarp color has historically correlated strongly with prolonged seed dormancy.
* Breeders long debated whether flavonoids/proanthocyanidins in the red seed coat directly impose dormancy biochemically, or whether independent dormancy genes are physically linked to *R* loci on group 3 chromosomes.
* Resolving this genetic question is vital for breeding white-grained wheat cultivars with robust resistance to PHS.

## Key Concepts & Theory
- **[[Seed Dormancy]]**: The temporary inability of viable seeds to germinate under favorable environmental conditions, protecting against preharvest sprouting.
- **[[Repulsion Linkage]]**: A linkage phase where a dominant favorable allele at one locus (e.g., dormancy) is linked to a recessive allele at a second locus (e.g., white grain color).
- **[[Pleiotropy vs Linkage]]**: The genetic distinction between a single gene controlling multiple phenotypic traits (pleiotropy) versus distinct physical genes co-segregating due to chromosomal proximity (linkage).
- **[[Preharvest Sprouting Tolerance]]**: The capacity of cereal spikes to resist premature grain germination during rainfall events prior to harvest.
- **[[Backcross Breeding]]**: A breeding methodology where hybrid progeny are repeatedly crossed to a recurrent parent to introgress specific donor alleles while recovering the recurrent genetic background.

## Important Entities
* **Genes/Proteins**: [[R-A1]], [[R-B1]], [[R-D1]], [[Tamyb10]], [[TaMFT]]
* **Organisms**: [[Triticum aestivum]] (wheat accessions 8198, 8207, cv. 'WL711')
* **Tools/Techniques/Software**: [[Spike Sprouting Test]], [[Petri Dish Germination Assay]], [[Pedigree Selection]], [[Backcrossing]]

## Methods & Experimental Design
* Plant materials: Red-grained, highly dormant accessions 8198 and 8207 crossed as donors with the white-grained, PHS-susceptible recipient cultivar 'WL711'.
* Population development: F1 hybrids backcrossed to WL711 to generate BC1 populations, followed by pedigree advancement to BC1F2 and BC1F3 generations.
* Grain color assessment: Pericarp color determined visually and verified using 5% NaOH chemical soaking assays to distinguish true white/amber grains from red grains.
* Dormancy and PHS phenotyping: Germination tests conducted on moist filter paper at 20 °C using freshly harvested seeds at physiological maturity; intact spike wetting tests conducted under high humidity misting chambers to score sprouting percentages.
* Segregation analysis: Chi-square tests of goodness-of-fit to evaluate single-gene vs multi-gene inheritance models and linkage recombination frequencies.

## Key Results & Data
* **Monogenic dominant inheritance**: F1 hybrids from 8198 × WL711 and 8207 × WL711 showed high seed dormancy, and F2 segregation conformed to a 3:1 (dormant : non-dormant) ratio, demonstrating that dormancy in accessions 8198 and 8207 is conferred by a single major dominant gene.
* **Linkage with red pericarp**: In early segregating generations, dormancy co-segregated strongly with red grain color, confirming close chromosomal linkage between the dormancy locus and the *R* gene on chromosome group 3.
* **Breaking the repulsion linkage**: In the BC1F2 and BC1F3 generations, rare recombinant events between the *R* locus and the dormancy gene were successfully detected among white/amber seeded segregants.
* **Selection of dormant white lines**: Five stable amber-grained BC1F3 recombinant lines were isolated: 90-56-30, 90-56-72, 90-56-159, 90-41-140, and 90-41-147.
* **PHS tolerance of recombinants**: Germination rates of the five amber lines remained <15% after 7 days of imbibition at maturity, matching the deep dormancy and spike sprouting tolerance of the red parental donors (8198 and 8207), whereas recurrent parent WL711 reached >90% germination within 3 days.

## Mechanistic Insights
* Demonstrates conclusively that red pigment accumulation in the seed coat is not an absolute physiological prerequisite for seed dormancy in hexaploid wheat.
* Sprouting resistance in accessions 8198 and 8207 is mediated by an independent embryonic/physiological dormancy gene located in close genetic proximity to the group 3 *R* loci.
* Recombination between the *R* locus and the linked dormancy locus permits the complete uncoupling of grain color from PHS resistance.

## Conclusions & Implications
* Proves that white-grained wheat varieties can achieve levels of seed dormancy and PHS tolerance equivalent to red-grained cultivars.
* The isolated amber-grained recombinant lines (90-56-30, etc.) serve as valuable elite genetic donors for breeding PHS-tolerant white wheat cultivars.
* Resolves a major historical debate in wheat genetics regarding pleiotropy versus linkage of grain color and seed dormancy.

## Limitations & Caveats
* The study predated molecular marker mapping, so exact centimorgan distances and physical chromosome arm assignments (3A, 3B, or 3D) could not be resolved in the original text.
* Phenotypic testing was performed across laboratory germination assays without multi-location agronomic yield evaluations.

## Contradictory Findings
* Contradicts earlier assertions that proanthocyanidin pigments in the red seed coat are strictly essential to impose mechanical or chemical dormancy in wheat.

## Outdated Models
* Overturns the pleiotropic model which stated that seed dormancy in red wheat is an unavoidable byproduct of *R* gene-mediated flavonoid biosynthesis.

## Under-Researched Populations
* White-grained wheat landraces and wild progenitor introgressions from regions with high harvest-season rainfall.

## Future Directions
* Map the recombinant dormancy gene using modern molecular markers (SSRs and SNPs) to identify its exact chromosomal locus relative to *Tamyb10* and *TaMFT*.
* Incorporate the recombinant white dormant lines into commercial breeding pipelines to develop high-yielding, PHS-resistant white spring and winter wheat varieties.

## Key References to Follow Up
* **Freed RD, et al. (1976)** *Inheritance of seed dormancy and pericarp color in wheat.* Crop Sci. 16:761-764.
* **Gordon AG (1971)** *The germination resistance test—a new test for measuring germination quality of cereals.* Can. J. Plant Sci. 51:181-183.
* **Derera NF (1989)** *Preharvest Field Sprouting in Cereals.* CRC Press, Boca Raton, FL.

---
**Source PDF:** `data/sano_1994_genetic_studies_speciation.pdf`
"""

# 5. gavazza_2012_methods_assessment_preharvest
SUMMARIES["gavazza_2012_methods_assessment_preharvest"] = """---
tags: [preharvest sprouting, rain simulation, germination test, falling number, triticum aestivum]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: 10.1590/S0100-204X2012000700007
authors: "Gavazza et al."
year: 2012
journal: "Pesquisa Agropecuária Brasileira"
format_version: 2
---

## Title & Metadata
* **Title:** Methods for assessment of pre-harvest sprouting in wheat cultivars
* **Authors:** Maria Isabel A. Gavazza, Manoel Carlos Bassoi, Tatiane Cristina Carvalho, Claudio Roberto Riede, Maria Brígida dos Santos Scholz, José Walter Pedroza Carneiro
* **Journal:** Pesquisa Agropecuária Brasileira (2012) 47(7):928-933
* **DOI:** 10.1590/S0100-204X2012000700007

## Abstract Summary
Preharvest sprouting (PHS) in wheat (*Triticum aestivum* L.) reduces grain yield and degrades end-use baking quality by elevating alpha-amylase activity. To determine the most effective and reliable screening methodology for PHS tolerance in wheat breeding programs, this study evaluated 14 Brazilian wheat cultivars harvested at physiological maturity across two field locations (Londrina and Ponta Grossa, Paraná, Brazil). Four assessment methods were compared: (1) artificial rainfall simulation in a mist chamber on intact spikes (280 mm water mist over 48 h), (2) germination in rolls of germitest paper using intact grains, (3) germination in rolls of germitest paper using mechanically damaged/cracked grains, and (4) germination in Petri dishes using intact grains. Intact spike rain simulation in a mist chamber was the only method that showed high, statistically significant Spearman rank correlations (r = 0.74 to 0.89, P < 0.01) with the standard technical resistance classification of the cultivars in both environments. In contrast, detached grain assays in paper rolls or Petri dishes yielded low and non-significant correlations (r = 0.07 to 0.36), failing to reflect cultivar dormancy. The cultivars 'Frontana', 'BRS 177', and 'BRS 220' were confirmed as highly tolerant to PHS, whereas 'BR 18-Terena' and 'Supera' were highly susceptible.

## Introduction & Background
* Rainfall during the harvest window is a recurrent problem in southern Brazil and other temperate wheat regions, triggering preharvest sprouting and downgrading milling quality.
* PHS tolerance is a complex trait determined by grain dormancy, spike morphology, glume tightness, and water uptake dynamics.
* Plant breeding programs require fast, low-cost, and biologically reliable phenotyping methods to screen large numbers of breeding lines for PHS resistance.
* While the Hagberg Falling Number (FN) assay is the industrial benchmark, its high equipment cost and requirement for grain milling limit its routine use in early-generation selection.
* There was an urgent need to validate whether detached grain germination assays (Petri dishes or paper rolls) can substitute for whole-spike rain simulation chambers in breeding pipelines.

## Key Concepts & Theory
- **[[Preharvest Sprouting]]**: The premature germination of grain in the wheat ear prior to harvest under wet conditions, causing starch degradation.
- **[[Rain Simulation Chamber]]**: A controlled misting chamber that applies standardized artificial precipitation to intact cereal spikes to evaluate field-like sprouting tolerance.
- **[[Sprouting Index]]**: A quantitative or visual score measuring the percentage of germinated grains exhibiting pericarp rupture or radicle emergence on the spike.
- **[[Spike Morphology Barrier]]**: Physical and anatomical attributes of the wheat spike (awn presence, glume adherence, waxiness) that restrict water penetration into the grain.
- **[[Germitest Paper Roll Assay]]**: A standard laboratory seed germination method evaluating detached seed germination between sheets of moistened paper.

## Important Entities
* **Genes/Proteins**: [[Alpha-Amylase]]
* **Organisms**: [[Triticum aestivum]] (wheat cultivars 'Frontana', 'BRS 177', 'BRS 220', 'CD 104', 'CD 108', 'CD 113', 'CD 115', 'IPR 85', 'IPR 128', 'IPR 129', 'IPR 130', 'IPR 136', 'BR 18-Terena', 'Supera')
* **Tools/Techniques/Software**: [[Rain Simulation Mist Chamber]], [[Germitest Paper Assays]], [[Petri Dish Germination Tests]], [[Spearman Rank Correlation]], [[Scott-Knott Test]]

## Methods & Experimental Design
* Plant materials: 14 wheat cultivars with known standard PHS classifications grown in Londrina (warmer, lower altitude) and Ponta Grossa (cooler, higher altitude), Paraná, Brazil.
* Harvesting: 100 spikes per cultivar collected at physiological maturity (complete loss of green color from peduncle and glumes) and air-dried under ambient conditions.
* Method 1 (Rain simulation): 20 intact spikes per cultivar inserted into Styrofoam blocks placed in a mist chamber receiving 280 mm mist/day (30 min on/off cycles) for 48 h, dried, threshed, and examined under 10x magnification for pericarp rupture.
* Method 2 (Intact grains in paper rolls): 50 hand-threshed intact grains placed in moistened germitest paper rolls at 20 °C for 7 days.
* Method 3 (Damaged grains in paper rolls): 50 grains with mechanically cracked pericarps placed in paper rolls at 20 °C for 7 days.
* Method 4 (Petri dishes): 50 intact grains placed on moistened filter paper in Petri dishes at 20 °C for 7 days.
* Statistical analysis: ANOVA on arcsine-transformed germination percentages, Scott-Knott cluster tests (P <= 0.05), and Spearman rank correlation with official cultivar PHS classifications.

## Key Results & Data
* **Superiority of rain simulation**: Whole-spike rain simulation produced germination percentages ranging from 11.0% to 88.0%, showing strong and highly significant Spearman rank correlations with standard cultivar classifications in both Londrina (r = 0.89, P < 0.01) and Ponta Grossa (r = 0.74, P < 0.01).
* **Failure of detached grain methods**:
  * Intact grains in paper rolls: Non-significant correlation in Londrina (r = 0.28) and Ponta Grossa (r = 0.36).
  * Damaged grains in paper rolls: Poor and non-significant correlation in Londrina (r = 0.16) and Ponta Grossa (r = 0.14).
  * Petri dish assay: Very low and non-significant correlation in Londrina (r = 0.07) and Ponta Grossa (r = 0.19).
* **Cultivar performance**:
  * Tolerant group: 'Frontana' (11.0% sprouting), 'BRS 177' (17.5%), and 'BRS 220' (21.5%).
  * Moderately tolerant: 'IPR 128', 'IPR 129', 'IPR 130', 'CD 113', 'CD 115'.
  * Susceptible group: 'BR 18-Terena' (88.0% sprouting), 'Supera' (84.5%), 'CD 104' (76.0%), and 'CD 108' (72.5%).
* **Location effects**: Cultivars grown in Ponta Grossa (cooler maturation temperatures) exhibited slightly deeper dormancy and lower average sprouting percentages than those grown in Londrina.

## Mechanistic Insights
* Preharvest sprouting resistance is an integrated phenotype that depends on both physiological embryo/seed dormancy and whole-spike physical barriers (glume waxy cuticles, glume tightness, spike architecture) that regulate water penetration.
* Detached grain germination assays remove the physical protective structures of the chaff and glumes and alter water uptake rates, thereby decoupling seed germination from true in-spike sprouting resistance.
* Mechanically damaging grain pericarps accelerates water absorption but completely masks genetic differences in seed dormancy.

## Conclusions & Implications
* Artificial rainfall simulation in a mist chamber using intact spikes is the most accurate, reliable, and discriminatory screening method for assessing PHS tolerance in wheat breeding.
* Detached seed germination tests in paper rolls or Petri dishes should not be used as standalone screening tools for PHS resistance.
* Cultivars 'Frontana' and 'BRS 177' represent highly stable genetic sources of PHS tolerance for incorporation into Brazilian and international wheat breeding programs.

## Limitations & Caveats
* Rain simulation chambers require dedicated misting infrastructure and space compared to compact Petri dish tests.
* The study evaluated 14 cultivars across two environments in a single Brazilian state; broader germplasm sets in other climatic zones should also be tested.

## Contradictory Findings
* Not reported in this paper.

## Outdated Models
* Refutes the premise that simple detached grain germination assays (Petri dishes or germitest paper) provide an adequate surrogate for wheat preharvest sprouting phenotyping.

## Under-Researched Populations
* Modern subtropical and tropical spring wheat lines grown under high harvest-season precipitation in South America.

## Future Directions
* Integrate automated digital imaging and machine learning to score pericarp rupture on spikes following mist chamber rain simulation.
* Dissect the relative genetic contributions of spike morphological traits versus embryo dormancy genes in 'Frontana' and 'BRS 177'.

## Key References to Follow Up
* **Paterson AH, Sorrells ME, Obendorf RL (1989)** *Methods of evaluation for preharvest sprouting resistance in wheat breeding programs.* Can. J. Plant Sci. 69:681-689.
* **Bassoi MC, Flintham J (2005)** *Relationship between grain colour and preharvest sprouting-resistance in wheat.* Pesqui. Agropecu. Bras. 40:981-988.
* **Andreoli C, et al. (2006)** *Genetic control of seed dormancy and pre-harvest sprouting in wheat.* Sci. Agric. 63:564-566.

---
**Source PDF:** `data/gavazza_2012_methods_assessment_preharvest.pdf`
"""

# 6. imtiaz_2008_characterization_quantitative_trait
SUMMARIES["imtiaz_2008_characterization_quantitative_trait"] = """---
tags: [preharvest sprouting, synthetic wheat, aegilops tauschii, quantitative trait loci, triticum aestivum]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: 10.1534/genetics.107.081828
authors: "Imtiaz et al."
year: 2008
journal: "Genetics"
format_version: 2
---

## Title & Metadata
* **Title:** Characterization of Quantitative Trait Loci Controlling Genetic Variation for Preharvest Sprouting in Synthetic Backcross-Derived Wheat Lines
* **Authors:** Muhammad Imtiaz, Francis C. Ogbonnaya, Jason Oman, Maarten van Ginkel
* **Journal:** Genetics (2008) 178(3):1725-1736
* **DOI:** 10.1534/genetics.107.081828

## Abstract Summary
Preharvest sprouting (PHS) in bread wheat (*Triticum aestivum* L.) results from insufficient seed dormancy and is exacerbated in white-grained cultivars due to linkage or pleiotropic effects with red coat color genes. To exploit novel genetic variation from wild wheat relatives, a mapping population of 271 BC1F7 advanced backcross lines derived from the cross 'Syn37/2*Janz' (where Syn37 is a synthetic hexaploid wheat from *Aegilops tauschii* AUS18836 × *Triticum turgidum* ssp. *durum* cv. 'Altar 84', and 'Janz' is an elite Australian white wheat) was evaluated across multiple field environments. Quantitative trait locus (QTL) analysis identified four major genomic regions controlling PHS resistance: two on chromosome 3D and two on chromosome 4A. On chromosome 3DL, *QPhs.dpivic-3D.1* (flanked by *cfd211-XRGC-wms1200*) explained 18.4% to 43.2% of phenotypic variation and was linked at 5 cM to the red grain color gene [[R-D1b]]. A second locus on 3D, *QPhs.dpivic-3D.2* (flanked by *gdm8-gwm52*), explained 11.2% of variation and acted completely independently of grain color. On chromosome 4AL, two distinct QTLs (*QPhs.dpivic-4A.1* explaining 16.3-25.1% and *QPhs.dpivic-4A.2* explaining 13.4-24.3%) were identified. Epistatic interactions and QTL × environment interactions were characterized, and white-grained, PHS-resistant recombinant lines carrying *Ae. tauschii* dormancy alleles were successfully identified.

## Introduction & Background
* Preharvest sprouting severely damages end-use wheat quality by initiating premature alpha-amylase synthesis, resulting in reduced falling numbers and ruined baking performance.
* In commercial breeding, white-grained wheat is favored for high milling flour yield and Asian noodle products, but white cultivars are generally more susceptible to PHS than red wheat.
* *Aegilops tauschii* Coss. (the D-genome progenitor of hexaploid wheat) possesses immense genetic diversity for abiotic stress tolerance and prolonged seed dormancy that remains largely untapped in cultivated wheat.
* Synthetic hexaploid wheats (SHWs) produced by hybridizing tetraploid durum wheat (*T. turgidum*) with *Ae. tauschii* provide an effective bridge to introgress wild D-genome alleles into elite bread wheat.
* The objectives of this study were to map and characterize QTLs for PHS resistance introgressed from *Ae. tauschii*, dissect additive, epistatic, and QTL × environment interactions, and identify white-grained PHS-resistant recombinant lines.

## Key Concepts & Theory
- **[[Synthetic Hexaploid Wheat]]**: Artificially synthesized hexaploid wheat generated by crossing tetraploid wheat (AABB) with diploid *Aegilops tauschii* (DD) followed by chromosome doubling.
- **[[Advanced Backcross QTL Analysis]]**: A mapping strategy that combines QTL discovery with cultivar development by evaluating advanced backcross populations (e.g., BC1F7) derived from elite × wild crosses.
- **[[Red Grain Color]]**: Seed coat pigmentation controlled by duplicate [[R-1]] genes on chromosome group 3 (*R-A1*, *R-B1*, *R-D1*), historically associated with seed dormancy.
- **[[Epistatic QTL Interaction]]**: Non-additive interactions between distinct genomic loci influencing the phenotypic expression of seed dormancy.
- **[[QTL by Environment Interaction]]**: Variations in the magnitude or significance of QTL effects across differing temperature and rainfall environments.

## Important Entities
* **Genes/Proteins**: [[R-D1b]], [[R-A1]], [[R-B1]], [[TaMFT]], [[TaMKK3]], [[Alpha-Amylase]]
* **Organisms**: [[Triticum aestivum]] (wheat cv. 'Janz'), [[Aegilops tauschii]] (accession AUS18836), [[Triticum turgidum]] (cv. 'Altar 84')
* **Tools/Techniques/Software**: [[Simple Sequence Repeat]] (SSR markers), [[Composite Interval Mapping]] (CIM), [[WinQTLCartographer]], [[QTL Network]], [[Rain Simulator Assay]]

## Methods & Experimental Design
* Plant material: 271 BC1F7 lines developed from the cross Syn37 (Altar 84/*Ae. tauschii* AUS18836) / 2*Janz.
* Field trials: Evaluated across four environments in Victoria, Australia (Horsham 2003, 2004, 2005, and Walpeup 2005) in randomized complete block designs.
* Phenotyping: Intact spikes harvested at physiological maturity (50% ripe), dried, and subjected to artificial rainfall in a rotating mist chamber for 7 days at 20 °C. Spikes scored on a 0-9 scale (0 = no sprouting, 9 = fully sprouted). Grain color assessed visually and confirmed with 5% NaOH.
* Genotyping: Linkage map constructed using 196 SSR markers and 1 morphological marker (red grain color, *RGC* / *R-D1b*) covering all 21 chromosomes.
* Statistical analysis: Composite Interval Mapping (CIM) with WinQTLCartographer v2.5; mixed-model QTL mapping with QTLNetwork v2.0 to detect additive, epistatic, and QTL × environment (Q × E) effects.

## Key Results & Data
* **Major 3D QTLs**:
  * *QPhs.dpivic-3D.1* on 3DL (flanked by *cfd211-XRGC-wms1200*): LOD up to 28.5, explaining 18.4% to 43.2% of phenotypic variance; *Ae. tauschii* allele increased dormancy; tightly linked to *R-D1b* at 5.0 cM.
  * *QPhs.dpivic-3D.2* on 3D (flanked by *gdm8-gwm52*): LOD up to 6.8, explaining 11.2% of phenotypic variance; *Ae. tauschii* allele increased dormancy, completely independent of grain color.
* **Major 4AL QTLs**:
  * *QPhs.dpivic-4A.1* (flanked by *barc170-gwm269c* on 4AL): LOD 11.2, explaining 16.3% to 25.1% of phenotypic variance; Janz allele increased resistance.
  * *QPhs.dpivic-4A.2* (flanked by *wms937-wms894* on 4AL): LOD 10.4, explaining 13.4% to 24.3% of phenotypic variance; Altar 84 allele increased resistance.
* **Epistasis and Q × E interactions**: Significant epistatic interactions detected between loci on chromosomes 1D, 2D, and 6D. *QPhs.dpivic-3D.1* and *QPhs.dpivic-4A.1* exhibited consistent main effects across environments with minor Q × E interaction.
* **White-grained resistant lines**: Multiple BC1F7 lines with white grain color (*r-d1b* allele) inherited the dormant *QPhs.dpivic-3D.2* and 4AL alleles, achieving sprouting scores comparable to red-grained resistant synthetic parents.

## Mechanistic Insights
* *Aegilops tauschii* harbors two distinct genetic mechanisms for PHS tolerance on chromosome 3D: a major locus (*QPhs.dpivic-3D.1*) linked to the red pericarp gene *R-D1b*, and an independent locus (*QPhs.dpivic-3D.2*) that confers strong seed dormancy in white-seeded backgrounds.
* Chromosome 4AL harbors two separate QTLs (*QPhs.dpivic-4A.1* and *QPhs.dpivic-4A.2*), demonstrating multi-genic control of dormancy within the 4AL region.
* Introgression of wild D-genome chromatin introduces novel dormancy alleles that act additively with elite hexaploid alleles without carrying deleterious linkage drag.

## Conclusions & Implications
* Synthetic backcross lines provide an effective vehicle for enriching the hexaploid wheat gene pool with novel PHS resistance alleles from *Aegilops tauschii*.
* Identification of *QPhs.dpivic-3D.2* and 4AL QTLs confirms that robust PHS tolerance can be successfully engineered into white-grained bread wheat.
* SSR markers *cfd211*, *gdm8*, *gwm269c*, and *wms894* enable marker-assisted pyramiding of 3D and 4A resistance loci in breeding programs.

## Limitations & Caveats
* The synthetic donor Syn37 is derived from a single *Ae. tauschii* accession (AUS18836), representing only a fraction of total D-genome genetic diversity.
* QTL mapping resolution was bounded by the density of the 196 SSR markers.

## Contradictory Findings
* Not reported in this paper.

## Outdated Models
* Refutes the dogma that D-genome PHS resistance is inseparable from red grain color, establishing the existence of color-independent dormancy locus *QPhs.dpivic-3D.2*.

## Under-Researched Populations
* Diverse *Aegilops tauschii* subsp. *strangulata* accessions and hexaploid synthetic backcross derivative panels under varied climatic zones.

## Future Directions
* Fine-map *QPhs.dpivic-3D.2* to isolate the underlying causal gene and assess its molecular mechanism in relation to ABA signaling.
* Validate the performance of white-grained synthetic backcross lines under commercial field conditions across diverse wheat-growing countries.

## Key References to Follow Up
* **Flintham JE (2000)** *Resolution of meta-QTLs for seed dormancy in wheat.* Ann. Bot. 85:125-134.
* **Mares DJ, et al. (2005)** *Identification of a major QTL for preharvest sprouting resistance on chromosome 4A in white-grained wheat.* Aust. J. Agric. Res. 56:859-865.
* **Ogbonnaya FC, et al. (2007)** *Mapping QTLs for preharvest sprouting resistance in synthetic backcross-derived wheat lines.* Mol. Breed. 20:371-384.

---
**Source PDF:** `data/imtiaz_2008_characterization_quantitative_trait.pdf`
"""

# 7. wang_2019_phenotypic_genotypic_characterization
SUMMARIES["wang_2019_phenotypic_genotypic_characterization"] = """---
tags: [near-isogenic lines, quantitative trait loci, snp array, candidate genes, triticum aestivum]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: 10.1186/s12870-019-1981-6
authors: "Wang et al."
year: 2019
journal: "BMC Plant Biology"
format_version: 2
---

## Title & Metadata
* **Title:** Phenotypic and genotypic characterization of near-isogenic lines targeting a major 4BL QTL responsible for pre-harvest sprouting in wheat
* **Authors:** Xingyi Wang, Hui Liu, Guannan Liu, Md Sultan Mia, Kadambot H. M. Siddique, Guijun Yan
* **Journal:** BMC Plant Biology (2019) 19:351
* **DOI:** 10.1186/s12870-019-1981-6

## Abstract Summary
Preharvest sprouting (PHS) in bread wheat (*Triticum aestivum* L.) reduces grain yield and end-use quality. While chromosome 4AL has received extensive study, major PHS QTLs on chromosome 4BL remain poorly characterized. In this study, five confirmed pairs of near-isogenic lines (NILs) targeting the major 4BL QTL, *QPhs.ocs-4B.1*, were generated from two distinct biparental populations (SUN326AE × Westonia and Chara × DM5637B*8) using the marker-assisted heterogeneous inbred family (HIF) method combined with a fast generation cycling system. Phenotypic characterization revealed that the resistant allele reduced spike sprouting by 54.0% to 81.9% (mean 70.8%) and decreased the germination index (GI) by 59.4% to 70.5% (mean 66.2%). Genotyping with the wheat 90K iSelect SNP array identified eight contrasting SNPs on 4BL associated with five candidate genes in the *QDor-4B* / *QPhs.ocs-4B.1* interval: [[TraesCS4B01G239700]] (heat shock transcription factor *HsfA9*), [[TraesCS4B02G247900]] (DEAD-box ATP-dependent RNA helicase), [[TraesCS4B02G253300]] (alpha-L-fucosidase 2), [[TraesCS4B02G217800]] (myosin-binding protein), and [[TraesCS4B02G229600]] (2OG-Fe(II) oxygenase). Furthermore, PHS susceptibility was positively correlated with plant height (r² = 0.34) and grain number per spike (r² = 0.73), providing near-isogenic genetic resources for fine-mapping and gene isolation.

## Introduction & Background
* Preharvest sprouting causes worldwide cereal losses estimated at over $1.2 billion annually by degrading grain starch into simple sugars during wet pre-harvest conditions.
* PHS resistance is a complex polygenic trait influenced by seed dormancy, glume inhibitors, spike water penetration, and morphological features.
* While the 4AL dormancy locus (*TaMKK3-A* / *PM19*) has been cloned, the centromeric/long arm region of chromosome 4B harbors another major, consistent QTL (*QPhs.ocs-4B.1*) explaining 20% to 60% of phenotypic variation across diverse wheat backgrounds.
* Chromosome 4B is recognized as a 'QTL hotspot' influencing plant height (e.g., [[Rht-B1]]), spike length, and yield components such as grain number per spike.
* Developing near-isogenic lines (NILs) using heterogeneous inbred families (HIF) combined with fast generation cycling turns quantitative variation into Mendelian segregation, enabling fine mapping and candidate gene identification.

## Key Concepts & Theory
- **[[Near-Isogenic Lines]]**: Pairs of genetic lines that possess identical genetic backgrounds except for a defined target chromosomal introgression, allowing precise phenotypic dissection.
- **[[Heterogeneous Inbred Family]]**: A breeding method where single plants heterozygous at a target marker are selfed and selected across generations to derive isogenic sister lines.
- **[[Fast Generation Cycling]]**: An *in vitro* young embryo culture technique that accelerates wheat generation turnover to rapidly advance breeding generations.
- **[[Germination Index]]**: A time-weighted numerical index quantifying the rate and uniformity of seed germination over a 7-day period.
- **[[Heat Shock Transcription Factor]]**: Specialized transcription factors (such as *HsfA9*) expressed late in seed maturation that regulate seed dormancy acquisition and ABA sensitivity.

## Important Entities
* **Genes/Proteins**: [[TraesCS4B01G239700]], [[TraesCS4B02G247900]], [[TraesCS4B02G253300]], [[TraesCS4B02G217800]], [[TraesCS4B02G229600]], [[Rht-B1]], [[HsfA9]]
* **Organisms**: [[Triticum aestivum]] (wheat cultivars 'SUN326AE', 'Westonia', 'Chara', 'DM5637B*8')
* **Tools/Techniques/Software**: [[Illumina 90K iSelect SNP Array]], [[Heterogeneous Inbred Family Method]], [[Fast Generation Cycling]], [[Spike Sprouting Assay]], [[Germination Index Assay]], [[SSR Marker Xgwm495]]

## Methods & Experimental Design
* Population development: 240 F2 plants from two crosses (40 F2 plants from SUN326AE × Westonia and 200 F2 plants from Chara × DM5637B*8). Heterozygotes tracked at SSR marker *Xgwm495* close to *QPhs.ocs-4B.1* across F2-F7 generations via HIF and embryo culture.
* Isoline selection: From F7 heterozygous plants, contrasting homozygous F8 isolines (resistant 'R' vs susceptible 'S') were selected, generating 19 putative NIL pairs.
* Phenotypic assays: Sprouting tests on intact spikes immersed for 6 h and incubated at 22 °C / 100% humidity for 7 days. Germination index (GI) assays on 50 seeds per dish for 7 days. Agronomic measurements: plant height, spike number, grains per spike, yield per plant, and thousand-kernel weight.
* High-density SNP genotyping: 5 confirmed NIL pairs genotyped using the Illumina 90K iSelect SNP array; contrasting SNPs blasted against the Chinese Spring IWGSC reference genome to identify candidate genes.

## Key Results & Data
* **Phenotypic validation of NILs**:
  * Eight pairs showed significant differences in whole-spike sprouting tests: resistant isolines had sprouting rates of 7.1% to 33.6% compared to 39.2% to 73.6% in susceptible counterparts (average 70.8% sprouting reduction).
  * Five pairs showed significant differences in GI: resistant isolines had GI values of 0.19 to 0.33 vs 0.64 to 0.81 in susceptible lines (average 66.2% dormancy increase).
* **Correlations with agronomic traits**:
  * PHS susceptibility showed significant positive correlations with plant height (r² = 0.34, P < 0.05) and grain number per spike (r² = 0.73, P < 0.001).
  * Resistant isolines were significantly shorter (by 4-8 cm) and had fewer grains per spike, but final yield per plant was not compromised.
* **SNP mapping and candidate genes on 4BL**:
  * Eight consistent contrasting SNPs mapped within the *QPhs.ocs-4B.1* interval, identifying five candidate genes:
    1. *TraesCS4B01G239700* (Heat shock transcription factor *HsfA9*, linked to SNPs *BS00096604_51* and *IAAV5117*)
    2. *TraesCS4B02G247900* (DEAD-box ATP-dependent RNA helicase, linked to SNP *Ra_c3117_2098*)
    3. *TraesCS4B02G253300* (Alpha-L-fucosidase 2, linked to SNPs *Ra_c27465_569* and *Ra_c27465_564*)
    4. *TraesCS4B02G217800* (Myosin-binding protein / DUF593, linked to SNP *wsnp_Ra_c1992_3876325*)
    5. *TraesCS4B02G229600* (2OG-Fe(II) oxygenase, linked to SNP *Tdurum_contig69405_332*)

## Mechanistic Insights
* *QPhs.ocs-4B.1* regulates PHS through both embryo-imposed dormancy and whole-spike physical interactions.
* Candidate gene *TraesCS4B01G239700* (*HsfA9*) is known in Arabidopsis and sunflower to act during late seed maturation to coordinate ABA responsiveness and desiccation tolerance.
* Candidate gene *TraesCS4B02G247900* (DEAD-box RNA helicase) is implicated in ABA stress signaling and temperature-dependent germination regulation.
* The positive genetic correlation between plant height, floret fertility, and PHS susceptibility on chromosome 4BL suggests shared hormonal crosstalk (such as GA/ABA or brassinosteroid balance) or tight linkage of developmental regulators in the 4B pericentromeric region.

## Conclusions & Implications
* Successfully confirmed the major effect of *QPhs.ocs-4B.1* across two diverse genetic backgrounds using validated near-isogenic lines.
* Pinpointed *HsfA9* and a DEAD-box RNA helicase as the primary functional candidate genes controlling 4BL-mediated seed dormancy.
* The confirmed NILs and diagnostic SNPs provide powerful tools for fine-mapping, functional cloning, and marker-assisted selection for PHS resistance in commercial wheat breeding.

## Limitations & Caveats
* Functional validation through transgenic complementation or CRISPR knockouts of the candidate genes was not conducted in this study.
* Evaluations were conducted under controlled glasshouse and growth room conditions, requiring multi-location field validation.

## Contradictory Findings
* Not reported in this paper.

## Outdated Models
* Refutes the view that chromosome 4A is the sole group 4 determinant of wheat seed dormancy, highlighting 4BL (*QPhs.ocs-4B.1*) as an equally potent and independent locus.

## Under-Researched Populations
* Commercial semi-dwarf wheat cultivars segregating for 4BL alleles in combination with *Rht-B1* and *TaMKK3-A*.

## Future Directions
* Perform high-resolution recombinant screening of NIL progeny to clone *TraesCS4B01G239700* / *TraesCS4B02G247900*.
* Convert the 4BL diagnostic SNPs into high-throughput KASP assays for routine marker-assisted selection in commercial breeding programs.

## Key References to Follow Up
* **Mori M, et al. (2005)** *Mapping QTLs for grain dormancy on wheat chromosome 3A and the group 4 chromosomes, and their combined effect.* Theor. Appl. Genet. 110:1315-1323.
* **Almoguera C, et al. (2002)** *A seed-specific heat-shock transcription factor involved in developmental regulation.* J. Biol. Chem. 277:43866-43872.
* **Wang S, et al. (2014)** *Characterization of polyploid wheat genomic diversity using a high-density 90 000 single nucleotide polymorphism array.* Plant Biotechnol. J. 12:787-796.

---
**Source PDF:** `data/wang_2019_phenotypic_genotypic_characterization.pdf`
"""

# 8. margaritopoulou_2019_molecular_advances
SUMMARIES["margaritopoulou_2019_molecular_advances"] = """---
tags: [crop improvement, marker-assisted selection, genomic selection, abiotic stress, helianthus annuus]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: 10.2478/hppj-2019-0003
authors: "Margaritopoulou and Milioni"
year: 2019
journal: "Hellenic Plant Protection Journal"
format_version: 2
---

## Title & Metadata
* **Title:** Molecular advances on agricultural crop improvement to meet current cultivating demands
* **Authors:** T. Margaritopoulou, D. Milioni
* **Journal:** Hellenic Plant Protection Journal (2019) 12(1):1-26
* **DOI:** 10.2478/hppj-2019-0003

## Abstract Summary
Meeting global agricultural demands under changing climatic conditions requires accelerating crop breeding for yield stability, disease resistance, and stress tolerance. This review comprehensively examines modern molecular advances, genomic resources, and biotechnological tools applied to three major non-cereal and cereal/tuber crops: sunflower (*Helianthus annuus*), maize (*Zea mays*), and potato (*Solanum tuberosum*). The authors summarize the transition from classical simple sequence repeat (SSR) and amplified fragment length polymorphism (AFLP) markers to high-throughput single nucleotide polymorphism (SNP) genotyping, expressed sequence tag (EST) databases, genome-wide association studies (GWAS), marker-assisted backcrossing (MABC), marker-assisted recurrent selection (MARS), and genomic selection (GS). Key breeding targets discussed include disease resistance (e.g., *Sclerotinia sclerotiorum* and downy mildew in sunflower; maize streak virus and leaf blights in maize; *Phytophthora infestans* and Potato virus Y in potato), abiotic stress resilience (drought, salinity, and cold tolerance via [[ABA]] signaling pathways, [[PYL]] receptors, [[NF-Y]] transcription factors, and osmotic adjustment), and quality traits (oleic acid modification in sunflower, biofortification and bioethanol conversion in maize, and bruising resistance in potato).

## Introduction & Background
* Over 10,000 years of crop domestication and artificial selection have narrowed genetic diversity in modern crop cultivars relative to wild relatives, necessitating molecular introgression of adaptive traits.
* High-throughput next-generation sequencing and bioinformatics now enable genome-wide dissection of complex quantitative traits controlled by polygenic networks.
* The availability of reference genome sequences for maize (B73, 2.3 Gb), potato (850 Mb), and sunflower (3.6 Gb) has transformed functional genomics and molecular breeding.
* While single-gene traits (such as herbicide resistance and monogenic disease resistance) are readily handled via marker-assisted selection (MAS), complex quantitative traits (yield, drought, and broad-spectrum disease resistance) require high-density linkage maps, meta-QTL analyses, and genomic selection models.
* This review synthesizes molecular breeding breakthroughs and genetic engineering strategies across sunflower, maize, and potato to meet contemporary agronomic demands.

## Key Concepts & Theory
- **[[Marker-Assisted Selection]]**: An indirect selection process where a trait of interest is selected based on a linked DNA marker rather than the phenotype itself.
- **[[Genomic Selection]]**: A form of marker-assisted selection where whole-genome marker profiles are used to calculate genomic estimated breeding values (GEBVs) for complex quantitative traits.
- **[[Marker-Assisted Recurrent Selection]]**: A multi-parent breeding strategy utilizing association mapping and marker cycles to accumulate favorable QTL alleles across generations.
- **[[Abscisic Acid Receptors]]**: The PYR/PYL/RCAR family of soluble ligand-binding proteins that perceive ABA and initiate core stress-responsive signaling cascades.
- **[[Copy Number Variation]]**: Structural genomic variations involving deletions or duplications of large DNA segments that impact gene dosage and phenotypic variation.

## Important Entities
* **Genes/Proteins**: [[PYL]], [[ZmNF-YB2]], [[ZmNF-YB16]], [[AHAs-1]], [[FAD2-1]], [[Rf1]], [[Or5]], [[RB]], [[R8]], [[Ryadg]], [[Gro1]], [[Rx1]], [[StZFP1]], [[PR10a]], [[GLOase]], [[PPDK]], [[mop1]]
* **Organisms**: [[Helianthus annuus]], [[Zea mays]], [[Solanum tuberosum]], [[Phytophthora infestans]], [[Sclerotinia sclerotiorum]], [[Orobanche cumana]], [[Potato virus Y]]
* **Tools/Techniques/Software**: [[Affymetrix GeneChip]], [[Illumina Sequencing]], [[Bacterial Artificial Chromosomes]] (BAC libraries), [[RNA Interference]] (RNAi), [[Cleaved Amplified Polymorphic Sequences]] (CAPS), [[High-Throughput SNP Genotyping]]

## Methods & Experimental Design
* Literature synthesis: Comprehensive evaluation of published molecular mapping, transcriptomic profiling, QTL meta-analyses, and transgenic breeding studies across sunflower, maize, and potato.
* Data compilation: Genomic resource inventories (BAC libraries, EST databases, high-density SNP arrays, and reference assemblies).
* Comparative methodology: Evaluation of marker systems (AFLP, SSR, DArT, SNP), mapping frameworks (biparental linkage mapping vs GWAS), and breeding schemes (MABC vs MARS vs GS).

## Key Results & Data
* **Sunflower genomics and breeding**:
  * BAC libraries covering ~8 haploid genome equivalents and 2.6-million feature Affymetrix chips developed; 94.3% of ESTs mapped to 90,935 predicted genes.
  * Validation of markers for broomrape resistance (*Or5*), downy mildew (*Pl* genes), rust (*R1*, *Pu6*), and imidazolinone resistance (*AHAs-1* codon 205 mutation).
  * Transgenic expression of oxalate oxidase and human lysozyme enhanced resistance against *Sclerotinia sclerotiorum*.
* **Maize molecular advances**:
  * Decoding of B73 (2.3 Gb) and Palomero genomes; HapMap development across 27 diverse inbreds revealed subgenome dominance and historical gene loss.
  * Cloned QTLs and validated markers for maize streak virus (explaining 50-70% of variation), Cercospora resistance, and root ABA accumulation (*root-ABA1* on bin 2.04).
  * Drought tolerance improved via constitutive overexpression of *ZmNF-YB2* and *ZmNF-YB16*, natural variants of ABA receptors (*PYL*), and bacterial RNA chaperones.
* **Potato structural and functional genomics**:
  * 850 Mb genome sequenced by PGSC, uncovering copy number variations affecting 30.2% (219.8 Mb) of the genome and ~30% of annotated genes.
  * Development of ultrahigh-density genetic maps (10,000 AFLP markers; 8,303 SNPs) integrating candidate genes for tuberization earliness, late blight (*R8*, *RB*, *Rpi* genes), and virus resistance (*Ryadg*, *Rx1*).
  * Stress-responsive transcription factors (*StZFP1*, *PR10a*, *GLOase*) characterized for enhanced salinity and drought tolerance.

## Mechanistic Insights
* ABA signaling cascades serve as a central, conserved hub for abiotic stress adaptation across crops; natural variation in [[PYL]] receptors and downstream SnRK2/PP2C modules modulates stomatal conductance and water-use efficiency without severe yield penalty.
* Plant architecture and stress resilience are governed by complex epistatic and dosage-sensitive networks (e.g., NF-Y heterotrimeric complexes and chromatin remodeling factors like *mop1*).
* Broad-spectrum disease resistance in polyploids (like potato) relies on multi-gene clusters of NBS-LRR resistance genes exhibiting extensive structural copy number variation and dynamic evolution.

## Conclusions & Implications
* Marker-assisted selection and genomic selection have fundamentally transitioned crop improvement from phenotypic screening to predictive, sequence-based breeding.
* Harnessing wild germplasm collections through high-throughput SNP arrays and genomic mapping unlocks novel alleles for disease resistance, stress tolerance, and quality traits.
* Integrating multi-omics platforms (genomics, transcriptomics, metabolomics) accelerates the design of climate-resilient crop ideotypes.

## Limitations & Caveats
* Transgenic approaches face significant regulatory hurdles and public acceptance constraints in many agricultural markets, limiting commercialization of transgenic abiotic stress-tolerant lines.
* Outcrossing, heterozygous species (like potato and sunflower) present more complex phasing and linkage disequilibrium patterns than inbred self-pollinating cereals.

## Contradictory Findings
* Not reported in this paper.

## Outdated Models
* Replaces the paradigm of single-gene marker-assisted selection for complex quantitative traits with whole-genome genomic selection and multi-parent MARS schemes.

## Under-Researched Populations
* Wild sunflower relatives (*Helianthus* wild species), potato landraces from the Andean center of origin, and teosinte accessions for novel stress-resilience alleles.

## Future Directions
* Expand genomic selection training populations to predict hybrid performance and multi-environment stability in stress-prone environments.
* Deploy CRISPR/Cas genome editing to precisely modify negative regulators of disease susceptibility (*S-genes*) and hormone receptors across diverse crop backgrounds.

## Key References to Follow Up
* **Schnable PS, et al. (2009)** *The B73 maize genome: complexity, diversity, and dynamics.* Science 326:1112-1115.
* **Potato Genome Sequencing Consortium (2011)** *Genome sequence and analysis of the tuber crop potato.* Nature 475:189-195.
* **Badouin H, et al. (2017)** *The sunflower genome provides insights into oil metabolism, flowering and Asterid evolution.* Nature 546:148-152.

---
**Source PDF:** `data/margaritopoulou_2019_molecular_advances.pdf`
"""

# 9. knox_2012_enhancing_identication_genetic
SUMMARIES["knox_2012_enhancing_identication_genetic"] = """---
tags: [seed dormancy, preharvest sprouting, transgressive segregation, durum wheat, triticum turgidum]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: 10.1007/s10681-011-0570-5
authors: "Knox et al."
year: 2012
journal: "Euphytica"
format_version: 2
---

## Title & Metadata
* **Title:** Enhancing the identification of genetic loci and transgressive segregants for preharvest sprouting resistance in a durum wheat population
* **Authors:** R. E. Knox, F. R. Clarke, J. M. Clarke, S. L. Fox, R. M. DePauw, A. K. Singh
* **Journal:** Euphytica (2012) 186:17-32
* **DOI:** 10.1007/s10681-011-0570-5

## Abstract Summary
Preharvest sprouting (PHS) in durum wheat (*Triticum turgidum* L. var. *durum*) causes severe grain downgrading and economic losses by lowering falling numbers and pasta processing quality. Evaluating PHS resistance and seed dormancy is challenging due to environmental volatility and differences among measurement protocols. This study investigated a mapping population of 98 recombinant inbred lines (RILs) derived from a cross between the minimally dormant cv. 'Sentry' and the moderately dormant cv. 'Kyle', evaluated across three field years (1996, 1997, 1998) and one growth chamber trial. Sprouting was evaluated on intact spikes using a rain simulator sprouting index (SI) and on threshed grain using germination index (GI), germination resistance (GR), and percent germination (PG) scored across multiple incubation durations (7, 14, and 21 days). Phenotypic correlations varied substantially across test durations, with extended PG counts showing low correlations. Different measurement types and count durations identified distinct QTLs and transgressive segregants: GI at 7, 14, and 21 days and GR at 21 days identified a major QTL on chromosome 1A (*QPhsd.spa-1A.1*, P < 0.001); GR at 7 days identified a major QTL on chromosome 2A (*QPhsd.spa-2A.1*, P < 0.001); and GI at 21 days and PG at 7 days identified a major QTL on chromosome 7B (*QPhsd.spa-7B.1*, P < 0.001). The results prove that applying multiple phenotyping methods across multiple test durations is essential to capture the full genetic architecture and transgressive potential of PHS resistance in durum wheat.

## Introduction & Background
* Western Canada produces approximately 2 million hectares of durum wheat annually for domestic and export pasta markets, where preharvest sprouting causes tens of millions of dollars in downgrading losses during wet harvest seasons.
* Preharvest sprouting resistance is predominantly governed by seed dormancy, which degrades progressively during after-ripening from physiological maturity.
* Expression of PHS resistance is influenced by genotype, environment, and genotype × environment interactions, making characterization highly dependent on sampling timing and storage conditions.
* Various laboratory measures exist to assess dormancy: weighted germination index (GI), germination resistance (GR, time to 50% germination), percent germination (PG), and intact spike rain simulator sprouting index (SI).
* Whether different measurement methods and different germination count durations identify identical or distinct QTLs and transgressive segregants in durum wheat remained unresolved prior to this investigation.

## Key Concepts & Theory
- **[[Germination Index]]**: A weighted index calculating seed germination speed where early-germinating seeds receive higher numerical weights than late-germinating seeds.
- **[[Germination Resistance]]**: A dormancy metric calculating the time (in days) required to reach 50% germination of viable seeds.
- **[[Transgressive Segregation]]**: The emergence of progeny individuals that display phenotypes more extreme (superior resistance or greater susceptibility) than either parent.
- **[[Rain Simulator Sprouting Index]]**: A whole-spike assay that evaluates sprouting percentage in an artificial rain chamber equipped with rotating carousels and mist nozzles.
- **[[After-Ripening Period]]**: The post-maturity dry storage period during which primary seed dormancy is gradually lost, enabling rapid germination upon imbibition.

## Important Entities
* **Genes/Proteins**: [[Alpha-Amylase]]
* **Organisms**: [[Triticum turgidum]] (durum wheat cv. 'Sentry', cv. 'Kyle', cv. 'RL4137', cv. 'SC8021-V2', cv. 'Genesis', cv. 'AC Karma')
* **Tools/Techniques/Software**: [[Simple Sequence Repeat]] (SSR markers), [[Amplified Fragment Length Polymorphism]] (AFLP), [[Composite Interval Mapping]] (CIM), [[JoinMap]], [[MQTL Software]], [[Rain Simulator Chamber]]

## Methods & Experimental Design
* Mapping population: 98 F5-derived recombinant inbred lines (RILs) from the cross Sentry (moderately susceptible) × Kyle (moderately dormant).
* Environments: Replicated field tests near Swift Current, Saskatchewan, Canada in 1996 (two harvest sampling dates: T1 at 50% collapsed peduncle nodes, T2 two weeks later), 1997, 1998, and a controlled growth chamber trial in 1998 (17 °C).
* Intact spike rain simulator test: Harvested spikes subjected to standardized misting cycles at 17 °C for 5 days, scoring sprouted spikes to calculate SI.
* Threshed seed germination tests: Hand-threshed grains germinated at 15 °C in darkness, recording daily germination counts up to 21 days; non-germinated seeds treated with 0.5 mM GA3 to confirm viability. Calculations: GI7, GI14, GI21, GR7, GR14, GR21, PG7, PG14, PG21.
* Molecular genotyping and mapping: 156 SSR markers and 74 AFLP markers mapped on 96 lines using JoinMap 3.0. MQTL software used for simple (SIM) and composite interval mapping (CIM) with 1,500 permutations.

## Key Results & Data
* **Phenotypic correlations across durations**:
  * GR21 and GR14 were highly correlated (r = 0.99 in field), but correlations between GR21 and GR7 dropped to r = 0.82-0.91.
  * PG showed poor to moderate correlations with GR and GI; correlation between PG21 and PG7 was very low in 1996 (r = 0.19-0.21).
  * Rain simulator SI was moderately correlated with GR (r = -0.58 to -0.70) and GI (r = 0.68-0.70) across field environments.
* **Transgressive segregants**:
  * Transgressive segregation for high resistance (lines outperforming dormant parent Kyle) occurred across all environments.
  * GR7 consistently identified the highest number of transgressive resistant lines (up to 22 lines in 1997), while PG identified resistant segregants even at 14 and 21 days.
* **QTL detection across methods**:
  * *QPhsd.spa-1A.1* (chromosome 1A, flanked by *Xwmc611-Xwmc333*): Highly significant (P < 0.001) for GI7, GI14, GI21, and GR21.
  * *QPhsd.spa-2A.1* (chromosome 2A, flanked by *Xgwm515-Xgwm425*): Highly significant (P < 0.001) in multiple environments for GR7.
  * *QPhsd.spa-7B.1* (chromosome 7B, flanked by *Xgwm297-Xwmc532*): Highly significant (P < 0.001) for GI21 and PG7.
  * Additional minor QTLs detected at 1-10% significance on chromosomes 4A (*Xgwm397*), 6B (*Xgwm508-Xgwm156*), and 7A.

## Mechanistic Insights
* Seed dormancy degradation is a kinetic, time-dependent process; early-interval germination metrics (e.g., GR7, GI7) capture initial dormancy release barriers, whereas late-interval metrics (GR21, GI21) reflect residual embryo dormancy depth.
* Different physiological components of dormancy are controlled by distinct genetic loci: chromosome 1A (*QPhsd.spa-1A.1*) governs long-term dormancy retention, chromosome 2A (*QPhsd.spa-2A.1*) regulates initial germination delay, and chromosome 7B (*QPhsd.spa-7B.1*) controls germination capacity.
* Whole-spike rain simulator assays integrate both internal embryo dormancy and external chaff/glume physical barriers, explaining moderate correlation with threshed grain assays.

## Conclusions & Implications
* Demonstrates that no single phenotyping method or evaluation duration captures the entire genetic landscape of PHS resistance in durum wheat.
* Combining multiple phenotyping protocols (GI, GR, and SI) across multiple durations is critical to identify transgressive segregants and resolve environment-specific QTLs.
* Markers *Xwmc611* (1A), *Xgwm515* (2A), and *Xgwm297* (7B) represent key diagnostic targets for marker-assisted breeding of sprouting-tolerant durum cultivars.

## Limitations & Caveats
* Genetic map resolution was constrained by the 98 RIL population size and marker density available for tetraploid wheat at the time of the study.
* Causal genes within the 1A, 2A, and 7B intervals were not isolated.

## Contradictory Findings
* Not reported in this paper.

## Outdated Models
* Overturns the simple hypothesis that all dormancy measurement methods identify identical QTLs and identical transgressive lines, proving that different parameters reveal distinct underlying genetic loci.

## Under-Researched Populations
* Tetraploid durum wheat breeding germplasm from Mediterranean and North American semiarid regions.

## Future Directions
* Fine-map *QPhsd.spa-1A.1*, *QPhsd.spa-2A.1*, and *QPhsd.spa-7B.1* using high-density SNP arrays and reference genomes.
* Pyramid the 1A, 2A, and 7B resistance alleles in elite durum cultivars and evaluate pasta quality under simulated preharvest rain conditions.

## Key References to Follow Up
* **Reddy LV, et al. (1985)** *Inheritance of seed dormancy in wheat.* Cereal Res. Commun. 13:181-187.
* **Gordon AG (1971)** *The germination resistance test—a new test for measuring germination quality of cereals.* Can. J. Plant Sci. 51:181-183.
* **Clarke JM, et al. (2005)** *Registration of 'Kyle' durum wheat.* Crop Sci. 28:1026.

---
**Source PDF:** `data/knox_2012_enhancing_identication_genetic.pdf`
"""

# 10. li_2026_translating_research_seed
SUMMARIES["li_2026_translating_research_seed"] = """---
tags: [seed dormancy, preharvest sprouting, abscisic acid, brachypodium distachyon, triticum aestivum]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: 10.3389/fpls.2026.1763984
authors: "Li et al."
year: 2026
journal: "Frontiers in Plant Science"
format_version: 2
---

## Title & Metadata
* **Title:** Translating research on seed dormancy and germination from Arabidopsis to temperate cereals to control pre-harvest sprouting
* **Authors:** Renqiang Li, Muhammad Usama Hameed, Koen Geuten
* **Journal:** Frontiers in Plant Science (2026) 17:1763984
* **DOI:** 10.3389/fpls.2026.1763984

## Abstract Summary
Preharvest sprouting (PHS) in temperate cereals (wheat and barley) is an agricultural consequence of reduced seed dormancy resulting from domestication selection for rapid, uniform germination. This comprehensive review systematically examines the genetic, hormonal, anatomical, and epigenetic pathways governing seed dormancy and germination, comparing the eudicot model *Arabidopsis thaliana* with temperate cereals and highlighting the undomesticated grass model *Brachypodium distachyon*. The authors analyze the conserved antagonistic hormone balance between abscisic acid ([[ABA]]) and gibberellic acid ([[GA]]), detailing core metabolic enzymes ([[NCED]], [[CYP707A]], [[GA20ox]], [[GA2ox]]) and signaling cascades ([[PYR/PYL/RCAR]], [[PP2C]], [[SnRK2]], [[ABI3]], [[ABI4]], [[ABI5]], [[GID1]], and [[DELLA]] / [[RGL2]]). Key cereal-specific dormancy loci discovered through natural variation are reviewed, including [[TaMFT]] / *TaPHS1*, [[TaMKK3-A]] / *HvMKK3*, *Qsd1*, [[OsSdr4]] / [[TaSdr]], and [[DOG1]]. Crucial structural distinctions between Arabidopsis and cereals—such as the large persistent starchy endosperm, living aleurone layer, fused caryopsis pericarp, adherent palea/lemma husks, and embryonic coleorhiza—are evaluated in the context of oxygen permeability and coat-imposed dormancy. Finally, the authors explore epigenetic mechanisms (histone modifications, DNA methylation, and microRNAs) and propose translational strategies using *Brachypodium* to engineer tunable seed dormancy for climate-resilient crop breeding.

## Introduction & Background
* Artificial selection during cereal domestication eliminated primary seed dormancy to achieve fast, uniform stand establishment, inadvertently creating widespread vulnerability to preharvest sprouting during wet harvest seasons.
* PHS causes premature endosperm starch breakdown by alpha-amylase, sharply lowering Hagberg Falling Numbers in bread wheat and causing malting filter clogging in barley.
* An ideal commercial ideotype requires 'tunable dormancy': strong, reliable primary dormancy on the mother plant to resist PHS, followed by a short, controllable after-ripening or chemical switch to permit rapid, uniform malting or seeding.
* Extensive research in *Arabidopsis thaliana* has delineated core hormonal circuits and environmental signaling pathways (temperature, light, nitrate), but translation to monocot crops is complicated by profound anatomical, physiological, and genomic divergences.
* The wild temperate grass *Brachypodium distachyon* (small ~300 Mb diploid genome, short life cycle, close taxonomic relatedness to wheat and barley) serves as a vital intermediate model for functional translational genomics.

## Key Concepts & Theory
- **[[Tunable Seed Dormancy]]**: A crop breeding strategy aiming to maintain robust dormancy at crop maturity while enabling rapid, synchronized dormancy release prior to planting or malting.
- **[[ABA/GA Antagonism]]**: The central hormonal rheostat wherein abscisic acid induces and maintains dormancy while gibberellins trigger reserve mobilization and germination.
- **[[Coat-Imposed Dormancy]]**: Inhibition of germination exerted by maternal seed coverings (caryopsis pericarp, testa, and adherent husk) through mechanical constraint, phenolic oxidation, and oxygen restriction.
- **[[DELAY OF GERMINATION 1]]**: An evolutionarily conserved protein phosphatase-interacting dormancy master regulator that functions alongside ABA signaling to control seed dormancy depth.
- **[[Coleorhiza]]**: A sheath-like tissue enclosing the embryonic root in monocot grasses that regulates water uptake, hormone metabolism, and radicle emergence.

## Important Entities
* **Genes/Proteins**: [[NCED]], [[CYP707A]], [[GA20ox]], [[GA2ox]], [[ABI3]], [[ABI4]], [[ABI5]], [[SnRK2]], [[PP2C]], [[GID1]], [[DELLA]], [[RGL2]], [[SLY1]], [[DOG1]], [[TaMFT]], [[TaMKK3-A]], [[HvMKK3]], [[Qsd1]], [[OsSdr4]], [[TaSdr]], [[Tamyb10]], [[VIVIPAROUS-1]], [[MYB107]]
* **Organisms**: [[Arabidopsis thaliana]], [[Brachypodium distachyon]], [[Triticum aestivum]], [[Hordeum vulgare]], [[Oryza sativa]]
* **Tools/Techniques/Software**: [[CRISPR/Cas Genome Editing]], [[Comparative Genomics]], [[RNA Sequencing]], [[Germination Index Assay]], [[Falling Number Assay]]

## Methods & Experimental Design
* Systematic literature review: Integration of molecular, physiological, genetic, epigenetic, and anatomical datasets across Arabidopsis, Brachypodium, wheat, barley, and rice.
* Comparative pathway synthesis: Alignment of orthologous gene families, hormonal signaling components, and downstream transcriptional networks regulating seed dormancy induction, maintenance, and release.

## Key Results & Data
* **Structural differences and dormancy**:
  * Arabidopsis seeds contain a small single-celled endosperm and dead testa; temperate cereals have a large persistent starchy endosperm, living single-celled aleurone layer, fused caryopsis pericarp, adherent lemma/palea husks, and embryonic coleorhiza.
  * Husks in cereals impose dormancy primarily by restricting oxygen diffusion (oxygen level under barley husks drops to 0.3% at 30 °C vs 15.8% at 15 °C) and accumulating phenolic compounds (flavan-4-ols, phlobaphenes regulated by *Tamyb10* / *R-1*).
* **Conserved hormonal circuitry**:
  * ABA synthesis (*NCED6/9* in Arabidopsis; *TaNCED1/2*, *HvNCED1/2*) and catabolism (*CYP707A1/2/3*; *HvABA8'OH1*) operate antagonistically with GA biosynthesis (*GA20ox*, *GA3ox*) and catabolism (*GA2ox*).
  * ABA perception via PYR/PYL receptors inhibits PP2Cs, activating SnRK2 kinases to phosphorylate ABI3/ABI4/ABI5 transcription factors.
  * GA perception by GID1 triggers 26S proteasome-mediated degradation of DELLA repressors (such as RGL2) via SLY1 F-box proteins, enabling aleurone enzyme activation.
* **Cereal-specific dormancy loci**:
  * [[TaMFT]] / *TaPHS1* (3AS): PEBP-family signaling regulator upregulating *ABI3/5* and repressing germination under low temperature.
  * [[TaMKK3-A]] / *HvMKK3* (*QPhs.spa-4A* / *Qsd2*): MAP kinase kinase 3 with a causal SNP conferring ABA sensitivity and seed dormancy.
  * *Qsd1* (barley chromosome 5H): Encodes an alanine aminotransferase (*HvAlaAT1*) controlling seed dormancy independently of the classical ABA pathway.
  * [[TaSdr]] / *OsSdr4*: Orthologous transcription factor acting downstream of *Vp1* to impose dormancy.
  * [[DOG1]]: Functional conservation in wheat and barley modulating dormancy via protein phosphatase PP2C (AHG1/AHG3) interaction.
* **Epigenetic regulation**: Dynamic histone H3K4 trimethylation (activating) and H3K27 trimethylation (repressing), DNA methylation, and small RNAs (such as miR156 and miR159) fine-tune dormancy transitions.

## Mechanistic Insights
* Seed dormancy in temperate cereals operates through an integrated two-tier mechanism: (1) maternal coat-imposed and husk-imposed hypoxia/inhibitory constraints, and (2) zygotic embryo- and aleurone-regulated hormonal signaling networks.
* The [[ABA/GA]] ratio acts as the ultimate biochemical executioner of germination, modulated upstream by the [[DOG1]]-PP2C module, [[TaMFT]], and the [[TaMKK3]] MAPK cascade in response to environmental temperature and light cues.
* The aleurone layer in cereals serves a unique dual function: acting as an ABA-responsive dormancy sensor and synthesizing hydrolytic enzymes (alpha-amylase, endo-beta-mannanase) upon GA activation.

## Conclusions & Implications
* Translation of seed dormancy knowledge from Arabidopsis to temperate cereals requires careful accounting for monocot-specific anatomical structures (aleurone, coleorhiza, adherent husks).
* *Brachypodium distachyon* provides a tractable, highly transformable model that bridges the phylogenetic and physiological gap between Arabidopsis and temperate polyploid crops.
* Pyramiding elite natural alleles or employing precision CRISPR editing of negative dormancy regulators (e.g., *CYP707A*, *GA20ox*, *MKK3*) offers a viable path toward creating climate-resilient cereals with tunable PHS resistance.

## Limitations & Caveats
* Functional validation of many Arabidopsis-derived candidate genes in polyploid wheat is hindered by homoeologous gene redundancy and transformation recalcitrance.
* The molecular mechanism connecting the major barley dormancy locus *Qsd1* (*HvAlaAT1*) to nitrogen/amino acid metabolism and germination control remains incompletely resolved.

## Contradictory Findings
* Not reported in this paper.

## Outdated Models
* Refutes the eudicot-centric model that seed coverings act solely as a physical barrier to water uptake, demonstrating that in temperate cereals husks primarily control dormancy through oxygen diffusion restriction and phenolic oxidation.

## Under-Researched Populations
* Wild *Brachypodium* accessions and undomesticated wild cereal relatives (*Aegilops*, *Triticum dicoccoides*, *Hordeum spontaneum*) harboring uncharacterized dormancy alleles.

## Future Directions
* Exploit Brachypodium mutant libraries and CRISPR genome editing to functionally characterize unmapped cereal dormancy QTLs.
* Develop environmentally responsive, chemical-inducible promoter switches driving dormancy release for industrial malting barley and bread wheat.

## Key References to Follow Up
* **Nakamura S, et al. (2011)** *A wheat homolog of MOTHER OF FT AND TFL1 acts in the regulation of seed dormancy.* Plant Cell 23:3215-3229.
* **Torada A, et al. (2016)** *A causal gene for seed dormancy on wheat chromosome 4A encodes a MAP kinase kinase.* Curr. Biol. 26:782-787.
* **Sato K, et al. (2016)** *Identification of a functional gene for seed dormancy in barley.* Nat. Commun. 7:11202.

---
**Source PDF:** `data/li_2026_translating_research_seed.pdf`
"""

# 11. okuyama_2022_pre_harvest_sprouting
SUMMARIES["okuyama_2022_pre_harvest_sprouting"] = """---
tags: [preharvest sprouting, rain simulation, pericarp rupture, germplasm evaluation, triticum aestivum]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: 10.18006/2022.10(5).1129.1137
authors: "Okuyama et al."
year: 2022
journal: "Journal of Experimental Biology and Agricultural Sciences"
format_version: 2
---

## Title & Metadata
* **Title:** Pre-Harvest Sprouting Tolerance in 36 Bread Wheat Genotypes
* **Authors:** L. A. Okuyama, C. R. Riede, M. M. Kohli
* **Journal:** Journal of Experimental Biology and Agricultural Sciences (2022) 10(5):1129-1137
* **DOI:** 10.18006/2022.10(5).1129.1137

## Abstract Summary
Preharvest sprouting (PHS) caused by excessive rainfall during wheat (*Triticum aestivum* L.) maturation leads to severe yield losses and degrades baking quality across global wheat-producing regions. To identify superior parental donors for breeding PHS-tolerant cultivars in subtropical Brazil, 36 national and international varieties and advanced breeding lines were evaluated across two 3-year experiments at IAPAR-EMATER in Londrina, Paraná, Brazil. Intact spikes harvested at physiological maturity were subjected to standardized artificial rainfall simulation in a nebulizer mist chamber (applying ~280 mm water mist daily for 48 h). Sprouting was quantified via high-magnification (10x) assessment of pericarp rupture, and stability was analyzed using ANOVA, the Scott-Knott cluster test, and the Lin and Binns adaptability model. Germination percentages ranged widely from 8.8% to 85.3%. Genotypes classified as highly tolerant included 'ND 674' (13.8%), 'Grandin*2/RL 4137' (17.7%), 'Grandin' (8.8%), and 'Frontana' (19.8%). Genotypes classified as moderately tolerant included 'Alsen', 'CD 114', 'Milan/3/Attila//Fang 69/CIMMYT 3', 'Avante', 'BRS 177', 'IAC 5-Maringá', 'Onix', 'OR 1', 'RL 4137', and 'Rubi' (24.0% to 41.3%). These elite tolerant progenitors provide proven genetic sources for combining PHS resistance with high yield and superior end-use quality.

## Introduction & Background
* In Brazil and many temperate/subtropical wheat zones, frequent rain events near harvest cause extensive preharvest sprouting, downgrading grain from breadmaking to animal feed.
* Marker-assisted selection for PHS resistance is not yet accessible in many global breeding pipelines, necessitating rapid, reliable, low-cost phenotyping methodologies based on early sprouting symptoms.
* Early initiation of germination is accurately marked by seed pericarp rupture near the embryo before visual shoot or root elongation occurs.
* While the Hagberg Falling Number (FN) assay is the definitive quality standard, previous work demonstrated that pericarp rupture germination percentage under artificial rain correlates strongly with FN (r = -0.91, P < 0.01).
* Comprehensive multi-year germplasm evaluations of domestic and international cultivars are required to categorize parental lines for hybridization programs.

## Key Concepts & Theory
- **[[Preharvest Sprouting Tolerance]]**: The genetic and physiological capability of intact spikes to resist germination and alpha-amylase activation under wet pre-harvest conditions.
- **[[Pericarp Rupture]]**: The earliest physical indicator of wheat seed germination characterized by breakage of the outer pericarp layer covering the embryo.
- **[[Nebulizer Mist Chamber]]**: An artificial rainfall system generating controlled, uniform water mist (280 mm/day) on intact spikes to simulate severe field rainfall.
- **[[Lin and Binns Method]]**: A non-parametric statistical method estimating cultivar adaptability and stability parameter (Pi) across multiple environments.
- **[[Scott-Knott Test]]**: A hierarchical clustering algorithm that groups treatment means without ambiguous overlapping clusters.

## Important Entities
* **Genes/Proteins**: [[Alpha-Amylase]], [[Lr34]], [[Lr13]]
* **Organisms**: [[Triticum aestivum]] (wheat cultivars 'ND 674', 'Grandin', 'Frontana', 'RL 4137', 'Alsen', 'CD 114', 'BRS 177', 'BR 18-Terena', 'Supera', 'Rubi')
* **Tools/Techniques/Software**: [[Nebulizer Rainfall Chamber]], [[Scott-Knott Clustering]], [[Lin and Binns Model]], [[SAS Software]], [[GENES Software]]

## Methods & Experimental Design
* Plant materials: 36 bread wheat genotypes (16 in Experiment 1, 16 in Experiment 2, plus repeated standard checks) evaluated over two sowing dates across three years at IDR-Paraná (IAPAR-EMATER), Londrina, Brazil.
* Harvesting: ~100 spikes per genotype harvested by hand at physiological maturity (complete peduncle color loss) and air-dried at 20-25 °C.
* Misting chamber assay: 20 spikes per genotype inserted vertically into Styrofoam blocks in duplicate and exposed to nebulizer misting (30 min on/off cycles, ~280 mm mist/day) for 48 h.
* Sprouting scoring: Spikes sun-dried, hand-threshed, and 50 grains per sample examined under 10x magnification for pericarp rupture; germination percentages arcsine-transformed for ANOVA.
* Statistical models: Scott-Knott cluster analysis (P <= 0.05) and Lin and Binns (1988) superiority measure (Pi) using GENES and SAS software.

## Key Results & Data
* **Experiment 1 results**:
  * Genotype and year effects were highly significant (P <= 0.01); genotype × year interaction was non-significant, demonstrating consistent cultivar performance across years.
  * Germination percentages ranged from 13.83% to 78.83% (mean 56.67%).
  * Highly tolerant: 'ND 674' (13.8%) and 'Grandin*2/RL 4137' (17.7%).
  * Moderately tolerant: 'CD 114' (28.8%), 'Alsen' (32.2%), and 'Milan/3/Attila//Fang 69/CIMMYT 3' (40.2%).
  * Highly susceptible: 'BRS 208' (63.8%), 'Chirya 7' (67.5%), 'IPR 144' (69.7%), 'BRS Pardela' (71.0%), 'CD 104' (71.7%), 'BRS 210' (72.5%), 'BRS Guabiju' (73.7%), 'BRS 220' (74.0%), 'CD 108' (74.5%), and 'SW89-5124*2/Fasan' (78.8%).
* **Experiment 2 results**:
  * Germination percentages ranged from 8.83% to 85.33% (mean 44.43%).
  * Highly tolerant: 'Grandin' (8.8%) and 'Frontana' (19.8%).
  * Moderately tolerant: 'RL 4137' (24.0%), 'BRS 177' (25.7%), 'Rubi' (26.0%), 'IAC 5-Maringá' (29.5%), 'OR 1' (31.8%), 'Onix' (32.0%), and 'Avante' (41.3%).
  * Highly susceptible: 'CD 116' (63.2%), 'IAPAR 17-Caeté' (65.0%), 'Supera' (71.3%), 'Alcover' (78.8%), and 'BR 18-Terena' (85.3%).
* **Falling Number estimation**: Based on calibrated correlations, tolerant cultivars (<19% germination) maintain FN > 300 s under 48 h rain, while susceptible cultivars (>46% germination) exhibit severe sprout damage with FN < 200 s.

## Mechanistic Insights
* Multi-parent pedigree analysis revealed that PHS tolerance in 'Grandin*2/RL 4137' and 'ND 674' originates from ancestral donors including 'Frontana', 'Thatcher', and 'Kenya Farmer', confirming the durability of Frontana-derived dormancy across generations.
* Scoring pericarp rupture directly detects the initial cellular hydration and embryo expansion events, bypassing confounding varietal differences in post-germination coleoptile growth rates.

## Conclusions & Implications
* Standardized 48 h nebulizer misting combined with pericarp rupture scoring provides a rapid, high-throughput, and reliable screen for PHS tolerance in wheat breeding.
* Identified 'Frontana', 'Grandin', 'ND 674', and 'Grandin*2/RL 4137' as elite parental progenitors possessing stable PHS tolerance.
* These donors enable breeders to combine robust sprouting tolerance with high grain yield, excellent milling/baking properties, and disease resistances (e.g., leaf rust *Lr34/Lr13*, FHB).

## Limitations & Caveats
* The study did not perform molecular marker genotyping or QTL mapping on the evaluated cultivars.
* Controlled misting assays exclude wind, temperature swings, and microbial weathering present during natural field sprouting events.

## Contradictory Findings
* 'BRS 220' exhibited high susceptibility (74.0% germination) in this multi-year trial, in contrast to earlier single-year reports classifying it as moderately tolerant.

## Outdated Models
* Disproves the reliance on visual shoot/root emergence as the primary PHS screening criterion, proving that microscopic pericarp rupture detection provides earlier and more sensitive discrimination.

## Under-Researched Populations
* South American subtropical breeding lines and CIMMYT synthetic-derived advanced lines adapted to warm, humid environments.

## Future Directions
* Genotype the 36 cultivars for known functional alleles of *TaPHS1*, *TaMKK3*, and *Vp1B* to determine the genetic basis of tolerance in 'ND 674' and 'Grandin'.
* Develop automated image-processing pipelines to rapidly quantify pericarp rupture on threshed grain samples.

## Key References to Follow Up
* **Okuyama LA, et al. (2020)** *Relationship between falling number, germination percentage and sprouting score in wheat.* J. Exp. Biol. Agric. Sci. 8:680-686.
* **Andreoli C, et al. (2006)** *Genetic control of seed dormancy and pre-harvest sprouting in wheat.* Sci. Agric. 63:564-566.
* **DePauw RM, et al. (2009)** *RL4137 contributes preharvest sprouting resistance to Canadian wheats.* Euphytica 168:347-361.

---
**Source PDF:** `data/okuyama_2022_pre_harvest_sprouting.pdf`
"""

# 12. raverdy_2022_linkage_mapping_biomass
SUMMARIES["raverdy_2022_linkage_mapping_biomass"] = """---
tags: [linkage mapping, quantitative trait loci, biomass composition, cell wall, miscanthus sinensis]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: 10.1007/s12155-022-10402-8
authors: "Raverdy et al."
year: 2022
journal: "BioEnergy Research"
format_version: 2
---

## Title & Metadata
* **Title:** Linkage Mapping of Biomass Production and Composition Traits in a Miscanthus Sinensis Population
* **Authors:** Raphael Raverdy, Kristelle Lourgant, Emilie Mignot, Stéphanie Arnoult, Guillaume Bodineau, Yves Griveau, Cristiane H. Taniguti, Maryse Brancourt-Hulmel
* **Journal:** BioEnergy Research (2022) 15:1580-1601
* **DOI:** 10.1007/s12155-022-10402-8

## Abstract Summary
*Miscanthus sinensis* is a leading perennial C4 bioenergy crop valued for high lignocellulosic biomass production. Dissecting the genetic architecture of biomass yield and cell-wall composition is complicated by outcrossing heterozygosity and perennial ontogenetic changes across stand establishment and yield-plateau phases. This study conducted high-density quantitative trait locus (QTL) mapping in a full-sib F1 population of 157 *M. sinensis* genotypes derived from crossing ornamental cultivars 'Malepartus' and 'Silberspinne'. The population was evaluated across five consecutive years in two contrasting locations in France using a staggered-start design that partitioned the 'year' effect into 'age' (ages 1-4) and 'climatic condition' effects. An integrated linkage map of 2,602 single nucleotide polymorphism (SNP) markers spanning 2,770 cM across 19 linkage groups aligned to the *M. sinensis* reference genome was constructed. Composite Interval Mapping identified 260 QTLs for biomass production traits and 283 QTLs for biomass composition traits. In each location, 40-60% of production QTLs and ~30% of composition QTLs were stable across climatic conditions and ages, with 10-15% stable across locations. Twelve robust QTL clusters were identified on LG4, LG5, LG7, LG13, LG15, LG16, and LG18, containing 62 putative cell-wall candidate genes orthologous to maize and sorghum, providing key targets for marker-assisted breeding.

## Introduction & Background
* Commercial miscanthus production relies almost exclusively on a single sterile triploid clone (*Miscanthus × giganteus*), creating genetic vulnerability and limiting adaptation to diverse agro-ecological zones.
* The diploid progenitor *M. sinensis* (2n = 2x = 38) possesses wide genetic diversity, cold tolerance, and high biomass potential, serving as a primary target for breeding fertile intraspecific cultivars and novel interspecific hybrids.
* Phenotyping perennial grasses during the juvenile establishment phase (years 1-2) can produce misleading selections because biomass yield and composition stabilize only upon reaching the mature yield-plateau phase (years 3+).
* Staggered-start experimental designs establish overlapping cohorts across successive years, enabling linear mixed models to statistically disentangle plant age effects from annual climatic fluctuations.
* Constructing an integrated reference-aligned SNP linkage map and identifying stable QTLs across ages and climates is essential for implementing marker-assisted selection (MAS) in perennial grasses.

## Key Concepts & Theory
- **[[Integrated Genetic Map]]**: A comprehensive linkage map constructed for outcrossing heterozygous species that simultaneously incorporates all segregating marker configurations (1:2:1, 1:1) into a single phased map.
- **[[Staggered-Start Design]]**: An experimental field layout where multiple cohorts are planted in successive years in adjacent plots to separate plant age from growing season/weather effects.
- **[[Cell Wall Composition]]**: The proportional allocation of plant dry matter into lignocellulosic polymers: cellulose, hemicellulose, and acid detergent lignin.
- **[[Composite Interval Mapping]]**: A statistical method for QTL detection that incorporates selected background markers as cofactors to control genetic background variance.
- **[[Perennial Yield-Plateau Phase]]**: The developmental stage reached 3 to 4 years post-establishment where perennial root systems and aboveground biomass yields achieve steady-state stability.

## Important Entities
* **Genes/Proteins**: [[Cellulose Synthase]], [[Cinnamyl Alcohol Dehydrogenase]], [[Phenylalanine Ammonia-Lyase]], [[4-Coumarate--CoA Ligase]]
* **Organisms**: [[Miscanthus sinensis]] (cv. 'Malepartus', cv. 'Silberspinne'), [[Miscanthus x giganteus]], [[Sorghum bicolor]], [[Zea mays]]
* **Tools/Techniques/Software**: [[Genotyping-By-Sequencing]] (GBS), [[OneMap Package]], [[fullsibQTL Package]], [[breedR Package]], [[Near-Infrared Spectroscopy]] (NIRS), [[Van Soest Fiber Analysis]]

## Methods & Experimental Design
* Plant population: 157 F1 full-sib genotypes derived from 'Malepartus' × 'Silberspinne' planted as single plants at 1 plant/m² in an incomplete randomized block design (5 blocks).
* Locations & Design: Two contrasting sites in France: Estrées-Mons (deep loam soil) and Orléans (sandy soil). Staggered cohorts planted in 2014 (G1) and 2015 (G2) evaluated over 5 consecutive years (2014-2018).
* Phenotyping: Morphological/production traits: canopy height, maximum height, stem number, circumference at 50 cm, aboveground dry matter yield (late winter harvest). Composition traits via NIRS (calibrated by Van Soest method): NDF (neutral detergent fiber), ADF (acid detergent fiber), cellulose, hemicellulose, and ADL (acid detergent lignin).
* GBS genotyping & map construction: PstI 96-plex GBS libraries sequenced on Illumina HiSeq 3000 (150 bp single-end); 9,330 filtered SNPs mapped using OneMap; 2,602 non-distorted SNPs ordered according to the *M. sinensis* v7.1 reference genome across 19 LGs.
* Statistical analysis: Linear mixed models in breedR to compute BLUPs partitioned for age (Model 1) and climate (Model 2). QTL mapping with fullsibQTL using CIM with 1,000 permutations (5% LOD threshold). Orthology search against 2,148 sorghum and 2,470 maize cell-wall genes.

## Key Results & Data
* **High-density integrated genetic map**:
  * Total map length: 2,770 cM across 19 LGs (matching base chromosome number x = 19), with an average inter-marker distance of 1.06 cM (LG4 most saturated at 0.72 cM).
  * 613 bridge markers (1:2:1), 1,256 'Mal' markers (1:1), and 733 'Sil' markers (1:1).
* **QTL discovery and stability**:
  * 260 QTLs detected for biomass production traits and 283 QTLs for biomass composition traits.
  * 40% to 60% of production QTLs and ~30% of composition QTLs were stable across climatic conditions and ages within each location.
  * 10% to 15% of QTLs were stable across both geographic locations.
  * QTL R² values reached 19.5% in Estrées-Mons and 24.5% in Orléans.
* **QTL clusters and candidate genes**:
  * Twelve major QTL clusters identified: 5 for production traits (LG4, LG7, LG18), 6 for composition traits (LG4, LG5, LG13, LG15, LG16), and 1 joint cluster on LG15 combining canopy height and fiber content.
  * 62 putative *M. sinensis* cell-wall candidate genes identified within QTL clusters orthologous to sorghum and maize, including 12 differentially expressed genes belonging to cellulose synthase and lignin biosynthesis families.

## Mechanistic Insights
* Genetic control of biomass production in *M. sinensis* is predominantly governed by stable, constitutive additive and dominance alleles that maintain efficacy across juvenile establishment and mature plateau phases.
* The co-localization of canopy height, stem circumference, and total aboveground yield QTLs in clusters on LG4, LG7, and LG18 explains the strong positive genetic correlations among these morphometric components.
* Orthology with maize and sorghum confirms that core C4 grass cell-wall biosynthetic networks are highly conserved, allowing translational utilization of panicoid grass functional genomics in miscanthus breeding.

## Conclusions & Implications
* First reference-aligned, integrated SNP linkage map constructed for *Miscanthus sinensis*, providing high-resolution marker-trait associations across multi-year and multi-location field trials.
* Disentangling age from climatic effects confirms that juvenile-stage MAS can reliably predict mature-stand biomass performance.
* Stable QTL clusters and linked SNP markers on LG4, LG7, LG15, and LG18 provide direct targets for marker-assisted breeding to optimize biomass yield and biofuel quality.

## Limitations & Caveats
* The mapping population (157 full-sib individuals) was derived from a single cross between two Japanese ornamental cultivars, capturing a subset of wild *M. sinensis* diversity.
* GBS markers may leave minor gap regions in complex repetitive pericentromeric heterochromatin.

## Contradictory Findings
* Not reported in this paper.

## Outdated Models
* Replaces pseudo-testcross separate parental maps with unified integrated genetic maps for outcrossing full-sib perennial populations.

## Under-Researched Populations
* Wild diploid and tetraploid *Miscanthus sinensis* and *Miscanthus sacchariflorus* germplasm accessions from mainland Asia and northern latitudes.

## Future Directions
* Validate candidate cell-wall genes within LG4 and LG15 clusters via CRISPR/Cas editing or functional association genetics.
* Implement genomic prediction models incorporating age-independent stable QTLs into elite miscanthus breeding schemes.

## Key References to Follow Up
* **Mitic-Kopanja D, et al. (2017)** *Reference genome sequence of the perennial bioenergy grass Miscanthus sinensis.* Phytozome JGI.
* **Gifford JM, et al. (2015)** *Quantitative trait loci mapping of biomass yield and quality traits in Miscanthus sinensis.* G3 5:1981-1994.
* **Taniguti CH, et al. (2020)** *OneMap 2.0: modernizing and expanding a widely used R package for genetic mapping in outcrossing species.* Mol. Ecol. Resour. 20:1146-1153.

---
**Source PDF:** `data/raverdy_2022_linkage_mapping_biomass.pdf`
"""

# 13. kulwal_2012_association_mapping_pre
SUMMARIES["kulwal_2012_association_mapping_pre"] = """---
tags: [association mapping, preharvest sprouting, seed dormancy, dart markers, triticum aestivum]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: 10.1007/s00122-012-1872-0
authors: "Kulwal et al."
year: 2012
journal: "Theoretical and Applied Genetics"
format_version: 2
---

## Title & Metadata
* **Title:** Association mapping for pre-harvest sprouting resistance in white winter wheat
* **Authors:** Pawan Kulwal, Goro Ishikawa, David Benscher, Zongyun Feng, Long-Xi Yu, Ashok Jadhav, Subhash Mehetre, Mark E. Sorrells
* **Journal:** Theoretical and Applied Genetics (2012) 125:793-805
* **DOI:** 10.1007/s00122-012-1872-0

## Abstract Summary
Preharvest sprouting (PHS) in white winter wheat (*Triticum aestivum* L.) results from premature seed germination under wet harvest conditions, causing extensive milling and baking quality degradation. To identify quantitative trait loci (QTLs) and linked diagnostic markers in elite breeding germplasm, an association mapping panel of 198 soft white winter wheat genotypes was genotyped with 1,166 marker loci (1,103 DArT and 62 SSR/PLUG markers) covering all 21 chromosomes. PHS response was evaluated over four consecutive field years (2008-2011) in Ithaca, New York, incorporating functional genome-wide association mapping (fGWAS) across varying after-ripening (AR) durations (3, 5, and 7 days). General linear models (GLM) and mixed linear models (MLM) accounting for population structure (Q) and kinship (K) identified eight QTLs linked to 13 markers across seven chromosomes: 1BS, 2BS, 2BL, 2DS, 4AL, 6DL, 7BS, and 7DS. A major QTL on chromosome arm 4AL linked to SSR markers [[gwm397]] and [[gwm610]] was consistently detected across three environments and in 4-year BLUP analyses, explaining up to 12% of phenotypic variation. A novel QTL was discovered on chromosome arm 7BS linked to DArT marker [[wPt-8283]]. The results validate known PHS loci and demonstrate the power of association mapping in elite breeding germplasm.

## Introduction & Background
* Preharvest sprouting is a severe quality bottleneck in soft white winter wheat, which is preferred for pastry, cookie, and cake flour, but lacks the seed dormancy typically associated with red wheat.
* While biparental QTL mapping has identified genomic regions on chromosomes 2B, 3A, and 4A, it samples only two parental alleles and suffers from restricted recombination resolution.
* Association mapping (AM) based on linkage disequilibrium (LD) exploits historical recombination across diverse elite germplasm panels, offering higher mapping resolution and direct applicability to breeding pipelines.
* Evaluating PHS response across multiple after-ripening durations (functional GWAS or fGWAS) can reveal stage-dependent QTLs that regulate the rate of dormancy breakdown.
* The objectives were to perform genome-wide association mapping for PHS resistance in elite soft white winter wheat, implement fGWAS across AR durations, and discover diagnostic markers for breeding selection.

## Key Concepts & Theory
- **[[Association Mapping]]**: A high-resolution genetic mapping approach utilizing ancestral recombination and linkage disequilibrium in natural or breeding populations to identify marker-trait associations.
- **[[Functional Genome-Wide Association Mapping]]**: A dynamic GWAS strategy evaluating trait expression across multiple developmental time points or after-ripening durations.
- **[[Diversity Array Technology]]**: A high-throughput, microarray-based hybridization marker system that simultaneously profiles thousands of polymorphic genomic loci without prior sequence knowledge.
- **[[Mixed Linear Model]]**: A statistical framework incorporating fixed population structure effects (Q) and random individual kinship relatedness (K) to control spurious false-positive associations.
- **[[After-Ripening Decay]]**: The progressive loss of primary physiological seed dormancy during dry post-harvest storage, leading to increased germination competence.

## Important Entities
* **Genes/Proteins**: [[gwm397]], [[gwm610]], [[wPt-730913]], [[wPt-8283]], [[wPt-0697]], [[wPt-666931]], [[wPt-666564]], [[wPt-6003]], [[cfd37]], [[barc328]], [[stm773]], [[Ppd-B1]], [[TaPHS1]], [[TaMKK3]]
* **Organisms**: [[Triticum aestivum]] (soft white winter wheat cultivars 'Cayuga', 'Caledonia', 'Whatford')
* **Tools/Techniques/Software**: [[Diversity Array Technology]] (DArT), [[Simple Sequence Repeat]] (SSR), [[TASSEL Software]], [[STRUCTURE Software]], [[JMP]], [[MATMODEL Software]]

## Methods & Experimental Design
* Plant population: 198 elite soft white winter wheat genotypes (varieties, parental lines, advanced breeding selections from Cornell University).
* Field phenotyping: 4 years (2008-2011) at two locations in Ithaca, NY (Snyder and McGowan). Spikes harvested at physiological maturity, air-dried, and tested in a misting chamber for 4 days at 100% humidity, scoring visual sprouting on a 0-9 scale.
* fGWAS trial: In 2011, spikes were evaluated after 3, 5, and 7 days of after-ripening drying to assess dormancy degradation kinetics.
* Molecular genotyping: 1,103 DArT markers and 62 SSR/PLUG markers; filtered to 657 non-redundant markers (MAF >= 10%, r² < 1.0).
* Statistical analysis: Population structure modeled via STRUCTURE (K=2) and Principal Component Analysis (PCA); Kinship matrix (K) generated in TASSEL; association testing using GLM (Q) and MLM (Q + K) with False Discovery Rate (FDR) and q-value thresholds.

## Key Results & Data
* **Phenotypic variance and heritability**:
  * PHS scores ranged from 0.00 to 5.95 across environments. Broad-sense heritability across 4 years was 0.37 (0.71 at McGowan location).
  * Significant correlations were observed across after-ripening durations in 2011 (r = 0.58 to 0.65, P < 0.001); 5-day AR period exhibited the highest genetic variance.
* **Eight QTLs mapped across seven chromosomes**:
  * **4AL QTL**: Linked to SSR markers *gwm610.162* (P = 1.69E-07, R² = 11%), *gwm610.172* (P = 2.29E-07, R² = 11%), and *gwm397.191* (P = 1.17E-05, R² = 9%), detected in three individual years and in 4-year BLUPs.
  * **7BS QTL (Novel)**: Linked to DArT marker *wPt-8283* at 68.9 cM (P = 1.74E-04, R² = 4-5%), significant across 3-day and 5-day AR periods and 4-year BLUPs.
  * **2BL QTL**: Linked to DArT markers *wPt-0697* (86.6 cM, R² = 3-7%) and *wPt-666931* (97.8 cM, R² = 3-7%), significant across AR durations.
  * **1BS QTL**: Linked to *wPt-666564* (33.5 cM, P = 2.77E-04, R² = 5%).
  * **2BS QTL**: Linked to SSRs *barc328* (20.2 cM) and *stm773* (48.0 cM), explaining 3-4% variance.
  * **2DS QTL**: Linked to *wPt-6003* (14.7 cM, R² = 2-5%).
  * **6DL QTL**: Linked to *cfd37.208* (60.0 cM, R² = 3-6%).
  * **7DS QTL**: Linked to *wPt-663918* (0.5 cM, R² = 2-4%).
* **Functional GWAS (AR duration dynamics)**:
  * Markers *wPt-0697* (2BL) and *wPt-666223* were significant across all three AR durations (3, 5, and 7 days), while *wPt-8283* (7BS) was prominent at early AR (3-5 days).

## Mechanistic Insights
* PHS resistance in elite white winter wheat is polygenic, conditioned by a major, stable locus on chromosome arm 4AL (*gwm397* / *gwm610*) acting in concert with dynamic modifier loci across chromosomes 1B, 2B, 2D, 6D, 7B, and 7D.
* fGWAS reveals that loci on 2BL and 7BS maintain dormancy retention during initial hydration periods, whereas the 4AL locus provides sustained basal resistance throughout post-maturity desiccation.
* The elite panel exhibited minimal population structure, confirming that historical selection in soft white winter wheat has maintained favorable dormancy alleles across distinct breeding lineages.

## Conclusions & Implications
* Association mapping in elite germplasm successfully identified eight PHS QTLs directly relevant to commercial wheat breeding pipelines.
* Validated the 4AL QTL (*gwm397* / *gwm610*) as a robust, multi-environment donor of dormancy in soft white winter wheat.
* Identified a novel QTL on chromosome 7BS (*wPt-8283*) providing a new genetic target for marker-assisted selection against preharvest sprouting.

## Limitations & Caveats
* DArT marker density was moderate compared to contemporary high-density SNP arrays (e.g., 90K or GBS), limiting physical candidate gene resolution.
* PHS evaluations relied on mist chamber scoring rather than direct Falling Number viscosity assays.

## Contradictory Findings
* The 4AL QTL exhibited minor to moderate effect sizes (R² ~ 9-12%) in this elite association panel compared to >40% R² reported in biparental crosses, reflecting allelic fixation or background epistasis in elite lines.

## Outdated Models
* Refutes the view that biparental mapping QTLs necessarily represent the dominant sources of variation in elite commercial germplasm panels.

## Under-Researched Populations
* Commercial soft white winter wheat gene pools outside North America (e.g., European and East Asian winter wheat diversity panels).

## Future Directions
* Convert significant DArT and SSR markers (*wPt-8283*, *gwm397*, *wPt-0697*) into high-throughput KASP assays for marker-assisted selection.
* Re-genotype the Cornell association panel with high-density SNP arrays to fine-map the novel 7BS QTL.

## Key References to Follow Up
* **Anderson JA, et al. (1993)** *RFLP analysis of genomic regions associated with resistance to preharvest sprouting in wheat.* Crop Sci. 33:453-459.
* **Munkvold JD, et al. (2009)** *Mapping quantitative trait loci for preharvest sprouting resistance in white wheat.* Theor. Appl. Genet. 119:1223-1235.
* **Yu J, Buckler ES (2006)** *Genetic association mapping and genome organization of maize.* Curr. Opin. Biotechnol. 17:155-160.

---
**Source PDF:** `data/kulwal_2012_association_mapping_pre.pdf`
"""

# 14. vetch_2019_allelic_impacts_taphs1
SUMMARIES["vetch_2019_allelic_impacts_taphs1"] = """---
tags: [preharvest sprouting, taphs1, tamkk3, viviparous-1, triticum aestivum]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: 10.2135/cropsci2018.05.0341
authors: "Vetch et al."
year: 2019
journal: "Crop Science"
format_version: 2
---

## Title & Metadata
* **Title:** Allelic Impacts of TaPHS1, TaMKK3, and Vp1B3 on Preharvest Sprouting of Northern Great Plains Winter Wheats
* **Authors:** Justin M. Vetch, Robert N. Stougaard, John M. Martin, Mike Giroux
* **Journal:** Crop Science (2019) 59(1):140-149
* **DOI:** 10.2135/cropsci2018.05.0341

## Abstract Summary
Preharvest sprouting (PHS) in bread wheat (*Triticum aestivum* L.) reduces grain yield and degrades end-use baking quality by initiating premature alpha-amylase synthesis. To determine the utility of previously cloned dormancy genes in regional wheat improvement, 21 winter wheat cultivars and experimental lines adapted to the Northern Great Plains (grown across two field seasons in northwestern Montana) were assayed for allelic variation at three major PHS loci: [[TaPHS1-3A]] (a PEBP/MFT signaling factor), [[TaMKK3-4A]] (a mitogen-activated protein kinase kinase 3), and [[Vp1-1B]] (a B3 domain regulator). Whole spikes harvested at physiological maturity were subjected to 7 days of continuous misting chamber evaluation (scoring sprouting on a 1-7 scale), alongside assessments of falling number, alpha-amylase activity, and agronomic parameters. Sprouting scores ranged from 1.0 (fully dormant) to 7.0 (fully non-dormant). While allelic variation was detected at all three candidate genes, [[TaPHS1-3A]] was the only locus significantly associated with PHS resistance (P < 0.01), where lines carrying the resistant allele had significantly lower sprout scores (mean 2.9 vs 4.3 in susceptible lines) and accounted for ~18% of phenotypic variance. In contrast, [[TaMKK3-4A]] and [[Vp1-1B]] showed no significant main effect on PHS scores, suggesting their phenotypic effects were masked by *TaPHS1* allelic segregation in this germplasm.

## Introduction & Background
* Preharvest sprouting causes worldwide wheat losses exceeding $1 billion annually by degrading endosperm starch into simple sugars, causing flour stickiness and poor loaf volume.
* Artificial selection during domestication reduced seed dormancy to ensure rapid, uniform field emergence, leaving commercial cultivars vulnerable to harvest-season rainfall.
* Multiple major QTLs have been mapped and cloned in global germplasm:
  * *TaPHS1-3A* (*TaMFT*, chromosome 3AS), where coding SNPs (+646, +666) and promoter SNPs (-222) regulate transcript functionality and dormancy depth.
  * *TaMKK3-4A* (chromosome 4AL), where a C660A exon 5 SNP alters an amino acid residue and modulates ABA responsiveness.
  * *TaVp1-1B* (chromosome 1B), an ortholog of maize *Viviparous-1* detected via STS marker *Vp1B3*.
* Because PHS genetics is highly background- and region-specific, the actual allelic frequencies and phenotypic contributions of these cloned loci required empirical validation in Northern Great Plains winter wheat germplasm.

## Key Concepts & Theory
- **[[Preharvest Sprouting]]**: The premature germination of grains on the mother plant before harvest, leading to endosperm starch hydrolytic degradation.
- **[[TaPHS1-3A]]**: A cloned 3AS dormancy regulator encoding a phosphatidylethanolamine-binding protein (PEBP) related to MOTHER OF FT AND TFL1.
- **[[TaMKK3-4A]]**: A cloned 4AL dormancy gene encoding a mitogen-activated protein kinase kinase 3 involved in ABA signal transduction.
- **[[Viviparous-1]]**: A B3-domain transcription factor homolog (*Vp1-1B*) that regulates embryo maturation and ABA sensitivity in cereal seeds.
- **[[Hagberg Falling Number]]**: An international standard viscometric test measuring alpha-amylase activity in flour slurries, where low times indicate high enzymatic sprout damage.

## Important Entities
* **Genes/Proteins**: [[TaPHS1-3A]], [[TaMKK3-4A]], [[Vp1-1B]], [[Alpha-Amylase]], [[TaMFT]]
* **Organisms**: [[Triticum aestivum]] (winter wheat cv. 'Bearpaw', 'Loma', 'Keldin', 'Northern', 'Yellowstone', 'Brawl CLP', 'Decade', 'Judee', 'Warhorse')
* **Tools/Techniques/Software**: [[Misting Chamber Assay]], [[Hagberg Falling Number Machine]], [[Ceralpha Alpha-Amylase Micro-Assay]], [[Sanger DNA Sequencing]], [[Sequence-Tagged Site]] (STS marker Vp1B3), [[Linear Mixed Models]] (lme4 R package)

## Methods & Experimental Design
* Plant materials: 21 winter wheat genotypes (13 named varieties, 8 advanced lines; 20 hard red, 1 hard white) grown in replicated field trials (RCBD, 3 reps) at Creston, MT (2016) and Bozeman, MT (2017).
* Phenotyping: Intact spikes harvested at physiological maturity, dried for 24 h at 37 °C, stored at -20 °C, and tested in a custom automated misting chamber (4 s mist every 5 min) for 7 days. Spikes scored on a 1-7 scale (1 = 0% sprouted, 7 = 100% sprouted with shoots >5 cm).
* Quality assays: Hagberg Falling Number measured on sound grain using Perten FN1000; alpha-amylase activity determined via Ceralpha micro-assay at 400 nm; single-kernel characterization (SKCS 4100) for grain hardness, diameter, and weight.
* Molecular genotyping: *TaPHS1-3A* sequenced across an 863-bp fragment covering +646/+666 SNPs; *TaMKK3-4A* sequenced across an 800-bp fragment covering the C660A SNP; *Vp1-1B* assayed using STS marker *Vp1B3* (yielding 845/569 bp in resistant and 652 bp in susceptible lines).
* Statistical analysis: Linear mixed-effects models in R (lme4 and emmeans) treating entry within allelic class as random and year, gene, and year × gene as fixed effects.

## Key Results & Data
* **Allelic distribution across 21 genotypes**:
  * *TaPHS1-3A*: 11 resistant (R), 10 susceptible (S).
  * *TaMKK3-4A*: 9 resistant (R), 12 susceptible (S).
  * *Vp1B3*: 12 resistant (R), 9 susceptible (S).
* **Significant impact of TaPHS1-3A**:
  * *TaPHS1* was the only gene significantly associated with PHS score (P < 0.01).
  * Resistant allele group mean PHS score was 2.9 ± 0.23 vs 4.3 ± 0.35 in the susceptible group (~18% phenotypic variation explained).
  * *TaPHS1* resistant lines were significantly shorter (95.8 cm vs 100.2 cm, P = 0.01) and had higher grain protein (132.8 g/kg vs 125.0 g/kg, P = 0.02).
* **Lack of main effect for TaMKK3-4A and Vp1-1B**:
  * *TaMKK3-4A* allelic groups showed no significant difference in PHS scores (R: 3.46 vs S: 3.63, P = 0.37).
  * *Vp1B3* allelic groups showed no significant difference in PHS scores (R: 3.50 vs S: 3.64, P = 0.39).
  * *TaMKK3* susceptible lines had ~20 s higher FN (368.9 s vs 347.1 s, P = 0.002) and larger kernel diameter (2.7 mm vs 2.6 mm, P = 0.04) in sound grain.
* **Environmental interaction**: PHS scores were significantly influenced by year (P < 0.01) and year × *TaPHS1* interaction (P = 0.03), reflecting drier conditions and later spike harvest in 2017.

## Mechanistic Insights
* In Northern Great Plains winter wheat, [[TaPHS1-3A]] acts as the primary genetic gatekeeper governing seed dormancy and preharvest sprouting resistance.
* The lack of significant PHS impact from [[TaMKK3-4A]] and [[Vp1-1B]] indicates epistatic masking by *TaPHS1* or inadequate statistical power in small panels segregating for multiple large-effect loci.
* The phenotypic effect of *TaPHS1* diminishes as spikes remain in the field past physiological maturity, consistent with the developmental decline of *TaPHS1* transcript abundance during post-maturation desiccation.

## Conclusions & Implications
* Selection for the resistant *TaPHS1-3A* allele provides an immediate, highly effective breeding strategy to enhance PHS tolerance in Northern Great Plains winter wheat.
* Causal SNP genotyping of *TaPHS1* can be reliably deployed for marker-assisted selection in regional breeding pipelines.
* Breeding programs must fix the favorable *TaPHS1* allele before attempting to select for secondary modifier loci like *TaMKK3* or *Vp1-1B*.

## Limitations & Caveats
* The study evaluated 21 genotypes; larger mapping populations fixed for *TaPHS1* are necessary to accurately resolve minor or epistatic contributions of *TaMKK3* and *Vp1B*.
* Sound grain rather than sprout-damaged grain was used for baseline FN and alpha-amylase assays, explaining the absence of correlation between sound grain FN and PHS scores.

## Contradictory Findings
* *TaMKK3-4A* and *Vp1-1B*, previously reported as major PHS determinants in Asian and European wheats, showed no detectable effect on sprouting scores in this Montana winter wheat panel.

## Outdated Models
* Challenges the assumption that previously validated global dormancy genes (*TaMKK3*, *Vp1B*) will automatically exhibit large main effects in all regional breeding germplasms without consideration of genetic background epistasis.

## Under-Researched Populations
* Hard red and hard white winter wheat cultivars grown in the Northern Great Plains and Intermountain West of North America.

## Future Directions
* Evaluate *TaMKK3* and *Vp1-1B* in biparental populations fixed for the susceptible *TaPHS1* allele to test for conditional gene expression.
* Develop multiplex KASP assays combining *TaPHS1*, *TaMKK3*, and *Vp1B* causal SNPs for high-throughput breeding screening.

## Key References to Follow Up
* **Nakamura S, et al. (2011)** *A wheat homolog of MOTHER OF FT AND TFL1 acts in the regulation of seed dormancy.* Plant Cell 23:3215-3229.
* **Liu S, et al. (2013)** *A natural mutation in the promoter of TaPHS1 causes pre-harvest sprouting in wheat.* Nat. Commun. 4:2127.
* **Torada A, et al. (2016)** *A causal gene for seed dormancy on wheat chromosome 4A encodes a MAP kinase kinase.* Curr. Biol. 26:782-787.

---
**Source PDF:** `data/vetch_2019_allelic_impacts_taphs1.pdf`
"""

# 15. liu_2020_artificial_selection_breeding
SUMMARIES["liu_2020_artificial_selection_breeding"] = """---
tags: [taphs1, seed dormancy, preharvest sprouting, artificial selection, triticum aestivum]
type: source
date_created: 2026-03-30
date_updated: 2026-03-30
source_count: 1
doi: 10.1007/s00122-020-03700-2
authors: "Liu et al."
year: 2020
journal: "Theoretical and Applied Genetics"
format_version: 2
---

## Title & Metadata
* **Title:** Artificial selection in breeding extensively enriched a functional allelic variation in TaPHS1 for pre-harvest sprouting resistance in wheat
* **Authors:** Shubing Liu, Danfeng Wang, Meng Lin, Sunish K. Sehgal, Lei Dong, Yuye Wu, Guihua Bai
* **Journal:** Theoretical and Applied Genetics (2020) 133(12):3453-3463
* **DOI:** 10.1007/s00122-020-03700-2

## Abstract Summary
Preharvest sprouting (PHS) in wheat (*Triticum aestivum* L.) results from insufficient seed dormancy (SD) and causes catastrophic yield and quality losses globally. While three functional causal mutations in [[TaPHS1]] (*Qphs.pseru-3AS*)—including a promoter SNP at -222 and exon 3 / intron 3 splicing mutations at +646 and +666—were previously cloned, several wheat accessions carrying resistant alleles at all three sites remain highly susceptible to PHS. In this study, the authors discovered a novel fourth causal mutation in [[TaPHS1]]: a C to T transition at position 732 nt in the 3'-untranslated region (3'-UTR) that dramatically downregulates *TaPHS1* transcript expression during seed maturation. Screening across 343 wild/domesticated wheat progenitors, 295 Iranian landraces, 205 U.S. elite lines, and 617 worldwide cultivars revealed that the PHS-susceptible T allele originated in wild wheat progenitors at low frequency (*T. urartu* 7.1%, *T. dicoccoides* 1.75%, Iranian landraces 11.2%) but was dramatically enriched by human artificial selection during modern breeding to 53.3% in modern cultivars. Haplotype analysis across the four functional SNPs (-222, +646, +666, 732 nt) revealed that the ancestral [[CGAC]] haplotype confers the strongest PHS resistance (sprouting rate 26.1%), whereas the [[TATT]] haplotype carrying all four susceptibility alleles causes severe sprouting (67.4%). A high-throughput KASP assay was developed to enable marker-assisted selection for elite *TaPHS1* haplotypes.

## Introduction & Background
* Preharvest sprouting is triggered by rainfall during grain maturation, causing substantial downgrading of end-use flour quality and over $1 billion in annual global losses.
* Seed dormancy is the primary physiological mechanism protecting wheat against PHS, but dormancy was intentionally reduced during domestication to achieve fast, uniform stand establishment.
* The major 3AS dormancy QTL *Qphs.pseru-3AS* was previously cloned as *TaPHS1* (a homolog of *MOTHER OF FT AND TFL1* / *TaMFT*), with three known functional mutations:
  * Splicing mutations at +646 (G to A) and +666 (A to C) causing mis-splicing, premature stop codons, and truncated non-functional proteins.
  * Promoter mutation at -222 (C to T) reducing *TaPHS1* transcription.
* However, common wheat line 'NW97S078' and certain tetraploid accessions exhibit complete PHS susceptibility despite possessing resistant alleles at all three previously known sites, pointing to an undiscovered causal mutation.
* This study aimed to isolate the causal mutation in NW97S078, trace its evolutionary origins across diploid, tetraploid, and hexaploid germplasm, evaluate haplotype combinations, and develop high-throughput KASP breeding markers.

## Key Concepts & Theory
- **[[TaPHS1]]**: A major cloned seed dormancy gene on chromosome 3AS encoding a phosphatidylethanolamine-binding protein that promotes embryo dormancy and ABA sensitivity.
- **[[3'-UTR Functional Mutation]]**: A single nucleotide polymorphism located in the 3'-untranslated region of an mRNA transcript that alters transcript stability or translational efficiency.
- **[[Artificial Selection Enrichment]]**: The rapid increase in frequency of a specific allele in modern crop populations driven by human breeding selection for rapid germination.
- **[[Haplotype Pyramiding]]**: Combining favorable wild-type alleles across multiple polymorphic nucleotide sites within a single gene locus to maximize phenotypic expression.
- **[[Kompetitive Allele-Specific PCR]]**: A fluorescence-based homogeneous genotyping assay using allele-specific primers for cost-effective, high-throughput SNP discrimination.

## Important Entities
* **Genes/Proteins**: [[TaPHS1]], [[TaMFT]], [[TaMKK3-A]], [[TaSdr4-A]], [[TaSdr4-B]], [[Vrn-A1]], [[Ppd-A1]], [[Lr34]], [[Yr36]], [[Actin]]
* **Organisms**: [[Triticum aestivum]] (wheat cv. 'Rio Blanco', 'Danby', 'Tiger', lines 'NW97S186', 'NW97S078', '08F485'), [[Triticum durum]], [[Triticum dicoccoides]], [[Triticum dicoccum]], [[Triticum urartu]], [[Triticum boeoticum]], [[Triticum monococcum]]
* **Tools/Techniques/Software**: [[Kompetitive Allele-Specific PCR]] (KASP Assay), [[Illumina 90K SNP Chip]], [[Genome Association and Prediction Integrated Tool]] (GAPIT), [[Haploview]], [[Semi-Quantitative RT-PCR]], [[Sanger Sequencing]]

## Methods & Experimental Design
* Plant materials: 343 wheat progenitor accessions (diploid *T. boeoticum*, *T. monococcum*, *T. urartu*; tetraploid *T. dicoccoides*, *T. dicoccum*, *T. durum*, *T. carthlicum*), 295 Iranian common wheat landraces, 205 U.S. elite winter wheat lines, and 617 worldwide cultivars/breeding lines.
* PHS phenotyping: Intact spikes harvested at physiological maturity, air-dried for 4 days, stored at -20 °C, and tested in a moist chamber at 23 °C / 100% humidity for 7 days.
* Sequencing and expression analysis: Full-length genomic DNA (5,172 bp) and cDNA (883 bp) of *TaPHS1* sequenced from resistant ('Rio Blanco', 'Danby', '08F485') and susceptible ('NW97S078', 'Tiger') genotypes; semi-quantitative RT-PCR at 20 DPA (grain filling stage) normalized to *Actin*.
* KASP assay design: Allele-specific primers developed for the 732 nt 3'-UTR SNP (*TaPHS1-732FAM* / *TaPHS1-732HEX* / *TaPHS1-732 common reverse*).
* GWAS and haplotype analysis: Association analysis via GAPIT using 21,600 SNPs from the 90K chip and candidate KASP markers. Linkage disequilibrium and haplotype blocks evaluated with Haploview.

## Key Results & Data
* **Discovery of the 4th functional mutation at 732 nt in 3'-UTR**:
  * Sequencing *TaPHS1* in NW97S078 identified a C-to-T transition at position 732 nt of the full-length cDNA in the 3'-UTR.
  * Coding sequence was identical to resistant 'Rio Blanco' (encoding a 175-aa functional protein), but *TaPHS1* transcript expression was severely downregulated in NW97S078 and susceptible *T. durum* accessions (PI145720, PI480148).
  * LD analysis confirmed that the 732 nt SNP is independent of -222, +646, and +666 SNPs (r² = 0.10 to 0.18).
* **GWAS validation in 205 U.S. elite lines**:
  * The 732 nt SNP was highly significant across 2012, 2013, and 2014 trials (P = 1.52E-04 to 1.42E-03, explaining 11.2% to 17.8% of phenotypic variance).
* **Evolutionary trajectory and human selection enrichment**:
  * T allele frequency in wild diploid *T. urartu* (7.14%) and wild tetraploid *T. dicoccoides* (1.75%) was very low.
  * T allele frequency was 4.34% in *T. durum*, 6.18% in *T. dicoccum*, and 11.18% in Iranian landraces.
  * In modern cultivars and elite breeding lines, T allele frequency surged to 53.32%, demonstrating massive enrichment by artificial selection during modern breeding.
* **Haplotype analysis across four causal SNPs (-222, +646, +666, 732 nt)**:
  * Four predominant haplotypes identified in 431 cultivars:
    1. **CGAC (All wild-type/resistant)**: Sprouting rate = 26.1% (Rio Blanco, Danby, 08F485).
    2. **TGAC (Single susceptible allele at -222)**: Sprouting rate = 42.9%.
    3. **TGAT (Two susceptible alleles at -222 and 732)**: Sprouting rate = 56.8%.
    4. **TATT (All four susceptible alleles)**: Sprouting rate = 67.4%.
  * Cultivars with the C allele at 732 nt had a significantly lower mean sprouting rate (39.1%) than those carrying the T allele (58.7%, P < 0.0001).

## Mechanistic Insights
* *TaPHS1* expression and seed dormancy are quantitatively co-regulated by four distinct nucleotide variations: promoter transcription efficiency (-222), pre-mRNA splicing fidelity (+646, +666), and 3'-UTR mRNA stability/post-transcriptional processing (732 nt).
* The 3'-UTR C-to-T mutation disrupts transcript stability, drastically reducing *TaPHS1* protein abundance in the developing embryo without altering the amino acid sequence.
* Artificial selection for rapid, synchronized field germination inadvertently selected for the 732 nt T allele, converting a rare ancestral wild variant into the dominant allele in modern hexaploid cultivars.

## Conclusions & Implications
* Discovered a novel 3'-UTR causal mutation in *TaPHS1* that explains previously unresolved PHS susceptibility in common and durum wheat germplasm.
* Established that pyramiding all four wild-type nucleotides into the [[CGAC]] haplotype delivers maximum seed dormancy and PHS resistance.
* The validated high-throughput KASP assay enables breeders to purge the susceptible T allele and fix the elite [[CGAC]] haplotype in commercial wheat breeding programs worldwide.

## Limitations & Caveats
* The precise RNA-binding proteins or microRNAs interacting with the 3'-UTR polymorphic site were not identified in this study.
* Although T allele frequency was high in *T. boeoticum* (81.8%), these wild accessions remained dormant, indicating epistatic suppression by other wild dormancy loci.

## Contradictory Findings
* Not reported in this paper.

## Outdated Models
* Overturns the three-mutation model of *TaPHS1*, demonstrating that *TaPHS1* possesses at least four functional causal variations that must be jointly genotyped to predict dormancy.

## Under-Researched Populations
* Tetraploid durum wheat breeding germplasm and South Asian / Middle Eastern landrace collections segregating for 3'-UTR variants.

## Future Directions
* Investigate the molecular mechanism by which the 3'-UTR C-to-T transition modulates *TaPHS1* mRNA stability or translation.
* Deploy the 4-SNP multiplex KASP diagnostic panel in commercial breeding programs to convert susceptible [[TATT]] and [[TGAT]] cultivars into resistant [[CGAC]] genotypes.

## Key References to Follow Up
* **Liu S, et al. (2013)** *A natural mutation in the promoter of TaPHS1 causes pre-harvest sprouting in wheat.* Nat. Commun. 4:2127.
* **Nakamura S, et al. (2011)** *A wheat homolog of MOTHER OF FT AND TFL1 acts in the regulation of seed dormancy.* Plant Cell 23:3215-3229.
* **Shao M, et al. (2018)** *A new functional SNP in TaPHS1 promoter region associated with pre-harvest sprouting resistance in wheat.* Mol. Breed. 38:53.

---
**Source PDF:** `data/liu_2020_artificial_selection_breeding.pdf`
"""

print(f"Total summaries prepared: {len(SUMMARIES)}")

def run_all():
    validator = SummaryValidator()
    wiki_sources_dir = root_dir / "wiki" / "sources" / "uncategorized"
    wiki_sources_dir.mkdir(parents=True, exist_ok=True)
    
    passed_count = 0
    for stem, content in SUMMARIES.items():
        # Validate source page linting
        lint_errs = validate_source_page(content)
        
        # Validate summary schema & scoring
        val_res = validator.validate(content)
        
        print(f"\n--- Checking {stem} ---")
        print(f"Validator score: {val_res.score:.2f}, valid: {val_res.valid}")
        if val_res.errors:
            print(f"Validator errors: {val_res.errors}")
        if val_res.warnings:
            print(f"Validator warnings: {val_res.warnings}")
        if lint_errs:
            print(f"Lint errors ({len(lint_errs)}): {lint_errs}")
            
        if val_res.valid and len(lint_errs) == 0:
            passed_count += 1
            # Write to file
            target_file = wiki_sources_dir / f"{stem}.md"
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Successfully wrote to {target_file}")
            
            # Mark done in queue
            mark_done(stem, "worker_phs", val_res.score)
            print(f"Marked done in queue with score {val_res.score}")
        else:
            print(f"FAILED validation for {stem}")
            
    print(f"\nSummary: {passed_count}/{len(SUMMARIES)} passed perfectly!")

if __name__ == "__main__":
    run_all()
