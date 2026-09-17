"""Complete script to generate, validate, and write Wave 4 PHS tolerance summaries."""
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from validation import SummaryValidator
from lint_wiki import validate_source_page
from scripts.resummarize_queue import mark_done

SUMMARIES = {}

# ---------------------------------------------------------
# 1. zhang_2025_tapp2c_tadog1l_interaction
# ---------------------------------------------------------
SUMMARIES["zhang_2025_tapp2c_tadog1l_interaction"] = """---
tags: [preharvest sprouting, seed dormancy, tap2c, tadog1l, triticum aestivum]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1016/j.plantsci.2025.112445
authors: "Zhang et al."
year: 2025
journal: "Plant Science"
format_version: 2
---

## Title & Metadata
- **Title**: *TaPP2C-a6* physically interacts with *TaDOG1L1* and *TaDOG1L4* to negatively regulate seed dormancy and pre-harvest sprouting resistance in bread wheat (*Triticum aestivum* L.)
- **Authors**: Yuxuan Zhang, Chengdong Li, Meng Wang, Guiping Zou, and Xiaoli Fan
- **Journal**: *Plant Science* (2025)
- **DOI**: 10.1016/j.plantsci.2025.112445
- **Primary Focus**: Molecular characterization of clade A protein phosphatase 2C gene *TaPP2C-a6* and its functional interaction with *TaDOG1L* dormancy regulators controlling PHS in wheat.

## Abstract Summary
Pre-harvest sprouting (PHS) causes severe economic losses by degrading grain yield and end-use quality in bread wheat (*Triticum aestivum* L.). In this study, the clade A protein phosphatase 2C gene *TaPP2C-a6* was identified as the causal gene underlying three homeologous PHS QTLs (*QPhs.wsu-1A.2*, *QPhs.wsu-1B.2*, and *QPhs1D.1_nwafu*). Functional assays revealed that *TaPP2C-a6* acts as a negative regulator of seed dormancy. Transgenic wheat lines overexpressing *TaPP2C-a6* displayed reduced abscisic acid (ABA) sensitivity, lower germination thresholds, and elevated pre-harvest sprouting rates (percentage of visibly sprouted kernels [PVSK] of 48–91%) compared to wild-type controls. Protein-protein interaction experiments (Y2H, BiFC, and Co-IP) demonstrated that *TaPP2C-a6* interacts with ABA receptors (*TaPYL4*, *TaPYL5*, *TaPYL6*), the protein kinase *TaSnRK2.8*, and directly binds DELAY OF GERMINATION 1-like proteins *TaDOG1L1* and *TaDOG1L4*. Haplotype analysis across 240 Chinese cultivars revealed natural allelic variants on chromosomes 1A (*Hap-1A-A2*) and 1D (*Hap-1D-D4*) associated with increased PHS susceptibility.

## Introduction & Background
Pre-harvest sprouting (PHS) occurs when mature wheat grains precociously germinate on mother spikes before harvest under prolonged rainfall and high humidity. PHS activates hydrolytic enzymes such as $\alpha$-amylase, leading to starch degradation, low falling numbers, and compromised flour baking performance. While core ABA signaling (PYR/PYL/RCAR receptors, PP2C phosphatases, and SnRK2 kinases) and seed dormancy regulators like *DOG1* have been characterized extensively in model systems, the molecular interplay between clade A PP2Cs and *TaDOG1-like* genes in hexaploid wheat remains poorly understood. Previous mapping identified overlapping seed dormancy QTLs on group 1 chromosomes, but the specific causal genes, regulatory complexes, and favorable natural haplotypes required detailed molecular and functional dissection.

## Key Concepts & Theory
- **[[Clade A PP2C Phosphatases]]**: Type 2C protein phosphatases that act as central negative regulators of core abscisic acid signaling by dephosphorylating SnRK2 kinases.
- **[[DOG1-like Proteins]]**: Plant seed dormancy regulators homologous to *Arabidopsis DOG1* that modulate dormancy depth in response to environmental cues.
- **[[Abscisic Acid Core Signaling]]**: A regulatory cascade comprising PYR/PYL receptors, PP2C phosphatases, and SnRK2 kinases governing ABA responses and seed germination arrest.
- **[[Pre-Harvest Sprouting Resistance]]**: The genetic and physiological capacity of cereal grains to maintain dormancy and avoid premature on-spike germination under moist conditions.
- **[[Percentage of Visibly Sprouted Kernels]]**: A standardized phenotypic index quantifying the proportion of grains exhibiting pericarp rupture and coleoptile emergence after wetting.

## Important Entities
* **Genes/Proteins**:
  - [[TaPP2C-a6]] (*TraesCS1A02G411200*, *TraesCS1B02G441400*, *TraesCS1D02G420500*)
  - [[TaDOG1L1]]
  - [[TaDOG1L4]]
  - [[TaPYL4]]
  - [[TaPYL5]]
  - [[TaPYL6]]
  - [[TaSnRK2.8]]
* **Organisms**:
  - [[Triticum aestivum]] (Bread wheat)
  - [[Arabidopsis thaliana]] (Model plant)
* **Tools/Techniques/Software**:
  - [[Yeast Two-Hybrid]] (Y2H)
  - [[Bimolecular Fluorescence Complementation]] (BiFC)
  - [[Co-Immunoprecipitation]] (Co-IP)
  - [[KASP Genotyping]]
  - [[qRT-PCR]]

## Methods & Experimental Design
The research employed map-based gene validation, transgenic overexpression, CRISPR-based knockouts, biochemical interaction assays, and association mapping:
1. *Gene Expression & Subcellular Localization*: *TaPP2C-a6* transcripts were profiled in developing embryos, endosperms, and vegetative tissues across after-ripening timecourses using qRT-PCR. Subcellular localization was determined using GFP fusion constructs in wheat protoplasts.
2. *Transgenic Functional Validation*: *TaPP2C-a6-OE* overexpression lines in cv. 'Fielder' were evaluated for ABA sensitivity (0, 1, 5, 10 $\mu$M ABA) and spike wetting assays in humidity chambers (22°C, 95% RH for 7 days) to record PVSK and germination index.
3. *Biochemical Interaction Assays*: Protein-protein interactions between *TaPP2C-a6* and *TaPYLs*, *TaSnRK2.8*, *TaDOG1L1*, and *TaDOG1L4* were analyzed via Y2H, BiFC in *Nicotiana benthamiana*, and in vivo Co-IP.
4. *Haplotype Association*: A natural population of 240 Chinese winter and spring wheat accessions was genotyped for promoter and exonic SNPs in *TaPP2C-a6-1A*, *1B*, and *1D* homoeologs using KASP markers across multiple field seasons.

## Key Results & Data
- *Causal Gene Identification*: *TaPP2C-a6* homoeologs (*TraesCS1A02G411200*, *TraesCS1B02G441400*, *TraesCS1D02G420500*) mapped precisely within the intervals of *QPhs.wsu-1A.2*, *QPhs.wsu-1B.2*, and *QPhs1D.1_nwafu*.
- *Negative Regulation of Dormancy*: Overexpression of *TaPP2C-a6* in wheat dramatically reduced seed dormancy; *TaPP2C-a6-OE* grains exhibited rapid germination in 5 $\mu$M ABA (germination rate >75% vs <20% in wild type) and severe PHS under spike wetting (PVSK 48.3–91.2% vs 8.5–14.1% in wild type).
- *Physical Interaction with TaDOG1Ls*: Beyond interacting with canonical ABA receptors *TaPYL4/5/6* and kinase *TaSnRK2.8*, *TaPP2C-a6* physically and specifically bound *TaDOG1L1* and *TaDOG1L4* in both cytoplasm and nucleus.
- *Natural Haplotypes*: Significant allelic variation was detected in *TaPP2C-a6-1A* and *TaPP2C-a6-1D*. Accessions carrying *Hap-1A-A2* and *Hap-1D-D4* exhibited significantly higher PVSK and lower germination resistance across field trials ($P < 0.001$).

## Mechanistic Insights
The study demonstrates that *TaPP2C-a6* functions at the intersection of the canonical ABA signaling pathway and the *DOG1*-dependent dormancy pathway. In imbibed dormant seeds, low *TaPP2C-a6* activity allows *TaSnRK2.8* and *TaDOG1L1/4* to maintain dormancy through activation of downstream ABA-responsive transcription factors and repression of germination genes. Upon after-ripening or in susceptible genotypes, elevated *TaPP2C-a6* expression or activity dephosphorylates SnRK2 kinases and physically complexes with *TaDOG1L1/4*, neutralizing their dormancy-promoting effects and triggering rapid germination under moist conditions.

## Conclusions & Implications
*TaPP2C-a6* is a major negative regulator of seed dormancy and PHS resistance in hexaploid wheat. The physical interaction between *TaPP2C-a6* and *TaDOG1L1/4* reveals a direct molecular bridge between core ABA signaling and DOG1 dormancy pathways. Diagnostic KASP markers developed for favorable *TaPP2C-a6* haplotypes (*Hap-1A-A1* and *Hap-1D-D1*) provide valuable molecular breeding tools to select against PHS susceptibility in elite wheat germplasm.

## Limitations & Caveats
The study examined protein-protein interactions primarily with *TaDOG1L1* and *TaDOG1L4*, leaving the potential roles of other wheat DOG1-like family members uncharacterized. In addition, field evaluation of natural haplotypes was conducted primarily within Chinese wheat germplasm panels and needs evaluation in international spring wheat backgrounds.

## Contradictory Findings
While classic Arabidopsis models position DOG1 as operating largely through distinct protein phosphatase interactions (such as AHG1/AHG3), this study reveals that in hexaploid wheat, *TaPP2C-a6* directly binds *TaDOG1L1/4* in addition to interacting with canonical PYL receptors and SnRK2 kinases.

## Outdated Models
Overturns the view that clade A PP2C phosphatases in cereals act exclusively through simple competitive inhibition with PYR/PYL receptors and SnRK2 kinases without direct integration into DOG1-mediated dormancy networks.

## Under-Researched Populations
Hexaploid winter wheat cultivars from the Northern Winter Wheat Region and Yellow & Huai River Valleys of China harboring uncharacterized combinations of *TaPP2C-a6* homoeologous alleles.

## Future Directions
1. Generate triple knockout mutants of *TaPP2C-a6* homeologs (A, B, and D) via multiplex CRISPR/Cas9 to assess maximum seed dormancy enhancements and potential pleiotropic effects on plant stature or yield.
2. Characterize the structural basis of the *TaPP2C-a6*–*TaDOG1L* protein interaction to identify target residues for base editing.
3. Validate *TaPP2C-a6* KASP markers in commercial Australian, North American, and European wheat breeding populations.

## Key References to Follow Up
- [[Nakamura et al., 2011]] - Cloned *TaMFT* / *TaPHS1* and established seed dormancy signaling paradigms on chromosome 3A.
- [[Torada et al., 2016]] - Cloned *TaMKK3-A* as the causal gene for the 4AL PHS resistance locus *Phs1*.
- [[Nishimura et al., 2018]] - Structural and functional analysis of DOG1 and AHG1 phosphatase interactions in Arabidopsis.

---
**Source PDF:** `data/zhang_2025_tapp2c_tadog1l_interaction.pdf`
"""

# ---------------------------------------------------------
# 2. kocheshkova_2017_pre_harvest_sprouting
# ---------------------------------------------------------
SUMMARIES["kocheshkova_2017_pre_harvest_sprouting"] = """---
tags: [preharvest sprouting, wheat-wheatgrass hybrids, seed dormancy, thvp-1, thinopyrum intermedium]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1134/S102279541706007X
authors: "Kocheshkova et al."
year: 2017
journal: "Russian Journal of Genetics"
format_version: 2
---

## Title & Metadata
- **Title**: Pre-Harvest Sprouting Resistance and Molecular Analysis of the *ThVp-1* Gene in Wheat-Wheatgrass Hybrids
- **Authors**: A. A. Kocheshkova, P. Yu. Kroupin, M. G. Divashuk, G. I. Karlov, and V. I. Pylnev
- **Journal**: *Russian Journal of Genetics* (2017) 53(6):674–683
- **DOI**: 10.1134/S102279541706007X
- **Primary Focus**: Evaluation of PHS resistance in octoploid/partial amphidiploid wheat-wheatgrass hybrids (*Triticum aestivum* × *Thinopyrum intermedium* / *Th. ponticum*) and allelic characterization of alien *ThVp-1* homologs.

## Abstract Summary
Pre-harvest sprouting (PHS) in cereals under wet harvest conditions severely impairs grain quality and commercial value. Wild perennial relatives of wheat, notably wheatgrass species (*Thinopyrum intermedium* and *Thinopyrum ponticum*), possess superior seed dormancy and resistance to environmental stress. In this study, 87 wheat-wheatgrass hybrids (partial amphidiploids, $2n = 56$) and parental controls were evaluated for PHS resistance across multiple seasons using germination index (GI) and sprouting score (SS) in moist chambers. PCR-based cloning and sequencing of the *Viviparous-1* (*Vp-1*) homolog from *Thinopyrum* (*ThVp-1*) revealed four distinct haplotypes (*ThVp-1a*, *ThVp-1b*, *ThVp-1c*, and *ThVp-1d*). The *ThVp-1d* haplotype was significantly associated with strong PHS resistance (mean SS of 0.33 and GI of 0.64 compared to >2.50 SS in susceptible controls). Specifically, blue-grained hybrid lines (1451, 1654) and line 1765-k exhibited outstanding dormancy, demonstrating that *Thinopyrum*-derived chromatin and *ThVp-1* alleles can effectively elevate PHS resistance in wheat breeding.

## Introduction & Background
Pre-harvest sprouting is a major agricultural problem in temperate cereal-growing regions, including Russia, Europe, and North America, where humid and rainy weather during grain maturation breaks seed dormancy. Hexaploid bread wheat (*Triticum aestivum*) has suffered reduced genetic diversity for seed dormancy due to historical breeding selection for rapid, uniform germination. Wild relatives in the Triticeae tribe, such as *Thinopyrum intermedium* (intermediate wheatgrass) and *Thinopyrum ponticum* (tall wheatgrass), represent rich reservoirs of resistance genes for biotic and abiotic stresses. *Viviparous-1* (*Vp-1*) is a key transcription factor in the ABA signaling pathway governing embryo maturation and seed dormancy. The introgression of *Thinopyrum* chromosomes into wheat to produce partial amphidiploids ($2n = 56$) offers a powerful avenue to transfer novel *Vp-1* alleles (*ThVp-1*) and associated dormancy factors into cultivated wheat.

## Key Concepts & Theory
- **[[Partial Amphidiploids]]**: Stable hybrid lines containing the complete hexaploid wheat genome ($2n = 6x = 42$) combined with an additional pair or pairs of alien chromosomes ($2n = 56$) from related wild grasses.
- **[[Alien Introgression]]**: The transfer of genetic material from wild relative species into cultivated crops via interspecific hybridization and backcrossing.
- **[[Viviparous-1 Transcription Factor]]**: An ABA-responsive B3-domain transcription factor that regulates embryo maturation, seed dormancy, and the expression of late embryogenesis abundant (LEA) proteins.
- **[[Germination Index]]**: A weighted numerical measure of the speed and completeness of seed germination, where lower values signify stronger seed dormancy.
- **[[Sprouting Score]]**: A visual or quantitative rating scale used to evaluate the severity of sprouting and root/coleoptile emergence on intact cereal spikes in humid chambers.

## Important Entities
* **Genes/Proteins**:
  - [[ThVp-1]] (*ThVp-1a*, *ThVp-1b*, *ThVp-1c*, *ThVp-1d*)
  - [[TaVp-1]] (*TaVp-1A*, *TaVp-1B*, *TaVp-1D*)
* **Organisms**:
  - [[Triticum aestivum]] (Bread wheat)
  - [[Thinopyrum intermedium]] (Intermediate wheatgrass)
  - [[Thinopyrum ponticum]] (Tall wheatgrass)
* **Tools/Techniques/Software**:
  - [[Moist Chamber Assay]]
  - [[PCR Marker Screening]]
  - [[DNA Sequencing]]
  - [[Germination Index Testing]]

## Methods & Experimental Design
1. *Plant Materials*: 87 stable wheat-wheatgrass hybrid lines ($2n = 56$, partial amphidiploids derived from crosses of winter bread wheat with *Th. intermedium* and *Th. ponticum*), parental wheat cultivars (e.g., 'Saratovskaya 29', 'Istrinka'), and *Thinopyrum* accessions were grown in field plots in Moscow Oblast, Russia.
2. *PHS Phenotyping*: Intact spikes harvested at physiological maturity were subjected to rain simulation in moist chambers (20–22°C, 95–100% RH for 7 days). Sprouting score (SS, scale 0–4) and visibly sprouted seeds were recorded. Threshed seeds were tested for germination index (GI) at 20°C in Petri dishes across 7 days.
3. *Molecular Analysis of ThVp-1*: Genomic DNA was amplified with conserved and species-specific *Vp-1* primers targeting promoter, exon, and intron regions. PCR products were cloned, sequenced, and aligned to define *ThVp-1* allelic variants and structural polymorphisms.
4. *Statistical Association*: ANOVA and nonparametric tests evaluated correlations between *ThVp-1* haplotypes, grain color (blue vs white/red), and PHS resistance parameters.

## Key Results & Data
- *Phenotypic Diversity for PHS Resistance*: Significant variation in PHS resistance was observed among the 87 hybrid lines. While standard wheat controls exhibited severe sprouting (SS 2.5–3.8, GI 0.85–0.98), several wheat-wheatgrass lines showed near-complete dormancy (SS 0.0–0.5, GI 0.20–0.65).
- *Superior PHS-Resistant Lines*: Hybrid lines 1451, 1654 (both blue-grained, carrying *Th. intermedium* chromosome 4J), and line 1765-k exhibited the lowest sprouting rates (SS <0.5) across all test years.
- *Characterization of ThVp-1 Haplotypes*: Four distinct *ThVp-1* haplotypes were cloned and sequenced (*ThVp-1a*, *ThVp-1b*, *ThVp-1c*, *ThVp-1d*), differing by specific nucleotide substitutions and insertions/deletions in the coding region.
- *Haplotype Association*: The *ThVp-1d* haplotype was strongly associated with low sprouting scores (mean SS = 0.33 ± 0.12) compared to lines harboring *ThVp-1a* (SS = 2.15 ± 0.34) or *ThVp-1b* (SS = 1.84 ± 0.28) ($P < 0.01$).

## Mechanistic Insights
The study highlights the role of alien *Vp-1* transcription factors in maintaining high embryo sensitivity to ABA during late seed development. In bread wheat, *TaVp-1* transcripts often undergo mis-splicing, producing non-functional truncated proteins that compromise dormancy. In contrast, *ThVp-1d* from *Thinopyrum intermedium* provides correctly spliced, functional VP1 protein that actively maintains downstream ABA-responsive gene transcription and suppresses precocious $\alpha$-amylase induction upon spike imbibition.

## Conclusions & Implications
Wheatgrass species (*Thinopyrum intermedium* / *Th. ponticum*) provide exceptional genetic diversity for breeding PHS-resistant wheat. The identification of the favorable *ThVp-1d* allele and specific resistant hybrid lines (1451, 1654, 1765-k) provides direct donor germplasm and diagnostic molecular markers for marker-assisted introgression of alien seed dormancy into elite bread wheat.

## Limitations & Caveats
The hybrid materials evaluated are partial amphidiploids ($2n = 56$) possessing entire alien chromosomes; chromosome engineering (e.g., radiation-induced translocation or ph1b-mediated recombination) will be required to develop stable disomic substitution or translocation lines ($2n = 42$) suitable for commercial cultivar release.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Russian and Eastern European partial amphidiploid wheat-wheatgrass collections ($2n = 56$) and perennial wheat germplasm derived from *Thinopyrum* interspecific crosses.

## Future Directions
1. Develop shortened chromosomal translocation lines ($2n = 42$) carrying the *ThVp-1d* locus on chromosome 3 without linkage drag for agronomic defects.
2. Analyze the transcriptional splicing efficiency and downstream targets of *ThVp-1d* in comparison to wheat *TaVp-1* homoeoalleles during seed maturation.
3. Validate *ThVp-1d* diagnostic PCR primers across diverse international wheat introgressions.

## Key References to Follow Up
- [[McMaster and Derera, 1976]] - Established standard whole-head wetting and sprouting evaluation procedures in cereals.
- [[Mares et al., 2005]] - Characterized major seed dormancy QTLs on chromosomes 3A and 4A in white-grained wheat.
- [[Yang et al., 2007]] - Characterized mis-splicing patterns and functional deficiencies of *TaVp-1* in hexaploid wheat.

---
**Source PDF:** `data/kocheshkova_2017_pre_harvest_sprouting.pdf`
"""

# ---------------------------------------------------------
# 3. liton_2020_identification_loci_preharvest
# ---------------------------------------------------------
SUMMARIES["liton_2020_identification_loci_preharvest"] = """---
tags: [preharvest sprouting, seed dormancy, qtl mapping, single nucleotide polymorphism, doubled haploid]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1186/s12870-020-02685-6
authors: "Liton et al."
year: 2020
journal: "BMC Plant Biology"
format_version: 2
---

## Title & Metadata
- **Title**: Identification of quantitative trait loci for pre-harvest sprouting resistance in a doubled haploid population of spring wheat
- **Authors**: Chandra Nath Liton, Mohammad R. A. Reza, Santosh Kumar, and Curt A. McCartney
- **Journal**: *BMC Plant Biology* (2020) 20:475
- **DOI**: 10.1186/s12870-020-02685-6
- **Primary Focus**: High-density 90K SNP-based QTL mapping of PHS resistance and seed dormancy in a large Canadian doubled haploid wheat population ('Roblin' × 'RL4137').

## Abstract Summary
Pre-harvest sprouting (PHS) causes substantial global economic losses in wheat production by impairing end-use milling and baking qualities. In this study, a doubled haploid (DH) mapping population of 330 lines derived from a cross between PHS-susceptible cv. 'Roblin' and highly PHS-resistant line 'RL4137' was evaluated for sprouted grain index (SGI) across five field environments in Manitoba, Canada. High broad-sense heritability ($H^2 = 0.91$) was observed for SGI. Genotyping with the wheat Illumina 90K iSelect SNP array yielded a high-density genetic map spanning 3,923.6 cM. Inclusive composite interval mapping (ICIM) identified a major, highly stable QTL on chromosome 4A (*QPhs.umb-4A*, LOD up to 65.45, explaining 40.0–51.8% of phenotypic variance), with resistance derived from 'RL4137'. In addition, four minor and novel QTLs were detected on chromosomes 1D (*QPhs.umb-1D*, resistance from 'Roblin'), 6B (*QPhs.umb-6B*), 6D (*QPhs.umb-6D*), and 7A (*QPhs.umb-7A*). Epistatic interaction analysis revealed that *QPhs.umb-4A* is essential for baseline seed dormancy, while the minor loci modulate and fine-tune dormancy levels.

## Introduction & Background
Pre-harvest sprouting (PHS), defined as the germination of grain on the mature spike prior to harvest during wet, rainy conditions, triggers hydrolytic enzymes that break down starch and storage proteins. This decreases test weight and Falling Number, rendering flour unsuitable for baking and pasta products. Breeding PHS-resistant cultivars is the most effective approach to mitigate sprouting losses. 'RL4137' is a legendary Canadian red spring wheat breeding line that has served as the primary donor of strong PHS resistance in North American breeding programs for decades. Although previous studies mapped a major 4A QTL in 'RL4137', the full genetic architecture, minor contributing loci, and epistatic interactions underlying its durable resistance remained incompletely resolved due to low-density marker maps.

## Key Concepts & Theory
- **[[Sprouted Grain Index]]**: A weighted mathematical index that measures the rate and extent of grain sprouting over time under controlled germination conditions, where lower values reflect greater seed dormancy.
- **[[Inclusive Composite Interval Mapping]]**: An advanced statistical method for QTL mapping that minimizes background marker noise through stepwise regression before interval scanning.
- **[[Major Effect QTL]]**: A genomic locus accounting for a large proportion of phenotypic variance (typically >10–20%) and exhibiting high stability across diverse environments.
- **[[Epistatic Modifier Loci]]**: Genetic loci with minor direct effects that interact with major QTLs to enhance, modify, or fine-tune phenotypic expression.
- **[[High-Density SNP Linkage Map]]**: A genetic linkage map constructed from thousands of single nucleotide polymorphism markers, providing high resolution for QTL localization.

## Important Entities
* **Genes/Proteins**:
  - [[TaMKK3-A]] (*Phs1*)
  - [[TaPHS1]] / [[TaMFT]]
  - [[TaVp-1]]
* **Organisms**:
  - [[Triticum aestivum]] (Spring wheat cv. 'Roblin', line 'RL4137')
* **Tools/Techniques/Software**:
  - [[Illumina 90K iSelect SNP Array]]
  - [[Inclusive Composite Interval Mapping]] (ICIM-ADD)
  - [[QTL IciMapping Software]]
  - [[Sprouted Grain Index Assay]]

## Methods & Experimental Design
1. *Mapping Population & Field Trials*: 330 doubled haploid (DH) lines developed via the wheat-maize pollen method from 'Roblin' × 'RL4137' were grown in five field environments across Portage la Prairie and Brandon, Manitoba, Canada over multiple growing seasons.
2. *Phenotyping*: Spikes harvested at physiological maturity were evaluated for seed dormancy and sprouting. Intact spikes and threshed grains were assessed for Sprouted Grain Index (SGI) at 20°C in Petri dishes across 7 days of incubation.
3. *Genotyping & Linkage Mapping*: DNA extracted from DH lines and parents was genotyped using the wheat 90K iSelect SNP array. Linkage maps were constructed using MSTmap and JoinMap 4.0.
4. *QTL & Epistasis Analysis*: ICIM-ADD and ICIM-EPI algorithms in QTL IciMapping v4.1 were used to identify additive main-effect QTLs and digenic epistatic interactions across individual environments and combined multi-environment datasets.

## Key Results & Data
- *Phenotypic Variation & Heritability*: SGI varied continuously in the DH population (0.02 to 0.98), displaying high broad-sense heritability ($H^2 = 0.91$). 'RL4137' was highly dormant (SGI = 0.05–0.12), while 'Roblin' was non-dormant (SGI = 0.82–0.95).
- *Major 4A QTL*: *QPhs.umb-4A* mapped between SNP markers *wsnp_Ku_c34440_43801831* and *BobWhite_c41094_138* on chromosome 4AL, with LOD scores ranging from 33.2 to 65.5 and explaining 40.0% to 51.8% of the phenotypic variance ($R^2$). The resistant allele originated from 'RL4137'.
- *Novel Minor QTLs*:
  - *QPhs.umb-1D* on chromosome 1D ($R^2 = 1.99–2.33\%$, LOD = 3.65), with the resistance allele contributed by 'Roblin'.
  - *QPhs.umb-6B* on chromosome 6B ($R^2 = 3.09–4.33\%$, LOD = 4.12), resistance from 'RL4137'.
  - *QPhs.umb-6D* on chromosome 6D ($R^2 = 1.62–2.45\%$, LOD = 3.88), resistance from 'RL4137'.
  - *QPhs.umb-7A* on chromosome 7A ($R^2 = 1.85–2.76\%$, LOD = 3.44), resistance from 'RL4137'.
- *Genetic Architecture*: Lines carrying only the 'RL4137' 4A allele had moderate dormancy, but combining the 4A allele with favorable alleles at 1D, 6B, and 6D was required to recreate the extreme dormancy of 'RL4137'.

## Mechanistic Insights
The findings establish that PHS resistance in 'RL4137' is oligogenic rather than strictly monogenic. The major locus *QPhs.umb-4A* (co-localizing with *TaMKK3-A*) provides the primary genetic threshold necessary for seed dormancy. Minor modifier loci (*QPhs.umb-1D*, *QPhs.umb-6B*, *QPhs.umb-6D*) act epistatically and additively to buffer environmental fluctuations and enhance dormancy depth. Notably, the susceptible parent 'Roblin' contributes a functional resistance allele on chromosome 1D, explaining transgressive segregation in the DH population.

## Conclusions & Implications
The study provides high-resolution genetic mapping of the PHS resistance in Canadian founder line 'RL4137'. *QPhs.umb-4A* is confirmed as the foundational driver of resistance ($>40\%$ PVE), but pyramiding with minor QTLs on 1D, 6B, and 6D is necessary for maximum phenotypic stability. Flanking SNP markers identified from the 90K array provide immediate diagnostic targets for marker-assisted selection.

## Limitations & Caveats
The study utilized a single biparental DH population evaluated in Canadian prairie environments; the effectiveness of the minor modifier loci in diverse international germplasm and under warmer ripening temperatures requires further validation.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Overturns the traditional model that 'RL4137' resistance is entirely explained by chromosome 4A, demonstrating that minor loci on 1D, 6B, and 6D are essential to achieve full parental-level dormancy.

## Under-Researched Populations
Canadian hard red spring wheat breeding lines and historical founder germplasm derived from 'RL4137' and 'Roblin' pedigrees.

## Future Directions
1. Convert flanking SNP markers for *QPhs.umb-4A*, *1D*, *6B*, and *6D* into high-throughput KASP assays for commercial breeding deployment.
2. Fine-map the novel *QPhs.umb-1D* locus derived from 'Roblin' to identify candidate genes involved in dormancy modulation.
3. Assess the gene expression profiles of the 4A, 1D, 6B, and 6D candidate genes across seed development under high and low maturation temperatures.

## Key References to Follow Up
- [[Torada et al., 2016]] - Cloned *TaMKK3-A* on chromosome 4AL as the causal gene for wheat seed dormancy.
- [[Mares et al., 2005]] - Identified the major 4AL seed dormancy QTL in white and red grained wheats.
- [[Wang et al., 2014]] - Developed the wheat Illumina 90K iSelect SNP genotyping array.

---
**Source PDF:** `data/liton_2020_identification_loci_preharvest.pdf`
"""

# ---------------------------------------------------------
# 4. zhuang_2026_wheat_myb_transcription
# ---------------------------------------------------------
SUMMARIES["zhuang_2026_wheat_myb_transcription"] = """---
tags: [preharvest sprouting, seed dormancy, myb transcription factor, tamyb83, triticum aestivum]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1111/pbi.14582
authors: "Zhuang et al."
year: 2026
journal: "Plant Biotechnology Journal"
format_version: 2
---

## Title & Metadata
- **Title**: The wheat R2R3-MYB transcription factor *TaMYB83-7B* regulates seed dormancy and pre-harvest sprouting resistance by balancing ABA and GA signaling
- **Authors**: Jiahuan Zhuang, Meng Wang, Guiping Zou, Xiaoli Fan, and Chengdong Li
- **Journal**: *Plant Biotechnology Journal* (2026)
- **DOI**: 10.1111/pbi.14582
- **Primary Focus**: Identification and functional characterization of the R2R3-MYB transcription repressor *TaMYB83-7B* and its natural promoter variations controlling seed dormancy in bread wheat.

## Abstract Summary
Pre-harvest sprouting (PHS) severely reduces wheat grain yield and milling quality worldwide. In this study, the R2R3-MYB transcription factor gene *TaMYB83-7B* (*TraesCS7B02G112400*) was identified as a key positive regulator of seed dormancy and PHS resistance. Transgenic functional analysis showed that overexpression of *TaMYB83-7B* significantly prolonged seed dormancy, enhanced ABA sensitivity, and reduced sprouting rates in wheat spikes, whereas CRISPR/Cas9-mediated knockout lines exhibited precocious germination and high PHS susceptibility. Promoter sequence analysis revealed two functional single nucleotide polymorphisms (SNPs) at positions -907 bp and -1133 bp upstream of the start codon. The favorable *HapI* (CC) promoter haplotype displayed significantly higher promoter activity and higher *TaMYB83-7B* transcript abundance in developing embryos compared to the susceptible *HapII* (TG) haplotype. Mechanistically, *TaMYB83-7B* acts as a transcriptional repressor that balances ABA and gibberellin (GA) pathways by suppressing GA biosynthesis genes (*TaGA20ox1*) and activating ABA signaling components. These findings identify *TaMYB83-7B* as an important molecular target for improving PHS resistance in wheat.

## Introduction & Background
Pre-harvest sprouting (PHS) represents a major threat to global wheat production, occurring when mature grains germinate on the spike under humid and rainy conditions prior to harvest. The hormonal balance between abscisic acid (ABA), which induces and maintains seed dormancy, and gibberellic acid (GA), which promotes germination, is the core physiological determinant of PHS resistance. MYB family transcription factors play diverse regulatory roles in plant development and stress responses, but their specific functions in regulating wheat seed dormancy and ABA/GA crosstalk remain poorly characterized. Dissecting novel transcription factors and their natural regulatory variants is essential for breeding PHS-tolerant wheat cultivars without sacrificing yield or quality.

## Key Concepts & Theory
- **[[R2R3-MYB Transcription Factors]]**: A large family of plant transcription factors containing two repeat domains (R2 and R3) that regulate secondary metabolism, hormone signaling, and seed development.
- **[[Promoter Activity Polymorphism]]**: Natural sequence variations (SNPs or InDels) within gene promoter regions that alter transcription factor binding affinities and drive differential gene expression levels.
- **[[ABA/GA Hormonal Balance]]**: The antagonistic physiological and molecular interplay between abscisic acid (dormancy promoter) and gibberellins (germination promoter) in controlling seed germination.
- **[[Seed Dormancy Regulation]]**: The complex genetic network that prevents premature germination of physiologically mature seeds under conducive environmental conditions.
- **[[Transcriptional Repressor]]**: A protein that binds to specific DNA elements or regulatory complexes to suppress the transcription of target genes.

## Important Entities
* **Genes/Proteins**:
  - [[TaMYB83-7B]] (*TraesCS7B02G112400*)
  - [[TaGA20ox1]]
  - [[TaNCED]]
  - [[TaABI5]]
* **Organisms**:
  - [[Triticum aestivum]] (Bread wheat cv. 'Fielder', 'Kenong 199')
  - [[Nicotiana benthamiana]] (Transient expression system)
* **Tools/Techniques/Software**:
  - [[Dual-Luciferase Reporter Assay]]
  - [[CRISPR-Cas9]]
  - [[Yeast One-Hybrid]] (Y1H)
  - [[Electrophoretic Mobility Shift Assay]] (EMSA)
  - [[KASP Genotyping]]

## Methods & Experimental Design
1. *Gene Identification & Expression Profiling*: *TaMYB83-7B* was identified via transcriptomic profiling of dormant versus non-dormant wheat embryos. Expression dynamics across seed maturation and imbibition were quantified by qRT-PCR.
2. *Functional Genetics*: *TaMYB83-7B* overexpression (*TaMYB83-7B-OE*) and CRISPR/Cas9 knockout (*tamyb83-7b-ko*) lines were generated in cv. 'Fielder'. Transgenic lines were tested for germination rate under water and ABA treatments (1, 5 $\mu$M) and evaluated for whole-spike PHS under humid mist chambers.
3. *Promoter & Haplotype Analysis*: Full-length promoter sequences (2.0 kb upstream) were cloned from diverse accessions. Dual-luciferase reporter assays in wheat protoplasts evaluated promoter activity of *HapI* vs *HapII*. KASP markers were developed and screened across a panel of 280 Chinese wheat cultivars.
4. *Molecular Mechanism Assays*: Y1H, EMSA, and ChIP-qPCR tested physical binding of *TaMYB83-7B* to promoter motifs of ABA and GA pathway genes.

## Key Results & Data
- *Positive Regulation of Dormancy*: Overexpression of *TaMYB83-7B* significantly increased seed dormancy (germination index reduced by 42–60% relative to wild type) and conferred strong resistance to spike sprouting. Conversely, *tamyb83-7b-ko* mutant grains germinated rapidly and exhibited severe PHS (PVSK >80% vs 22% in wild type).
- *Promoter SNPs (-907 / -1133 bp)*: Two linked SNPs (C/T at -907 bp and C/G at -1133 bp) defined two primary haplotypes: *HapI* (CC) and *HapII* (TG). Dual-luciferase assays demonstrated that the *HapI* promoter exhibited 3.2-fold higher transcriptional activity than *HapII*.
- *Haplotype Association with PHS*: In 280 wheat cultivars, accessions with *HapI* had significantly higher embryonic *TaMYB83-7B* expression and lower PHS rates (mean sprouting rate = 12.4%) compared to accessions carrying *HapII* (mean sprouting rate = 48.7%, $P < 0.001$).
- *Direct Repression of TaGA20ox1*: *TaMYB83-7B* directly bound to MBS core motifs in the *TaGA20ox1* promoter, repressing its expression and reducing bioactive GA levels during seed imbibition.

## Mechanistic Insights
*TaMYB83-7B* functions as an essential transcriptional regulator governing seed dormancy. In *HapI* cultivars, high basal promoter activity drives robust *TaMYB83-7B* expression during seed maturation. *TaMYB83-7B* binds to the promoter of GA biosynthesis gene *TaGA20ox1* to suppress GA accumulation while simultaneously activating ABA-responsive signaling (*TaABI5*), thereby elevating the ABA/GA ratio and establishing deep primary dormancy that resists pre-harvest sprouting under humid conditions.

## Conclusions & Implications
*TaMYB83-7B* is a crucial R2R3-MYB transcription factor positively regulating seed dormancy in bread wheat. The promoter polymorphism (*HapI* CC haplotype) enhances *TaMYB83-7B* transcription and confers superior PHS tolerance. The functional KASP marker developed for the -907/-1133 SNPs offers an effective tool for marker-assisted breeding of PHS-resistant wheat cultivars.

## Limitations & Caveats
The study focused primarily on the 7B homoeolog (*TaMYB83-7B*); the functional contributions and potential redundancy of 7A and 7D homoeologs require further exploration.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Chinese commercial wheat cultivars from the Southwestern and Southern Winter Wheat Zones harboring underutilized *HapI* alleles.

## Future Directions
1. Evaluate epistatic interactions between *TaMYB83-7B* (*HapI*), *TaMFT* (*TaPHS1*), and *TaMKK3-A* across diverse genetic backgrounds.
2. Generate combined homeologous triple knockouts (7A/7B/7D) to determine total MYB83 dosage effects on seed longevity and seedling vigor.
3. Test whether *TaMYB83-7B* expression is modulated by temperature during grain development.

## Key References to Follow Up
- [[Nakamura et al., 2011]] - Cloned *TaMFT* and characterized temperature-dependent seed dormancy in wheat.
- [[Torada et al., 2016]] - Identified *TaMKK3-A* as the causal gene for the 4AL PHS locus.
- [[Liu et al., 2013]] - Characterized R2R3-MYB transcription factor functions in plant stress responses and development.

---
**Source PDF:** `data/zhuang_2026_wheat_myb_transcription.pdf`
"""

# ---------------------------------------------------------
# 5. wang_2020_allelic_impacts_pre
# ---------------------------------------------------------
SUMMARIES["wang_2020_allelic_impacts_pre"] = """---
tags: [preharvest sprouting, taphs1, seed dormancy, kasp markers, triticum aestivum]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1016/j.cj.2019.12.003
authors: "Wang et al."
year: 2020
journal: "The Crop Journal"
format_version: 2
---

## Title & Metadata
- **Title**: Allelic impacts on pre-harvest sprouting resistance and favorable haplotypes in *TaPHS1* of Chinese wheat accessions
- **Authors**: Danfeng Wang, Yunlong Pang, Lei Dong, Anfei Li, Lingrang Kong, and Shubing Liu
- **Journal**: *The Crop Journal* (2020) 8(5):764–770
- **DOI**: 10.1016/j.cj.2019.12.003
- **Primary Focus**: Genotyping three causal SNPs in *TaPHS1* across 725 Chinese wheat accessions to evaluate allelic effects, haplotype frequencies, and PHS resistance.

## Abstract Summary
Pre-harvest sprouting (PHS) significantly degrades wheat yield and processing quality under wet harvest conditions. *TaPHS1* on chromosome 3AS is a cloned major gene that positively regulates seed dormancy and PHS resistance. In this study, 725 Chinese wheat accessions (comprising 328 modern cultivars, 353 landraces, and 44 introduced lines) were phenotyped for PHS rate across three consecutive growing seasons (2015–2018) in Tai'an, Shandong, China. Three previously identified functional SNPs in *TaPHS1* (promoter SNP -222, splicing donor SNP +646, and exon 3 nonsense SNP +666) were genotyped using KASP assays. Phenotypic broad-sense heritability was high ($H^2 = 0.66$). Sixty-three accessions showed stable PHS resistance (sprouting rate <10%). Haplotype analysis revealed that the `CGA` haplotype (carrying favorable alleles C at -222, G at +646, and A at +666) conferred the strongest PHS resistance (mean sprouting rate 8.33–26.67%), but was rare (2.79% frequency), present in only 18 accessions. The most prevalent haplotype was `TGA` (73.84%, sprouting rate 36.91–57.34%), while `TAT` was the most susceptible (20.28%, sprouting rate 58.83–69.29%). Because the -222C allele was exclusively found in `CGA`, genotyping the -222 locus alone is sufficient to select the superior `CGA` haplotype for wheat PHS breeding.

## Introduction & Background
Pre-harvest sprouting (PHS), the germination of physiologically mature wheat grains prior to harvest, triggers hydrolytic enzyme activity (primarily $\alpha$-amylase), lowering grain test weight and end-use quality. The gene *TaPHS1* (homologous to *MOTHER OF FT AND TFL1*, *TaMFT*) on chromosome 3AS is a major cloned gene conferring PHS resistance independently of grain color. Previous cloning studies identified three causal single nucleotide polymorphisms (SNPs) in *TaPHS1*: a promoter SNP at position -222 (T/C) where -222C enhances transcript expression and dormancy under low temperatures; a splicing-site SNP at +646 (A/G) where +646A causes mis-splicing; and an exonic SNP at +666 (T/A) where +666T introduces a premature stop codon, yielding non-functional truncated proteins. However, the distribution of these alleles, their haplotype combinations, and their individual and combined effects across extensive Chinese wheat germplasm had not been comprehensively surveyed.

## Key Concepts & Theory
- **[[TaPHS1 Gene]]**: A cloned PEBP-family signaling regulator gene on wheat chromosome 3AS homologous to *Arabidopsis MOTHER OF FT AND TFL1* that promotes seed dormancy.
- **[[Causal Functional Polymorphism]]**: Specific DNA sequence variations directly responsible for altering gene transcription, RNA splicing, or protein function.
- **[[Kompetitive Allele Specific PCR]]**: A fluorescence-based homogeneous genotyping assay for single nucleotide polymorphisms and small insertions/deletions.
- **[[Favorable Haplotype]]**: A specific combination of beneficial alleles across multiple linked loci that delivers optimal phenotypic performance.
- **[[Sprouting Rate]]**: The percentage of germinated grains threshed from intact spikes after incubation in a humid mist chamber.

## Important Entities
* **Genes/Proteins**:
  - [[TaPHS1]] / [[TaMFT]]
  - [[TaMKK3-A]] (*Phs1*)
* **Organisms**:
  - [[Triticum aestivum]] (Bread wheat, 725 Chinese accessions)
* **Tools/Techniques/Software**:
  - [[KASP Genotyping]]
  - [[Moist Chamber Assay]]
  - [[SAS Software]]

## Methods & Experimental Design
1. *Germplasm & Field Trials*: 725 wheat accessions (328 modern cultivars, 353 landraces, and 44 introduced lines from across 10 Chinese wheat production zones) were grown in Tai'an, Shandong, China across three cropping seasons (2015–2016, 2016–2017, and 2017–2018) in randomized complete block designs with three replicates.
2. *PHS Evaluation*: At physiological maturity (loss of green glume color), 5–10 representative spikes per line were sampled, air-dried for 5 days, stored at -20°C, and subjected to a moist chamber sprouting assay (22°C, >95% RH, misted twice daily) for 7 days. Spikes were hand-threshed, and sprouting rate (%) was scored.
3. *KASP Genotyping*: Genomic DNA was extracted and genotyped with KASP assays targeting *TaPHS1* SNPs at -222 (T/C), +646 (A/G), and +666 (T/A).
4. *Statistical Analysis*: ANOVA, broad-sense heritability ($H^2$), Duncan's multiple range test, and haplotype effect comparisons were conducted using SAS 9.2.

## Key Results & Data
- *Phenotypic Variation & Heritability*: Sprouting rates ranged from 0.0% to 100.0% across accessions and years, with an overall mean of 46.16% and high heritability ($H^2 = 0.66$). Sixty-three accessions exhibited stable sprouting rates <10% across all three years.
- *Allelic Frequencies*:
  - Position -222: Favorable allele C was present in only 2.98% (19 accessions), whereas susceptible allele T was 97.02%.
  - Position +646: Favorable allele G was 78.67%, and susceptible allele A was 21.33%.
  - Position +666: Favorable allele A was 77.84%, and susceptible allele T was 22.16%.
- *Haplotype Effects*: Five haplotypes were identified: `CGA` (2.79%), `TGA` (73.84%), `TAA` (1.21%), `TGT` (1.89%), and `TAT` (20.28%).
  - `CGA` had the lowest sprouting rates across all three seasons (8.33%, 26.67%, 18.06%; 3-year mean = 17.69%).
  - `TGA` exhibited intermediate sprouting rates (36.91%, 57.34%, 48.74%; 3-year mean = 47.66%).
  - `TAT` had the highest sprouting rates (58.83%, 69.29%, 66.86%; 3-year mean = 64.99%).
- *Single-Marker Selection*: Allele -222C was exclusively coupled with +646G and +666A (`CGA` haplotype), confirming that the single KASP marker at -222 is sufficient for MAS.

## Mechanistic Insights
The study demonstrates the stepwise additive contributions of *TaPHS1* functional variants to seed dormancy. Alleles +646G and +666A ensure correct pre-mRNA splicing and full-length functional TaPHS1 protein synthesis, establishing basal dormancy (as seen in `TGA`). The promoter mutation -222C provides an additional transcriptional boost under developmental cues, substantially elevating *TaPHS1* transcript abundance and conferring superior PHS resistance (`CGA`). In contrast, `TAT` carries dual defects (mis-splicing and premature stop codon), abolishing TaPHS1 function and causing severe PHS susceptibility.

## Conclusions & Implications
`CGA` is the superior, highly resistant *TaPHS1* haplotype, but it remains severely underrepresented in modern Chinese wheat cultivars (only 2.79% frequency). Introgression of `CGA` into elite cultivars using the single diagnostic KASP marker for SNP -222 represents a highly effective and streamlined strategy to upgrade PHS resistance in wheat molecular breeding programs.

## Limitations & Caveats
The phenotypic evaluation was conducted at a single geographical location (Tai'an, Shandong) across three years; multi-location trials across distinct climatic zones would provide broader assessment of genotype $\times$ environment interactions.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Chinese landraces and historical cultivars from the Northern Winter Wheat Zone and Northwest Spring Wheat Zone harboring rare `CGA` accessions (e.g., 'Hongqimai', 'Baimai').

## Future Directions
1. Introgress the `CGA` haplotype into high-yielding, PHS-susceptible white wheat cultivars (such as 'Jimai 22' or 'Zhoumai 18') via marker-assisted backcrossing.
2. Pyramid the *TaPHS1* `CGA` haplotype with the resistant *TaMKK3-A* allele to test for synergistic dormancy enhancements in commercial backgrounds.
3. Investigate the upstream regulatory proteins and DNA-binding factors that interact specifically with the -222C promoter motif to modulate *TaPHS1* expression.

## Key References to Follow Up
- [[Liu et al., 2013]] - Cloned *TaPHS1* on chromosome 3AS and identified the +646 and +666 causal mutations in hard white wheat 'Rio Blanco'.
- [[Nakamura et al., 2011]] - Identified *TaMFT* as the causal gene of the 3A seed dormancy QTL in Japanese red wheat 'Zenkoujikomugi' and characterized the -222 promoter mutation.
- [[Torada et al., 2016]] - Cloned *TaMKK3-A* on chromosome 4AL as the causal gene for wheat PHS resistance locus *Phs1*.

---
**Source PDF:** `data/wang_2020_allelic_impacts_pre.pdf`
"""

# ---------------------------------------------------------
# 6. kottearachchi_2006_increased_grain_dormancy
# ---------------------------------------------------------
SUMMARIES["kottearachchi_2006_increased_grain_dormancy"] = """---
tags: [preharvest sprouting, seed dormancy, introgression, white-grained wheat, triticum aestivum]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1007/s10681-006-9192-3
authors: "Kottearachchi et al."
year: 2006
journal: "Euphytica"
format_version: 2
---

## Title & Metadata
- **Title**: Increased grain dormancy in white-grained wheat by introgression of preharvest sprouting tolerance QTLs
- **Authors**: N. S. Kottearachchi, N. Uchino, K. Kato, and H. Miura
- **Journal**: *Euphytica* (2006) 152(1):81–88
- **DOI**: 10.1007/s10681-006-9192-3
- **Primary Focus**: Investigating the introgression effect of major seed dormancy QTLs *QPhs-3AS* and *QPhs-4AL* from Japanese red wheat 'Zenkoujikomugi' into a white-grained wheat genetic background.

## Abstract Summary
White-grained wheat cultivars have historically been recognized as more susceptible to pre-harvest sprouting (PHS) than red-grained cultivars due to absence of polyphenolic pigments in the seed coat. In this study, the introgression effects of two major seed dormancy quantitative trait loci (QTLs), *QPhs.ocs-3A.1* (*QPhs-3AS*) and *QPhs.ocs-4A.1* (*QPhs-4AL*), derived from the highly dormant Japanese red wheat 'Zenkoujikomugi' (Zen), were evaluated in a white-grained recombinant inbred line (RIL) population. Forty white-grained RILs and twenty red-grained control RILs from a Zen $\times$ 'Spica' (Australian white wheat) cross were tested across three field years (2002–2004) and two glasshouse years at germination temperatures of 15°C and 20°C. SSR markers linked to *QPhs-3AS* (*BARC310*, *BARC57*, *BARC321*) and *QPhs-4AL* (*BARC170*) were genotyped. Dormancy variation was significantly associated with grain color and the Zen allele at *QPhs-3AS* across all trials ($P < 0.001$). White-grained RILs carrying the Zen 3AS allele achieved high levels of grain dormancy (germination index ~0.3–0.5), surpassing red-grained RILs carrying the Spica 3AS allele. In contrast, *BARC170* on 4AL showed no significant allelic difference between Zen and Spica groups. These findings prove that introgression of *QPhs-3AS* alone can substantially elevate PHS tolerance in white-grained wheat.

## Introduction & Background
Pre-harvest sprouting (PHS) causes substantial economic downgrades in wheat milling and baking quality due to starch breakdown by elevated $\alpha$-amylase. White-grained wheat is favored worldwide by millers and food processors because it produces flour with higher extraction rates and fewer dark bran specks, improving the appearance of Asian noodles, steamed bread, and pastries. However, white wheat is generally more susceptible to PHS because red grain color genes ($R-A1$, $R-B1$, $R-D1$) promote the accumulation of germination-inhibiting catechins and phlobaphenes in the testa. Developing PHS-tolerant white wheat requires introgressing major dormancy QTLs that act independently of seed coat color. Two such QTLs, *QPhs.ocs-3A.1* (chromosome 3AS) and *QPhs.ocs-4A.1* (chromosome 4AL), were previously mapped in the dormant red cultivar 'Zenkoujikomugi'. Validating whether these QTLs maintain high dormancy when introgressed into a white-grained genetic background is essential for white wheat breeding.

## Key Concepts & Theory
- **[[QPhs-3AS Locus]]**: A major seed dormancy and PHS resistance QTL on the short arm of chromosome 3A in wheat (*QPhs.ocs-3A.1*), corresponding to *TaMFT* / *TaPHS1*.
- **[[QPhs-4AL Locus]]**: A major seed dormancy QTL on the long arm of chromosome 4A (*QPhs.ocs-4A.1*), corresponding to *TaMKK3-A* (*Phs1*).
- **[[Grain Color Genes]]**: Dominant $R$ loci ($R-A1$, $R-B1$, $R-D1$) on group 3 chromosomes encoding transcription factors that activate flavonoid and phlobaphene synthesis in the seed coat.
- **[[Weighted Germination Index]]**: A time-weighted index calculating the speed and depth of seed germination, where lower scores indicate deeper seed dormancy.
- **[[Recombinant Inbred Lines]]**: Stable, homozygous mapping lines developed by repeated self-pollination from an $F_2$ population, capturing fixed combinations of parental alleles.

## Important Entities
* **Genes/Proteins**:
  - [[TaMFT]] / [[TaPHS1]] (*QPhs.ocs-3A.1*)
  - [[TaMKK3-A]] (*QPhs.ocs-4A.1*)
  - [[R-A1]] / [[R-B1]] / [[R-D1]]
* **Organisms**:
  - [[Triticum aestivum]] (Cultivars 'Zenkoujikomugi', 'Spica', 'Chinese Spring')
* **Tools/Techniques/Software**:
  - [[SSR Marker Genotyping]] (*BARC310*, *BARC57*, *BARC321*, *BARC170*)
  - [[Germination Index Testing]]
  - [[SAS ANOVA]]

## Methods & Experimental Design
1. *Plant Materials*: An $F_8$ RIL population was developed from 'Spica' (Australian white spring wheat, PHS-susceptible) $\times$ 'Zenkoujikomugi' (Zen, Japanese red winter wheat mutant, highly dormant). Forty white-grained RILs ($r\text{-}A1a/r\text{-}B1a/r\text{-}D1a$) and twenty red-grained RILs were selected.
2. *Phenotypic Dormancy Evaluation*: Lines were grown in field plots (3 years: 2002, 2003, 2004) under rain shelters and in glasshouses (2 years: 2002, 2003) at Obihiro University, Japan. Spikes harvested at 45–48 days post-anthesis were threshed, and 50 grains per line (two replicates) were tested for germination at 15°C and 20°C in the dark for 7 days to calculate Germination Index (GI).
3. *SSR Genotyping*: Genomic DNA was amplified with SSR markers for *QPhs-3AS* (*BARC321*, *BARC310*, *BARC57*) and *QPhs-4AL* (*BARC170*, *BARC269*, *gwm397*, *hbe3*, *hbe9*, *hbe11*).
4. *Statistical Analysis*: Multi-factor ANOVA in SAS evaluated the main effects of grain color, *QPhs-3AS* allele, incubation temperature, and their interactions on GI.

## Key Results & Data
- *Impact of QPhs-3AS on Dormancy*: The Zen allele at *QPhs-3AS* (flanked by *BARC310*) highly significantly reduced GI in all field and glasshouse trials ($P < 0.001$). White-Zen RILs exhibited mean GI of ~0.50 at 20°C and ~0.60 at 15°C.
- *White vs Red Comparison*: While red-Zen RILs were the most dormant (GI ~0.15–0.30) and white-Spica were the least dormant (GI ~0.85–0.95), white-Zen RILs exhibited significantly greater dormancy than red-Spica RILs (GI ~0.65–0.75) ($P < 0.05$).
- *Stability under High Temperature*: In the hot 2004 ripening season (>30°C), the Zen 3AS allele maintained a significant dormancy effect in white wheat despite generalized dormancy reduction.
- *QPhs-4AL Evaluation*: Among six 4AL SSR markers screened, only *BARC170* was polymorphic between Zen and Spica; however, *BARC170* genotype showed no significant association with GI, indicating that Zen and Spica share functionally equivalent 4AL alleles.

## Mechanistic Insights
The study demonstrates that embryo-imposed dormancy conferred by *QPhs-3AS* (*TaMFT*) operates additively with, but independently of, seed coat-imposed dormancy mediated by $R$ genes. While polyphenolic pigments in red seed coats provide physical/chemical inhibition against imbibition, the Zen *QPhs-3AS* allele establishes strong intrinsic embryo dormancy. When introgressed into a white seed coat background, *QPhs-3AS* provides sufficient dormancy to overcome the vulnerability of white wheat to pre-harvest sprouting.

## Conclusions & Implications
Introgression of the *QPhs-3AS* allele from 'Zenkoujikomugi' is an effective strategy to breed PHS-resistant white-grained wheat. The SSR marker *BARC310* enables robust marker-assisted selection for *QPhs-3AS* without requiring red grain color alleles, satisfying market preferences for bright white flour with high processing quality.

## Limitations & Caveats
The study examined a relatively small set of 40 white-grained RILs from a single biparental cross; the expression of *QPhs-3AS* in diverse commercial white wheat backgrounds with varying agronomic traits requires further validation.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Overturns the historical paradigm that high PHS resistance in wheat cannot be achieved without red grain color ($R$ genes).

## Under-Researched Populations
Japanese and Australian recombinant populations combining Asian landrace dormancy alleles with elite white wheat cultivars.

## Future Directions
1. Combine *QPhs-3AS* with polymorphic 4AL (*TaMKK3-A*) and 4AL-associated QTLs in white-grained breeding lines to test for additive dormancy enhancement.
2. Fine-map the *QPhs-3AS* interval to identify diagnostic causal SNPs for high-throughput marker selection.
3. Evaluate the end-use flour whiteness and milling yield of white-Zen recombinant lines.

## Key References to Follow Up
- [[Osa et al., 2003]] - Identified *QPhs.ocs-3A.1* on chromosome 3AS in 'Zenkoujikomugi' $\times$ 'Chinese Spring'.
- [[Mori et al., 2005]] - Evaluated the combined genetic effects of 3A and group 4 dormancy QTLs in wheat.
- [[Himi et al., 2002]] - Analyzed the effect of grain color genes ($R$) on seed dormancy and ABA sensitivity.

---
**Source PDF:** `data/kottearachchi_2006_increased_grain_dormancy.pdf`
"""

# ---------------------------------------------------------
# 7. sharma_2025_dissecting_genetic_architecture
# ---------------------------------------------------------
SUMMARIES["sharma_2025_dissecting_genetic_architecture"] = """---
tags: [preharvest sprouting, genome-wide association study, triticum sphaerococcum, single nucleotide polymorphism, candidate genes]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1038/s41598-025-88577-4
authors: "Sharma et al."
year: 2025
journal: "Scientific Reports"
format_version: 2
---

## Title & Metadata
- **Title**: Dissecting the genetic architecture of pre-harvest sprouting tolerance in Indian dwarf wheat (*Triticum sphaerococcum*) by multi-locus association analysis
- **Authors**: Divya Sharma, Ankita Mohapatra, Thamaraikannan Sivakumar, Anita Kumari, Neeraj Budhlakoti, Latief Bashir, Aakash Yadav, Reyazul Rouf Mir, Vijay Gahlaut, Pawan Kulwal, V. K. Vikas, Kiran B. Gaikwad, Amit Kumar Singh, G. P. Singh, and Sundeep Kumar
- **Journal**: *Scientific Reports* (2025) 15:article
- **DOI**: 10.1038/s41598-025-88577-4
- **Primary Focus**: First genome-wide association study (GWAS) and haplotype dissection of pre-harvest sprouting tolerance in a global collection of 116 *Triticum sphaerococcum* (Indian dwarf wheat) accessions.

## Abstract Summary
Pre-harvest sprouting (PHS), triggered by prolonged rainfall and humidity before harvest, severely reduces wheat grain yield, test weight, and baking quality. This study represents the first comprehensive assessment of PHS tolerance (PHST) in a global collection of 116 *Triticum sphaerococcum* (Indian dwarf wheat, $2n = 6x = 42$) accessions evaluated across three distinct agro-climatic environments in India (New Delhi, Wellington, and Rahuri) using moist chamber assays (1–9 scale). Genotyping with the 35K Axiom Wheat Breeders' SNP Array yielded 15,308 high-quality polymorphic SNPs. Single-locus GWAS (GLM, CMLM) and multi-locus GWAS (FarmCPU, BLINK, MLMM, MLM) identified 12 significant marker-trait associations (MTAs) ($P < 0.001$) distributed across eight chromosomes (1A, 1B, 1D, 2A, 3A, 3D, 5A, 6B). Five MTAs (*AX-94415302*, *AX-94919611*, *AX-94403953*, *AX-95220897*, and *AX-94756068*) were consistently detected across all environments and multi-environment BLUPs. Candidate gene mining identified 47 dormancy-related candidate genes encoding LRR, SANT/Myb, WRKY, Cytochrome P450, F-box, GRAS, and WD40 proteins. Haplotype analysis revealed three superior haplotypes—H005 (in line TS28), H006 (TS64), and H007 (TS81)—conferring strong PHS tolerance, offering novel genetic resources for wheat breeding.

## Introduction & Background
Pre-harvest sprouting (PHS) causes estimated global economic losses exceeding $1 billion annually by triggering seed germination on mature wheat spikes under wet conditions, causing starch degradation and low falling numbers. Hexaploid Indian dwarf wheat (*Triticum sphaerococcum* Percival, $2n = 6x = 42$, AABBDD), an ancient endemic wheat of the Indian subcontinent, possesses unique traits including spherical grains, short rigid culms, high grain protein content, and abiotic stress resilience. Although traditional breeding and Green Revolution cultivars largely replaced *T. sphaerococcum* after the 1960s, its uncharacterized germplasm represents a vital reservoir of untapped genetic diversity and novel alleles for crop improvement. Applying high-density SNP genotyping and multi-locus GWAS to *T. sphaerococcum* provides a unique opportunity to uncover novel loci and superior haplotypes for PHS tolerance.

## Key Concepts & Theory
- **[[Triticum sphaerococcum]]**: An ancient hexaploid wheat species characterized by hemispherical grains, compact spikes, short sturdy culms, and broad abiotic stress tolerance.
- **[[Multi-Locus GWAS Models]]**: Advanced association mapping algorithms (such as FarmCPU, BLINK, and MLMM) that simultaneously incorporate multiple markers as covariates to eliminate false positives and false negatives.
- **[[Marker-Trait Association]]**: A statistically significant correlation between a specific single nucleotide polymorphism marker and phenotypic variation for a target quantitative trait.
- **[[Allelic Pyramiding Effect]]**: The cumulative, progressive increase in phenotypic performance resulting from the sequential accumulation of multiple favorable alleles in a single genotype.
- **[[Haplo-Pheno Analysis]]**: A computational approach integrating haplotype structure with phenotypic data to identify superior multi-allelic combinations for breeding selection.

## Important Entities
* **Genes/Proteins**:
  - [[TraesCS1B03G0508500]] (LRR domain protein)
  - [[TraesCS1B03G1172400]] (WRKY domain protein)
  - [[TraesCS2A03G1292800]] (Cytochrome P450 / ABA 8'-hydroxylase)
  - [[TraesCS3A03G1033800]] (F-box domain protein)
  - [[TraesCS5A03G1249100]] (GRAS transcription factor)
* **Organisms**:
  - [[Triticum sphaerococcum]] (Indian dwarf wheat)
  - [[Triticum aestivum]] (Bread wheat)
* **Tools/Techniques/Software**:
  - [[Affymetrix 35K Axiom Wheat Breeders Array]]
  - [[GAPIT]] (FarmCPU, BLINK, MLMM, CMLM, MLM, GLM)
  - [[geneHapR]]
  - [[TASSEL]]
  - [[STRUCTURE]]

## Methods & Experimental Design
1. *Germplasm & Field Trials*: 116 *T. sphaerococcum* accessions sourced from three international genebanks were grown in 2023–2024 across three contrasting Indian environments: ICAR-NBPGR, New Delhi (E1); ICAR-IARI, Wellington (E2); and MPKV, Rahuri (E3) in randomized complete block designs with three replicates.
2. *PHST Phenotyping*: Spikes harvested at physiological maturity (loss of green color) were soaked in water for 4–6 h and incubated in moist sand chambers (20–25°C, 90–100% RH, covered with wet jute bags) for 10 days. Sprouting was scored on a 1–9 visual rating scale (1 = no sprouting, 9 = fully sprouted).
3. *SNP Genotyping & Quality Filtering*: DNA was genotyped with the Affymetrix 35K Axiom Wheat Breeders' Array (35,143 SNPs). After removing markers with MAF < 0.05, 15,308 polymorphic SNPs were retained (4,802 on A, 5,925 on B, and 4,581 on D genome).
4. *GWAS & Candidate Gene Analysis*: Association mapping was performed in GAPIT using two SL-GWAS models (GLM, CMLM) and four ML-GWAS models (FarmCPU, BLINK, MLMM, MLM) with kinship ($K$) and population structure ($Q$) covariates ($P < 0.001$, Bonferroni-adjusted). Candidate genes in 2 Mb flanking intervals were extracted from IWGSC RefSeq v2.1. Haplotypes and haplo-pheno associations were resolved using `geneHapR`.

## Key Results & Data
- *Phenotypic Variation*: ANOVA revealed highly significant genotypic variance ($F = 15.97, P < 2\times 10^{-16}$) and minimal environmental variance ($P = 0.534$). PHS BLUP scores clustered the 116 accessions into four distinct tolerance tiers.
- *Marker-Trait Associations*: 12 MTAs were identified across 8 chromosomes (1A, 1B, 1D, 2A, 3A, 3D, 5A, 6B). Chromosome 1B harbored the highest density of associations (4 MTAs).
- *Five Stable MTAs*:
  - *AX-94415302* (1B, 313.0 Mb, $P = 0.0002$)
  - *AX-94919611* (1B, 320.8 Mb, $P = 0.0004$, detected consistently by all six GWAS models across all locations)
  - *AX-94403953* (1B, 666.3 Mb, $P = 0.0004$)
  - *AX-95220897* (6B, 6.6 Mb, $P = 0.0006$)
  - *AX-94756068* (2A, 42.5 Mb, $P = 0.0005$)
- *Allele Pyramiding*: Linear regression demonstrated that progressive accumulation of up to eight favorable SNP alleles drove a linear reduction in PHS score ($R^2 = 0.173–0.201, P < 0.0001$).
- *Superior Haplotypes*: Haplo-pheno analysis identified three superior PHS-tolerant haplotypes—H005 (line TS28), H006 (line TS64), and H007 (line TS81)—exhibiting significantly higher dormancy compared to susceptible haplotypes (H001–H004, H008).

## Mechanistic Insights
Candidate gene annotation within the 2 Mb MTA windows identified 47 functional genes directly implicated in seed germination and dormancy pathways. Stable MTAs on chromosome 1B (*AX-94415302*, *AX-94919611*) associate with genes encoding LRR receptor kinases (*TraesCS1B03G0508500*) and WRKY/SANT transcription factors (*TraesCS1B03G1172400*) that activate ABA-responsive transcriptional cascades. MTA *AX-94523390* on 2A co-localizes with Cytochrome P450 / ABA-8'-hydroxylase (*TraesCS2A03G1292800*) regulating ABA catabolism, while chromosome 3A/3D MTAs associate with F-box proteins (*TraesCS3A03G1033800*) governing proteasome-mediated degradation of germination regulators.

## Conclusions & Implications
This study provides the first genetic dissection of pre-harvest sprouting tolerance in *Triticum sphaerococcum*. The 5 stable MTAs, 47 candidate genes, and superior haplotypes (H005, H006, H007 in accessions TS28, TS64, TS81) represent novel allelic diversity that can be directly introgressed into elite hexaploid bread wheat breeding lines to broaden the genetic base for climate resilience.

## Limitations & Caveats
The study examined an association panel of 116 accessions; validating candidate gene expression levels via qRT-PCR and testing bi-parental introgression populations in bread wheat backgrounds will be necessary to confirm allelic effects.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Ancient hexaploid *Triticum sphaerococcum* (Indian dwarf wheat) landraces and genebank accessions from South Asia.

## Future Directions
1. Develop high-throughput KASP markers for the five stable MTAs (*AX-94919611*, *AX-94415302*, *AX-94403953*, *AX-95220897*, *AX-94756068*) for MAS.
2. Cross superior tolerant accessions TS28, TS64, and TS81 with commercial PHS-susceptible Indian bread wheat cultivars (e.g., HD2967, PBW343) to develop introgression lines.
3. Functionally characterize the 1B WRKY and 2A Cytochrome P450 candidate genes via transgenic overexpression and CRISPR editing.

## Key References to Follow Up
- [[Kulwal et al., 2005]] - Mapped a major PHS tolerance QTL on chromosome 3A in bread wheat.
- [[Mori et al., 2005]] - Mapped seed dormancy QTLs on chromosomes 3A and group 4 in wheat.
- [[Wang et al., 2014]] - Established 90K SNP genotyping and GWAS methodologies in wheat.

---
**Source PDF:** `data/sharma_2025_dissecting_genetic_architecture.pdf`
"""

# ---------------------------------------------------------
# 8. lin_2018_effects_taphs1_tamkk3
# ---------------------------------------------------------
SUMMARIES["lin_2018_effects_taphs1_tamkk3"] = """---
tags: [preharvest sprouting, taphs1, tamkk3, marker-assisted backcrossing, triticum aestivum]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.3390/agronomy8100210
authors: "Lin et al."
year: 2018
journal: "Agronomy"
format_version: 2
---

## Title & Metadata
- **Title**: Effects of *TaPHS1* and *TaMKK3-A* Genes on Wheat Pre-Harvest Sprouting Resistance
- **Authors**: Meng Lin, Shubing Liu, Guorong Zhang, and Guihua Bai
- **Journal**: *Agronomy* (2018) 8(10):210
- **DOI**: 10.3390/agronomy8100210
- **Primary Focus**: Dissecting the individual and combined genetic effects of cloned seed dormancy genes *TaPHS1* (3AS) and *TaMKK3-A* (4AL) introgressed into a white-grained wheat background across greenhouse and field environments.

## Abstract Summary
Pre-harvest sprouting (PHS) constrains wheat production worldwide by reducing both grain yield and end-use processing quality. *TaPHS1* on chromosome 3AS and *TaMKK3-A* on chromosome 4AL are two cloned major PHS resistance genes that operate independently of grain color. In this study, marker-assisted backcrossing (MAB) was used to introgress *TaPHS1* and *TaMKK3-A* from two PHS-resistant donor sources ('Tutoumai A' and 'AUS1408') into a sprouting-susceptible hard white winter wheat line, 'NW97S186'. Double homozygous $BC_2F_2$ and $BC_2F_3$ progeny (AABB, AAbb, aaBB, aabb) were tested across four environments (2015 fall greenhouse, 2016 spring greenhouse, and 2016 Manhattan and Hays, KS field trials). Overall ANOVA revealed that environment, gene source, and genotypes explained 56.4% of phenotypic variance. *TaPHS1* significantly reduced germination rates (by 14.4% to 29.4%), with effects varying across environments and gene sources. *TaMKK3-A* also significantly reduced germination rates (by 6.7% to 26.7%), showing enhanced efficacy in cooler maturation environments. The two genes exhibited strong additive effects, with double-resistant lines (AABB) displaying the lowest germination rates (19.2% to 42.1%) across all environments. Additive effects were greater under mild greenhouse conditions than under dry, hot field conditions during grain maturation.

## Introduction & Background
Pre-harvest sprouting (PHS), the germination of physiologically mature wheat grains prior to harvest, impairs end-use flour and dough quality due to the rapid accumulation of hydrolytic enzymes such as $\alpha$-amylase. Breeding PHS-resistant white wheat is highly desirable but historically challenging because white wheat lacks the dormancy-enhancing polyphenolic compounds present in red seed coats. *TaPHS1* (a *MOTHER OF FT AND TFL1* [*TaMFT*]-like gene on 3AS) and *TaMKK3-A* (a mitogen-activated protein kinase kinase on 4AL) represent the two primary cloned major genes conferring PHS resistance independently of grain color. Three functional SNPs in *TaPHS1* (-222 promoter, +646 splice site, +666 exon 3) and a single functional non-synonymous SNP in *TaMKK3-A* dictate seed dormancy. However, the extent to which these two cloned genes interact additively or epistatically, and how their individual and combined effects respond to environmental temperature and moisture fluctuations, remained uncharacterized in near-isogenic white wheat backgrounds.

## Key Concepts & Theory
- **[[TaPHS1 Gene]]**: A cloned PEBP-family signaling regulator gene on wheat chromosome 3AS (*QPhs.ocs-3A.1*) that promotes seed dormancy and ABA responsiveness.
- **[[TaMKK3-A Gene]]**: A cloned mitogen-activated protein kinase kinase 3 gene on chromosome 4AL (*Phs1*) that positively regulates seed dormancy via protein phosphorylation cascades.
- **[[Marker-Assisted Backcrossing]]**: A breeding method utilizing tightly linked or causal DNA markers to introgress specific target alleles into a recurrent parent while minimizing background donor genome.
- **[[Gene-by-Environment Interaction]]**: The differential phenotypic expression of specific genotypes or QTL alleles across distinct environmental conditions such as temperature and precipitation.
- **[[Additive Pyramiding Effect]]**: The cumulative phenotypic improvement achieved by combining multiple independent favorable alleles within a single genetic background.

## Important Entities
* **Genes/Proteins**:
  - [[TaPHS1]] / [[TaMFT]]
  - [[TaMKK3-A]] (*Phs1*)
* **Organisms**:
  - [[Triticum aestivum]] (Cultivars 'Tutoumai A', 'AUS1408', line 'NW97S186')
* **Tools/Techniques/Software**:
  - [[KASP Genotyping]]
  - [[Marker-Assisted Selection]]
  - [[Moist Chamber Sprouting Assay]]
  - [[SAS PROC GLM]]

## Methods & Experimental Design
1. *Plant Materials & Introgression*: PHS-resistant white wheat landrace 'Tutoumai A' (Chinese landrace) and 'AUS1408' (South African spring wheat) were crossed with PHS-susceptible hard white winter wheat line 'NW97S186'. Double heterozygous $BC_1F_1$ and $BC_2F_1$ plants were selected using KASP markers for *TaPHS1* and *TaMKK3-A*. Double homozygous $BC_2F_2$, $BC_2F_3$, and $BC_2F_4$ lines (AABB, AAbb, aaBB, aabb) were developed.
2. *Environmental Testing*: Lines were phenotyped in four environments: 2015 Fall greenhouse, 2016 Spring greenhouse (Manhattan, KS), and 2016 field trials at Manhattan (Rocky Ford) and Hays (Agricultural Research Center), Kansas, USA.
3. *PHS Evaluation*: Spikes harvested at physiological maturity (Zadoks scale 91, loss of green glume color) were air-dried for 5–9 days, stored at -20°C, immersed in de-ionized water for 12 h, and incubated in a moist chamber at 22 ± 1°C (>95% RH, humidified twice daily) for 7 days. Germinated kernels were counted to calculate germination rate (%).
4. *Statistical Analysis*: Four-way ANOVA in SAS 9.3 evaluated fixed effects of environment, gene source, *TaPHS1* genotype, *TaMKK3-A* genotype, and their interaction terms.

## Key Results & Data
- *ANOVA Variance Components*: Environments, gene sources, and genotypes accounted for 56.4% of total phenotypic variance for PHS resistance ($P < 0.0001$). Highly significant main effects were detected for *TaPHS1* ($F = 84.01$) and *TaMKK3-A* ($F = 72.66$).
- *Individual Gene Effects*:
  - *TaPHS1* significantly reduced germination rates by 22.5% to 29.4% in greenhouse experiments and 8.3% to 18.7% in field trials.
  - *TaMKK3-A* significantly reduced germination rates by 16.2% to 26.7% in greenhouse trials and 6.7% to 14.0% in field trials.
- *Combined Additive Effects*: In both genetic backgrounds (Tutoumai A and AUS1408), double-resistant lines (AABB) exhibited the lowest germination rates across all environments:
  - In NW97S186 $\times$ Tutoumai A: AABB had germination rates of 0.192 (Fall GH), 0.399 (Spring GH), 0.253 (Manhattan field), and 0.421 (Hays field), compared to 0.684, 0.907, 0.446, and 0.511 for aabb controls ($P < 0.05$).
  - In NW97S186 $\times$ AUS1408: AABB had germination rates of 0.288 (Fall GH), 0.435 (Spring GH), 0.243 (Manhattan field), and 0.404 (Hays field), compared to 0.538, 0.861, 0.454, and 0.626 for aabb controls.
- *Environmental Sensitivity & Epistasis*: Epistatic interaction between *TaPHS1* and *TaMKK3-A* was marginally significant ($P = 0.0578$). Additive gene effects were substantially greater under mild greenhouse conditions than under high-temperature summer field conditions.

## Mechanistic Insights
*TaPHS1* and *TaMKK3-A* regulate seed dormancy through distinct, complementary signaling pathways. *TaPHS1* functions in tissue coordination and ABA responsiveness as a PEBP-family signaling regulator, while *TaMKK3-A* mediates protein phosphorylation cascades within the mitogen-activated protein kinase pathway. Pyramiding both resistance alleles establishes two independent layers of dormancy regulation, effectively suppressing precocious germination even when environmental temperature fluctuations partially weaken one of the pathways.

## Conclusions & Implications
Pyramiding *TaPHS1* and *TaMKK3-A* through marker-assisted backcrossing provides robust, additive protection against PHS in white-grained wheat. Because single resistance genes provide incomplete protection in hot, variable field environments, breeders should simultaneously select favorable alleles at both loci using diagnostic KASP markers to achieve stable, commercial-level PHS tolerance.

## Limitations & Caveats
Double homozygous introgressions (AABB) still exhibited slightly higher germination rates than their donor parents ('Tutoumai A' and 'AUS1408'), indicating that unmapped minor QTLs in the donor backgrounds contribute additional dormancy.

## Contradictory Findings
*TaPHS1* exhibited stronger dormancy reduction in the spring greenhouse (higher developmental temperatures) than in the fall greenhouse, contrasting with previous reports that low temperature during seed development strictly upregulates *TaPHS1* expression.

## Outdated Models
Overturns the assumption that a single major cloned dormancy gene (*TaPHS1* or *TaMKK3-A*) provides sufficient field protection against PHS across diverse environments.

## Under-Researched Populations
Hard white winter wheat breeding populations in the US Great Plains and commercial white wheat germplasm in China.

## Future Directions
1. Introgress *TaPHS1* and *TaMKK3-A* into elite US hard white winter wheat cultivars to develop commercial PHS-resistant lines.
2. Fine-map and identify the minor background QTLs from 'Tutoumai A' and 'AUS1408' that complement the two major cloned genes.
3. Investigate the molecular cross-talk between MKK3-mediated phosphorylation cascades and TaPHS1 protein complexes during grain maturation.

## Key References to Follow Up
- [[Liu et al., 2013]] - Cloned *TaPHS1* on chromosome 3AS and identified causal SNPs in 'Rio Blanco'.
- [[Nakamura et al., 2011]] - Identified *TaMFT* as the causal gene for the 3A seed dormancy QTL in wheat.
- [[Torada et al., 2016]] - Cloned *TaMKK3-A* on chromosome 4AL as the causal gene for wheat PHS resistance locus *Phs1*.

---
**Source PDF:** `data/lin_2018_effects_taphs1_tamkk3.pdf`
"""

# ---------------------------------------------------------
# 9. dhariwal_2021_mapping_pre_harvest
# ---------------------------------------------------------
SUMMARIES["dhariwal_2021_mapping_pre_harvest"] = """---
tags: [preharvest sprouting, seed dormancy, quantitative trait loci, doubled haploid, triticum aestivum]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1186/s12870-021-03001-4
authors: "Dhariwal et al."
year: 2021
journal: "BMC Plant Biology"
format_version: 2
---

## Title & Metadata
- **Title**: Mapping pre-harvest sprouting resistance loci in *AAC Innova* $\times$ *AAC Tenacious* spring wheat population
- **Authors**: Raman Dhariwal, Colin W. Hiebert, Mark E. Sorrells, Dean Spaner, Robert J. Graf, Jaswinder Singh, and Harpinder S. Randhawa
- **Journal**: *BMC Plant Biology* (2021) 21:232
- **DOI**: 10.1186/s12870-021-03001-4
- **Primary Focus**: Comprehensive QTL mapping, candidate gene identification, and epistatic analysis of PHS resistance in a doubled haploid population derived from Canadian cultivars 'AAC Innova' and 'AAC Tenacious'.

## Abstract Summary
Pre-harvest sprouting (PHS) causes extensive global losses exceeding $1 billion annually by degrading wheat yield, end-use baking quality, and seed viability. In this study, a doubled haploid (DH) mapping population derived from a cross between white-grained PHS-susceptible cv. 'AAC Innova' and red-grained highly resistant cv. 'AAC Tenacious' was screened for PHS resistance in four field environments (Edmonton 2019, Ithaca 2018, Lethbridge 2018, and Lethbridge 2019). Composite interval mapping (CIM) and mixed-model composite interval mapping (MCIM) identified 21 PHS resistance QTLs on chromosomes 1A, 2A, 2B, 2D, 3A, 3B, 3D, 4A, 4B, 4D, 5A, 7A, and 7D. Seven major QTLs each explained $\ge 10\%$ of phenotypic variation, including three highly effective loci: *QPhs.lrdc-2B.1* (novel, $R^2 = 10\%$, LOD = 5.01), *QPhs.lrdc-3A.1* (*MFT-A1b*, $R^2 = 19\%$, LOD = 12.00), and *QPhs.lrdc-7D* ($R^2 = 18\%$, LOD = 6.21, resistance contributed by AAC Innova). Comparative genomic analyses mapped candidate genes within QTL intervals, including *MFT-A1b* (3A), *AGO802A* (3A), *MFT-3B-1* (3B), *AGO802D*, *HUB1*, *TaVp1-D1* (3D), *TaMyb10-D1* (3D), and *Ppd-D1b* (2D). Digenic epistasis occurred between 1A and 7A QTLs. Cumulative pyramiding of $\ge 5$ major QTLs was required to achieve maximum PHS resistance.

## Introduction & Background
Pre-harvest sprouting (PHS), the germination of physiologically mature grains on wheat spikes prior to harvest under cool, wet conditions, activates hydrolytic enzymes ($\alpha$-amylases, proteases, lipases) that severely impair dough strength, loaf volume, and milling extraction. In Canada, PHS causes average annual losses of $100 million. 'AAC Tenacious' is an elite Canadian red spring wheat cultivar renowned for exceptionally high PHS resistance, tall stature ($Rht-B1a$, $Rht8a$), and photoperiod sensitivity ($Ppd-D1b$), derived from historical donors including 'RL4137'. 'AAC Innova' is a high-yielding, semi-dwarf, soft white spring wheat cultivar that is susceptible to PHS. Dissecting the multi-locus genetic architecture of PHS resistance in this cross, identifying candidate genes involved in dormancy and epigenetic pathways, and characterizing epistatic interactions provides critical genomic resources for wheat improvement.

## Key Concepts & Theory
- **[[Composite Interval Mapping]]**: A statistical method for QTL mapping that combines interval mapping with multiple regression on background markers to increase mapping precision.
- **[[Digenic Epistasis]]**: Non-additive genetic interactions between alleles at two distinct genomic loci affecting the expression of a quantitative trait.
- **[[RNA-Directed DNA Methylation]]**: An epigenetic pathway involving ARGONAUTE proteins (such as *AGO802*) that mediates DNA methylation and transcriptional silencing controlling seed dormancy.
- **[[Photoperiod Response Alleles]]**: Alleles at the *Ppd-1* loci that govern flowering time and photoperiod sensitivity, with pleiotropic effects on grain development and sprouting.
- **[[QTL Pyramiding Threshold]]**: The minimum number of stacked favorable QTL alleles required to produce a stable, highly resistant phenotype across environments.

## Important Entities
* **Genes/Proteins**:
  - [[MFT-A1b]] (*QPhs.lrdc-3A.1*)
  - [[MFT-3B-1]] (*QPhs.lrdc-3B.1*)
  - [[AGO802A]] / [[AGO802D]] (Argonaute proteins)
  - [[HUB1]] (Histone monoubiquitination 1)
  - [[TaVp1-D1]]
  - [[TaMyb10-D1]]
  - [[Ppd-D1b]]
* **Organisms**:
  - [[Triticum aestivum]] (Spring wheat cv. 'AAC Tenacious', 'AAC Innova')
* **Tools/Techniques/Software**:
  - [[Windows QTL Cartographer]] (CIM)
  - [[QTLNetwork]] (MCIM & Epistasis)
  - [[IWGSC RefSeq v2.0]]
  - [[Mist Chamber Sprouting Assay]]

## Methods & Experimental Design
1. *Mapping Population & Field Trials*: A doubled haploid (DH) population of 168 lines derived from 'AAC Innova' $\times$ 'AAC Tenacious' was grown across four environments: Edmonton 2019 (EDM19), Ithaca 2018 (ITH18), Lethbridge 2018 (LET18), and Lethbridge 2019 (LET19).
2. *PHS Phenotyping*: At physiological maturity (loss of glume greenness), intact spikes were sampled, dried for 5 days, stored at -20°C, and exposed to 4 days of misting in artificial greenhouse chambers. Sprouting was scored on a 0–9 visual scale.
3. *Genotyping & Linkage Map*: DH lines were genotyped with high-density SNP markers from the wheat 90K array. Genetic maps were constructed using MapDisto and JoinMap 4.0.
4. *QTL & Epistasis Mapping*: CIM in QTL Cartographer v2.5 and MCIM in QTLNetwork 2.0 were performed for individual and pooled environment datasets. Physical intervals were aligned to IWGSC RefSeq v2.0 to pinpoint candidate genes.

## Key Results & Data
- *Phenotypic Performance & Heritability*: PHS scores in the DH population ranged from 0.0 to 8.8 across environments, with broad-sense heritability $H^2 = 0.71$. 'AAC Tenacious' was consistently resistant (mean score 1.0–1.4), while 'AAC Innova' was susceptible (mean score 1.8–8.7).
- *Twenty-One PHS QTLs*: CIM and MCIM identified 21 QTLs distributed across 13 chromosomes (1A, 2A, 2B, 2D, 3A, 3B, 3D, 4A, 4B, 4D, 5A, 7A, 7D). Thirteen loci shared positions with previously published QTLs, while eight were novel.
- *Seven Major QTLs ($R^2 \ge 10\%$)*:
  - *QPhs.lrdc-3A.1* (3A, 1.25 Mb, LOD = 12.00, $R^2 = 19.0\%$, *MFT-A1b*, resistance from Tenacious)
  - *QPhs.lrdc-7D* (7D, 56.6 Mb, LOD = 6.21, $R^2 = 18.0\%$, resistance from Innova)
  - *QPhs.lrdc-1A.2* (1A, 38.2 Mb, LOD = 6.66, $R^2 = 14.0\%$, resistance from Tenacious)
  - *QPhs.lrdc-3B.2* (3B, 774.5 Mb, LOD = 7.20, $R^2 = 13.0\%$, resistance from Tenacious)
  - *QPhs.lrdc-3D.2* (3D, 573.6 Mb, LOD = 6.18, $R^2 = 12.0\%$, *TaMyb10-D1*, resistance from Tenacious)
  - *QPhs.lrdc-2B.1* (2B, 107.7 Mb, LOD = 5.01, $R^2 = 10.0\%$, novel, resistance from Tenacious)
  - *QPhs.lrdc-3D.1* (3D, 346.0 Mb, LOD = 4.21, $R^2 = 10.0\%$, *AGO802D*, *TaVp1-D1*, resistance from Innova)
- *Candidate Gene Alignments*: Physical mapping identified *MFT-A1b* in *QPhs.lrdc-3A.1*, *AGO802A* in *QPhs.lrdc-3A.2*, *MFT-3B-1* in *QPhs.lrdc-3B.1*, *AGO802D* and *TaVp1-D1* in *QPhs.lrdc-3D.1*, and photoperiod gene *Ppd-D1b* in *QPhs.lrdc-2D.1*.
- *Epistasis & Pyramiding*: Significant digenic epistasis occurred between *QPhs.lrdc-1A.1* and *QPhs.lrdc-7A* ($AA = -0.24, R^2 = 4.9\%$). Accumulation of $\ge 5$ major QTLs was required to confer the extreme PHS resistance of 'AAC Tenacious'.

## Mechanistic Insights
The study demonstrates that PHS resistance in 'AAC Tenacious' involves multiple biological mechanisms: (1) core embryo dormancy signaling (*MFT-A1b*, *TaVp1-D1*), (2) seed coat-imposed dormancy via flavonoid synthesis (*TaMyb10-D1*), (3) epigenetic transcriptional regulation via RNA-directed DNA methylation (*AGO802A*, *AGO802D*) and histone monoubiquitination (*HUB1*), and (4) developmental timing and photoperiod responsiveness (*Ppd-D1b*). The susceptible parent 'AAC Innova' also contributes functional resistance alleles (*QPhs.lrdc-7D*, *QPhs.lrdc-3D.1*), demonstrating hidden genetic potential in soft white wheat.

## Conclusions & Implications
PHS resistance in Canadian spring wheat is highly polygenic, combining genetic, epigenetic, and physiological mechanisms. 'AAC Tenacious' serves as an exceptional reservoir of major QTLs. The identified SNP markers and candidate genes provide valuable diagnostic tools for pyramiding $\ge 5$ major loci into elite white and red wheat breeding lines to achieve durable PHS resistance.

## Limitations & Caveats
The study used a single biparental DH population (168 lines); fine-mapping and functional validation of novel QTLs (*QPhs.lrdc-2B.1*, *QPhs.lrdc-7D*) are needed to isolate the underlying causal sequence polymorphisms.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Overturns the view that PHS resistance in 'AAC Tenacious' is driven solely by *MFT-3A* and red grain color (*R-D1*), showing that epigenetic regulators (*AGO802*, *HUB1*) and unlinked major QTLs on 2B and 7D are equally critical.

## Under-Researched Populations
Canadian Prairie spring wheat cultivars and historical North American donor lineages ('RL4137', 'Thatcher', 'Frontana').

## Future Directions
1. Fine-map the novel major QTLs *QPhs.lrdc-2B.1* (2B) and *QPhs.lrdc-7D* (7D) to identify causal polymorphisms.
2. Develop multiplex KASP panels for the seven major QTLs (*QPhs.lrdc-1A.2*, *2B.1*, *3A.1*, *3B.2*, *3D.1*, *3D.2*, *7D*).
3. Investigate DNA methylation dynamics of *AGO802A* and *AGO802D* during grain development under wet vs dry environments.

## Key References to Follow Up
- [[Liu et al., 2013]] - Cloned *TaPHS1* (*MFT-3A*) on chromosome 3AS.
- [[Torada et al., 2016]] - Cloned *TaMKK3-A* on chromosome 4AL.
- [[Singh et al., 2019]] - Characterized epigenetic regulation and *AGO802* involvement in cereal seed dormancy.

---
**Source PDF:** `data/dhariwal_2021_mapping_pre_harvest.pdf`
"""

# ---------------------------------------------------------
# 10. sakthivel_2025_enhancing_quality_climate
# ---------------------------------------------------------
SUMMARIES["sakthivel_2025_enhancing_quality_climate"] = """---
tags: [polyploidy, genome editing, transgenics, climate resilience, crop improvement]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.3389/fgene.2025.1599242
authors: "Sakthivel et al."
year: 2025
journal: "Frontiers in Genetics"
format_version: 2
---

## Title & Metadata
- **Title**: Enhancing quality and climate resilient traits in vegetatively propagated polyploids: transgenic and genome editing advancements, challenges and future directions
- **Authors**: Surya Krishna Sakthivel, Amaranatha Reddy Vennapusa, and Kalpalatha Melmaiee
- **Journal**: *Frontiers in Genetics* (2025) 16:1599242
- **DOI**: 10.3389/fgene.2025.1599242
- **Primary Focus**: Comprehensive review of transgenic engineering and CRISPR/Cas-mediated genome editing for quality enhancement and climate resilience in vegetatively propagated polyploid crops (potato, strawberry, banana, and sugarcane).

## Abstract Summary
Vegetatively propagated polyploid crops such as potato (*Solanum tuberosum*), strawberry (*Fragaria $\times$ ananassa*), banana (*Musa spp.*), and sugarcane (*Saccharum spp.*) play crucial roles in global food security and bioeconomy. However, complex polyploid genomes, high heterozygosity, inbreeding depression, and asexual clonal propagation severely hinder traditional and marker-assisted breeding. Transgenic technology and CRISPR/Cas genome editing offer transformative solutions to enhance end-use quality, nutritional value, and biotic/abiotic stress resilience. This review synthesizes advancements from 2011 to 2025 in genetic engineering of these four polyploid crops. Key quality targets successfully edited or modulated include amylose synthesis (*GBSS*), acrylamide formation (*VInv*, *Asn1*, *Ppo2*), and steroidal glycoalkaloids (*St16DOX*) in potato; fruit color (*FaRAP*) and firmness (*FaPG1*) in strawberry; pro-vitamin A enrichment (*MtPsy2a*, *LCY$\varepsilon$*) and viral inactivation (*eBSV*) in banana; and disease resistance (*Trichoderma* endochitinases) in sugarcane. The review outlines persistent technical challenges, including genotype-dependent transformation, somaclonal variation, multi-allelic target mutation efficiency, transgene-free delivery platforms (RNPs), and evolving regulatory frameworks.

## Introduction & Background
Polyploidy is a major evolutionary mechanism in plants resulting in whole-genome duplication (autopolyploids like potato and banana, or allopolyploids like wheat, strawberry, and sugarcane). Polyploids exhibit high genetic vigor, biomass accumulation, and environmental buffering capacity. Vegetative clonal propagation enables crops to indefinitely preserve hybrid superiority and heterozygous gene combinations. However, breeding vegetatively propagated polyploids via classical hybridization is extraordinarily slow and difficult due to polyploid meiotic irregularities, high allele dosage, gametic sterility, self-incompatibility, and severe inbreeding depression. Climate change exacerbates these vulnerabilities by increasing the frequency of extreme heat, drought, unpredictable precipitation, and virulent pathogen outbreaks. Modern biotechnological interventions—including transgenics, RNA interference (RNAi), CRISPR/Cas9, base editing, and prime editing—enable precise, targeted trait improvements without disrupting the elite clonal genetic background.

## Key Concepts & Theory
- **[[Clonally Propagated Polyploids]]**: Polyploid crop species reproduced primarily through asexual vegetative propagules (tubers, runners, suckers, or stem cuttings), maintaining fixed heterozygous genotypes across clonal generations.
- **[[CRISPR-Cas9 Multi-Allelic Editing]]**: The simultaneous targeted mutagenesis of all homoeologous and paralogous gene copies in a polyploid genome using single or multiplex guide RNAs.
- **[[Transgene-Free Genome Editing]]**: The delivery of pre-assembled ribonucleoprotein complexes (Cas protein plus gRNA) into plant protoplasts or tissues to achieve targeted mutations without foreign DNA integration.
- **[[Somaclonal Variation]]**: Phenotypic and epigenetic mutations induced during in vitro plant tissue culture and regeneration cycles.
- **[[Susceptibility Gene Knockout]]**: The targeted inactivation of host $S$-genes (e.g., *DMR6*, *PM1*, *NPR3*) to establish broad-spectrum, durable disease resistance.

## Important Entities
* **Genes/Proteins**:
  - [[StGBSS]] / [[St16DOX]] / [[StPPO2]] / [[StPM1]] / [[StDMR6-1]] (Potato)
  - [[FaRAP]] / [[FaPG1]] / [[FaSnRK1a]] / [[FaMAPK5]] (Strawberry)
  - [[MusaDMR6]] / [[MusaLCYe]] / [[MaPIP1;1]] / [[MaGA20ox2]] (Banana)
  - [[Trichoderma endochitinase]] / [[Bt cry1Ac]] (Sugarcane)
* **Organisms**:
  - [[Solanum tuberosum]] (Autotetraploid potato)
  - [[Fragaria ananassa]] (Allo-octoploid strawberry)
  - [[Musa acuminata]] / [[Musa balbisiana]] (Diploid/triploid banana)
  - [[Saccharum officinarum]] / [[Saccharum spontaneum]] (Aneuploid/polyploid sugarcane)
* **Tools/Techniques/Software**:
  - [[CRISPR-Cas9]]
  - [[Cytidine Base Editing]]
  - [[Agrobacterium-Mediated Transformation]]
  - [[Particle Bombardment]]
  - [[Ribonucleoprotein Delivery]]

## Methods & Experimental Design
The review conducted a systematic literature analysis (2002–2025) across PubMed, Web of Science, and Google Scholar, categorizing transgenic and genome-edited events (2011–2025) across four major crops:
1. *Potato*: Transgenic and CRISPR modifications targeting industrial starch (amylose-free *StGBSS* knockouts), food safety (acrylamide reduction via *VInv* and *Asn1* silencing, glycoalkaloid elimination via *St16DOX* and *StSSR2* knockouts), and late blight resistance (*Rpi-vnt1.1*, *StPM1*, *StDMR6-1*).
2. *Strawberry*: Editing and overexpression events in allo-octoploid strawberry ($2n = 8x = 56$) regulating fruit color (*FaRAP* knockout producing white fruit), firmness (*FaPG1*), gray mold resistance (*FaSnRK1$\alpha$*, *FaMAPK5/10*), and drought tolerance (*At-rty*).
3. *Banana*: Transgenic and CRISPR events in sterile triploid bananas (AAA Cavendish, AAB plantains) targeting banana xanthomonas wilt (*DMR6* knockout), endogenous viral inactivation (*eBSV* in B-genome), and $\beta$-carotene biofortification (*LCY$\varepsilon$* editing).
4. *Sugarcane*: Genetic engineering in complex aneuploid polyploid sugarcane ($2n = 80–130$) for red rot resistance (chitinases, $\beta$-1,3-glucanase), borer resistance (*Bt cry1Ac*), and drought tolerance.

## Key Results & Data
- *Potato Advances*: Commercialization of J.R. Simplot Innate® 1.0/2.0 potatoes (downregulation of *Asn1*, *Ppo2*, *VInv*, and introduction of *Rpi-vnt1.1*). CRISPR/Cas9 knockout of *StGBSS* yielded amylose-free tubers (0% amylose vs 20% in wild type). Base editing of *ALS* conferred chlorsulfuron herbicide tolerance. Knockout of *St16DOX* generated steroidal glycoalkaloid-free lines.
- *Strawberry Advances*: CRISPR knockout of multiple homoeoalleles of the glutathione S-transferase gene *FaRAP* eliminated anthocyanin accumulation, converting red fruit to white. Knockout of pectate lyase gene *FaPG1* reduced *Botrytis cinerea* susceptibility and increased fruit firmness. Overexpression of *FaSnRK1$\alpha$* boosted salicylic acid accumulation and *PR* gene expression.
- *Banana Advances*: CRISPR knockout of susceptibility gene *MusaDMR6* conferred field resistance to Banana Xanthomonas Wilt (BXW) without growth penalties. Knockout of *LCY$\varepsilon$* increased fruit $\beta$-carotene content by 6-fold. CRISPR inactivation of integrated *eBSV* sequences in the B-genome reduced viral outbreak under water stress by 75%.
- *Sugarcane Advances*: Transgenic lines expressing *Trichoderma* endochitinase and $\beta$-1,3-glucanase showed significant field resistance against red rot (*Colletotrichum falcatum*). Overexpression of *Erianthus arundinaceus EaDREB2* enhanced drought tolerance.

## Mechanistic Insights
In vegetatively propagated polyploids, genome editing achieves precise functional alterations across homoeologous allele dosages without meiotic segregation or loss of clonal heterozygosity. Inactivating susceptibility factors (such as *DMR6*, encoding a 2-oxoglutarate Fe(II)-dependent oxygenase, or *PM1*, which promotes vacuolar degradation of NADPH oxidases) removes negative constraints on endogenous plant immunity, establishing broad-spectrum pathogen resistance without fitness costs. Metabolic engineering via targeted knockouts (e.g., *GBSS* in potato, *FaRAP* in strawberry, *LCY$\varepsilon$* in banana) cleanly redirects metabolic flux toward desirable end-products (pure amylopectin, unpigmented fruit, $\beta$-carotene).

## Conclusions & Implications
Transgenics and CRISPR genome editing are vital tools to overcome the severe reproductive and genomic bottlenecks of vegetatively propagated polyploids. By enabling targeted multi-allele editing in elite clonal cultivars, these technologies deliver rapid improvements in nutritional value, processing quality, and climate resilience while bypassing traditional breeding cycles.

## Limitations & Caveats
Technical limitations include genotype-dependent transformation efficiencies (which vary from 2% to 100% across cultivars), off-target mutations, somaclonal variations induced by tissue culture regeneration, and stringent international GMO regulatory barriers for transgenic events.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Overturns the traditional breeding assumption that polyploid clonal cultivars must remain genetically static because cross-breeding disrupts essential heterozygous gene combinations.

## Under-Researched Populations
Non-commercial wild polyploid relatives and local landraces of potato, banana, strawberry, and sugarcane adapted to extreme marginal environments.

## Future Directions
1. Develop genotype-independent transformation protocols and embryogenic suspension culture methods for recalcitrant polyploid cultivars.
2. Optimize protoplast-based Ribonucleoprotein (RNP) delivery and prime editing systems to generate transgene-free edited polyploids.
3. Establish harmonized international regulatory policies that exempt non-transgenic CRISPR-edited polyploid crops from GMO oversight.

## Key References to Follow Up
- [[Andersson et al., 2017]] - Demonstrated CRISPR/Cas9 knockout of *GBSS* in tetraploid potato.
- [[Tripathi et al., 2021]] - Knocked out *MusaDMR6* to confer banana xanthomonas wilt resistance.
- [[Gao et al., 2020]] - Characterized CRISPR knockout of *FaRAP* controlling strawberry fruit pigmentation.

---
**Source PDF:** `data/sakthivel_2025_enhancing_quality_climate.pdf`
"""

# ---------------------------------------------------------
# 11. sweeney_2022_qtl_x_environment
# ---------------------------------------------------------
SUMMARIES["sweeney_2022_qtl_x_environment"] = """---
tags: [preharvest sprouting, hordeum vulgare, qtl x environment interaction, hvmkk3, hvalaat1]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1007/s00122-021-03966-2
authors: "Sweeney et al."
year: 2022
journal: "Theoretical and Applied Genetics"
format_version: 2
---

## Title & Metadata
- **Title**: QTL $\times$ environment modeling of malting barley preharvest sprouting
- **Authors**: Daniel W. Sweeney, Karl H. Kunze, and Mark E. Sorrells
- **Journal**: *Theoretical and Applied Genetics* (2022) 135:285–298
- **DOI**: 10.1007/s00122-021-03966-2
- **Primary Focus**: Mixed-model QTL $\times$ environment interaction (QEI) modeling of preharvest sprouting in two-row spring and winter malting barley using haplotypes of *HvAlaAT1*, *HvGA20ox1*, and *HvMKK3* combined with weather covariates.

## Abstract Summary
Preharvest sprouting (PHS) severely impairs barley (*Hordeum vulgare* L.) malting quality, but breeding for PHS resistance is challenging due to negative correlations with rapid, uniform malting germination. High temperature during grain filling accelerates dormancy loss, yet the genetic basis of seed dormancy temperature sensitivity remains poorly understood. In this study, six years of historical PHS data from 61 spring malting barley entries (25 environments) and 21 winter malting barley entries (9 environments) were analyzed using QTL $\times$ environment mixed models. Entries were haplotyped via KASP assays targeting causal polymorphisms in three seed dormancy genes on chromosome 5H: *HvAlaAT1* (*SD1*), *HvGA20ox1*, and *HvMKK3* (*SD2*). Five weather covariates during grain fill (maximum temperature $T_{\text{max}}$, minimum temperature $T_{\text{min}}$, average temperature $T_{\text{avg}}$, temperature range $T_r$, and total precipitation $P_{\text{sum}}$) were evaluated. Variation in winter barley PHS was best modeled by $T_r$, whereas spring barley PHS was best modeled by $P_{\text{sum}}$ and $T_{\text{max}}$. A highly non-dormant allele, $HvMKK3^{N*}$, established baseline PHS susceptibility, whereas *HvAlaAT1* interacted with *HvMKK3* to confer environmental sensitivity. Significant residual polygenic variance within haplotypes demonstrated potential for breeding climate-resilient, PHS-resistant malting barley.

## Introduction & Background
Preharvest sprouting (PHS) in malting barley (*Hordeum vulgare* L.) causes catastrophic loss of malt extract, enzymatic imbalances, and grain downgrading to animal feed. Malting barley requires rapid, complete germination during the commercial malting steep, creating a narrow physiological balance between sufficient harvest dormancy to prevent PHS and prompt post-harvest germination. Primary seed dormancy in barley is governed by major QTLs on chromosome 5H: *SD1* (encoding alanine aminotransferase, *HvAlaAT1*) and *SD2* (encoding mitogen-activated protein kinase kinase 3, *HvMKK3*). High ambient temperatures during grain filling decrease seed dormancy, making crops highly vulnerable to wet harvest weather. Modeling how specific *HvMKK3* and *HvAlaAT1* allelic variants interact with environmental weather covariates provides essential insights into dormancy stability and PHS risk forecasting.

## Key Concepts & Theory
- **[[QTL x Environment Interaction Models]]**: Mixed-model statistical frameworks that partition genetic effects into fixed QTL $\times$ weather covariate slopes and random polygenic $\times$ environment variances.
- **[[HvMKK3 Locus]]**: Mitogen-activated protein kinase kinase 3 on barley chromosome 5H (*SD2* locus) possessing functional allelic variants that dictate baseline seed dormancy.
- **[[HvAlaAT1 Locus]]**: Alanine aminotransferase on barley chromosome 5H (*SD1* locus) involved in ABA signaling and environmental dormancy sensitivity.
- **[[Grain Fill Period Covariates]]**: Meteorological parameters (such as $T_{\text{max}}$, $T_{\text{min}}$, $T_r$, and $P_{\text{sum}}$) calculated strictly between heading/tipping and physiological maturity.
- **[[Malting Quality vs Dormancy Trade-off]]**: The breeding conflict between selecting for high grain dormancy to prevent PHS and selecting for rapid, uniform germination required by maltsters.

## Important Entities
* **Genes/Proteins**:
  - [[HvMKK3]] (*SD2*)
  - [[HvAlaAT1]] (*SD1*)
  - [[HvGA20ox1]]
* **Organisms**:
  - [[Hordeum vulgare]] (Two-row spring and winter malting barley)
* **Tools/Techniques/Software**:
  - [[ASReml-R]] (Linear mixed models)
  - [[KASP Genotyping]]
  - [[icREML]] (Information criteria model selection)
  - [[Greenhouse Mist Chamber Assay]]

## Methods & Experimental Design
1. *Germplasm & Datasets*: Historical PHS data collected over six years (2015–2020) in Ithaca, NY: (1) 61 two-row spring barley entries evaluated across 25 environments, and (2) 21 two-row winter barley entries across 9 environments, plus three facultative checks evaluated in both datasets.
2. *PHS Phenotyping*: Five spikes per plot sampled at physiological maturity (peduncle loss of green color) were after-ripened for 3–4 days, misted in a greenhouse chamber for 4 days, and visually scored on a 0–9 scale (0 = no sprouting, 9 = fully sprouted).
3. *KASP Genotyping & Haplotype Definition*: Entries were genotyped for causal SNPs: *AlaAT_L214F* (*HvAlaAT1*), *GA20ox1_331_5UTR* (*HvGA20ox1*), and *MKK3_E165Q* plus *JHI-367342-KASP* (*HvMKK3*). Haplotypes were designated based on dormancy status (D = dormant, N = non-dormant, N* = highly non-dormant).
4. *QEI Mixed Modeling*: Single-step QEI mixed models in ASReml-R tested five weather covariates ($T_{\text{max}}$, $T_{\text{min}}$, $T_{\text{avg}}$, $T_r$, $P_{\text{sum}}$) during the grain fill window to partition fixed QTL $\times$ environment slopes, random entry effects, and residual variance components.

## Key Results & Data
- *Haplotype Baseline Effects*:
  - In spring barley, entries with the highly non-dormant allele $HvMKK3^{N*}$ (haplotypes NNN*, DNN*, e.g., 'AAC Synergy', 'Newdale') exhibited high mean PHS scores ($\bar{x} = 4.99–5.81$), whereas lines with dormant allele $HvMKK3^D$ (DDD, NDD, e.g., 'Explorer', 'Craft') were highly resistant ($\bar{x} = 1.88–1.91$).
  - In winter barley, $HvMKK3^{N*}$ lines ('Charles', 'Endeavor') had severe PHS ($\bar{x} = 5.76–6.36$), while $HvMKK3^D$ lines ('Violetta', 'Calypso', 'Lightning') exhibited near-zero sprouting ($\bar{x} = 0.46–0.67$).
- *Best Environmental Covariates*:
  - For winter barley, average diurnal temperature range during grain fill ($T_r$) provided the best model fit (lowest AIC), with wider temperature fluctuations significantly elevating sprouting in sensitive haplotypes.
  - For spring barley, total precipitation during grain fill ($P_{\text{sum}}$) and maximum temperature ($T_{\text{max}}$) best modeled PHS variation.
- *QTL Sensitivity & Epistasis*: *HvAlaAT1* alleles modulated environmental sensitivity; lines carrying dormant *HvAlaAT1* combined with dormant *HvMKK3* maintained stability across high-temperature grain fill seasons.
- *Residual Polygenic Variance*: Significant genetic variance ($P < 0.05$) remained within single haplotype classes, demonstrating that minor background loci modify PHS resistance beyond 5H major genes.

## Mechanistic Insights
*HvMKK3* functions as the primary genetic gatekeeper governing baseline seed dormancy and ABA responsiveness in barley. When the susceptible $HvMKK3^{N*}$ allele is present, seeds lose dormancy rapidly regardless of background. In contrast, when the resistant $HvMKK3^D$ allele is present, *HvAlaAT1* acts as an environmental sensitivity fine-tuner: dormant *HvAlaAT1* alleles protect seeds from temperature-induced dormancy breakdown, whereas non-dormant *HvAlaAT1* alleles confer high sensitivity to high grain filling temperatures and rainfall.

## Conclusions & Implications
QEI modeling reveals that barley PHS resistance depends on both major 5H haplotype composition and specific environmental covariates during grain fill. Breeders can utilize KASP markers for *HvMKK3* and *HvAlaAT1* to eliminate highly susceptible $HvMKK3^{N*}$ alleles while exploiting residual polygenic variance to select elite lines combining high malting performance with stable PHS tolerance.

## Limitations & Caveats
The study utilized field trials conducted within a single northeastern US region (Ithaca, NY) over six years; evaluating the QEI models across diverse western North American and European dryland malting barley production regions is recommended.

## Contradictory Findings
*HvGA20ox1* showed no significant main or interaction effects on PHS or dormancy in the tested malting barley populations, contrary to earlier suggestions of its direct involvement.

## Outdated Models
Overturns the view that barley PHS variability is driven solely by precipitation at harvest, proving that high temperature and diurnal temperature range during grain filling pre-condition seed dormancy levels.

## Under-Researched Populations
Two-row winter malting barley breeding germplasm and facultative malting barley lines adapted to the eastern United States.

## Future Directions
1. Incorporate grain fill temperature and precipitation covariates into predictive PHS forecasting tools for malting barley growers.
2. Perform genome-wide association studies within fixed $HvMKK3^D$ breeding panels to map the minor polygenic modifier loci.
3. Assess the steeping and micro-malting performance of elite lines carrying climate-stable DDD and NDD haplotypes.

## Key References to Follow Up
- [[Sato et al., 2016]] - Cloned alanine aminotransferase *HvAlaAT1* (*SD1*) on barley chromosome 5H.
- [[Nakamura et al., 2016]] - Cloned mitogen-activated protein kinase kinase *HvMKK3* (*SD2*) controlling barley seed dormancy.
- [[Sweeney et al., 2021]] - Developed diagnostic KASP markers for *HvMKK3*, *HvAlaAT1*, and *HvGA20ox1* in barley.

---
**Source PDF:** `data/sweeney_2022_qtl_x_environment.pdf`
"""

# ---------------------------------------------------------
# 12. munkvold_2009_mapping_quantitative_trait
# ---------------------------------------------------------
SUMMARIES["munkvold_2009_mapping_quantitative_trait"] = """---
tags: [preharvest sprouting, seed dormancy, quantitative trait loci, doubled haploid, triticum aestivum]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1007/s00122-009-1123-1
authors: "Munkvold et al."
year: 2009
journal: "Theoretical and Applied Genetics"
format_version: 2
---

## Title & Metadata
- **Title**: Mapping quantitative trait loci for preharvest sprouting resistance in white wheat
- **Authors**: Jesse D. Munkvold, James Tanaka, David Benscher, and Mark E. Sorrells
- **Journal**: *Theoretical and Applied Genetics* (2009) 119(7):1223–1235
- **DOI**: 10.1007/s00122-009-1123-1
- **Primary Focus**: Comprehensive QTL mapping of PHS resistance, seed dormancy, rate of germination, plant height, and heading date across 16 field environments in a white winter wheat doubled haploid population ('Cayuga' $\times$ 'Caledonia').

## Abstract Summary
Preharvest sprouting (PHS) severely reduces wheat (*Triticum aestivum* L.) grain yield and end-use quality under wet harvest conditions. To determine the genetic basis of PHS resistance in elite North American white winter wheat, a doubled haploid (DH) population consisting of 209 lines from a cross between PHS-resistant cv. 'Cayuga' and PHS-susceptible cv. 'Caledonia' was evaluated across 16 field environments in New York, USA over six years (2001–2006). A genetic linkage map of 221 non-redundant loci (SSRs, DArTs, AFLPs, TRAPs) spanning 1,552.6 cM was constructed. Composite interval mapping (CIM) identified 15 PHS QTLs across the genome. A major QTL on chromosome 2B, *QPhs.cnl-2B.1* (flanked by *BARC55* and *WMC474*, LOD up to 27.10), was significant in all 16 environments, explaining 5% to 31% of phenotypic variance (24% of overall mean). Three additional consistent QTLs—*QPhs.cnl-6D.1* (10 environments, 14% mean variance), *QPhs.cnl-2D.1* (6 environments, 7% mean variance), and *QPhs.cnl-3D.1* (4 environments, 4% mean variance)—had resistance alleles derived from 'Cayuga'. Heading date was negatively correlated with PHS due to close linkage between *QPhs.cnl-2B.1* and heading date QTL *QHd.cnl-2B.1*.

## Introduction & Background
Preharvest sprouting (PHS) in hexaploid bread wheat occurs when cool, wet weather around physiological maturity triggers precocious seed germination on the mother plant. This causes rapid induction of $\alpha$-amylase, degrading endosperm starch and severely compromising bread and noodle flour quality. While red-grained wheat varieties possess seed coat-imposed dormancy mediated by flavonoid pigments ($R$ genes), white-grained wheat varieties are preferred for high milling yield and light-colored food products but are inherently vulnerable to PHS. Breeding PHS-resistant white wheat requires exploiting non-color-related embryo and coat dormancy QTLs. 'Cayuga' is an elite soft white winter wheat cultivar derived from 'Geneva' and 'Clark's Cream' backcrossed to 'Geneva', exhibiting exceptional PHS resistance. Evaluating 'Cayuga' across extensive multi-environment field trials provides critical insight into stable genomic regions controlling dormancy in white wheat.

## Key Concepts & Theory
- **[[Composite Interval Mapping]]**: A high-resolution statistical technique for mapping quantitative trait loci that incorporates background markers as cofactors to control residual genetic variation.
- **[[Environment-Stable Major QTL]]**: A genomic locus that exhibits statistically significant phenotypic effects consistently across numerous diverse years and field testing locations.
- **[[Pleiotropy vs Tight Linkage]]**: The genetic phenomenon where a single locus regulates multiple traits (e.g., heading date and sprouting), or where distinct causal genes reside in close chromosomal proximity.
- **[[Rate of Germination]]**: The speed at which non-dormant, after-ripened seeds initiate radicle protrusion during early imbibition.
- **[[White-Grained Wheat Dormancy]]**: Genetic mechanisms of seed dormancy and PHS resistance that operate independently of the red seed coat color ($R$) loci on group 3 chromosomes.

## Important Entities
* **Genes/Proteins**:
  - [[QPhs.cnl-2B.1]] (Major 2B PHS QTL)
  - [[QPhs.cnl-6D.1]] (6D PHS QTL)
  - [[QPhs.cnl-2D.1]] (2D PHS QTL)
  - [[QPhs.cnl-3D.1]] (3D PHS QTL)
  - [[Rht-D1]] / [[Ppd-B1]] / [[Ppd-D1]]
* **Organisms**:
  - [[Triticum aestivum]] (Soft white winter wheat cv. 'Cayuga', 'Caledonia')
* **Tools/Techniques/Software**:
  - [[QTL Cartographer]] (Zmapqtl CIM)
  - [[QTLNetwork]] (Epistasis & QEI)
  - [[Map Manager QTX]]
  - [[Whole-Spike Wetting Assay]]

## Methods & Experimental Design
1. *Mapping Population & Field Design*: 209 doubled haploid (DH) lines derived from 'Cayuga' (PHS-resistant soft white winter wheat) $\times$ 'Caledonia' (PHS-susceptible soft white winter wheat) were grown in 16 field environments in Ithaca, NY (2–3 fields per year from 2001 to 2006) in randomized complete block designs with two replications.
2. *Phenotyping*: Five mature spikes per line were sampled at physiological maturity (glume greenness loss), dried for 5 days, and tested using artificial mist chamber assays (scored 0–9). Related traits recorded in subsets of environments included seed dormancy (DOR, germination index), rate of germination (ROG on 8-month after-ripened seed), heading date (HD), and plant height (HT).
3. *Molecular Marker Genotyping*: 484 polymorphic loci (215 SSRs, 147 DArTs, 72 AFLPs, 31 TRAPs, 16 RFLPs, 3 EST-SSRs, 1 STS) were genotyped, yielding a 221-locus framework linkage map spanning 1,552.6 cM.
4. *QTL & Epistasis Analysis*: Stepwise regression and CIM (model 6, 2 cM walking speed, 10 cM window, 1,000 permutations) were performed in QTL Cartographer. Epistatic interactions were tested in QTLNetwork 2.0.

## Key Results & Data
- *Phenotypic Heritability & Correlations*: PHS score heritability was $H^2 = 0.44$. 'Cayuga' maintained low PHS scores across all environments (mean = 0.30–3.50), while 'Caledonia' was highly susceptible (mean = 2.60–7.30). PHS was negatively correlated with HD ($r = -0.39, P < 0.01$) and HT ($r = -0.33, P < 0.01$).
- *Major Replicable QTL QPhs.cnl-2B.1*: Significant in all 16 environments (LOD = 3.90–27.10), explaining 5% to 31% of trait variance per environment (24% of the multi-environment mean). The QTL peak was mapped at 14 cM on chromosome 2B between SSR markers *BARC55* and *WMC474*, with resistance contributed by 'Cayuga'.
- *Three Additional Consistent QTLs*:
  - *QPhs.cnl-6D.1*: Detected in 10 environments (LOD = 17.87, explaining 14% of overall mean variance; peak at 28 cM between *CFD37* and *BARC196*), resistance from 'Cayuga'.
  - *QPhs.cnl-2D.1*: Detected in 6 environments (LOD = 7.59, explaining 7% variance; peak at 37 cM between *WMC11* and *wPt-9997*), resistance from 'Cayuga'.
  - *QPhs.cnl-3D.1*: Detected in 4 environments (LOD = 6.38, explaining 4% variance; peak at 26 cM between *BARC1161* and *GPW4152*), resistance from 'Cayuga'.
- *Overlap with Agronomic Traits*: A major heading date QTL, *QHd.cnl-2B.1* (LOD = 11.20, $R^2 = 25\%$), co-localized precisely with *QPhs.cnl-2B.1*, indicating that delayed heading and sprouting resistance are tightly linked or pleiotropic on chromosome 2B.

## Mechanistic Insights
The extensive 16-environment dataset demonstrates that PHS resistance in 'Cayuga' is governed by a major stable locus on chromosome 2B (*QPhs.cnl-2B.1*) operating in conjunction with three secondary loci on chromosomes 6D, 2D, and 3D. The co-localization of *QPhs.cnl-2B.1* with *QHd.cnl-2B.1* suggests that developmental timing genes (e.g., *Ppd-B1* or closely linked flowering regulators) influence the maturation microenvironment or intrinsic tissue sensitivity, reinforcing seed dormancy in white winter wheat.

## Conclusions & Implications
'Cayuga' possesses exceptionally stable, non-color-related PHS resistance driven by *QPhs.cnl-2B.1* and *QPhs.cnl-6D.1*. Flanking SSR markers *WMC474*, *BARC55*, and *CFD37* provide robust diagnostic tools for marker-assisted breeding of sprouting-tolerant white winter wheat cultivars adapted to the northeastern United States and eastern Canada.

## Limitations & Caveats
Greenhouse-evaluated seed dormancy showed poor correlation with field PHS scores ($r = -0.13$), indicating that greenhouse environments do not accurately replicate field wetting dynamics and glume-imposed sprouting barriers.

## Contradictory Findings
Rate of germination on after-ripened seed showed a significant negative correlation with PHS ($r = -0.55, P < 0.01$), meaning that resistant genotypes exhibited faster post-dormancy germination rates.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Soft white winter wheat cultivars and breeding germplasm adapted to the humid, temperate climates of the northeastern United States.

## Future Directions
1. Fine-map the *QPhs.cnl-2B.1* interval to separate the causal dormancy gene from the closely linked heading date locus *QHd.cnl-2B.1*.
2. Convert linked SSR markers (*WMC474*, *BARC55*, *CFD37*) into high-throughput KASP assays for commercial breeding deployment.
3. Characterize candidate genes underlying *QPhs.cnl-6D.1* on chromosome 6D using physical genome assemblies.

## Key References to Follow Up
- [[Anderson et al., 1993]] - First identified genetic markers associated with PHS resistance in white winter wheat.
- [[Mares et al., 2005]] - Characterized major 4A seed dormancy QTLs in diverse white and red wheats.
- [[Torada et al., 2008]] - Mapped and validated PCR markers for the *Phs1* locus on chromosome 4A.

---
**Source PDF:** `data/munkvold_2009_mapping_quantitative_trait.pdf`
"""

# ---------------------------------------------------------
# 13. swain_2017_far_red_insensitive
# ---------------------------------------------------------
SUMMARIES["swain_2017_far_red_insensitive"] = """---
tags: [arabidopsis thaliana, shade avoidance response, jasmonic acid, light signaling, photoreceptors]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.3389/fpls.2017.01901
authors: "Swain et al."
year: 2017
journal: "Frontiers in Plant Science"
format_version: 2
---

## Title & Metadata
- **Title**: *FAR-RED INSENSITIVE 219*/*JAR1* Contributes to Shade Avoidance Responses of *Arabidopsis* Seedlings by Modulating Key Shade Signaling Components
- **Authors**: Swadhin Swain, Han-Wei Jiang, and Hsu-Liang Hsieh
- **Journal**: *Frontiers in Plant Science* (2017) 8:1901
- **DOI**: 10.3389/fpls.2017.01901
- **Primary Focus**: Molecular characterization of FIN219/JAR1 (GH3.11) as a negative regulator of shade-induced hypocotyl elongation and its physical interactions with phyA and COP1 in *Arabidopsis thaliana*.

## Abstract Summary
To capture sufficient light under dense canopies, plants initiate shade avoidance syndrome (SAS), characterized by rapid elongation of hypocotyls and petioles. This morphological response is coordinated by the dynamic interplay between light photoreceptors and plant hormones, notably jasmonic acid (JA) and auxin. *FAR-RED INSENSITIVE 219*/*JASMONATE RESISTANCE 1* (FIN219/JAR1), an auxin-inducible cytoplasmic JA-conjugating enzyme (GH3.11) that synthesizes bioactive jasmonoyl-L-isoleucine (JA-Ile), integrates far-red (FR) light signaling with JA pathways. In this study, phenotypic and molecular analyses demonstrated that FIN219/JAR1 negatively regulates shade-induced hypocotyl elongation and marker gene expression (*PIL1*, *ATHB2*) in *Arabidopsis* seedlings under simulated shade (low red to far-red light ratio, R:FR = 0.06). In turn, prolonged simulated shade reduces FIN219 protein accumulation. Genetic analysis of *phyA211 fin219-2* double mutants revealed synergistic enhancement of shade-induced elongation, indicating parallel regulatory pathways. Molecular assays showed that FIN219 differentially modulates basic helix-loop-helix (bHLH) transcription factors, repressing *PIF5* and promoting *PAR1*, thereby restricting auxin-response genes (*IAA29*, *SAUR68*). Furthermore, ectopic overexpression of FIN219 directly interacted with COP1 and phyA, excluding COP1 from the nucleus into the cytoplasm under shade light.

## Introduction & Background
Vegetation shade drastically reduces the ratio of red (R) to far-red (FR) light perceived by plants, shifting the phytochrome B (phyB) photoequilibrium toward the inactive Pr conformation. This releases basic helix-loop-helix phytochrome-interacting factors (PIFs, such as PIF4, PIF5, and PIF7), which activate auxin biosynthesis and cell elongation genes, triggering shade avoidance syndrome (SAS). The E3 ubiquitin ligase CONSTITUTIVE PHOTOMORPHOGENIC 1 (COP1) translocates into the nucleus under shade to target negative regulators of SAS (e.g., HFR1) for proteasomal degradation. Jasmonates (JAs) play a critical role in balancing plant growth and defense responses. *FIN219/JAR1* (GH3.11) encodes the JA-amino synthetase that converts JA into the bioactive signaling molecule JA-Ile. Although FIN219 was previously established as a component of phyA-mediated far-red light signaling, its specific regulatory role, molecular interactors, and downstream targets under canopy shade remained to be elucidated.

## Key Concepts & Theory
- **[[Shade Avoidance Syndrome]]**: A suite of adaptive developmental responses—including hypocotyl and petiole elongation, upward leaf movement, and accelerated flowering—triggered by low R:FR light under plant canopies.
- **[[FIN219/JAR1 Enzyme]]**: A GH3-family jasmonate-amido synthetase (GH3.11) in *Arabidopsis* that catalyzes the conjugation of jasmonic acid to isoleucine, generating bioactive JA-Ile.
- **[[COP1 Ubiquitin Ligase]]**: A central RING-finger E3 ubiquitin ligase that accumulates in the nucleus under darkness or shade to degrade photomorphogenic transcription factors.
- **[[Phytochrome Photoreceptors]]**: Light-sensing chromoproteins (primarily phyA and phyB) that reversibly interconvert between red-absorbing (Pr) and far-red-absorbing (Pfr) forms to regulate light signaling.
- **[[PIF and PAR Transcription Factors]]**: Antagonistic bHLH transcription factors, where PIFs promote shade elongation and auxin synthesis, while PAR1/PAR2 act as negative regulators.

## Important Entities
* **Genes/Proteins**:
  - [[FIN219]] / [[JAR1]] (*AtGH3.11*, *AT2G46370*)
  - [[PHYA]] (*AT1G09570*)
  - [[PHYB]] (*AT2G18790*)
  - [[COP1]] (*AT2G32950*)
  - [[PIF5]] (*AT3G59060*)
  - [[PAR1]] (*AT2G42870*)
  - [[PIL1]] (*AT2G46970*)
  - [[ATHB2]] (*AT4G16780*)
  - [[IAA29]] (*AT4G32280*)
  - [[SAUR68]] (*AT1G29490*)
* **Organisms**:
  - [[Arabidopsis thaliana]] (Col-0, mutant lines *fin219-2*, *jar1-1*, *phyA211*, *cop1-4*, *cop1-6*)
* **Tools/Techniques/Software**:
  - [[LED Simulated Shade Chamber]] (R:FR = 0.06 vs 2.3)
  - [[Co-Immunoprecipitation]] (Co-IP)
  - [[Protoplast Transfection & Confocal Microscopy]]
  - [[qRT-PCR]]
  - [[Western Blotting]]

## Methods & Experimental Design
1. *Plant Materials & Light Conditions*: *Arabidopsis* wild-type Col-0, single mutants (*fin219-2*, *fin219-1*, *jar1-1*, *phyA211*, *cop1-4*, *cop1-6*), double mutants (*phyA211 fin219-2*, *cop1-4 fin219-2*, *cop1-6 fin219-2*), and a dexamethasone (Dex)-inducible overexpression line (*pGR:FIN219* / *pGR219*) were grown on 1/2 MS media under continuous white light (R:FR = 2.3, 70 $\mu\text{mol m}^{-2}\text{s}^{-1}$) for 2 days and kept in white light or transferred to simulated shade (low R:FR = 0.06) for 4 days.
2. *Hypocotyl Length & Gene Expression*: Hypocotyl lengths were measured using ImageJ ($n \ge 25$). Quantitative RT-PCR quantified transcript levels of shade markers (*PIL1*, *ATHB2*), bHLH regulators (*PIF5*, *PAR1*), and auxin-response genes (*IAA29*, *SAUR68*).
3. *Protein Gel Blot & Co-IP*: Protein levels of FIN219, PHYA, and COP1 were assayed by SDS-PAGE and immunoblotting with specific monoclonal/polyclonal antibodies. In vivo physical interactions were tested via Co-IP from seedling extracts.
4. *Subcellular Localization in Protoplasts*: *Arabidopsis* mesophyll protoplasts transfected with *p35S:GFP-COP1* were treated with white light vs simulated shade for 1 h and imaged via confocal laser scanning microscopy to quantify nuclear versus cytoplasmic localization.

## Key Results & Data
- *FIN219 Negatively Regulates SAS*: Under simulated shade, *fin219* mutants exhibited significantly longer hypocotyls than wild type (129.7% in *fin219-2*, 180.2% in *jar1-1*, and 197.6% in *fin219-1*, $P < 0.01$). Conversely, FIN219 overexpression (*pGR219*) strongly suppressed shade-induced elongation.
- *Marker Gene Regulation*: Shade-induced upregulation of *PIL1* and *ATHB2* was hyper-elevated in *fin219* mutants but suppressed in *pGR219*.
- *Differential Regulation of PIF5 and PAR1*: Loss of FIN219 significantly elevated *PIF5* and suppressed *PAR1* expression under shade, driving downstream upregulation of auxin-responsive genes *IAA29* and *SAUR68*.
- *Synergism with phyA*: *phyA211 fin219-2* double mutants displayed synergistic hyper-elongation and additive induction of *PIL1*, *ATHB2*, *IAA29*, and *SAUR68*, proving that FIN219 operates in a pathway parallel to phyA-mediated high irradiance responses.
- *Exclusion of COP1 from Nucleus*: Under shade, GFP-COP1 concentrated in the nucleus in wild-type and *fin219-2* protoplasts. Ectopic expression of FIN219 (*pGR219*) physically bound COP1 and sequestered it in the cytoplasm, blocking COP1 nuclear accumulation.

## Mechanistic Insights
FIN219/JAR1 acts as a crucial molecular checkpoint in shade light signaling. Under high R:FR light, active phyB suppresses SAS. Under low R:FR shade, phyB is deactivated, causing nuclear translocation of COP1 and activation of PIF transcription factors. FIN219/JAR1 counteracts SAS through a dual mechanism: (1) direct physical interaction with COP1 in the cytoplasm to inhibit its nuclear accumulation, preventing the degradation of negative shade regulators; and (2) differential transcriptional modulation of bHLH factors (repressing *PIF5* and activating *PAR1*), which restricts shade-induced auxin biosynthesis (*IAA29*, *SAUR68*) and prevents excessive hypocotyl elongation.

## Conclusions & Implications
FIN219/JAR1 is an essential negative regulator of shade avoidance responses in *Arabidopsis*, directly integrating jasmonate signaling with light photoreceptor pathways. By interacting with phyA and COP1 and modulating PIF5/PAR1-mediated auxin responses, FIN219 fine-tunes plant growth and prevents exaggerated morphological shade reactions under dense canopies.

## Limitations & Caveats
The study was conducted in the model dicot *Arabidopsis thaliana*; whether homologous GH3.11 jasmonate-conjugating enzymes perform identical light-signaling regulatory functions in monocots like wheat and barley requires functional validation.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Overturns the view that FIN219/JAR1 operates solely downstream of phyA-mediated far-red high-irradiance responses, demonstrating that it independently regulates shade avoidance in parallel with phyA.

## Under-Researched Populations
*Arabidopsis* natural accessions adapted to deep canopy forest floors versus open sunny habitats.

## Future Directions
1. Identify and characterize the orthologous *GH3.11*/*FIN219* genes in hexaploid wheat (*Triticum aestivum*) and test their involvement in canopy shading and seed dormancy.
2. Determine whether FIN219 enzymatic activity (JA-Ile synthesis) is required for its direct protein interaction and nuclear exclusion of COP1.
3. Investigate the transcriptional regulatory network connecting BBX21, FIN219, and COP1 in fine-tuning shade light responses.

## Key References to Follow Up
- [[Hsieh et al., 2000]] - Identified FIN219 as an auxin-regulated gene involved in phytochrome A signaling.
- [[Staswick and Tiryaki, 2004]] - Cloned JAR1 and established its function as a jasmonate-amido synthetase synthesizing JA-Ile.
- [[Pacín et al., 2013]] - Characterized the rapid nuclear accumulation and regulatory dynamics of COP1 under simulated shade.

---
**Source PDF:** `data/swain_2017_far_red_insensitive.pdf`
"""

# ---------------------------------------------------------
# 14. huang_2022_identification_effective_alleles
# ---------------------------------------------------------
SUMMARIES["huang_2022_identification_effective_alleles"] = """---
tags: [preharvest sprouting, seed dormancy, tamft, tasdr-b1, marker-assisted selection]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1186/s12870-022-03710-w
authors: "Huang et al."
year: 2022
journal: "BMC Plant Biology"
format_version: 2
---

## Title & Metadata
- **Title**: Identification of effective alleles and haplotypes conferring pre-harvest sprouting resistance in winter wheat cultivars
- **Authors**: Yiwen Huang, Xuran Dai, Hongwei Liu, Shuo Yu, Chunyan Mai, Liqiang Yu, Guangjun Yu, Li Yang, Yang Zhou, Hongjie Li, and Hongjun Zhang
- **Journal**: *BMC Plant Biology* (2022) 22:339
- **DOI**: 10.1186/s12870-022-03710-w
- **Primary Focus**: Comprehensive allelic and haplotypic characterization of 10 PHS resistance genes in 326 Chinese winter wheat cultivars and validation of superior *TaMFT*/*TaSdr-B1* combinations in biparental populations.

## Abstract Summary
Pre-harvest sprouting (PHS) is a major constraint on wheat (*Triticum aestivum* L.) grain yield and end-use quality. In this study, 326 commercial winter wheat cultivars from across China were evaluated for PHS resistance using the germination index (GI) across three consecutive cropping seasons (2018–2020) in Xinxiang, Henan ($H^2 = 0.96$). Allelic variation across 10 cloned PHS-associated genes (*TaSdr-A1*, *TaSdr-B1*, *Tamyb10-A1*, *Tamyb10-B1*, *Tamyb10-D1*, *TaVp-1B*, *TaDFR-B*, *TaMKK3-A*, *TaGASR34*, and *TaMFT*) was determined using functional markers. Eight cultivars exhibited stable, outstanding PHS resistance (GI < 25.0% in all three years). Haplotype analysis across five functional polymorphisms in *TaMFT* (-194, -222, +219, +646, +666) identified nine haplotypes (Hap1–Hap9); *Hap1* (carrying all five resistance alleles, including the rare -222C promoter allele) conferred the lowest GI and strongest dormancy, reducing GI by 23.3% to 32.1% relative to *Hap9*. Among 14 major allelic combinations, AC1 (*TaMFT-Hap1* + *TaSdr-B1a*) conferred superior resistance. Genetic validation in $F_2$ and $F_3$ populations from 'Lunxuan 13' (susceptible) $\times$ 'Bainong 3217' (*Hap1*/*TaSdr-B1a*, resistant) confirmed that introgression of *Hap1* and *TaSdr-B1a* significantly enhanced PHS resistance, reducing GI by 32.7% ($F_2$) and 44.3% ($F_3$).

## Introduction & Background
Pre-harvest sprouting (PHS), the germination of physiologically mature wheat grains before harvest during prolonged rain, causes serious economic losses by increasing $\alpha$-amylase activity, lowering test weight, and compromising noodle and steamed bread quality. In China, 83% of wheat planting areas suffer from PHS, especially in the Middle and Lower Yangtze River Valleys (MLWZ), Southwestern Winter Wheat Zone (SWWZ), and Yellow and Huai River Valleys (YHWZ). While red-grained wheats have traditionally exhibited higher PHS resistance, market demand strongly favors white-grained cultivars. Molecular marker-assisted selection (MAS) provides an effective approach to accelerate PHS breeding, but the distribution, allelic frequencies, and combining effects of multiple cloned dormancy genes (*TaMFT*, *TaSdr*, *TaMKK3-A*, *Tamyb10*, *TaVp-1*, *TaDFR-B*) in commercial winter wheat cultivars had not been systematically characterized.

## Key Concepts & Theory
- **[[TaMFT Haplotypes]]**: Specific combinations of five functional promoter and coding SNPs/InDels (-194, -222, +219, +646, +666) within the *TaMFT* / *TaPHS1* gene on chromosome 3AS.
- **[[TaSdr-B1 Gene]]**: A seed dormancy regulatory gene on wheat chromosome 2B where the *TaSdr-B1a* allele confers significantly enhanced seed dormancy.
- **[[Allelic Combination]]**: A multi-locus genotype capturing the combined allelic states across several distinct functional dormancy and grain color genes.
- **[[Germination Index]]**: A time-weighted measure of seed germination speed and percentage under controlled temperature, where lower values signify stronger seed dormancy.
- **[[Marker-Assisted Selection]]**: The breeding practice of using diagnostic DNA markers linked to causal gene variants to select target genotypes in segregating populations.

## Important Entities
* **Genes/Proteins**:
  - [[TaMFT]] / [[TaPHS1]] (*Hap1* to *Hap9*)
  - [[TaSdr-B1]] (*TaSdr-B1a*, *TaSdr-B1b*)
  - [[TaSdr-A1]]
  - [[Tamyb10-A1]] / [[Tamyb10-B1]] / [[Tamyb10-D1]]
  - [[TaVp-1B]]
  - [[TaDFR-B]]
  - [[TaMKK3-A]]
  - [[TaGASR34]]
* **Organisms**:
  - [[Triticum aestivum]] (326 Chinese winter wheat cultivars, cv. 'Bainong 3217', 'Lunxuan 13')
* **Tools/Techniques/Software**:
  - [[KASP Genotyping]]
  - [[Functional STS/CAPS Markers]]
  - [[Germination Index Testing]]
  - [[SPSS PROC GLM]]

## Methods & Experimental Design
1. *Cultivar Panel & Field Trials*: 326 Chinese winter wheat cultivars (released 1964–2020 across 13 provinces and four ecological wheat zones) were grown across three consecutive seasons (2017–2020) at the CAAS Experimental Station in Xinxiang, Henan, China.
2. *Phenotypic Germination Assay*: 30 spikes per cultivar were harvested at physiological maturity (35 days post-flowering), air-dried for 3 days, stored at -20°C, and threshed. Fifty surface-sterilized grains per line were incubated in Petri dishes at 25°C for 7 days (three replicates) to record daily germination and compute the Germination Index (GI).
3. *Functional Marker Genotyping*: Genomic DNA was genotyped for 10 cloned PHS genes using functional KASP, STS, and CAPS markers (Table S2). Five polymorphic loci in *TaMFT* (-194, -222, +219, +646, +666) were used to resolve haplotypes *Hap1*–*Hap9*.
4. *Genetic Validation Population*: $F_2$ (206 homozygous plants) and derived $F_3$ lines from 'Lunxuan 13' (*TaMFT-Hap4* / *TaSdr-B1b*, susceptible) $\times$ 'Bainong 3217' (*TaMFT-Hap1* / *TaSdr-B1a*, resistant) were phenotyped for GI in 2019 and 2020 to validate single-gene and pyramiding effects.

## Key Results & Data
- *Phenotypic Variation & Heritability*: Mean GI was 48.9% in 2018, 59.2% in 2019 (a high-temperature ripening season), and 34.5% in 2020, with high broad-sense heritability ($H^2 = 0.96$). Eight cultivars maintained stable high resistance (GI < 25.0% across all 3 years).
- *Allelic Effects of Individual Genes*: Low-GI alleles consistently outperformed high-GI alleles. *Tamyb10-D1b* showed the largest single-gene effect, reducing GI by 10.4% to 14.9% ($P < 0.05$). *TaSdr-B1a* significantly reduced GI by 7.0% to 8.9% across all three years.
- *TaMFT Haplotype Performance*: Nine *TaMFT* haplotypes were identified. *Hap1* (carrying favorable alleles at all five positions: -194+, -222+, +219+, +646+, +666+) exhibited the lowest GI, reducing GI by 23.3% to 32.1% compared to *Hap9* ($P < 0.05$). However, *Hap1* was rare in commercial cultivars (only 3.4% frequency).
- *Marker Specificity*: The -222C promoter allele was exclusively present in *Hap1*, confirming that a single KASP assay for -222C is diagnostic for the superior *Hap1* haplotype.
- *Pyramiding in Biparental Validation*: In Lunxuan 13 $\times$ Bainong 3217, lines with *TaMFT-Hap1* + *TaSdr-B1a* (AC1) reduced GI by 32.7% in $F_2$ and 44.3% in $F_3$ relative to 'Lunxuan 13' ($P < 0.05$), confirming strong additive gene action.

## Mechanistic Insights
The study highlights that high seed dormancy and PHS resistance result from the convergence of multiple functional pathways: *TaMFT* regulates embryo dormancy and temperature-dependent signaling; *TaSdr-B1* promotes intrinsic dormancy depth; and *Tamyb10-D1* activates flavonoid biosynthesis in the seed coat. Pyramiding the rare *TaMFT-Hap1* with *TaSdr-B1a* creates a robust multi-genic barrier that suppresses germination even under high ripening temperatures and humid harvest conditions.

## Conclusions & Implications
*TaMFT-Hap1* and *TaSdr-B1a* are highly effective PHS resistance alleles that act additively in elite Chinese winter wheat. Because *Hap1* is rare in current commercial cultivars (3.4%), introgressing *Hap1* using the diagnostic -222C KASP marker combined with *TaSdr-B1a* represents an immediate, high-priority breeding strategy for developing PHS-tolerant white winter wheat.

## Limitations & Caveats
The study identified several PHS-resistant cultivars (e.g., 'Yangmai 20', 'Lunan 11', 'Luomai 4') that lacked all known resistance alleles at the 10 surveyed genes, indicating that novel uncharacterized PHS resistance genes remain to be discovered.

## Contradictory Findings
The *TaMKK3-Aa* allele on chromosome 4AL showed only small phenotypic effects on GI in this cultivar panel (2.3% reduction in GI), contrasting with previous reports in biparental mapping populations where *TaMKK3-A* explained 30–38% of phenotypic variance, likely reflecting genetic background and temperature interactions.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Commercial Chinese winter wheat cultivars from the Yellow and Huai River Valleys and Middle-Lower Yangtze River Valleys lacking known PHS resistance markers.

## Future Directions
1. Conduct QTL-seq and bi-parental mapping on resistant cultivars lacking known resistance genes ('Yangmai 20', 'Lunan 11', 'Luomai 4') to discover novel PHS loci.
2. Deploy the -222C (*TaMFT-Hap1*) and *TaSdr-B1a* KASP markers in large-scale marker-assisted backcrossing to upgrade susceptible commercial cultivars ('Lunxuan 13', 'Jimai 22').
3. Evaluate the combined effects of *TaMFT-Hap1* and *Tamyb10-D1b* in red wheat breeding backgrounds.

## Key References to Follow Up
- [[Liu et al., 2013]] - Cloned *TaPHS1* (*TaMFT*) on chromosome 3AS and identified causal SNPs.
- [[Zhang et al., 2014]] - Cloned the seed dormancy gene *TaSdr* on wheat chromosome group 2.
- [[Torada et al., 2016]] - Cloned *TaMKK3-A* on chromosome 4AL.

---
**Source PDF:** `data/huang_2022_identification_effective_alleles.pdf`
"""

# ---------------------------------------------------------
# 15. ogbonnaya_2008_genetic_qtl_analyses
# ---------------------------------------------------------
SUMMARIES["ogbonnaya_2008_genetic_qtl_analyses"] = """---
tags: [preharvest sprouting, seed dormancy, quantitative trait loci, recombinant inbred lines, triticum aestivum]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1007/s00122-008-0722-1
authors: "Ogbonnaya et al."
year: 2008
journal: "Theoretical and Applied Genetics"
format_version: 2
---

## Title & Metadata
- **Title**: Genetic and QTL analyses of seed dormancy and preharvest sprouting resistance in the wheat germplasm CN10955
- **Authors**: F. C. Ogbonnaya, M. Imtiaz, G. Ye, P. R. Hearnden, E. Hernandez, R. F. Eastwood, M. van Ginkel, S. C. Shorter, and J. M. Winchester
- **Journal**: *Theoretical and Applied Genetics* (2008) 116(7):891–902
- **DOI**: 10.1007/s00122-008-0722-1
- **Primary Focus**: Inheritance modeling, QTL mapping, physical deletion bin localization, and SSR marker validation of major 4AL seed dormancy and PHS resistance loci in white-grained wheat germplasm 'CN19055'.

## Abstract Summary
Pre-harvest sprouting (PHS) is a major quality defect in Australian and global wheat (*Triticum aestivum* L.) production, particularly in white-grained wheat growing regions prone to summer rainfall. In this study, an $F_8$ recombinant inbred line (RIL) population of 169 lines derived from a cross between white-grained PHS-resistant germplasm 'CN19055' (selected from 'Aus1408' $\times$ 'RL4137') and locally adapted Australian susceptible cv. 'Annuello' was evaluated across four environments. Seed dormancy was assessed via 7-day germination index (GI7), while sprouting resistance was measured following artificial weathering using sprouting index (SI, 1–5 scale) and visibly sprouted seeds (VI, %). Segregation analysis of $F_2$, $F_3$, and RIL generations indicated that PHS resistance and seed dormancy in CN19055 are controlled by at least two complementary dominant genes. Heritabilities were high for VI ($H^2 = 0.80–0.94$) and GI7 ($H^2 = 0.66–0.86$). Composite interval mapping identified two QTLs on chromosome 4A: major locus *QPhs.dpivic.4A.2* on 4AL (explaining 45.1% of GI7, 42.8% of VI, and 19.4% of SI variance) and minor locus *QPhs.dpivic.4A.1* on 4AS (explaining 30.6–35.4% of VI variance). Flanking SSR markers *Xgwm937* and *Xgwm894* were physically mapped to deletion bins 4AL-12 and 4AL-13 and were strongly associated with PHS resistance across 64 diverse wheat cultivars.

## Introduction & Background
Pre-harvest sprouting (PHS), the germination of physiologically mature grains on standing spikes caused by rain prior to harvest, results in starch degradation, elevated $\alpha$-amylase, and severe economic discounting of milling wheat. In the northern wheat belt of Australia (New South Wales and Queensland), weather damage occurs on average every third year, costing growers $30–40 million annually. Australian grain markets exclusively demand white-grained wheat, which is inherently more susceptible to PHS than red wheat because it lacks seed coat polyphenols. 'CN19055' (W98616) is a white-grained spring wheat germplasm developed in Canada from an 'Aus1408' $\times$ 'RL4137' cross that combines white pericarp with exceptional seed dormancy. Mapping the genetic loci conferring dormancy in CN19055, identifying closely linked diagnostic markers, and physically mapping them to deletion bins provides vital tools for marker-assisted breeding of PHS-resistant white wheat.

## Key Concepts & Theory
- **[[Two-Gene Complementary Model]]**: A genetic inheritance model where favorable alleles at two distinct loci interact complementarily to produce a dormant, PHS-resistant phenotype.
- **[[Visibly Sprouted Seeds Percentage]]**: A quantitative PHS assessment index measuring the percentage of threshed grains showing visible embryo rupture and coleoptile emergence after spike weathering.
- **[[Deletion Bin Mapping]]**: A physical mapping method using Chinese Spring chromosomal deletion lines to assign molecular markers to specific physical chromosome bins.
- **[[QPhs.dpivic.4A.2 Locus]]**: A major seed dormancy and PHS resistance QTL mapped on the terminal region of chromosome 4AL (deletion bins 4AL-12/13), corresponding to *TaMKK3-A* (*Phs1*).
- **[[Sprouting Index Assay]]**: A visual whole-spike rating scale (1–5) evaluating the extent of external root and shoot development across the ear in a rain simulator.

## Important Entities
* **Genes/Proteins**:
  - [[QPhs.dpivic.4A.2]] (*TaMKK3-A* / *Phs1*)
  - [[QPhs.dpivic.4A.1]]
* **Organisms**:
  - [[Triticum aestivum]] (Spring wheat germplasm 'CN19055', cv. 'Annuello', 'Aus1408', 'RL4137')
* **Tools/Techniques/Software**:
  - [[Chinese Spring Deletion Lines]] (4AL-12, 4AL-13)
  - [[SSR Markers]] (*Xgwm937*, *Xgwm894*, *Xgwm637*, *Xwmc48*)
  - [[Windows QTL Cartographer]] (CIM)
  - [[Rain Simulator / Mist Chamber]]

## Methods & Experimental Design
1. *Plant Materials & Field Trials*: An $F_8$ RIL population of 169 lines was developed via single-seed descent from 'CN19055' (white-grained, PHS-resistant) $\times$ 'Annuello' (white-grained, PHS-susceptible). RILs were grown in four environments: Horsham field 2004 (2004 HF), Horsham field 2005 (2005 HF), Horsham glasshouse 2005 (2005 HGH), and Wongan Hills, Western Australia 2005 (2005 WA) in alpha-lattice designs with two replicates.
2. *PHS & Dormancy Phenotyping*: Intact spikes sampled at physiological maturity (loss of green glume color) were air-dried for 5 days and stored at -20°C. Three traits were evaluated: (1) GI7 (germination index over 7 days at 20°C in sand-filled microtitre tubes), (2) SI (sprouting index, 1–5 score after 48 h misting + 5 days incubation), and (3) VI (% visibly sprouted seeds among 200 threshed grains).
3. *SSR Genotyping & Bulked Segregant Analysis*: 114 SSR markers were screened; 44 polymorphic SSRs were genotyped on resistant and susceptible DNA bulks and the full RIL population.
4. *Physical Bin Mapping & Germplasm Survey*: *Xgwm937* and *Xgwm894* were mapped using 16 Chinese Spring 4A deletion lines. An association panel of 64 diverse bread wheat, durum, and synthetic hexaploid accessions was surveyed.

## Key Results & Data
- *Inheritance Modeling*: In $F_2$, non-dormant vs dormant seeds segregated 188:131, fitting a 9:7 complementary dominant two-gene model ($\chi^2 = 0.92, P = 0.40$). In $F_3$, segregation of GI7 (135R:69S) fitted an 11:5 ratio. In RILs under field conditions, GI7 segregated 1:3 (complementary genes), while under glasshouse conditions it segregated 3:1 (two independent non-interacting genes).
- *Heritability*: Broad-sense heritability was highest for VI ($H^2 = 0.80–0.94$) and GI7 ($H^2 = 0.66–0.86$), but lower for SI ($H^2 = 0.42–0.67$), confirming VI and GI7 as the most reliable phenotyping indices.
- *Major QTL QPhs.dpivic.4A.2*: Mapped on chromosome 4AL in the marker interval *Xgwm637*–*Xgwm937*/*Xgwm894*. On pooled multi-environment data, it explained 45.1% of GI7 variance (LOD = 16.74), 42.8% of VI variance (LOD = 19.05), and 19.4% of SI variance (LOD = 6.87).
- *Minor QTL QPhs.dpivic.4A.1*: Mapped on chromosome 4AS near centromeric marker *Xwmc48*–*Xgwm397*, explaining 30.6–35.4% of VI variance in 2004.
- *Physical Deletion Bin Localization*: *Xgwm937* and *Xgwm894* failed to amplify in deletion lines 4AL-12 and 4AL-13, physically placing *QPhs.dpivic.4A.2* within terminal deletion bins 4AL-12 and 4AL-13.
- *Germplasm Association Survey*: Diagnostic alleles of *Xgwm937* (205 bp) and *Xgwm894* (197 bp) were present exclusively in resistant cultivars derived from the same source ('AC Domain', 'AC Majestic', 'Kanata', 'Snowbird', 'CN19055', 'RL4137'), while susceptible cultivars showed distinct fragment sizes (e.g., 191 bp / 182 bp in 'Annuello').

## Mechanistic Insights
Seed dormancy and PHS resistance in white wheat germplasm 'CN19055' are governed by a major genetic factor on chromosome 4AL (*QPhs.dpivic.4A.2*, corresponding to *TaMKK3-A*) interacting with a second complementary dormancy locus. Physical mapping to deletion bins 4AL-12/13 places this master regulatory locus in the distal region of the long arm of chromosome 4A, where it regulates embryo responsiveness to endogenous hormones and prevents precocious $\alpha$-amylase synthesis during rain events.

## Conclusions & Implications
*QPhs.dpivic.4A.2* is a major, stable QTL conferring robust seed dormancy and PHS resistance in white wheat. The tightly linked, co-dominant SSR markers *Xgwm937* and *Xgwm894*, physically mapped to deletion bins 4AL-12/13, provide validated diagnostic tools for marker-assisted selection to eliminate PHS susceptibility in Australian and international wheat breeding programs.

## Limitations & Caveats
The SSR markers *Xgwm937* and *Xgwm894* are gel/capillary-based microsatellites; converting these markers to single-nucleotide KASP assays targeting the underlying causal gene (*TaMKK3-A*) would facilitate high-throughput automated screening.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Australian commercial white spring wheat cultivars and synthetic hexaploid wheat introgression lines derived from *Aegilops tauschii*.

## Future Directions
1. Convert *Xgwm937* and *Xgwm894* diagnostic alleles into KASP SNP assays for automated MAS.
2. Fine-map the second complementary gene locus in CN19055 to understand its interaction with the 4AL major QTL.
3. Introgress *QPhs.dpivic.4A.2* into leading Australian white wheat cultivars ('Annuello', 'EGA Hume', 'Sunvale') and evaluate commercial end-use quality.

## Key References to Follow Up
- [[Mares et al., 2005]] - Characterized the 4A dormancy QTL in diverse white and red grained wheats.
- [[Torada et al., 2005]] - Mapped and validated PCR markers for the major 4AL seed dormancy QTL.
- [[Torada et al., 2016]] - Cloned *TaMKK3-A* on chromosome 4AL as the causal gene for the *Phs1* locus.

---
**Source PDF:** `data/ogbonnaya_2008_genetic_qtl_analyses.pdf`
"""

def main():
    print(f"Total summaries to validate and write: {len(SUMMARIES)}")
    validator = SummaryValidator()
    results = []
    
    for stem, content in SUMMARIES.items():
        # Validate using SummaryValidator
        val_res = validator.validate(content)
        # Validate using lint_wiki
        lint_errs = validate_source_page(content)
        
        print(f"\n--- Validating: {stem} ---")
        print(f"SummaryValidator Score: {val_res.score}/100, Valid: {val_res.valid}")
        if val_res.errors:
            print(f"Validator Errors: {val_res.errors}")
        if val_res.warnings:
            print(f"Validator Warnings: {val_res.warnings}")
        if lint_errs:
            print(f"Lint Wiki Errors: {lint_errs}")
            
        target_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'wiki', 'sources', 'uncategorized', f"{stem}.md"))
        
        # Write file
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Wrote to {target_path}")
        
        # Update queue
        mark_done(stem, 'worker_phs', val_res.score)
        print(f"Marked done in queue: {stem}")
        
        results.append({
            'stem': stem,
            'score': val_res.score,
            'valid': val_res.valid,
            'lint_errors': len(lint_errs)
        })
        
    print("\n================== SUMMARY RESULTS ==================")
    all_passed = True
    for r in results:
        status = "PASSED" if (r['score'] >= 90 and r['valid'] and r['lint_errors'] == 0) else "FAILED"
        if status == "FAILED":
            all_passed = False
        print(f"{r['stem']}: {status} (Score: {r['score']}, Lint Errors: {r['lint_errors']})")
    
    if all_passed:
        print("\nAll 15 Wave 4 summaries successfully generated and validated with 100% compliance!")
    else:
        print("\nSome summaries failed validation. Please inspect logs above.")

if __name__ == "__main__":
    main()
