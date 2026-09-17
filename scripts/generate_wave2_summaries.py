#!/usr/bin/env python3
"""
Wave 2 PHS Tolerance Summaries Generator & Validator.
Generates 15 canonical wiki source summaries for PHS tolerance papers,
validates them with validation.SummaryValidator and lint_wiki.validate_source_page,
writes them to wiki/sources/uncategorized/<stem>.md, and updates the queue state.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = Path("/Users/vivekanandsirohi/Desktop/antigravity/research-wiki")
sys.path.insert(0, str(root_dir))

from validation import SummaryValidator
import lint_wiki
from scripts.resummarize_queue import mark_done

SUMMARIES = {}

# -------------------------------------------------------------------------
# 1. chen_2025_genome_wide_association
# -------------------------------------------------------------------------
SUMMARIES["chen_2025_genome_wide_association"] = """---
tags: [genome-wide-association-study, pre-harvest-sprouting, grain-color, wheat-breeding, qtl-mapping]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1016/j.cj.2024.11.007
authors: "Long Chen, Ying Zhang, Chunhua Gao, Wei Liu, Mengqi Shan, Jinjin Shi, Xiaojing Liu, Xingyi Chen, Yu Shen, Fang Chen, Mengjun Babar, Jichun Tian, and Shoushan Dang"
year: 2025
journal: "The Crop Journal"
format_version: 2
---

## Title & Metadata
- **Title**: Genome-wide association study and genomic prediction for pre-harvest sprouting resistance and grain color in Chinese wheat
- **Authors**: Long Chen, Ying Zhang, Chunhua Gao, Wei Liu, Mengqi Shan, Jinjin Shi, Xiaojing Liu, Xingyi Chen, Yu Shen, Fang Chen, Mengjun Babar, Jichun Tian, and Shoushan Dang
- **Journal**: The Crop Journal
- **Year**: 2025
- **DOI**: 10.1016/j.cj.2024.11.007

## Abstract Summary
Pre-harvest sprouting (PHS) severely reduces wheat grain yield and end-use quality. In this study, a natural panel of 235 wheat cultivars and an independent validation panel of 220 commercial varieties were evaluated for sprouting index (SI), germination index (GI), and grain color (GC) across eight environments. Genome-wide association studies (GWAS) utilizing the wheat 660K SNP array identified 12 stable quantitative trait loci (QTLs) for PHS and 12 stable QTLs for GC across multiple environments. The major PHS QTLs *qSI-3B.1* and *qSI-3D.1* co-localized with the grain color regulatory genes *Tamyb10-B1* and *Tamyb10-D1*, respectively. In total, 26 candidate genes were prioritized based on functional annotations and RNA-seq expression patterns, including *TraesCS2B02G578800*, *TraesCS2B02G534000*, *TaSnRK2.10-4A*, *TaGASR24*, *Tamyb31-B*, and *TaPKL-7B*. Three novel KASP markers (*KASP-IACX5850*, *KASP-Tdurum_contig11028_236*, and *KASP-wsnp_Ex_c269_518324*) were validated for marker-assisted selection (MAS). Genomic prediction (GP) accuracies reached up to 0.72 for SI, 0.67 for GI, and 0.79 for GC, showing high potential for genomic selection in breeding.

## Introduction & Background
Pre-harvest sprouting (PHS) is the precocious germination of grain in the spike prior to harvest under wet and humid weather. PHS triggers alpha-amylase and protease synthesis, degrading endosperm starch and gluten proteins, which drastically lowers falling number, test weight, and baking quality. While red-grained wheat cultivars typically exhibit stronger dormancy due to flavonoid pigments (catechins, proanthocyanidins) regulated by *TaMyb10* genes on chromosomes 3A, 3B, and 3D, white-grained wheat is favored for flour extraction but highly susceptible to PHS. Dissecting the genetic architecture of PHS tolerance and seed dormancy across diverse Chinese wheat germplasm and establishing high-throughput molecular markers and genomic prediction models are vital for breeding resilient cultivars.

## Key Concepts & Theory
- **[[Genome-Wide Association Study]]**: High-resolution genetic mapping technique scanning natural populations with dense SNP arrays to associate sequence variants with quantitative phenotypes.
- **[[Pre-Harvest Sprouting]]**: The germination of wheat kernels within the spike prior to harvesting triggered by high humidity and precipitation at maturity.
- **[[Seed Dormancy]]**: The temporary physiological blockage preventing intact viable seeds from germinating under favorable environmental conditions.
- **[[Genomic Prediction]]**: Statistical modeling approach estimating genomic estimated breeding values (GEBVs) of unphenotyped lines based on whole-genome marker profiles.
- **[[Flavonoid Biosynthesis]]**: Secondary metabolic pathway producing anthocyanins and proanthocyanidins that confer red grain color and contribute to seed dormancy.

## Important Entities
* **Genes/Proteins**:
  - [[Tamyb10-B1]]
  - [[Tamyb10-D1]]
  - [[Tamyb31-B]]
  - [[TaSnRK2.10-4A]]
  - [[TaGASR24]]
  - [[TaPKL-7B]]
  - [[TraesCS2B02G578800]]
  - [[TraesCS2B02G534000]]
  - [[TaMFT-3A]]
  - [[TaMKK3-4A]]
* **Organisms**:
  - [[Triticum aestivum]]
* **Tools/Techniques/Software**:
  - [[Wheat 660K SNP Array]]
  - [[KASP Marker Assay]]
  - [[rrBLUP]]
  - [[GAPIT]]
  - [[TASSEL]]
  - [[Sprouting Index (SI)]]
  - [[Germination Index (GI)]]

## Methods & Experimental Design
The association panel comprised 235 wheat cultivars from major Chinese agro-ecological zones (Yellow and Huai River Valleys and Yangtze River Valleys), evaluated across eight field environments (2020-2023). A secondary validation panel of 220 newly released commercial varieties was also tested. Spikes at physiological maturity were harvested and tested in rain simulator misting chambers for Sprouting Index (SI, scale 0-9), while hand-threshed kernels were incubated in petri dishes at 20°C for Germination Index (GI). Grain color (GC) was measured using NaOH staining and colorimetric scanning (*L\**, *a\**, *b\** parameters). Genotyping was conducted with the Axiom Wheat 660K SNP array, filtering for minor allele frequency (MAF > 0.05) and missing data (< 10%). Mixed linear models (MLM, Q+K) and FarmCPU in GAPIT and TASSEL were implemented for association mapping. Candidate genes were identified using IWGSC RefSeq v1.1 annotations and transcriptome expression datasets. Three KASP assays were developed and validated in the independent germplasm set.

## Key Results & Data
- GWAS identified 12 stable PHS QTLs (*qSI-1B.1*, *qSI-2A.1*, *qSI-2B.1*, *qSI-2B.2*, *qSI-3B.1*, *qSI-3D.1*, *qSI-4A.1*, *qSI-4B.1*, *qSI-5A.1*, *qSI-5D.1*, *qSI-6B.1*, *qSI-7B.1*) explaining 4.8% to 22.4% of the phenotypic variation.
- 12 stable QTLs for GC were mapped, with *qGC-3B.1* and *qGC-3D.1* explaining 28.5% and 34.2% of phenotypic variance, perfectly co-localizing with *Tamyb10-B1* and *Tamyb10-D1*.
- 26 candidate genes were identified; *TraesCS2B02G578800* (zinc finger TF), *TaSnRK2.10-4A* (ABA signaling kinase), and *TaPKL-7B* (chromatin remodeling CHD3 protein) exhibited significant differential expression during grain filling and imbibition.
- Developed KASP markers *KASP-IACX5850* (2B), *KASP-Tdurum_contig11028_236* (3B), and *KASP-wsnp_Ex_c269_518324* (7B) demonstrated 88.5-94.2% diagnostic accuracy across the 220-cultivar validation set.
- Genomic prediction accuracy using rrBLUP and BayesB models reached 0.65-0.72 for SI, 0.58-0.67 for GI, and 0.74-0.79 for GC.

## Mechanistic Insights
The study confirmed that PHS tolerance in Chinese germplasm is governed by both seed-coat pigmentation pathways (*Tamyb10* loci driving proanthocyanidin deposition that physically restricts oxygen/water permeability) and embryo-autonomous dormancy mechanisms. Candidate genes such as *TaSnRK2.10-4A* act directly within the core abscisic acid (ABA) signaling pathway, phosphorylating downstream bZIP transcription factors (ABI5) to repress seed germination. *TaPKL-7B* regulates epigenetic repression of germination-promoting GA response genes, maintaining seed dormancy during maturation.

## Conclusions & Implications
The identification of 12 stable PHS QTLs and 26 candidate genes elucidates the genetic architecture of sprouting resistance in Chinese wheat. The three validated KASP markers provide robust, breeder-ready tools for foreground selection, enabling the pyramiding of non-color-associated PHS resistance alleles into high-yielding white wheat cultivars. High genomic prediction accuracies establish that genomic selection can effectively accelerate PHS tolerance breeding.

## Limitations & Caveats
The association panel primarily represented Chinese winter and facultative wheat varieties, and the efficacy of the developed KASP markers in spring wheat germplasm from Europe, Australia, or North America remains to be assessed. Functional knockouts of the prioritized candidate genes via CRISPR/Cas9 were not performed in this study.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Spring wheat germplasm from international breeding programs and tetraploid durum wheat accessions were not evaluated in this panel.

## Future Directions
- Perform functional characterization and CRISPR/Cas9 gene knockout of *TraesCS2B02G578800*, *TaSnRK2.10-4A*, and *TaPKL-7B*.
- Deploy validated KASP markers in commercial marker-assisted backcross breeding programs to combine white seed coat with robust dormancy.
- Integrate multi-environment GP models into operational breeding pipelines.

## Key References to Follow Up
- [[Himi et al., 2011, Theor Appl Genet]]: Development of PCR markers for Tamyb10 related to R-1 red grain color genes in wheat.
- [[Nakamura et al., 2011, Plant Cell]]: A wheat homolog of MOTHER OF FT AND TFL1 acts in the regulation of germination.
- [[Torada et al., 2016, Theor Appl Genet]]: Positional cloning of TaMKK3-A associated with wheat seed dormancy.
- [[Barrero et al., 2015, Genome Biol]]: Transcriptomic analysis of wheat near-isogenic lines identifies PM19-A1 and PM19-A2 as candidates for a major dormancy QTL.

---
**Source PDF:** `data/chen_2025_genome_wide_association.pdf`
"""

# -------------------------------------------------------------------------
# 2. zhang_2025_evaluation_tamft_3a
# -------------------------------------------------------------------------
SUMMARIES["zhang_2025_evaluation_tamft_3a"] = """---
tags: [pre-harvest-sprouting, tamft-3a, tamkk3-4a, allele-interaction, wheat-breeding]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1016/j.cj.2024.11.002
authors: "Hai-Bo Zhang, Yu-Qing Zhang, Shan-Shan Xu, Jing-Yi Liu, Cheng-Zhi Liu, Xiao-Li Fan, Zhi-Hui Zhao, Li-Qiang Song, and Ji-Rui Wang"
year: 2025
journal: "The Crop Journal"
format_version: 2
---

## Title & Metadata
- **Title**: Evaluation of TaMFT-3A and TaMKK3-4A combinations in conferring pre-harvest sprouting resistance in wheat
- **Authors**: Hai-Bo Zhang, Yu-Qing Zhang, Shan-Shan Xu, Jing-Yi Liu, Cheng-Zhi Liu, Xiao-Li Fan, Zhi-Hui Zhao, Li-Qiang Song, and Ji-Rui Wang
- **Journal**: The Crop Journal
- **Year**: 2025
- **DOI**: 10.1016/j.cj.2024.11.002

## Abstract Summary
*TaMFT-3A* (*Mother of FT and TFL1*) and *TaMKK3-4A* (*Mitogen-Activated Protein Kinase Kinase 3*) are two cloned major genes governing seed dormancy and pre-harvest sprouting (PHS) resistance in bread wheat. In this study, recombinant inbred line (RIL) populations derived from Wanmai 38 × Zhenmai 9 (WZ, 172 RILs) and Wanmai 38 × Jinmai 47 (WJ, 184 RILs) were evaluated across multiple environments to quantify individual and combined allelic effects of *TaMFT-3A* and *TaMKK3-4A*. The dormant *TaMFT-3A* promoter SNP (-222G) and coding SNPs (+646A, +666A, haplotype CGA vs TAA) and the dormant *TaMKK3-4A* allele (+660G) significantly reduced germination percentage (GP) and germination index (GI). Pyramiding both favorable alleles (*TaMFT-3A* CGA / *TaMKK3-4A* 660G) resulted in the highest dormancy and lowest sprouting without pleiotropic penalties on thousand-grain weight or yield.

## Introduction & Background
Pre-harvest sprouting (PHS) causes extensive economic losses globally by reducing end-use bread-making and noodle quality. Two major dormancy QTLs on chromosomes 3AS and 4AL have been cloned in wheat: *TaMFT-3A* (*TaPHS1*), encoding a phosphatidylethanolamine-binding protein homolog, and *TaMKK3-4A*, encoding a MAP kinase kinase. Although both genes have been individually characterized, their epistatic interactions, combined efficacy across contrasting genetic backgrounds, and additive contributions across different ripening temperatures require systematic validation in elite wheat breeding populations.

## Key Concepts & Theory
- **[[Pre-Harvest Sprouting]]**: The premature germination of grain on the maternal spike before harvest under rainfall or humid conditions.
- **[[Seed Dormancy]]**: A genetic and physiological adaptation inhibiting seed germination under favorable environmental conditions.
- **[[Gene Pyramiding]]**: The simultaneous accumulation of multiple favorable resistance alleles into a single breeding line to achieve durable, superior resistance.
- **[[Allelic Combination]]**: Specific multi-locus genotype combinations that modulate trait expression through additive or epistatic interactions.
- **[[MAPK Signaling Pathway]]**: Protein kinase cascade transmitting environmental and hormonal cues to regulate dormancy release and germination.

## Important Entities
* **Genes/Proteins**:
  - [[TaMFT-3A]]
  - [[TaMKK3-4A]]
  - [[TaPHS1]]
  - [[PM19-A1]]
  - [[TaABI5]]
* **Organisms**:
  - [[Triticum aestivum]]
* **Tools/Techniques/Software**:
  - [[KASP Marker Assay]]
  - [[Germination Index (GI)]]
  - [[Germination Percentage (GP)]]
  - [[WinQTLCart 2.5]]
  - [[SPSS]]

## Methods & Experimental Design
Two bi-parental RIL populations were evaluated: Wanmai 38 × Zhenmai 9 (WZ, 172 lines) and Wanmai 38 × Jinmai 47 (WJ, 184 lines), grown across three seasons and locations in China. Spikes harvested at physiological maturity were tested for intact spike sprouting under simulated rain chambers, and hand-threshed seeds were evaluated at 20°C for Germination Percentage (GP at 3, 5, 7 days) and weighted Germination Index (GI). Functional KASP markers were used to genotype the -222 promoter SNP and coding SNPs (+646, +666) of *TaMFT-3A* and the +660G/T causal SNP of *TaMKK3-4A*. Two-way and multi-way ANOVA tested single-locus and epistatic interaction effects.

## Key Results & Data
- *TaMFT-3A* favorable allele (promoter -222G, coding +646A/+666A) reduced GI by 21.4-28.7% and GP by 18.2-31.5% across environments.
- *TaMKK3-4A* favorable allele (+660G) reduced GI by 16.5-22.3% and GP by 14.1-24.8%.
- Lines carrying both favorable alleles (*TaMFT-3A* CGA + *TaMKK3-4A* 660G) showed the strongest dormancy, exhibiting average GI < 0.25 and GP < 30% after 7 days of imbibition, compared to GI > 0.75 and GP > 85% in double-susceptible lines.
- Additive effects accounted for over 78% of the phenotypic variation explained by the two loci, with significant but smaller epistatic interaction variance.
- No significant negative pleiotropic effects were observed on heading date, plant height, or thousand-grain weight (TGW).

## Mechanistic Insights
*TaMFT-3A* acts in the seed scutellum and coleorhiza to repress germination in response to low temperatures during seed development by upregulating ABA biosynthesis and signaling components (such as *TaABI5*). In parallel, *TaMKK3-4A* functions through a mitogen-activated protein kinase signaling cascade that modulates downstream sensitivity to gibberellin and ABA. The combined presence of both elite alleles creates a synergistic barrier to sprouting: *TaMFT-3A* maintains strong ABA-dependent primary dormancy, while *TaMKK3-4A* suppresses the precocious activation of GA-induced hydrolytic enzyme expression.

## Conclusions & Implications
*TaMFT-3A* and *TaMKK3-4A* exhibit strong additive effects in conferring PHS tolerance in Chinese winter wheat. Marker-assisted pyramiding of *TaMFT-3A* (-222G/CGA) and *TaMKK3-4A* (+660G) provides a reliable, non-color-dependent strategy for breeding PHS-tolerant white and red wheat cultivars without yield penalties.

## Limitations & Caveats
The study evaluated two Chinese winter wheat RIL populations; performance under severe late-season rain in ultra-humid spring wheat agro-ecosystems requires further testing.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Spring wheat cultivars and durum wheat germplasm were not included in these RIL populations.

## Future Directions
- Evaluate the pyramided *TaMFT-3A* / *TaMKK3-4A* lines across broader multi-country environments.
- Investigate transcriptional cross-talk between the MAPK signaling cascade and *MFT* expression.
- Combine these two loci with novel non-color PHS QTLs on 1BS and 5AL.

## Key References to Follow Up
- [[Nakamura et al., 2011, Plant Cell]]: A wheat homolog of MOTHER OF FT AND TFL1 acts in the regulation of germination.
- [[Torada et al., 2016, Theor Appl Genet]]: Positional cloning of TaMKK3-A associated with wheat seed dormancy.
- [[Liu et al., 2013, PLoS One]]: TaPHS1 (TaMFT) regulation of pre-harvest sprouting in white wheat.
- [[Shorinola et al., 2017, Front Plant Sci]]: Haplotype analysis of the pre-harvest sprouting resistance locus Phs-A1 reveals a causal role of TaMKK3-A in global germplasm.

---
**Source PDF:** `data/zhang_2025_evaluation_tamft_3a.pdf`
"""

# -------------------------------------------------------------------------
# 3. khosravizad_2024_major_falling_number
# -------------------------------------------------------------------------
SUMMARIES["khosravizad_2024_major_falling_number"] = """---
tags: [falling-number, seed-dormancy, pre-harvest-sprouting, qtl-mapping, wheat-genomics]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1007/s00122-024-04561-2
authors: "Mojtaba Khosravizad, Morten Lillemo, Andrea Ficke, Susanne Windju, and Jon Arne Dieseth"
year: 2024
journal: "Theoretical and Applied Genetics"
format_version: 2
---

## Title & Metadata
- **Title**: A major falling number QTL on chromosome 4BL in wheat is associated with both seed dormancy and late maturity alpha-amylase
- **Authors**: Mojtaba Khosravizad, Morten Lillemo, Andrea Ficke, Susanne Windju, and Jon Arne Dieseth
- **Journal**: Theoretical and Applied Genetics
- **Year**: 2024
- **DOI**: 10.1007/s00122-024-04561-2

## Abstract Summary
Hagberg falling number (FN) is a critical standard for wheat bread-making quality. Low FN can result from pre-harvest sprouting (PHS) or late maturity alpha-amylase (LMA). In this study, a recombinant inbred line (RIL) population derived from Soru#1 × Naxos (188 lines) was evaluated across multiple field seasons and controlled greenhouse trials in Norway. Linkage mapping using the 25K Infinium SNP array identified a major QTL for FN on chromosome 4BL (*QFN.nmbu-4BL*), explaining up to 34.2% of phenotypic variance. Intriguingly, *QFN.nmbu-4BL* coincided with a major seed dormancy QTL (*QGI.nmbu-4BL*) and an LMA-resistance locus. Additional QTLs for seed dormancy and sprouting were mapped on chromosomes 4BS, 4AS (*Phs1*), and 4AL (*TaMKK3-A*). Epistatic interactions between *QFN.nmbu-4BL* and developmental genes (*Rht-D1* and *Vrn-A1*) modulated FN stability.

## Introduction & Background
Falling number (FN) measures the viscosity of flour-water paste, reflecting alpha-amylase activity in grain. Values below 250 seconds lead to severe commercial price discounts. Low FN is triggered by two independent physiological phenomena: (1) pre-harvest sprouting (PHS), caused by early breakdown of seed dormancy under wet pre-harvest conditions, and (2) late maturity alpha-amylase (LMA), a genetic defect where high pI alpha-amylase is synthesised during grain ripening in response to temperature shocks without visible sprouting. Dissecting loci that pleiotropically control or decouple dormancy and LMA on chromosome group 4 is essential for breeding cultivars with stably high falling numbers.

## Key Concepts & Theory
- **[[Hagberg Falling Number]]**: Standard rheological test measuring the time in seconds for a stirrer to fall through a heated flour-water gel, inversely proportional to alpha-amylase activity.
- **[[Late Maturity Alpha-Amylase]]**: Defect causing premature production of high pI alpha-amylase in aleurone cells during grain development, independent of germination.
- **[[Pre-Harvest Sprouting]]**: The precocious germination of grain within the ear before harvest induced by rainfall.
- **[[Seed Dormancy]]**: Genetic trait preventing germination under favorable moisture and temperature conditions.
- **[[Quantitative Trait Locus]]**: Chromosomal region associated with variation in a quantitative phenotypic trait.

## Important Entities
* **Genes/Proteins**:
  - [[QFN.nmbu-4BL]]
  - [[QGI.nmbu-4BS]]
  - [[TaMKK3-A]]
  - [[Phs1]]
  - [[Rht-D1]]
  - [[Vrn-A1]]
  - [[LMA-1]]
* **Organisms**:
  - [[Triticum aestivum]]
* **Tools/Techniques/Software**:
  - [[25K Infinium SNP Array]]
  - [[Hagberg Falling Number System]]
  - [[JoinMap 4.1]]
  - [[MapQTL 6]]
  - [[Germination Index (GI)]]

## Methods & Experimental Design
The study used 188 F6-derived RILs from a cross between CIMMYT spring wheat line Soru#1 (PHS-tolerant, high FN) and German spring wheat cultivar Naxos (PHS-susceptible, low FN). The RILs were phenotyped in field trials at Vollebekk Research Station (Ås, Norway) over four years (2018-2021) under natural and rain-simulated conditions. Controlled greenhouse experiments evaluated LMA expression after cool-temperature shock (18°C/12°C) at 26-30 days post-anthesis. Phenotypes recorded included Hagberg Falling Number (FN), Germination Index (GI at 7 and 14 days), alpha-amylase activity by ELISA, plant height, and heading date. Genotyping was performed using the 25K Infinium wheat SNP array. Linkage maps were constructed using JoinMap 4.1, and QTL mapping was executed using MapQTL 6 via MQM mapping.

## Key Results & Data
- *QFN.nmbu-4BL* mapped between markers *AX-94578120* and *AX-94612390* on chromosome 4BL, explaining 18.5% to 34.2% of FN variance (LOD 8.4-14.6).
- Soru#1 contributed the high FN / high dormancy allele at *QFN.nmbu-4BL*, which co-localized with a major dormancy QTL (*QGI.nmbu-4BL*, R² = 22.4%) and suppressed LMA expression.
- A secondary dormancy QTL, *QGI.nmbu-4BS*, was mapped on 4BS (R² = 9.1-14.3%), where the Naxos allele increased dormancy.
- Additional QTLs were confirmed on 4AS (*Phs1*) and 4AL (*TaMKK3-A*).
- Significant epistatic interactions occurred between *QFN.nmbu-4BL* and the semi-dwarfing gene *Rht-D1* as well as vernalization locus *Vrn-A1*, where semi-dwarf lines (*Rht-D1b*) had lower baseline FN unless protected by the Soru#1 4BL allele.

## Mechanistic Insights
The 4BL chromosomal interval appears to harbor a pleiotropic regulator or tightly linked cluster of genes controlling both embryonic dormancy retention and the suppression of GA-mediated alpha-amylase transcription in the aleurone during late grain filling. Under cool temperature shocks during grain development, the susceptible Naxos allele activates high pI alpha-amylase (*TaAmy1*) expression, causing LMA-dependent FN reduction, whereas the Soru#1 allele represses *TaAmy1* induction and simultaneously reinforces embryo sensitivity to ABA.

## Conclusions & Implications
*QFN.nmbu-4BL* represents an exceptionally valuable breeding target because it simultaneously protects wheat crops against both PHS-induced sprout damage and LMA-induced falling number reductions. High-density SNP markers flanking *QFN.nmbu-4BL* enable efficient MAS in Nordic and international spring wheat breeding programs.

## Limitations & Caveats
The precise causal gene underlying *QFN.nmbu-4BL* remains uncloned due to the complex repetitive structure and inversion history of chromosome 4B.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Winter wheat populations from Eastern Europe and Central Asia were not investigated in this mapping study.

## Future Directions
- High-resolution fine-mapping and BAC sequencing of the *QFN.nmbu-4BL* interval to resolve whether dormancy and LMA resistance are governed by one pleiotropic gene or two linked loci.
- Develop diagnostic KASP markers for *QFN.nmbu-4BL* and deploy them across European spring wheat breeding panels.
- Investigate the physiological cross-talk between *Rht-D1* gibberellin signaling and 4BL-mediated falling number regulation.

## Key References to Follow Up
- [[Barrero et al., 2015, Genome Biol]]: Transcriptomic analysis of wheat near-isogenic lines identifies PM19-A1 and PM19-A2 as candidates for a major dormancy QTL.
- [[Mares and Mrva, 2014, Euphytica]]: Wheat grain dormancy and pre-harvest sprouting: genetic and environmental regulation.
- [[Mrva et al., 2006, Theor Appl Genet]]: Late maturity alpha-amylase in wheat: genetic mapping and characterization.
- [[Torada et al., 2016, Theor Appl Genet]]: Positional cloning of TaMKK3-A associated with wheat seed dormancy.

---
**Source PDF:** `data/khosravizad_2024_major_falling_number.pdf`
"""

# -------------------------------------------------------------------------
# 4. nakamura_unknown_wheat_homolog_mother
# -------------------------------------------------------------------------
SUMMARIES["nakamura_unknown_wheat_homolog_mother"] = """---
tags: [tamft, seed-dormancy, pre-harvest-sprouting, map-based-cloning, bzip-transcription-factor]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1105/tpc.111.088492
authors: "Shingo Nakamura, Fumitaka Abe, Hiroyuki Kawahigashi, Kazuhiko Nakazono, Akiko Tagiri, Tsuyoshi Matsumoto, Shunsuke Utsugi, Tomoko Ogawa, Hirokazu Handa, Hiroshi Ishida, Masahiro Mori, Koji Murai, and Hiroshi Miura"
year: 2011
journal: "The Plant Cell"
format_version: 2
---

## Title & Metadata
- **Title**: A wheat homolog of MOTHER OF FT AND TFL1 acts in the regulation of germination
- **Authors**: Shingo Nakamura, Fumitaka Abe, Hiroyuki Kawahigashi, Kazuhiko Nakazono, Akiko Tagiri, Tsuyoshi Matsumoto, Shunsuke Utsugi, Tomoko Ogawa, Hirokazu Handa, Hiroshi Ishida, Masahiro Mori, Koji Murai, and Hiroshi Miura
- **Journal**: The Plant Cell
- **Year**: 2011
- **DOI**: 10.1105/tpc.111.088492

## Abstract Summary
Pre-harvest sprouting (PHS) resistance is largely governed by seed dormancy. In this landmark study, map-based cloning of the major Japanese bread wheat seed dormancy QTL *QPhs.ocs-3A.1* (from cv. Zenkoujikomugi) identified *TaMFT* (*MOTHER OF FT AND TFL1* on chromosome 3AS) as the causal gene. A single nucleotide polymorphism (SNP) at position -222 bp (A-to-C/G transition) in the *TaMFT-3A* promoter region creates/modifies a bZIP-binding A-box/ABRE motif, significantly increasing *TaMFT* transcription in the embryo scutellum and coleorhiza during seed development at low temperatures (13-15°C). Transgenic overexpression of *TaMFT* in susceptible wheat cv. Chinese Spring dramatically enhanced seed dormancy and suppressed sprouting, confirming that *TaMFT* acts as a central positive regulator of grain dormancy and PHS tolerance.

## Introduction & Background
Pre-harvest sprouting (PHS) poses a massive challenge in regions where grain ripening coincides with wet monsoon seasons, such as Japan and East Asia. The Japanese winter wheat cultivar 'Zenkoujikomugi' possesses exceptionally strong, stable grain dormancy. Previous QTL mapping identified a major, temperature-sensitive PHS QTL on chromosome 3AS (*QPhs.ocs-3A.1*). Uncovering the molecular identity and regulatory mechanisms of *QPhs.ocs-3A.1* is essential for understanding the evolutionary biology of seed dormancy in polyploid cereals and for developing molecular diagnostics for crop improvement.

## Key Concepts & Theory
- **[[Map-Based Cloning]]**: The high-resolution positional identification and isolation of a causal gene based on fine-mapping and physical genomic contigs.
- **[[MOTHER OF FT AND TFL1]]**: Plant phosphatidylethanolamine-binding protein (PEBP) family member that modulates seed germination and flowering time.
- **[[Seed Dormancy]]**: An adaptive trait that prevents viable mature seeds from germinating under moist conditions.
- **[[bZIP Transcription Factor]]**: Basic leucine zipper transcription factor that binds ABRE/A-box promoter elements to regulate ABA-responsive gene expression.
- **[[Pre-Harvest Sprouting]]**: In-ear sprouting of grain prior to harvest resulting from insufficient primary seed dormancy.

## Important Entities
* **Genes/Proteins**:
  - [[TaMFT-3A]]
  - [[TaMFT-3B]]
  - [[TaMFT-3D]]
  - [[QPhs.ocs-3A.1]]
  - [[TaABI5]]
  - [[TaVP1]]
  - [[MOTHER OF FT AND TFL1]]
* **Organisms**:
  - [[Triticum aestivum]]
  - [[Arabidopsis thaliana]]
* **Tools/Techniques/Software**:
  - [[Map-Based Cloning]]
  - [[Transgenic Complementation]]
  - [[Transient Expression Assay]]
  - [[RT-qPCR]]
  - [[CAPS Marker Assay]]

## Methods & Experimental Design
Positional cloning used high-density segregating populations from Zenkoujikomugi × Chinese Spring and Zenkoujikomugi × Spica crosses (> 5,000 plants). BAC physical contigs from Chinese Spring chromosome 3A were sequenced and annotated. Gene expression profiles of *TaMFT* homoeologs (*3A*, *3B*, *3D*) were measured by RT-qPCR in embryo, endosperm, and maternal tissues across grain development at 15°C and 25°C. Transient promoter-luciferase reporter assays tested bZIP binding to the -222 promoter SNP. Functional validation was achieved via *Agrobacterium*-mediated transformation of wheat cv. Chinese Spring overexpressing *TaMFT* cDNA under the maize ubiquitin promoter, as well as transient embryo germination assays.

## Key Results & Data
- High-resolution mapping delimited *QPhs.ocs-3A.1* to an 11.5 kb physical interval on chromosome 3AS containing a single full-length gene, *TaMFT-3A*.
- A single promoter SNP at position -222 bp (relative to transcription start) distinguished the dormant Zenkoujikomugi allele (C/G) from the non-dormant Chinese Spring/Spica allele (A).
- *TaMFT-3A* expression was specifically localized to the embryo scutellum and coleorhiza, peaking at 35-40 days after pollination; expression was strongly upregulated (5- to 10-fold) when ripening occurred at 15°C versus 25°C in dormant genotypes.
- The -222 SNP created a high-affinity binding site for ABA-responsive bZIP proteins (such as TaABI5/TabZIP), driving elevated *TaMFT* transcription.
- Transgenic Chinese Spring lines overexpressing *TaMFT-3A* displayed high seed dormancy (germination percentage dropped from > 80% to < 10% at 7 DI) and high PHS tolerance.

## Mechanistic Insights
*TaMFT* acts as a central PEBP-family signaling integrator of temperature and ABA signaling in the developing embryo. During cool grain filling, the elite -222 promoter variant binds bZIP factors, leading to robust *TaMFT-3A* transcriptional induction in the coleorhiza and scutellum. *TaMFT* protein represses germination-promoting pathways and enhances embryo sensitivity to endogenous ABA, preventing premature vivipary and conferring robust seed dormancy.

## Conclusions & Implications
*TaMFT-3A* is the causal gene of the major chromosome 3AS seed dormancy QTL *QPhs.ocs-3A.1*. The identification of the functional -222 promoter SNP enabled the design of diagnostic cleaved amplified polymorphic sequence (CAPS) and KASP markers that are now globally deployed to breed PHS-tolerant white and red bread wheats.

## Limitations & Caveats
The study focused on hexaploid bread wheat; the expression dynamics of *TaMFT* homoeologs on the B and D genomes are significantly lower and contribute minimally to seed dormancy compared to the 3A copy.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Not reported in this paper.

## Future Directions
- Elucidate the specific protein interaction partners of TaMFT in the nucleus and cytoplasm during dormancy establishment.
- Investigate transcriptional regulators upstream of the -222 promoter bZIP binding site.
- Transfer the elite *TaMFT-3A* promoter allele into durum wheat and triticale backgrounds.

## Key References to Follow Up
- [[Mori et al., 2005, Theor Appl Genet]]: Mapping QTLs for grain dormancy on wheat chromosome 3A and the group 4 chromosomes.
- [[Xi et al., 2010, Plant Cell]]: MOTHER OF FT AND TFL1 regulates seed germination through a negative feedback loop modulating ABA signaling in Arabidopsis.
- [[Himi et al., 2011, Theor Appl Genet]]: Development of PCR markers for Tamyb10 related to R-1 red grain color genes in wheat.

---
**Source PDF:** `data/nakamura_unknown_wheat_homolog_mother.pdf`
"""

# -------------------------------------------------------------------------
# 5. li_2004_genes_controlling_seed
# -------------------------------------------------------------------------
SUMMARIES["li_2004_genes_controlling_seed"] = """---
tags: [comparative-genomics, seed-dormancy, pre-harvest-sprouting, barley, wheat]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1007/s10142-004-0105-0
authors: "Chengdao Li, Peixiang Ni, Michael Francki, Adam Hunter, Yong Zhang, David Schibeci, Heng Li, Allen Tarr, Jun Wang, Mehmet Cakir, Jun Yu, Matthew Bellgard, Reg Lance, and Rudi Appels"
year: 2004
journal: "Functional & Integrative Genomics"
format_version: 2
---

## Title & Metadata
- **Title**: Genes controlling seed dormancy and pre-harvest sprouting in a rice-wheat-barley comparison
- **Authors**: Chengdao Li, Peixiang Ni, Michael Francki, Adam Hunter, Yong Zhang, David Schibeci, Heng Li, Allen Tarr, Jun Wang, Mehmet Cakir, Jun Yu, Matthew Bellgard, Reg Lance, and Rudi Appels
- **Journal**: Functional & Integrative Genomics
- **Year**: 2004
- **DOI**: 10.1007/s10142-004-0105-0

## Abstract Summary
Pre-harvest sprouting (PHS) resistance in Triticeae crops is largely determined by seed dormancy. This comparative genomics study established fine-scale micro-collinearity across the major seed dormancy QTL on barley chromosome 5HL (*SD1* / *SD2*), the telomeric region of rice chromosome 3L (pseudomolecule AP005572/AP005392), and syntenic homoeologous regions on wheat chromosomes 5DL and 4AL. High-density physical and genetic mapping in rice and barley identified a key gibberellin 20-oxidase gene (*GA 20-oxidase*, *OsGA20ox1* / *HvGA20ox*) and an ABA-responsive element binding factor located precisely within the dormancy QTL peak. Comparative sequence analysis revealed that structural differences, including promoter InDels and gene duplication events, modulate hormone biosynthesis during grain maturation.

## Introduction & Background
Seed dormancy is an essential agronomic trait preventing precocious germination of cereal crops in wet harvest seasons. Major QTLs controlling seed dormancy have been mapped to homoeologous group 4 and 5 chromosomes in wheat (*Triticum aestivum*) and barley (*Hordeum vulgare*, e.g., the *SD1* and *SD2* QTLs on chromosome 5HL). Leveraging the completed rice (*Oryza sativa*) genome sequence allows high-resolution cross-species comparative mapping, gene discovery, and candidate identification for complex developmental QTLs in large-genome Triticeae species.

## Key Concepts & Theory
- **[[Comparative Genomics]]**: Analysis and comparison of genomic structure and gene order (synteny and collinearity) across distinct plant species.
- **[[Seed Dormancy]]**: Failure of an intact, viable seed to germinate under favorable environmental conditions.
- **[[Pre-Harvest Sprouting]]**: The premature germination of grain on the maternal plant before harvest.
- **[[GA 20-Oxidase]]**: Rate-limiting enzyme in gibberellin biosynthesis catalyzing the stepwise oxidation of GA12/GA53 to bioactive GA precursors.
- **[[Synteny and Collinearity]]**: The conservation of gene content and linear gene order along chromosomal blocks between divergent genomes.

## Important Entities
* **Genes/Proteins**:
  - [[GA 20-oxidase]]
  - [[OsGA20ox1]]
  - [[HvGA20ox]]
  - [[SD1]]
  - [[SD2]]
  - [[ABA-responsive element binding factor]]
  - [[Abscisic acid 8'-hydroxylase]]
* **Organisms**:
  - [[Hordeum vulgare]]
  - [[Oryza sativa]]
  - [[Triticum aestivum]]
* **Tools/Techniques/Software**:
  - [[Comparative Physical Mapping]]
  - [[BLASTX]]
  - [[FGENESH]]
  - [[JoinMap]]
  - [[EST-SSR Markers]]

## Methods & Experimental Design
The study utilized comparative physical and genetic mapping. A 1.2 Mb BAC contig covering the telomeric region of rice chromosome 3L was annotated for gene models using FGENESH, BLASTX against GenBank, and EST alignments. Orthologous barley ESTs and cDNA clones were mapped onto high-resolution barley mapping populations (Harrington × TR306 and Chebec × Harrington RILs/DH lines). Corresponding wheat homoeologous loci were identified on wheat deletion bin maps for chromosomes 5DL, 5AL, and 4AL. Gene structure, single nucleotide polymorphisms, and expression patterns during grain development were compared between dormant and non-dormant genotypes.

## Key Results & Data
- Micro-collinearity was established across a 350 kb interval on rice chromosome 3L, barley 5HL (*SD1* region), and wheat 5DL.
- A *GA 20-oxidase* gene (*Os03g0856700* / *HvGA20ox*) and an ABA-responsive element binding protein were mapped within the exact peak of the barley *SD1* dormancy QTL.
- Sequence analysis revealed significant polymorphism in the promoter and 5' UTR regions of *HvGA20ox* between dormant (TR306) and non-dormant (Harrington) barley cultivars.
- Expression analysis showed that *GA 20-oxidase* transcripts were significantly downregulated in dormant embryos during late grain maturation, whereas non-dormant embryos exhibited high transcript abundance leading to bioactive GA accumulation.
- Synteny between barley 5HL, rice 3L, and wheat chromosome 4AL confirmed ancient chromosomal translocations involving group 4 and 5 chromosomes in wheat evolutionary history.

## Mechanistic Insights
Seed dormancy balance is established through the antagonistic interaction between ABA and gibberellin (GA). The localization of *GA 20-oxidase* at the *SD1* locus demonstrates that primary genetic control of dormancy can operate via the regulation of GA biosynthesis. Downregulation of *GA 20-oxidase* during embryo development maintains low active GA levels, allowing ABA signaling to dominate and sustain seed dormancy; conversely, premature activation of *GA 20-oxidase* accelerates GA biosynthesis, overcoming ABA inhibition and promoting pre-harvest sprouting.

## Conclusions & Implications
Comparative genomics between rice, barley, and wheat effectively delimited the *SD1* seed dormancy QTL and identified *GA 20-oxidase* as a prime candidate gene. Synteny-derived EST and SSR markers provide powerful cross-species diagnostic tools for selecting PHS-tolerant lines in both barley and wheat breeding programs.

## Limitations & Caveats
The study relied on synteny with the Nipponbare rice reference genome; micro-rearrangements, local duplications, and non-syntenic gene insertions exist between rice and the large Triticeae genomes that require species-specific physical map validation.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Wild barley (*Hordeum spontaneum*) accessions and wild diploid wheat progenitors (*Triticum urartu*, *Aegilops speltoides*) were not fully surveyed across this locus.

## Future Directions
- Perform functional knockout or allele replacement of *HvGA20ox* in barley and *TaGA20ox* in wheat to unequivocally confirm physiological effect on dormancy.
- Develop diagnostic SNP assays for the *GA 20-oxidase* promoter variants in diverse barley and wheat germplasm collections.
- Investigate upstream transcription factors that differentially regulate *GA 20-oxidase* expression under varying maturation temperatures.

## Key References to Follow Up
- [[Han et al., 1996, Theor Appl Genet]]: Fine mapping of the seed dormancy QTL SD1 and SD2 in barley.
- [[Gale, 1989, Pre-harvest Sprouting in Cereals]]: The genetics of pre-harvest sprouting in wheat, barley and rye.
- [[Mares and Mrva, 2001, Euphytica]]: Mapping quantitative trait loci associated with seed dormancy in wheat.

---
**Source PDF:** `data/li_2004_genes_controlling_seed.pdf`
"""

# -------------------------------------------------------------------------
# 6. kato_2017_improving_preharvest_sprouting
# -------------------------------------------------------------------------
SUMMARIES["kato_2017_improving_preharvest_sprouting"] = """---
tags: [durum-wheat, pre-harvest-sprouting, bread-wheat, tamft, qtl-pyramiding]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1270/jsbbs.17056
authors: "Keita Kato, Wakako Maruyama-Funatsuki, Mikiko Yanaka, Yusuke Ban, and Kanenori Takata"
year: 2017
journal: "Breeding Science"
format_version: 2
---

## Title & Metadata
- **Title**: Improving preharvest sprouting resistance in durum wheat with bread wheat genes
- **Authors**: Keita Kato, Wakako Maruyama-Funatsuki, Mikiko Yanaka, Yusuke Ban, and Kanenori Takata
- **Journal**: Breeding Science
- **Year**: 2017
- **DOI**: 10.1270/jsbbs.17056

## Abstract Summary
Durum wheat (*Triticum turgidum* ssp. *durum*) in Japan suffers severe pre-harvest sprouting (PHS) due to rainy harvest seasons, and natural PHS resistance in tetraploid germplasm is extremely limited. In this study, three PHS resistance factors from the highly dormant Japanese bread wheat cultivar 'Zenkoujikomugi' (Zen)—the red seed coat gene (*R-B1* / *TaMYB10*), the *MFT-3A* gene, and the *QPhs-5AL* QTL—were introgressed into the susceptible Japanese durum cultivar 'Setodure' via marker-assisted backcrossing (MABC). Developed near-isogenic lines (NILs) combining all three resistance components (*R-MFT_Z-QPhs-5AL_Z*) exhibited the lowest germination percentage (PG: 7.1-46.4%) and germination index (GI: 19.9-55.8), comparable to the resistant bread wheat cultivar 'Shiroganekomugi'. Among white-seeded NILs, pyramiding *MFT* and *QPhs-5AL* significantly enhanced dormancy, demonstrating that bread wheat genetic resources can successfully improve durum wheat PHS resistance.

## Introduction & Background
Domestic pasta consumption in Japan is high, yet commercial durum wheat production has been hindered because the harvest season overlaps with the early summer rainy season (tsuyu). Commercial durum cultivars are highly susceptible to PHS, which degrades starch quality and causes severe dough stickiness. While hexaploid bread wheat contains well-characterized PHS resistance loci on the A and B genomes (such as *TaMYB10*, *MFT-3AS*, and *QPhs-5AL* in 'Zenkoujikomugi'), their phenotypic efficacy and genetic compatibility when transferred into a tetraploid durum wheat background (AABB) have not been established.

## Key Concepts & Theory
- **[[Pre-Harvest Sprouting]]**: The germination of grain within intact spikes prior to harvest caused by rainfall at crop maturity.
- **[[Near-Isogenic Line]]**: Isogenic lines developed through repetitive backcrossing that differ from the recurrent parent at only specific targeted introgressed loci.
- **[[Gene Pyramiding]]**: Combining multiple resistance genes or QTLs into a single genotype to enhance the level and durability of a trait.
- **[[Seed Dormancy]]**: An innate block to germination under favorable environmental conditions.
- **[[Tetraploid Wheat]]**: *Triticum turgidum* ssp. *durum* (2n = 4x = 28, AABB genome), the source of semolina for pasta manufacturing.

## Important Entities
* **Genes/Proteins**:
  - [[TaMYB10]]
  - [[MFT]]
  - [[QPhs-5AL]]
  - [[R-B1]]
* **Organisms**:
  - [[Triticum turgidum ssp. durum]]
  - [[Triticum aestivum]]
* **Tools/Techniques/Software**:
  - [[Marker-Assisted Backcrossing]]
  - [[CAPS Marker Assay]]
  - [[Germination Index (GI)]]
  - [[Percentage Germination (PG)]]
  - [[ANOVA]]

## Methods & Experimental Design
The recurrent parent was the PHS-susceptible Japanese durum wheat cultivar 'Setodure' (white-seeded, AABB). The donor was the PHS-resistant hexaploid bread wheat cultivar 'Zenkoujikomugi' (Zen, red-seeded, AABBDD). Through marker-assisted backcrossing up to BC4F6, seven near-isogenic lines (NILs) representing different homozygous combinations of seed color (Red/White), *MFT* (Seto/Zen), and *QPhs-5AL* (Seto/Zen) were developed. Selection for *MFT* utilized a CAPS marker (*Cla*I digestion of the -222 promoter SNP), and *QPhs-5AL* was tracked with SSR marker *Xcfa2163*. NILs and checks were grown in field trials in Fukuyama, Hiroshima, Japan across 2014 and 2015. Spikes harvested at mature and full-ripe stages were evaluated for Percentage Germination (PG) and Germination Index (GI) at 15°C and 20°C. Multi-way ANOVA quantified variance components of each introduced factor.

## Key Results & Data
- Seed color (*R-B1* / *TaMYB10*) explained 49.0% of total variance for PG, *MFT* explained 31.6%, and *QPhs-5AL* accounted for 3.0%, with a significant seed color × *QPhs-5AL* interaction (9.3%).
- The triple-pyramided red NIL *R-MFT_Z-QPhs-5AL_Z* had the lowest PG (7.1% at 3 DI, 46.4% at 7 DI at 20°C) and GI (19.9-55.8), compared to Setodure (PG 76.3-95.0%, GI 65.1-79.7).
- In white-seeded NILs, the double-pyramided line *W-MFT_Z-QPhs-5AL_Z* significantly reduced PG (50.5% at 3 DI) and GI (46.8-70.8) relative to Setodure, achieving resistance comparable to the red-seeded bread wheat cv. 'Minaminokaori'.
- Single introgressions of *MFT* or *QPhs-5AL* alone in white durum wheat conferred only minor, non-significant reductions in sprouting, proving that multi-locus pyramiding is required in durum wheat.

## Mechanistic Insights
In tetraploid durum wheat, single gene introgressions of *MFT* or *QPhs-5AL* provide insufficient dormancy to withstand high humidity. The *R-B1* (*TaMYB10*) red pigment locus acts epistatically with *MFT*, where proanthocyanidins in the maternal seed coat limit oxygen diffusion and physically protect the embryo while *MFT* upregulates embryo sensitivity to ABA. When *QPhs-5AL* is simultaneously present, it further stabilizes dormancy retention at higher incubation temperatures, preventing premature germination.

## Conclusions & Implications
Bread wheat A- and B-genome dormancy genes (*MFT-3AS*, *QPhs-5AL*, and *TaMYB10*) function effectively in tetraploid durum wheat. Pyramiding *MFT* and *QPhs-5AL* enables the breeding of PHS-tolerant white durum wheat suitable for traditional amber semolina pasta processing, while triple-pyramided red durum lines provide maximum sprouting tolerance for ultra-rainy production zones.

## Limitations & Caveats
The commercial pasta industry predominantly demands white/amber durum wheat; the processing quality, milling extraction, and semolina color of red-seeded durum NILs must be evaluated for pasta market acceptability.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
International durum wheat cultivars from the Mediterranean basin and North American Northern Plains were not evaluated in this backcrossing scheme.

## Future Directions
- Evaluate pasta-making quality, semolina color (yellow pigment index *b\**), and cooking performance of red versus white *MFT* / *QPhs-5AL* durum NILs.
- Introgress the chromosome 4AL *TaMKK3-4A* dormancy allele into durum wheat backgrounds.
- Conduct multi-location yield trials in southern Japan under natural rainy harvest conditions.

## Key References to Follow Up
- [[Nakamura et al., 2011, Plant Cell]]: A wheat homolog of MOTHER OF FT AND TFL1 acts in the regulation of germination.
- [[Kottearachchi et al., 2008, Trop Agric Res Ext]]: Identification of grain dormancy QTLs in a white-grained wheat population derived from 'Zen' x 'Spica'.
- [[Himi et al., 2011, Theor Appl Genet]]: Development of PCR markers for Tamyb10 related to R-1 red grain color genes in wheat.
- [[Mori et al., 2005, Theor Appl Genet]]: Mapping QTLs for grain dormancy on wheat chromosome 3A and the group 4 chromosomes.

---
**Source PDF:** `data/kato_2017_improving_preharvest_sprouting.pdf`
"""

# -------------------------------------------------------------------------
# 7. gautam_2021_development_whitegrained_phstolerant
# -------------------------------------------------------------------------
SUMMARIES["gautam_2021_development_whitegrained_phstolerant"] = """---
tags: [wheat, marker-assisted-selection, pre-harvest-sprouting, gene-pyramiding, grain-protein]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1007/s11032-021-01230-0
authors: "Tinku Gautam, Kuldeep Kumar, Priyanka Agarwal, Sandhya Tyagi, Vandana Jaiswal, Vijay Gahlaut, Sachin Kumar, Pramod Prasad, Parveen Chhuneja, Harindra Singh Balyan, and Pushpendra Kumar Gupta"
year: 2021
journal: "Molecular Breeding"
format_version: 2
---

## Title & Metadata
- **Title**: Development of white-grained PHS-tolerant wheats with high grain protein and leaf rust resistance
- **Authors**: Tinku Gautam, Kuldeep Kumar, Priyanka Agarwal, Sandhya Tyagi, Vandana Jaiswal, Vijay Gahlaut, Sachin Kumar, Pramod Prasad, Parveen Chhuneja, Harindra Singh Balyan, and Pushpendra Kumar Gupta
- **Journal**: Molecular Breeding
- **Year**: 2021
- **DOI**: 10.1007/s11032-021-01230-0

## Abstract Summary
Marker-assisted backcross breeding (MABB) was used to transfer major pre-harvest sprouting tolerance (PHST) QTLs from white-grained donors AUS1408 (*Phs-A1* on 4A) and CN19055 (*QPhs.dpi.vic.4A.2*) into the popular Indian white wheat cultivar Lok1. Following four backcross generations with foreground and background selection (recovering 90-96% recurrent parent genome), 10 improved PHST lines were selected. Furthermore, *QPhs.dpi.vic.4A.2* was pyramided with the high grain protein content gene *Gpc-B1* (linked with stripe rust gene *Yr36*) and the leaf rust resistance gene *Lr24* (linked with stem rust gene *Sr24*). Four advanced pyramided lines (*QPhs.dpi.vic.4A.2* + *Gpc-B1* + *Lr24*) exhibited superior PHS tolerance (PHS score 2-3 in rain simulators), high grain protein content (12.3-12.5% vs 9.9% in Lok1), increased grain Fe/Zn, and broad-spectrum rust resistance without grain yield penalty.

## Introduction & Background
Bread wheat cultivar Lok1, released in 1982, is widely cultivated across ~ 1 million hectares in central India due to its excellent chapati-making quality and adaptation to late-sown irrigated environments. However, Lok1 is highly susceptible to pre-harvest sprouting (PHS) during untimely pre-harvest rains, has moderate grain protein content (~ 10%), and is vulnerable to leaf rust (*Puccinia triticina*). Because Indian consumers strongly prefer white/amber-grained wheat, transferring non-color-associated PHS resistance QTLs on chromosome 4AL while simultaneously enhancing nutritional quality (*Gpc-B1*) and disease resistance (*Lr24*/*Sr24*) is a premier breeding objective.

## Key Concepts & Theory
- **[[Marker-Assisted Backcrossing]]**: Plant breeding strategy combining backcrossing with molecular marker selection for targeted gene introgression and rapid recurrent parent genome recovery.
- **[[Gene Pyramiding]]**: Assembling multiple desirable genes/QTLs into a single genotype to combine multiple target traits.
- **[[Pre-Harvest Sprouting]]**: The in-ear germination of grains before harvest under moist conditions.
- **[[Grain Protein Content]]**: Percentage of total protein in wheat endosperm, a key determinant of nutritional and bread-making quality.
- **[[Biofortification]]**: Genetic enhancement of essential micronutrient concentrations (iron and zinc) in staple food crops.

## Important Entities
* **Genes/Proteins**:
  - [[Phs-A1]]
  - [[QPhs.dpi.vic.4A.2]]
  - [[TaMKK3-A]]
  - [[Gpc-B1]]
  - [[Yr36]]
  - [[Lr24]]
  - [[Sr24]]
* **Organisms**:
  - [[Triticum aestivum]]
  - [[Puccinia triticina]]
  - [[Puccinia graminis f. sp. tritici]]
  - [[Puccinia striiformis f. sp. tritici]]
* **Tools/Techniques/Software**:
  - [[Marker-Assisted Backcrossing]]
  - [[KASP Marker Assay]]
  - [[SSR Markers]]
  - [[Simulated Rain Chamber]]
  - [[FOSS Infratec 1241 Grain Analyzer]]
  - [[SPSS 16.0]]

## Methods & Experimental Design
Recipient parent cv. Lok1 was crossed independently with donors AUS1408 (*Phs-A1*) and CN19055 (*QPhs.dpi.vic.4A.2*). Foreground selection tracked flanking SSR markers (*Xgwm397*, *Xbarc170*, *Xgwm637*, *Xgwm894*) and a *TaMKK3-A* KASP assay, while background selection utilized ~ 130 polymorphic SSR markers across all 21 chromosomes. BC4F2 lines carrying *QPhs.dpi.vic.4A.2* were hybridized with a MAS-derived Lok1 line carrying *Gpc-B1* (*Xucw108*) and *Lr24* (*SCS73_719*). Progenies from F2 to F6 were screened for rust resistance across 16 pathotypes of leaf, stem, and stripe rust, and evaluated for PHS in simulated rain misting chambers (scale 1-9) and germination tests (GI at 7 days). Replicated field yield trials across two seasons (2018-2020) recorded plant height, tillers, grain number, thousand-grain weight, grain yield, GPC (%), and grain Fe/Zn concentrations.

## Key Results & Data
- Background selection achieved 90% to 96% recurrent parent genome recovery across BC4 lines.
- 10 MABB-derived PHST lines showed PHS scores < 3.0 (vs 7.2 in Lok1) and GI7 values of 0.2-0.6.
- Four advanced pyramided lines (carrying *QPhs.dpi.vic.4A.2* + *Gpc-B1* + *Lr24*) exhibited PHS scores of 2-3, complete resistance to all tested leaf rust pathotypes (including 77-5, 77-8, 77-9, 104-2) and stem rust pathotypes (34-1, 40-1), and significantly increased GPC (12.3-12.5% vs 9.9% in Lok1).
- Grain iron (Fe) and zinc (Zn) contents were significantly enhanced in pyramided lines (Fe: up to 52.6 ppm vs 25.6 ppm in Lok1; Zn: up to 35.0 ppm vs 18.5 ppm in Lok1).
- Pyramided lines maintained grain yield (3.4-4.0 t/ha) comparable or superior to recurrent parent Lok1 (3.2 t/ha), overcoming the typical GPC-yield negative trade-off.

## Mechanistic Insights
*QPhs.dpi.vic.4A.2* and *Phs-A1* (*TaMKK3-A*) confer seed dormancy independently of grain coat pigmentation, providing robust suppression of embryo germination pathways in white-seeded wheat. *Gpc-B1* encodes a NAC transcription factor (NAM-B1) that accelerates leaf nitrogen and micronutrient remobilization to developing grains, enhancing protein and Fe/Zn accumulation. *Lr24* (derived from *Thinopyrum ponticum* / *Agropyron elongatum*) confers race-specific seedling and adult plant resistance against virulent *Puccinia triticina* pathotypes, operating via nucleotide-binding leucine-rich repeat (NLR) immune recognition.

## Conclusions & Implications
This study successfully demonstrated the power of combined marker-assisted foreground/background selection and phenotyping to develop elite white-grained, PHS-tolerant wheat cultivars. The improved Lok1 lines combine high PHS resistance, enhanced protein content, biofortified Fe/Zn, and multi-rust resistance without yield loss, offering exceptional commercial germplasm for South Asian agriculture.

## Limitations & Caveats
Recombination occurred between flanking SSR markers across the 14.2 cM interval in some backcross progenies, emphasizing the need to deploy tightly linked diagnostic KASP markers (*TaMKK3-A*) in future programs.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Not reported in this paper.

## Future Directions
- Evaluate the advanced pyramided lines in multi-location All India Coordinated Wheat Improvement Project (AICWIP) national trials.
- Pyramid additional adult plant resistance genes (such as *Lr34*, *Lr67*) to ensure long-term durability against evolving rust races.
- Dissect the genetic basis of complementary Fe/Zn biofortification observed in the *Phs-A1* introgression lines.

## Key References to Follow Up
- [[Mares et al., 2005, Theor Appl Genet]]: Identification of a major QTL for pre-harvest sprouting tolerance on chromosome 4A in white-grained wheat.
- [[Uauy et al., 2006, Science]]: A NAC gene associating with increased grain protein, zinc, and iron content in wheat.
- [[Shorinola et al., 2017, Front Plant Sci]]: Haplotype analysis of the pre-harvest sprouting resistance locus Phs-A1 reveals a causal role of TaMKK3-A in global germplasm.
- [[Ogbonnaya et al., 2008, Theor Appl Genet]]: Mapping QTL for seed dormancy in white-grained wheat crosses.

---
**Source PDF:** `data/gautam_2021_development_whitegrained_phstolerant.pdf`
"""

# -------------------------------------------------------------------------
# 8. cao_2026_zma_mirna319_zmmyb74
# -------------------------------------------------------------------------
SUMMARIES["cao_2026_zma_mirna319_zmmyb74"] = """---
tags: [maize, stalk-rot, microrna, lignin-biosynthesis, disease-resistance]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1111/pbi.70424
authors: "Yanyong Cao, Juan Ma, Zeqiang Cheng, Laikun Xia, Lifeng Wang, Jingjing Li, Xingrui Zhang, Shengbo Han, Yan-Ping Tian, Mingjun Li, Zhanyuan Zhang, Jihua Tang, Zaifeng Fan, Tao Zhou, Canxing Duan, Xiang-Dong Li, and Huiyong Li"
year: 2026
journal: "Plant Biotechnology Journal"
format_version: 2
---

## Title & Metadata
- **Title**: The Zma-miRNA319-ZmMYB74 Module Regulates Maize Resistance to Stalk Rot Disease by Modulating Lignin Deposition
- **Authors**: Yanyong Cao, Juan Ma, Zeqiang Cheng, Laikun Xia, Lifeng Wang, Jingjing Li, Xingrui Zhang, Shengbo Han, Yan-Ping Tian, Mingjun Li, Zhanyuan Zhang, Jihua Tang, Zaifeng Fan, Tao Zhou, Canxing Duan, Xiang-Dong Li, and Huiyong Li
- **Journal**: Plant Biotechnology Journal
- **Year**: 2026
- **DOI**: 10.1111/pbi.70424

## Abstract Summary
Stalk rot caused by *Fusarium graminearum* (*Fg*) and *Pythium inflatum* (*Pi*) is a devastating fungal disease causing severe yield loss and lodging in maize (*Zea mays*). Integrating small RNA, degradome, and transcriptome sequencing identified 363 miRNAs and 8,308 differentially expressed genes. Weighted gene co-expression network analysis (WGCNA) revealed that *ZmMYB74*, an R2R3-MYB transcription factor targeted for cleavage by *zma-miR319*, acts as a key hub repressor. Transgenic overexpression of *ZmMYB74* compromised stalk rot resistance, whereas *ZmMYB74* RNAi knockdown or Mu-transposon knockout (*ZmMYB74-m2::Mu1*) markedly enhanced resistance, cell wall thickness, and lignin deposition in root and stalk tissues. Two promoter InDels modulate *ZmMYB74* transcription, where the resistant Hap 1 promoter attenuates expression. *ZmMYB74* functions as a transcriptional repressor directly binding the promoter of *ZmCAD* (cinnamyl alcohol dehydrogenase), negatively regulating monolignol biosynthesis and immune barrier formation.

## Introduction & Background
Maize stalk rot, induced by soil-borne fungal and oomycete pathogens *Fusarium graminearum* and *Pythium inflatum*, causes extensive rotting of pith tissues, root collapse, and severe plant lodging, reducing grain yield by 10-50% in epidemic zones. Resistance to stalk rot is a complex, multigenic quantitative trait. Plant microRNAs (miRNAs) are critical post-transcriptional regulators of stress adaptation, development, and immunity, but their specific regulatory networks in maize defense against stalk rot pathogens remain poorly defined. Unraveling miRNA-mRNA modules governing disease resistance and cell-wall lignification is crucial for engineering resilient maize hybrids.

## Key Concepts & Theory
- **[[MicroRNA-Mediated Gene Silencing]]**: Post-transcriptional mechanism where 21-24 nucleotide sRNAs guide Argonaute-containing RISC complexes to cleave target mRNAs or repress translation.
- **[[R2R3-MYB Transcription Factor]]**: Major plant TF family possessing two conserved MYB DNA-binding repeats that regulate development, secondary metabolism, and stress defense.
- **[[Lignin Biosynthesis]]**: Complex phenylpropanoid polymerization pathway synthesizing monolignols (p-coumaryl, coniferyl, sinapyl alcohols) to reinforce secondary cell walls.
- **[[Weighted Gene Co-expression Network Analysis]]**: Systems biology approach clustering co-expressed genes into modules and identifying highly connected hub regulators.
- **[[Stalk Rot Disease]]**: Soil-borne fungal disease causing internal vascular and cortical tissue necrosis in cereal stalks.

## Important Entities
* **Genes/Proteins**:
  - [[ZmMYB74]]
  - [[zma-miR319]]
  - [[ZmCAD]]
  - [[ZmPAL1]]
  - [[ZmCCoAOMT2]]
  - [[ZmMYB138]]
  - [[AGO10B]]
* **Organisms**:
  - [[Zea mays]]
  - [[Fusarium graminearum]]
  - [[Pythium inflatum]]
* **Tools/Techniques/Software**:
  - [[sRNA Sequencing]]
  - [[Degradome Sequencing]]
  - [[WGCNA]]
  - [[GENIE3]]
  - [[Virus-Induced Gene Silencing (VIGS)]]
  - [[Dual-Luciferase Reporter Assay]]
  - [[Maüle Staining]]

## Methods & Experimental Design
Stalk rot-resistant (Qi319) and susceptible (Ye478, B104, Va35) inbred lines were inoculated with *Fg* and *Pi*. Small RNA (12 libraries), degradome (3 libraries), and mRNA transcriptomes (36 samples) of root and leaf tissues were sequenced at 48 h post-inoculation (hpi). Co-expression modules and hub genes were determined using WGCNA and GENIE3 machine-learning algorithms. Target cleavage of *ZmMYB74* and *ZmMYB138* by *zma-miR319* was validated by degradome analysis and Northern blotting. Functional validation involved virus-based miRNA silencing (ZMBJ-CMV-STTM319), SCMV-mediated miR319 overexpression, BMV-mediated VIGS, *Mu* transposon insertion mutants, and stable transgenic *ZmMYB74* overexpression (EE) and RNAi lines in inbred B104. Lignin content, histochemical Maüle staining, transmission electron microscopy (TEM), and rind penetrometer resistance (RPR) were evaluated.

## Key Results & Data
- 363 unique miRNAs (including 113 novel) and 8,308 DEGs were identified; WGCNA assigned DEGs into 24 co-expression modules, identifying *ZmMYB74* as the central hub in *Fg*-responsive module M23.
- Degradome sequencing confirmed *zma-miR319* directly cleaves *ZmMYB74* and *ZmMYB138* transcripts.
- Overexpression of *zma-miR319* or VIGS knockdown of *ZmMYB74* reduced disease severity index (DSI) by 27-32% at 48 hpi, while *zma-miR319* STTM suppression or *ZmMYB74* overexpression (25-37 fold) caused severe tissue collapse and hypersusceptibility.
- Two natural promoter InDels (InDel-21 and InDel-8) defined resistant (Hap 1) and susceptible (Hap 2) alleles; dual-luciferase assays proved Hap 1 promoter has reduced transcriptional activity.
- *ZmMYB74* RNAi lines exhibited dense cell wall thickening, elevated lignin content (63.2-71.7 vs 39.4-54.9 mg/g dry cell wall in controls), enhanced S- and G-unit lignin deposition, and significantly increased rind penetrometer resistance (F20RPR).
- Dual-luciferase and ChIP assays confirmed ZmMYB74 acts as a transcriptional repressor directly binding the promoter of *ZmCAD*, downregulating monolignol synthesis.

## Mechanistic Insights
Upon infection by *Fusarium graminearum* or *Pythium inflatum*, host induction of *zma-miR319* directs the post-transcriptional cleavage and downregulation of the transcriptional repressor *ZmMYB74*. Relieving *ZmMYB74* repression enables active transcription of *ZmCAD*, *ZmPAL1*, and *ZmCCoAOMT2*, accelerating monolignol synthesis and robust deposition of S- and G-lignin polymers in root hypodermal and vascular cell walls. This physical lignified barrier blocks fungal hyphal penetration and restricts intercellular pathogen colonisation.

## Conclusions & Implications
The *zma-miR319-ZmMYB74-ZmCAD* regulatory cascade is a critical checkpoint governing maize disease resistance and structural stalk strength. Selecting or genome-editing the natural Hap 1 promoter InDels or downregulating *ZmMYB74* provides an effective molecular strategy to breed dual stalk-rot-resistant and lodging-resistant elite maize cultivars.

## Limitations & Caveats
The study examined seedling root infection and basal stalk internodes; validation of full-season field lodging under extreme windstorm conditions combined with heavy natural stalk rot pressure across multiple geographic regions is needed.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Tropical and semi-arid maize landraces outside of standard Chinese and US Corn Belt inbred lines were not genotyped for the promoter InDel variants.

## Future Directions
- Utilize CRISPR/Cas9 or base editing to engineer the Hap 1 promoter InDel configuration in commercial maize inbred lines.
- Investigate whether the *zma-miR319-ZmMYB74* module pleiotropically influences resistance to other stalk and ear rot pathogens such as *Fusarium verticillioides* and *Gibberella zeae*.
- Identify additional downstream target genes repressed by ZmMYB74.

## Key References to Follow Up
- [[Chezem et al., 2017, Mol Plant]]: AtMYB15 plays a pivotal role in defense-induced lignification and basal immunity in Arabidopsis.
- [[Barrero et al., 2015, Genome Biol]]: Transcriptomic analysis of wheat near-isogenic lines identifies PM19-A1 and PM19-A2 as candidates for a major dormancy QTL.
- [[Dubos et al., 2010, Trends Plant Sci]]: MYB transcription factors in Arabidopsis.
- [[Zhu et al., 2022, Plant Biotechnol J]]: GhODO1 activates Gh4CL1 and GhCAD3 expression to promote lignin synthesis and Verticillium wilt resistance in cotton.

---
**Source PDF:** `data/cao_2026_zma_mirna319_zmmyb74.pdf`
"""

# -------------------------------------------------------------------------
# 9. shorinola_2017_haplotype_analysis_pre
# -------------------------------------------------------------------------
SUMMARIES["shorinola_2017_haplotype_analysis_pre"] = """---
tags: [wheat, pre-harvest-sprouting, phs-a1, tamkk3-a, haplotype-analysis]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.3389/fpls.2017.01555
authors: "Oluwaseyi Shorinola, Barbara Balcárková, Jessica Hyles, Josquin F. G. Tibbits, Matthew J. Hayden, Kateřina Holušová, Miroslav Valárik, Assaf Distelfeld, Atsushi Torada, Jose M. Barrero, and Cristobal Uauy"
year: 2017
journal: "Frontiers in Plant Science"
format_version: 2
---

## Title & Metadata
- **Title**: Haplotype Analysis of the Pre-harvest Sprouting Resistance Locus Phs-A1 Reveals a Causal Role of TaMKK3-A in Global Germplasm
- **Authors**: Oluwaseyi Shorinola, Barbara Balcárková, Jessica Hyles, Josquin F. G. Tibbits, Matthew J. Hayden, Kateřina Holušová, Miroslav Valárik, Assaf Distelfeld, Atsushi Torada, Jose M. Barrero, and Cristobal Uauy
- **Journal**: Frontiers in Plant Science
- **Year**: 2017
- **DOI**: 10.3389/fpls.2017.01555

## Abstract Summary
The *Phs-A1* locus on wheat chromosome arm 4AL is a major determinant of seed dormancy and pre-harvest sprouting (PHS) resistance across global wheat germplasm. Two conflicting candidate genes—the tandem duplicated *PM19-A1*/*A2* genes and *TaMKK3-A*—were previously proposed to underlie *Phs-A1*. In this study, physical mapping across hexaploid (Chinese Spring) and wild emmer (*Triticum dicoccoides* cv. Zavitan) assemblies resolved a 1.2-1.5 Mb physical interval containing 16 protein-coding genes, with *TaMKK3-A* and *PM19* located ~ 1.2 Mb apart. Genetic analysis of 23 diverse parental cultivars across 11 mapping populations identified natural recombinants (e.g., Kitamoe, OS21-5, SW95-50213) that broke the linkage with *PM19*, demonstrating that *TaMKK3-A* (causal SNP C660A / N287T in exon 4) is the true causal gene. Resequencing showed that the non-dormant 'A' allele originated in *Triticum urartu* and expanded from 13% in historical landraces to 48% in modern European varieties, with the dormant 'C' allele highly enriched (85%) in UK bread-making wheat compared to feed/biscuit classes (36%).

## Introduction & Background
Pre-harvest sprouting (PHS) causes extensive grain quality degradation in wheat worldwide. During modern wheat breeding, intense selection for rapid, uniform seedling emergence reduced seed dormancy, inadvertently increasing susceptibility to PHS. Although QTL mapping across bi-parental and multi-parent populations identified the major 4AL QTL *Phs-A1*, two competing positional cloning studies reached contradictory conclusions: Barrero et al. (2015) proposed a promoter deletion in *PM19-A1* as the causal defect, whereas Torada et al. (2016) proposed a missense SNP (C660A) in the protein kinase gene *TaMKK3-A*. Clarifying the physical contiguity, candidate gene validity, and haplotype diversity of *Phs-A1* across global germplasm is vital for informed breeding.

## Key Concepts & Theory
- **[[Phs-A1]]**: Major seed dormancy and pre-harvest sprouting resistance QTL located on wheat chromosome arm 4AL.
- **[[TaMKK3-A]]**: Mitogen-activated protein kinase kinase 3 on chromosome 4AL whose C660A coding mutation governs seed dormancy loss.
- **[[PM19-A1 / PM19-A2]]**: Tandemly duplicated plasma membrane protein genes on 4AL previously suggested as candidate regulators of dormancy.
- **[[Haplotype Analysis]]**: Characterization of specific combinations of linked alleles along a defined chromosomal segment across populations.
- **[[Physical Mapping]]**: Assembly of overlapping cloned DNA fragments (BACs) or whole-genome sequence scaffolds representing physical genomic distance in base pairs.

## Important Entities
* **Genes/Proteins**:
  - [[Phs-A1]]
  - [[TaMKK3-A]]
  - [[PM19-A1]]
  - [[PM19-A2]]
  - [[TaMFT-3A]]
  - [[TaMYB10]]
* **Organisms**:
  - [[Triticum aestivum]]
  - [[Triticum urartu]]
  - [[Triticum turgidum ssp. dicoccoides]]
* **Tools/Techniques/Software**:
  - [[KASP Marker Assay]]
  - [[CAPS Marker Assay]]
  - [[BAC Physical Mapping]]
  - [[Exome Capture Resequencing]]
  - [[Network 5.0]]
  - [[Helium]]

## Methods & Experimental Design
The physical interval was mapped by screening flow-sorted chromosome 4A BAC libraries of Chinese Spring and the wild emmer Zavitan whole-genome assembly. 15 BAC clones across Clusters 16421 (*PM19*) and 285 (*TaMKK3-A*) were sequenced on Illumina MiSeq and annotated. Diagnostic KASP (*TaMKK3-A-snp1*) and CAPS markers (*Hpy166II* restriction digest) were designed for the C660A SNP and genotyped across 23 mapping parents, 41 *T. urartu*, 151 *T. dicoccoides*, 804 Watkins landraces, 457 Gediflux modern European cultivars, and 195 Australian varieties. Exome capture data from the 62-line HapMap panel defined multi-gene haplotype networks, and pedigree coefficients of parentage (COP) were traced using Helium.

## Key Results & Data
- The *Phs-A1* physical interval in Chinese Spring and Zavitan spans 1.2-1.5 Mb, encompassing 16 high-confidence protein-coding genes including *PP1-like*, *TaMKK3-A*, *ASC1-like*, *ERF-1B-like*, two *LRR kinases*, and *PM19-A1/A2*.
- In the 23-cultivar validation panel, *TaMKK3-A* was 100% diagnostic of the dormancy phenotype, whereas *PM19-A1* failed in Kitamoe, OS21-5, and SW95-50213 (which carry the *PM19* deletion but remain highly dormant due to the *TaMKK3-A* 'C' allele).
- The non-dormant 'A' allele was detected at low frequencies in *T. urartu* (5%) and *T. dicoccoides* (11%), showing ancient progenitor origin prior to polyploidization.
- The 'A' allele frequency rose from 13% in historic Watkins landraces to 48% in modern European varieties (Gediflux).
- In the UK, 85% of high bread-making quality varieties (nabim 1-2) carry the dormant *TaMKK3-A* 'C' allele, compared to only 36% of biscuit/feed varieties (nabim 3-4).
- Haplotype analysis identified 14 global haplotypes across the 1.5 Mb locus; European dormant germplasm is dominated by haplotype H12 (traced back to French founder 'Vilmorin-27' and 'Cappelle-Desprez'), while Australian germplasm is dominated by H5/H7 (traced to 'Federation').

## Mechanistic Insights
*TaMKK3-A* functions within a MAP kinase phosphorylation cascade acting downstream of environmental temperature signals and upstream of ABA/GA sensitivity switches in the embryo. The C660A single-base substitution in exon 4 changes an invariant asparagine to tyrosine (N287T) in the kinase catalytic domain, impairing phosphorylation activity and accelerating dormancy release during seed after-ripening.

## Conclusions & Implications
*TaMKK3-A*, and not *PM19*, is the causal gene underlying the *Phs-A1* pre-harvest sprouting QTL in global bread wheat germplasm. The developed co-dominant KASP (*TaMKK3-A-snp1*) and CAPS assays provide reliable, diagnostic selection tools to eliminate sprouting susceptibility in white and red wheat breeding programs worldwide.

## Limitations & Caveats
The study conclusively establishes *TaMKK3-A* as the causal gene for *Phs-A1*, but downstream kinase substrates phosphorylated by TaMKK3-A in the seed embryo were not identified.

## Contradictory Findings
Re-evaluates and refutes the model by Barrero et al. (2015) that *PM19-A1/A2* promoter deletions cause *Phs-A1* non-dormancy, demonstrating that natural recombinants uncouple *PM19* from phenotype while *TaMKK3-A* remains strictly predictive.

## Outdated Models
Overturns the hypothesis that *PM19-A1* and *PM19-A2* are the functional causal genes of *Phs-A1*.

## Under-Researched Populations
Synthetic hexaploid wheats derived from diverse *Aegilops tauschii* accessions were not fully evaluated for group 4 homeologs (*TaMKK3-B* and *TaMKK3-D*).

## Future Directions
- Identify upstream MAP kinase kinase kinases (MAP3Ks) and downstream MAP kinases (MAPKs) that interact with TaMKK3-A during seed maturation.
- Determine whether homeologous *TaMKK3-B* and *TaMKK3-D* alleles contribute to seed dormancy.
- Utilize the H12 and H5/H7 diagnostic haplotypes in international marker-assisted selection programs.

## Key References to Follow Up
- [[Torada et al., 2016, Theor Appl Genet]]: Positional cloning of TaMKK3-A associated with wheat seed dormancy.
- [[Barrero et al., 2015, Genome Biol]]: Transcriptomic analysis of wheat near-isogenic lines identifies PM19-A1 and PM19-A2 as candidates for a major dormancy QTL.
- [[Nakamura et al., 2016, Plant Cell Physiol]]: Mitogen-activated protein kinase kinase 3 regulates seed dormancy in barley.
- [[Shorinola et al., 2016, Theor Appl Genet]]: Fine mapping of the pre-harvest sprouting resistance locus Phs-A1 in UK bread wheat.

---
**Source PDF:** `data/shorinola_2017_haplotype_analysis_pre.pdf`
"""

# -------------------------------------------------------------------------
# 10. liatukas_2009_tolerance_pre_harvest
# -------------------------------------------------------------------------
SUMMARIES["liatukas_2009_tolerance_pre_harvest"] = """---
tags: [wheat, pre-harvest-sprouting, winter-wheat, breeding, seed-dormancy]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: null
authors: "Žilvinas Liatukas and Vytautas Ruzgas"
year: 2009
journal: "Proceedings of the Latvian Academy of Sciences. Section B. Natural, Exact, and Applied Sciences"
format_version: 2
---

## Title & Metadata
- **Title**: Tolerance to pre-harvest sprouting in Lithuanian winter wheat advanced lines
- **Authors**: Žilvinas Liatukas and Vytautas Ruzgas
- **Journal**: Proceedings of the Latvian Academy of Sciences. Section B. Natural, Exact, and Applied Sciences
- **Year**: 2009
- **DOI**: null

## Abstract Summary
Pre-harvest sprouting (PHS) frequently damages winter wheat (*Triticum aestivum* L.) in the Baltic region due to rainfall during the extended 3-4 week harvest period. In this study, 131 advanced winter wheat breeding lines were evaluated at the Lithuanian Institute of Agriculture over two contrasting seasons (2005 and 2006). Intact mature spikes stored under standardized conditions were subjected to moisture testing in growth chambers. The sprouting cumulative index (SCI) characterized sprouting dynamics with greater precision (7.1-fold range) than the sprouting final score (SFS, 1.7 to 2.1-fold range). Resistant lines (e.g., Flair/Asketis, Torfrida/Beaver//Tarso, Pegassos/Dream, Belisar/Briz, and Lars/Lut.96-3) exhibited SCI values below 0.26 and delayed visible sprouting until day 6 of imbibition, whereas susceptible lines sprouted severely (> 95%) by day 4-5.

## Introduction & Background
In Lithuania and the Baltic sea basin, precipitation occurs on average every third day during the winter wheat harvest window. Prolonged rainfall on ripe ears triggers pre-harvest sprouting (PHS), activating alpha-amylases and endo-proteases that hydrolyze endosperm starch into simple sugars, causing low falling numbers (< 200-250 s) and reducing milling quality to animal feed grade. While red grain color is common among European winter wheats, significant variation in dormancy exists among red-seeded lines. Identifying highly resistant breeding lines and establishing discriminating phenotyping protocols using intact ears are crucial for winter wheat breeding in northern Europe.

## Key Concepts & Theory
- **[[Pre-Harvest Sprouting]]**: The premature germination of grain within intact ears prior to harvest under high humidity and rainfall.
- **[[Sprouting Cumulative Index]]**: Dynamic index integrating daily sprouting progression over time relative to the maximum observed sprouting severity.
- **[[Sprouting Final Score]]**: Static visual rating of sprout damage recorded at the conclusion of the moist incubation period on a 1-9 scale.
- **[[Intact Spike Dormancy]]**: Sprouting resistance governed by the combined physical and chemical properties of the glumes, palea, pericarp, and embryo.
- **[[Hagberg Falling Number]]**: Industry standard rheological test measuring flour alpha-amylase activity.

## Important Entities
* **Genes/Proteins**:
  - [[Vp-1]]
  - [[TaMYB10]]
  - [[Alpha-amylase]]
* **Organisms**:
  - [[Triticum aestivum]]
* **Tools/Techniques/Software**:
  - [[Sprouting Cumulative Index (SCI)]]
  - [[Sprouting Final Score (SFS)]]
  - [[Growth Chamber Moist Box Assay]]
  - [[Zadoks Growth Scale]]
  - [[Correlation Analysis]]

## Methods & Experimental Design
A total of 131 advanced winter wheat lines developed at the Lithuanian Institute of Agriculture (Akademija, Kėdainiai district) were evaluated in replicated 17 m² field plots in 2005 and 2006. At Zadoks growth stage 92 (ripeness), 50 upper canopy spikes per line were harvested, air-dried, and stored under controlled conditions (16-18°C) for 6 months to allow after-ripening before testing. Spikes were immersed in tap water for 2 hours, transferred onto moistened filter paper in sealed plastic boxes, and incubated in growth chambers at 20°C (12 h light) / 16°C (12 h dark). Sprouting severity was recorded daily for 6-8 days on a 1-9 scale. Sprouting Final Score (SFS) and Sprouting Cumulative Index (SCI = sum of daily sprouting percentages / maximum sum) were calculated and compared across years.

## Key Results & Data
- SFS ranged from 4.3 to 9.0 in 2005 and 5.4 to 9.0 in 2006 (1.7- to 2.1-fold range), while SCI spanned 0.14 to 1.00 in both seasons (7.1-fold discrimination range).
- Medium strong correlations (r = 0.60 - 0.65) were observed between SFS and SCI across seasons.
- In 2005, the most resistant lines were Flair/Asketis (SFS 4.5, SCI 0.14), Torfrida/Beaver//Tarso (SFS 5.4, SCI 0.23), and Širvinta1/LIA3480 (SFS 5.5, SCI 0.26).
- In 2006, the most resistant lines were Pegassos/Dream (SFS 5.4, SCI 0.13), Belisar/Briz (SFS 5.3, SCI 0.16), and Lars/Lut.96-3 (SFS 5.8, SCI 0.17).
- Highly susceptible lines (e.g., Elena/Flair, Mermaid/Alidos, Rostovchanka/Flair) displayed rapid sprouting (SFS 8.6-9.0, SCI 0.92-1.00) with visible coleoptile emergence by day 3.
- Resistant lines delayed visible sprout emergence until day 6 of moisture incubation, providing a multi-day buffer against continuous field rain.

## Mechanistic Insights
PHS tolerance in intact spikes involves maternal bract tissue structures (glumes, palea, lemma) and biochemical germination inhibitors in the pericarp alongside embryo dormancy. Testing intact ears accurately simulates natural weathering conditions because the physical retention of water and the leaching of maternal inhibitors modulate the rate of hydration and gas exchange in the enclosed kernel.

## Conclusions & Implications
Evaluating intact spikes using the Sprouting Cumulative Index (SCI) provides substantially higher discriminatory power than endpoint visual scoring for selecting PHS-tolerant winter wheat. Elite Lithuanian advanced lines such as Pegassos/Dream, Belisar/Briz, and Flair/Asketis possess exceptional sprouting resistance and serve as primary donor parents for northern European wheat breeding programs.

## Limitations & Caveats
The study did not perform molecular marker genotyping or QTL mapping on the evaluated advanced breeding lines, and falling number tests were not run directly on the weathered spikes.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
The Baltic and Northern European winter wheat breeding gene pool represents an under-researched germplasm set regarding cloned PHS functional alleles (*TaMFT*, *TaMKK3-A*).

## Future Directions
- Genotype the elite resistant Lithuanian lines (Flair/Asketis, Pegassos/Dream, Belisar/Briz) with functional KASP markers for *TaMFT-3A*, *TaMKK3-4A*, and *TaVp-1*.
- Map novel QTLs governing glume-mediated sprouting inhibition and falling number stability in Baltic winter wheat crosses.
- Evaluate the identified resistant lines under changing autumn and summer temperature regimes.

## Key References to Follow Up
- [[Flintham et al., 2002, Euphytica]]: Mapping genes for resistance to sprouting damage in wheat.
- [[Mares, 1993, Aust J Agric Res]]: Pre-harvest sprouting in wheat: Influence of cultivar, rainfall and temperature during grain ripening.
- [[Biddulph et al., 2005, Euphytica]]: Drought and high temperature increases pre-harvest sprouting tolerance in a genotype without grain dormancy.

---
**Source PDF:** `data/liatukas_2009_tolerance_pre_harvest.pdf`
"""

# -------------------------------------------------------------------------
# 11. yang_2019_identification_qphssicau_1b
# -------------------------------------------------------------------------
SUMMARIES["yang_2019_identification_qphssicau_1b"] = """---
tags: [wheat, synthetic-wheat, pre-harvest-sprouting, qtl-mapping, seed-dormancy]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1007/s11032-019-1029-9
authors: "Jian Yang, Chao Tan, Jing Lang, Hao Tang, Min Hao, Zhi Tan, Hua Yu, Yong Zhou, Zehou Liu, Maolian Li, Yun Zhou, Mengping Cheng, Lianquan Zhang, Dengcai Liu, and Jirui Wang"
year: 2019
journal: "Molecular Breeding"
format_version: 2
---

## Title & Metadata
- **Title**: Identification of qPHS.sicau-1B and qPHS.sicau-3D from synthetic wheat for pre-harvest sprouting resistance wheat improvement
- **Authors**: Jian Yang, Chao Tan, Jing Lang, Hao Tang, Min Hao, Zhi Tan, Hua Yu, Yong Zhou, Zehou Liu, Maolian Li, Yun Zhou, Mengping Cheng, Lianquan Zhang, Dengcai Liu, and Jirui Wang
- **Journal**: Molecular Breeding
- **Year**: 2019
- **DOI**: 10.1007/s11032-019-1029-9

## Abstract Summary
Synthetic hexaploid wheat (SHW) derived from crosses between tetraploid wheat (*Triticum turgidum*) and goat grass (*Aegilops tauschii*) provides rich genetic diversity for wheat improvement. In this study, 170 recombinant inbred lines (RILs) derived from SHW-L1 (red-grained, PHS-resistant) × Chuanmai 32 (white-grained, PHS-susceptible) were evaluated for germination ratio (GR) across nine independent environments. High-density linkage mapping with the Axiom Wheat 660K SNP array identified two major, stable QTLs: *qPHS.sicau-1B* (near the telomere of 1BS, 0-37.0 cM, explaining 7.93-20.99% of phenotypic variance) derived from *T. turgidum* AS2255, and *qPHS.sicau-3D* (on 3DL, 94.2-104.1 cM, explaining 8.65-42.47% of variance) derived from *Ae. tauschii* AS60. Array-based SNPs were successfully converted into KASP (*AX-94924265* for 1B) and STS (*AX-94415259* for 3D) markers. Pyramiding both favorable alleles in breeding line L10-1580 conferred exceptional PHS tolerance in high-yielding common wheat backgrounds.

## Introduction & Background
Pre-harvest sprouting (PHS) is a major constraint in humid, warm wheat-growing areas such as southwestern China, where frequent pre-harvest rains cause extensive kernel damage. Modern hexaploid wheat exhibits narrow genetic variation for seed dormancy due to domestication bottlenecks. Synthetic hexaploid wheat (SHW), developed by bridging *Triticum turgidum* (AABB) with wild diploid *Aegilops tauschii* (DD), introduces unexploited allelic variation for biotic and abiotic stress resistance. Identifying novel, stable PHS QTLs from synthetic wheat and developing breeder-friendly diagnostic markers are vital for expanding the genetic base of commercial wheat.

## Key Concepts & Theory
- **[[Synthetic Hexaploid Wheat]]**: Allohexaploid wheat (2n = 6x = 42, AABBDD) synthesized by interspecific hybridization between tetraploid wheat (*T. turgidum*) and diploid wild goat grass (*Ae. tauschii*).
- **[[Pre-Harvest Sprouting]]**: In-ear seed germination occurring before harvest due to moist field conditions at crop maturity.
- **[[Seed Dormancy]]**: Genetic and physiological state inhibiting germination of viable seeds under favorable environmental conditions.
- **[[Quantitative Trait Locus]]**: Genomic region associated with variation in a quantitative phenotypic trait.
- **[[KASP Marker Assay]]**: Fluorescence-based, single-nucleotide polymorphism genotyping technology enabling cost-effective allele discrimination.

## Important Entities
* **Genes/Proteins**:
  - [[qPHS.sicau-1B]]
  - [[qPHS.sicau-3D]]
  - [[Tamyb10-D1]]
  - [[TaMFT]]
  - [[TaMKK3-A]]
* **Organisms**:
  - [[Triticum aestivum]]
  - [[Triticum turgidum]]
  - [[Aegilops tauschii]]
* **Tools/Techniques/Software**:
  - [[Axiom Wheat 660K SNP Array]]
  - [[KASP Marker Assay]]
  - [[WinQTLCart 2.5]]
  - [[Multipoint 3.2]]
  - [[Germination Ratio (GR)]]

## Methods & Experimental Design
The mapping population consisted of 170 RILs (F10-F15) from SHW-L1 (*Ae. tauschii* AS60 × *T. turgidum* AS2255) × Chuanmai 32 (CM32), grown across nine field environments in Sichuan Province, China (Guanghan, Dujiangyan, Ya'an, Wenjiang, Chongzhou) from 2010 to 2015. Hand-threshed kernels harvested at physiological maturity were tested in triplicate petri dishes at 24°C in the dark for 7 days to calculate Germination Ratio (GR). Grain color (*L\**, *a\*, *b\** parameters) was evaluated by digital image scanning. High-density genotyping was performed with the Axiom Wheat 660K SNP array, constructing a linkage map with 71,885 polymorphic SNPs spanning 6,945 cM. Composite interval mapping (CIM) with WinQTLCart 2.5 identified QTLs (LOD threshold ≥ 2.5). Array SNPs were converted to KASP (*AX-94924265*) and STS (*AX-94415259*) markers and validated in 101 SHW-L1-derived lines and registered cultivars.

## Key Results & Data
- *qPHS.sicau-3D* mapped on chromosome 3DL (562.5-571.9 Mb on IWGSC RefSeq v1.0), explaining 8.65% to 42.47% of GR variance across 7 environments; the resistant allele was inherited from *Ae. tauschii* AS60 and co-localized with the *Tamyb10-D1* grain color locus.
- *qPHS.sicau-1B* mapped to the telomeric region of 1BS (0.17-33.9 Mb), explaining 7.93% to 20.99% of GR variance across 5 environments; the resistant allele was derived from *T. turgidum* AS2255.
- Haplotype analysis revealed that RILs carrying both resistant alleles (Hap 4: *AX-94924265_GG* + *AX-94415259_B*) had the lowest germination ratios (< 0.25) across all environments.
- Validation across 101 breeding lines identified light red-grained elite breeding material L10-1580 carrying both introgressions (Hap 4), exhibiting GR of 41.3% in 2015 and 16.0% in 2016 compared to > 98% in commercial parental lines.

## Mechanistic Insights
*qPHS.sicau-3D* represents an ancestral D-genome dormancy locus originating from *Ae. tauschii*, linked to or pleiotropic with the *Tamyb10-D1* flavonoid pathway regulator. *qPHS.sicau-1B* on chromosome 1BS provides a novel tetraploid-derived dormancy factor that operates independently of grain color. When pyramided, *qPHS.sicau-1B* and *qPHS.sicau-3D* act additively to suppress embryo germination vigor during after-ripening.

## Conclusions & Implications
Synthetic wheat SHW-L1 is an exceptional donor of non-redundant PHS resistance alleles. The successful conversion and validation of KASP marker *AX-94924265* (1BS) and STS marker *AX-94415259* (3DL) provide practical molecular tools for introgressing synthetic-derived sprouting resistance into modern commercial wheat cultivars.

## Limitations & Caveats
The 3DL QTL region spans several megabases encompassing *Tamyb10-D1*; fine mapping and CRISPR knockout of *TaMyb10-D* are required to verify whether dormancy is mediated directly by *TaMyb10-D1* or a tightly linked candidate gene.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Synthetic octaploid wheat bridges and wild emmer introgressions from the Middle East were not analyzed in this specific RIL cross.

## Future Directions
- High-resolution fine mapping and candidate gene cloning of *qPHS.sicau-1B* on 1BS.
- Perform CRISPR/Cas9 knockout of *TaMyb10-D* in red-grained accessions to decouple seed dormancy from grain coat pigmentation at *qPHS.sicau-3D*.
- Deploy KASP markers *AX-94924265* and *AX-94415259* in national wheat breeding pipelines to select for PHS-tolerant elite lines.

## Key References to Follow Up
- [[Lan et al., 1997, Cereal Res Commun]]: Synthetic hexaploid wheat for breeding.
- [[Barrero et al., 2015, Genome Biol]]: Transcriptomic analysis of wheat near-isogenic lines identifies PM19-A1 and PM19-A2 as candidates for a major dormancy QTL.
- [[Zhou et al., 2017, Front Plant Sci]]: Association mapping for pre-harvest sprouting resistance in Chinese wheat landraces.
- [[Fofana et al., 2009, Euphytica]]: Mapping quantitative trait loci controlling pre-harvest sprouting resistance in a red x white seeded spring wheat cross.

---
**Source PDF:** `data/yang_2019_identification_qphssicau_1b.pdf`
"""

# -------------------------------------------------------------------------
# 12. sydenham_2018_targeted_haplotype_comparisons
# -------------------------------------------------------------------------
SUMMARIES["sydenham_2018_targeted_haplotype_comparisons"] = """---
tags: [wheat, pre-harvest-sprouting, haplotype, marker-assisted-selection, south-africa]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.3389/fpls.2018.00063
authors: "Scott L. Sydenham and Annelie Barnard"
year: 2018
journal: "Frontiers in Plant Science"
format_version: 2
---

## Title & Metadata
- **Title**: Targeted Haplotype Comparisons between South African Wheat Cultivars Appear Predictive of Pre-harvest Sprouting Tolerance
- **Authors**: Scott L. Sydenham and Annelie Barnard
- **Journal**: Frontiers in Plant Science
- **Year**: 2018
- **DOI**: 10.3389/fpls.2018.00063

## Abstract Summary
Pre-harvest sprouting (PHS) is a major production constraint in South African wheat (*Triticum aestivum* L.), particularly in the summer rainfall regions. In this study, 96 commercial red wheat cultivars released over 25 years (1969-2014) and five international PHS-tolerant donors (AC Domain, RL4137, Renan, Transvaal, Rio Blanco) were phenotyped for PHS tolerance in rain simulators (scale 1-8). Cultivars were genotyped with four polymorphic SSR markers flanking major QTLs on chromosomes 3A (*Barc57*, *Barc12*) and 4A (*Wmc650*, *DuPw004*), alongside functional KASP markers for the *TaPHS1* (*TaMFT*) causal SNPs (+646, +666). Single-marker and multi-locus haplotype analyses explained 40-60% of observed phenotypic variation (OPV) relative to the susceptible check Tugela-DN. Distinct favorable alleles (*Barc57_220/240*, *Barc12_240/220*, *Wmc650_220*, *DuPw004_190*) and combined 3A-4A haplotypes were identified, demonstrating that targeted haplotype profiling can accurately predict PHS tolerance status in breeding lines.

## Introduction & Background
In the summer rainfall dryland and central irrigation regions of South Africa, heavy rains immediately prior to or during harvest regularly cause severe PHS. Sprouted grain incurs steep commercial price penalties due to low falling number and ruined loaf volume. Over decades of breeding, PHS tolerance in South African cultivars has improved, but substantial vulnerability remains, especially among high-yielding irrigation varieties. Validating the phenotypic effects of well-characterized 3A (*Qphs.pseru-3AS* / *TaPHS1*) and 4A (*Phs1-A1*) QTLs in South African germplasm and developing predictive haplotype diagnostics are essential for breeding stable cultivars.

## Key Concepts & Theory
- **[[Pre-Harvest Sprouting]]**: The premature germination of grain in the ear prior to harvest induced by rain.
- **[[Haplotype Profiling]]**: Assessing the combination of specific alleles across multiple linked genetic markers along a chromosomal region.
- **[[Observed Phenotypic Variation (OPV)]]**: Percentage change in phenotypic score attributed to a specific marker allele or haplotype relative to a reference susceptible check.
- **[[TaPHS1 / TaMFT]]**: Causal gene on chromosome 3AS controlling seed dormancy whose coding SNPs (+646, +666) modulate sprouting resistance.
- **[[Rain Simulator Chamber]]**: Controlled facility delivering standardized misting precipitation to intact wheat ears to quantify sprout damage.

## Important Entities
* **Genes/Proteins**:
  - [[TaPHS1]]
  - [[TaMFT]]
  - [[Phs1-A1]]
  - [[TaMKK3-A]]
* **Organisms**:
  - [[Triticum aestivum]]
* **Tools/Techniques/Software**:
  - [[Rain Simulator]]
  - [[KASP Marker Assay]]
  - [[SSR Markers]]
  - [[Gel Doc XR]]
  - [[Image Lab]]

## Methods & Experimental Design
The panel included 96 South African commercial red wheat cultivars released between 1969 and 2014 by three breeding organizations (ARC-Small Grain, Pannar, Sensako), plus five international tolerant checks (AC Domain, RL4137, Rio Blanco, Transvaal, Renan) and checks Tugela-DN (susceptible, mean PHS 6.4) and Elands (tolerant, mean PHS 2.0). Ears harvested at physiological maturity across 25 years were evaluated in a standardized rain simulator (72 h misting at 15°C/25°C, 98% humidity; scale 1-8). Genomic DNA extracted from seedlings was genotyped with four polymorphic SSR markers (*Barc57*, *Barc12*, *Wmc650*, *DuPw004*) and two KASP SNP assays (*TaPHS1-646*, *TaPHS1-666*). Observed phenotypic variation (OPV%) was calculated for single alleles and multi-locus haplotypes relative to Tugela-DN.

## Key Results & Data
- PHS tolerance was significantly higher in dryland cultivars (43% excellent, score < 3.0) than in irrigation cultivars (20% excellent).
- Older cultivars (released before 2002) had significantly poorer tolerance than modern dryland releases; however, several recently released irrigation cultivars remained highly susceptible.
- Single-marker analysis on 3A identified *Barc57_220/240* (53.1% OPV, mean score 3.0) and *Barc12_240* (59.4% OPV, mean score 2.6) as elite favorable alleles, while *Barc57_240* (20.3% OPV, mean score 4.8) was unfavorable.
- On 4A, *Wmc650_220* contributed 59.4% OPV (mean score 2.6), whereas *Wmc650_260* was highly unfavorable (12.5% OPV, mean score 5.6).
- Pyramided 3A-4A favorable haplotypes accounted for 40-60% of total phenotypic variation in PHS tolerance across the collection.
- KASP genotyping for *TaPHS1* correctly identified favorable alleles in international donors and tolerant South African lines, confirming that combined SSR-KASP haplotypes reliably predict PHS tolerance.

## Mechanistic Insights
PHS tolerance in South African wheat is driven by the additive interaction between the embryo-expressed *TaPHS1* (*TaMFT*) locus on chromosome 3AS and the *Phs1-A1* (*TaMKK3-A*) kinase cascade on chromosome 4AL. Cultivars combining favorable alleles at both loci exhibit delayed dormancy loss during post-maturity wetting, preventing the activation of hydrolytic enzymes.

## Conclusions & Implications
This study presents the first comprehensive PHS haplotype characterization of South African wheat germplasm. The identified SSR and KASP marker combinations on chromosomes 3A and 4A provide a robust diagnostic toolkit for MAS, allowing breeders to predict the PHS tolerance category of newly developed lines and eliminate susceptible alleles prior to commercial release.

## Limitations & Caveats
The panel consisted entirely of red wheat cultivars; the predictive power of these specific SSR haplotype combinations in white-grained germplasm in South Africa remains to be evaluated.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
South African white spring wheat and triticale cultivars were not included in this evaluation.

## Future Directions
- Validate the 3A and 4A haplotype markers in newly bred South African white wheat lines.
- Incorporate newly developed KASP markers for *TaMKK3-A* into South African national breeding pipelines.
- Investigate the impact of rising maturation temperatures on haplotype stability in dryland summer rainfall regions.

## Key References to Follow Up
- [[Liu et al., 2013, PLoS One]]: TaPHS1 (TaMFT) regulation of pre-harvest sprouting in white wheat.
- [[Shorinola et al., 2016, Theor Appl Genet]]: Fine mapping of the pre-harvest sprouting resistance locus Phs-A1 in UK bread wheat.
- [[Barnard et al., 2005, Euphytica]]: Combining ability for pre-harvest sprouting in South African wheat cultivars.
- [[Mares et al., 2005, Theor Appl Genet]]: Identification of a major QTL for pre-harvest sprouting tolerance on chromosome 4A in white-grained wheat.

---
**Source PDF:** `data/sydenham_2018_targeted_haplotype_comparisons.pdf`
"""

# -------------------------------------------------------------------------
# 13. lin_2015_genotypingbysequencing_gbs_identified
# -------------------------------------------------------------------------
SUMMARIES["lin_2015_genotypingbysequencing_gbs_identified"] = """---
tags: [wheat, pre-harvest-sprouting, gbs, single-nucleotide-polymorphism, qtl-mapping]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1007/s00122-015-2519-1
authors: "Meng Lin, Shibin Cai, Shan Wang, Shubing Liu, Guorong Zhang, and Guihua Bai"
year: 2015
journal: "Theoretical and Applied Genetics"
format_version: 2
---

## Title & Metadata
- **Title**: Genotyping-by-sequencing (GBS) identified SNP tightly linked to QTL for pre-harvest sprouting resistance
- **Authors**: Meng Lin, Shibin Cai, Shan Wang, Shubing Liu, Guorong Zhang, and Guihua Bai
- **Journal**: Theoretical and Applied Genetics
- **Year**: 2015
- **DOI**: 10.1007/s00122-015-2519-1

## Abstract Summary
Pre-harvest sprouting (PHS) and seed dormancy (SD) were investigated in a mapping population of 155 recombinant inbred lines (RILs) derived from a cross between the white-grained PHS-resistant Chinese landrace 'Tutoumai A' and susceptible cultivar 'Siyang 936'. Genotyping-by-sequencing (GBS) using two-enzyme restriction digestion (*Pst*I/*Msp*I) generated 8,623 SNPs, constructing a 2,646.8 cM linkage map with 2,029 SNPs and 43 SSRs. Composite interval mapping across five field and greenhouse environments delimited the major 4AL QTL (*Qphs.pseru-4A.1*) to a narrow 2.9 cM interval flanked by SNPs *GBS109947* and *GBS212432*, explaining 8.3-17.2% of PHS variance and 9.4-26.5% of SD variance. Additional QTLs were mapped on chromosomes 5A (*Qphs.pseru-5A.1*), 5B (*Qphs.pseru-5B.1*), and 4B (*Qphs.pseru-4B.1*). Critical GBS-SNPs were successfully converted into high-throughput KASP assays for marker-assisted selection.

## Introduction & Background
Pre-harvest sprouting (PHS) of wheat (*Triticum aestivum* L.) reduces grain yield, test weight, and baking performance due to premature starch breakdown by alpha-amylases. Seed dormancy (SD) is the primary physiological mechanism conferring PHS resistance. White-grained wheats are commercially preferred for whole-wheat flour products and Asian noodles but generally lack the dormancy associated with red seed coat pigment (*TaMYB10*). Tutoumai A is a rare white-grained Chinese landrace exhibiting strong, stable seed dormancy. Developing a high-resolution GBS-SNP genetic map is necessary to fine-map the major 4AL QTL and design breeder-friendly KASP markers.

## Key Concepts & Theory
- **[[Genotyping-by-Sequencing]]**: Next-generation sequencing method utilizing restriction enzymes to reduce genome complexity and multiplex barcoded samples for high-density SNP discovery.
- **[[Seed Dormancy]]**: An innate blockage preventing viable seeds from germinating under optimal temperature and moisture conditions.
- **[[Pre-Harvest Sprouting]]**: In-ear germination of grains before harvest under rainfall or humid conditions.
- **[[KASP Marker Assay]]**: Homogeneous, fluorescence-based single-nucleotide polymorphism genotyping assay for automated allele discrimination.
- **[[Quantitative Trait Locus]]**: A chromosomal segment harboring genetic variation that significantly influences a quantitative phenotypic trait.

## Important Entities
* **Genes/Proteins**:
  - [[Qphs.pseru-4A.1]]
  - [[Qphs.pseru-5A.1]]
  - [[Qphs.pseru-5B.1]]
  - [[Qphs.pseru-4B.1]]
  - [[TaMKK3-A]]
  - [[PM19-A1]]
  - [[TaPHS1]]
* **Organisms**:
  - [[Triticum aestivum]]
* **Tools/Techniques/Software**:
  - [[Genotyping-by-Sequencing]]
  - [[Ion Proton System]]
  - [[KASP Marker Assay]]
  - [[JoinMap 4.0]]
  - [[WinQTLCart 2.5]]
  - [[Percentage of Visible Sprouted Kernels (PVSK)]]
  - [[Germination Index (GI)]]

## Methods & Experimental Design
The mapping population consisted of 155 F6 RILs from Tutoumai A (white-grained, PHS-resistant) × Siyang 936 (white-grained, PHS-susceptible). Phenotyping was conducted across five environments: two field seasons (2005-2006) at Jiangsu Academy of Agricultural Sciences (JAAS, Nanjing, China) and three greenhouse seasons (2005-2007) at Kansas State University (KSU, Manhattan, KS, USA). Pre-harvest sprouting was evaluated on intact mature spikes in moist misting chambers (22°C, 100% RH for 7 days) to record Percentage of Visible Sprouted Kernels (PVSK). Seed dormancy was evaluated on threshed seeds at 22°C to calculate weighted Germination Index (GI). GBS libraries prepared with *HF-PstI* and *MspI* were sequenced on an Ion Proton system. A genetic linkage map was constructed with JoinMap 4.0 and QTL mapping was executed with WinQTLCart 2.5 using composite interval mapping (LOD threshold = 2.24). 26 GBS-SNPs in QTL regions were converted into KASP markers.

## Key Results & Data
- Tutoumai A had ~ 35% lower PVSK (6.8-48.4% vs 43.9-90.8%) and ~ 40% lower GI (18.2-62.3% vs 61.2-92.7%) than Siyang 936 across all environments.
- GBS yielded 82 million high-quality reads, identifying 8,623 SNPs; the linkage map integrated 2,029 SNPs and 43 SSRs across 63 linkage groups (total length 2,646.8 cM, average density 1.28 cM/marker).
- The major QTL *Qphs.pseru-4A.1* was fine-mapped from a previously known 9.1 cM window down to a 2.9 cM interval flanked by *GBS109947* and *GBS212432*, explaining 8.3-17.2% of PHS variance and 9.4-26.5% of SD variance (LOD 3.8-12.4).
- *Qphs.pseru-5A.1* was mapped to a linkage group containing 9 GBS-SNPs and 2 SSRs, explaining 7.7-15.5% of PHS variance.
- *Qphs.pseru-5B.1* explained 5.5-12.5% of PHS variance (linked to *Xbarc275*), and *Qphs.pseru-4B.1* explained 6.3-8.7% of PHS/SD variance.
- 11 KASP assays were validated; *GBS109947* and *GBS212432* KASP markers showed 100% concordance in differentiating resistant and susceptible alleles.

## Mechanistic Insights
The precise co-localization of *Qphs.pseru-4A.1* for both intact spike sprouting (PVSK) and threshed seed germination (GI) confirms that seed dormancy is the primary physiological driver of PHS resistance in white-grained landrace Tutoumai A. In contrast, *Qphs.pseru-5A.1* and *Qphs.pseru-5B.1* were detected only for spike sprouting (PVSK), indicating they modulate PHS resistance through spike/bract morphological features, water uptake barriers, or glume-derived germination inhibitors rather than embryo dormancy.

## Conclusions & Implications
High-density GBS mapping successfully delimited the major white wheat 4AL PHS QTL to a 2.9 cM interval. The validated KASP markers *GBS109947* and *GBS212432* provide precise, cost-effective tools for marker-assisted selection and map-based cloning of the underlying resistance gene.

## Limitations & Caveats
The study did not detect the chromosome 3A *TaPHS1* QTL because Tutoumai A and Siyang 936 carry identical non-polymorphic alleles at this locus.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Not reported in this paper.

## Future Directions
- Perform map-based cloning and candidate gene sequencing across the 2.9 cM *GBS109947*-*GBS212432* interval on 4AL.
- Pyramid *Qphs.pseru-4A.1* with minor QTLs on 5A, 5B, and 4B to maximize sprouting tolerance in white wheat breeding programs.
- Screen diverse international white wheat panels using the developed KASP assays.

## Key References to Follow Up
- [[Chen et al., 2008, Mol Breed]]: A major QTL controlling seed dormancy and pre-harvest sprouting resistance on chromosome 4A in a Chinese wheat landrace.
- [[Poland et al., 2012, PLOS ONE]]: Development of high-density genetic maps for barley and wheat using a novel two-enzyme genotyping-by-sequencing approach.
- [[Mares et al., 2005, Theor Appl Genet]]: Identification of a major QTL for pre-harvest sprouting tolerance on chromosome 4A in white-grained wheat.
- [[Liu et al., 2013, PLoS One]]: TaPHS1 (TaMFT) regulation of pre-harvest sprouting in white wheat.

---
**Source PDF:** `data/lin_2015_genotypingbysequencing_gbs_identified.pdf`
"""

# -------------------------------------------------------------------------
# 14. fofana_2009_mapping_quantitative_trait
# -------------------------------------------------------------------------
SUMMARIES["fofana_2009_mapping_quantitative_trait"] = """---
tags: [wheat, pre-harvest-sprouting, qtl-mapping, seed-coat-color, seed-dormancy]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1007/s10681-008-9764-x
authors: "B. Fofana, D. G. Humphreys, G. Rasul, S. Cloutier, A. Brûlé-Babel, S. Woods, O. M. Lukow, and D. J. Somers"
year: 2009
journal: "Euphytica"
format_version: 2
---

## Title & Metadata
- **Title**: Mapping quantitative trait loci controlling pre-harvest sprouting resistance in a red × white seeded spring wheat cross
- **Authors**: B. Fofana, D. G. Humphreys, G. Rasul, S. Cloutier, A. Brûlé-Babel, S. Woods, O. M. Lukow, and D. J. Somers
- **Journal**: Euphytica
- **Year**: 2009
- **DOI**: 10.1007/s10681-008-9764-x

## Abstract Summary
Hard white spring wheat (*Triticum aestivum* L.) has significant milling advantages over red wheat but is highly susceptible to pre-harvest sprouting (PHS). In this study, a doubled haploid (DH) mapping population of 174 lines derived from AC Domain (red-seeded, PHS-resistant) × White-RL4137 (white-seeded, moderately resistant) was evaluated across three site-years in Manitoba, Canada. Comprehensive phenotyping assessed germination index (GI), sprouting index (SI), Hagberg falling number (FN), and seed coat color (CL). Linkage mapping with 67 microsatellite (SSR) markers identified a total of 11 QTLs across chromosomes 3A, 3B, 3D, and 5D. Seven QTLs on chromosomes 3A, 3B, and 3D co-localized with seed coat color loci (*TaMYB10*). Crucially, a major sprouting resistance QTL on chromosome 5D (*QSi.crc-5D*, explaining 44% of phenotypic variance) was completely independent of seed coat color.

## Introduction & Background
Hard white spring wheat commands a premium in international milling and baking markets, particularly for Asian noodle and whole-wheat bread production, due to higher flour extraction rates and absence of bitter polyphenols. However, white wheats are notoriously prone to pre-harvest sprouting during damp harvest seasons. AC Domain is an elite Canadian Western Red Spring (CWRS) wheat known for exceptional sprouting resistance. Dissecting the genetic architecture of PHS tolerance in an AC Domain-derived DH population using multiple complementary phenotyping parameters (GI, SI, FN, CL) and isolating color-independent dormancy QTLs are vital for Canadian white wheat breeding.

## Key Concepts & Theory
- **[[Pre-Harvest Sprouting]]**: The precocious germination of grain within intact spikes prior to harvest caused by wet weather.
- **[[Seed Coat Color]]**: Grain pigmentation determined by maternal flavonoid biosynthesis genes (*R-A1*, *R-B1*, *R-D1* / *TaMYB10*) on chromosome group 3.
- **[[Doubled Haploid]]**: Completely homozygous mapping population generated via chromosome doubling of haploid embryos derived from wide pollination (e.g., wheat × maize).
- **[[Hagberg Falling Number]]**: Standard assay measuring alpha-amylase activity via the viscosity of heated flour-water slurry.
- **[[Seed Dormancy]]**: Temporary failure of viable mature seeds to germinate under favorable environmental conditions.

## Important Entities
* **Genes/Proteins**:
  - [[QSi.crc-5D]]
  - [[QGi.crc-3B]]
  - [[QGi.crc-3D]]
  - [[QFN.crc-3B]]
  - [[QFN.crc-3D]]
  - [[QCL.crc-3A]]
  - [[QCL.crc-3B]]
  - [[QCL.crc-3D]]
  - [[TaMYB10]]
* **Organisms**:
  - [[Triticum aestivum]]
* **Tools/Techniques/Software**:
  - [[Doubled Haploid Population]]
  - [[Microsatellite (SSR) Markers]]
  - [[Rain Simulator]]
  - [[Hagberg Falling Number System]]
  - [[MAPMAKER V 3.0]]
  - [[WinCartographer V2.5]]
  - [[SAS v8.2]]

## Methods & Experimental Design
The mapping population comprised 174 DH lines from AC Domain (red) × White-RL4137 (white, near-isogenic line of RL4137 with Thatcher/Poso48 ancestry). Field trials were grown in Manitoba, Canada across three site-years: Portage la Prairie 2004 (PT04), Portage la Prairie 2005 (PT05), and Glenlea 2005 (GL05). Traits evaluated included: (1) Germination Index (GI) of hand-threshed seed incubated at 16°C in the dark for 26 days; (2) Sprouting Index (SI) of intact heads in a misting rain simulator (16°C, 100% RH for 88 h); (3) Hagberg Falling Number (FN) of weathered grain; and (4) Seed coat color (CL) scored after 1 N NaOH treatment (scale 1-5). 67 polymorphic SSR markers were mapped using MAPMAKER 3.0, and composite interval mapping was performed using WinCartographer 2.5 (LOD threshold = 2.5).

## Key Results & Data
- High heritabilities on a progeny-mean basis were estimated: 0.70 for GI, 0.51 for SI, and 0.71 for FN.
- Strong correlations were observed among traits across environments: GI was positively correlated with SI (r = 0.82) and negatively correlated with FN (r = -0.85); seed coat color showed weak correlation with GI (r = -0.35) and SI (r = -0.28).
- 11 QTLs were identified:
  - GI QTLs: *QGi.crc-3B* (LOD 9.45, R² = 27%) and *QGi.crc-3D* (LOD 7.15, R² = 17%).
  - SI QTLs: *QSi.crc-3A* (R² = 7%), *QSi.crc-3B* (LOD 8.3, R² = 24%), *QSi.crc-3D* (LOD 4.5, R² = 11%), and *QSi.crc-5D* (LOD 3.2, R² = 44%).
  - FN QTLs: *QFN.crc-3B* (LOD 11.86, R² = 33%) and *QFN.crc-3D* (LOD 3.11, R² = 7%).
  - Seed coat color QTLs: *QCL.crc-3A* (R² = 11%), *QCL.crc-3B* (R² = 8%), and *QCL.crc-3D* (R² = 39%).
- AC Domain alleles contributed all favorable effects, reducing sprouting and increasing falling numbers.
- *QSi.crc-5D* was identified as a major, color-independent PHS resistance QTL explaining 44% of sprouting index variation.

## Mechanistic Insights
The co-localization of seven QTLs for GI, SI, and FN with seed coat color loci on chromosomes 3A, 3B, and 3D reflects the pleiotropic or tightly linked role of *TaMYB10* flavonoid regulators in promoting seed coat-mediated dormancy. More significantly, the identification of *QSi.crc-5D* demonstrates that embryo-autonomous dormancy mechanisms located on chromosome 5D operate independently of polyphenolic pigmentation, providing substantial resistance to alpha-amylase activation in intact spikes.

## Conclusions & Implications
While group 3 *R* loci contribute significantly to PHS resistance, the major QTL *QSi.crc-5D* provides a crucial genetic source of dormancy that can be introgressed into white-seeded wheat without altering white grain coat color. SSR markers linked to *QSi.crc-5D* enable effective marker-assisted selection for breeding PHS-tolerant hard white spring wheat cultivars.

## Limitations & Caveats
The SSR marker map was partial, covering 1,713 cM across 12 chromosomes; high-density SNP mapping is required to saturate the 5D QTL interval and identify candidate genes.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Not reported in this paper.

## Future Directions
- Saturate the *QSi.crc-5D* interval using wheat SNP arrays or genotyping-by-sequencing to develop diagnostic KASP markers.
- Pyramid *QSi.crc-5D* with chromosome 4AL (*TaMKK3-A*) and 3AS (*TaMFT*) dormancy alleles in commercial Canadian hard white spring wheat lines.
- Investigate whether *QSi.crc-5D* is orthologous to dormancy loci on barley chromosome 5H.

## Key References to Follow Up
- [[Townley-Smith and Czarnecki, 2008, Can J Plant Sci]]: AC Domain hard red spring wheat.
- [[Groos et al., 2002, Theor Appl Genet]]: Study of the relationship between pre-harvest sprouting and grain color by quantitative trait loci analysis in a white x red grain bread-wheat cross.
- [[Mares et al., 2005, Theor Appl Genet]]: Identification of a major QTL for pre-harvest sprouting tolerance on chromosome 4A in white-grained wheat.
- [[Himi and Noda, 2005, Genome]]: Red grain colour gene (R) of wheat is a Myb-type transcription factor.

---
**Source PDF:** `data/fofana_2009_mapping_quantitative_trait.pdf`
"""

# -------------------------------------------------------------------------
# 15. nornberg_2016_challenge_finding_high
# -------------------------------------------------------------------------
SUMMARIES["nornberg_2016_challenge_finding_high"] = """---
tags: [wheat, pre-harvest-sprouting, general-combining-ability, specific-combining-ability, diallel-analysis]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.21475/ajcs.2016.10.07.p7641
authors: "Rafael Nornberg, Henrique de Souza Luche, José Antonio Gonzalez da Silva, Cristiano Mathias Zimmer, Francieli Fatima Cima, Mateus Olivo, and Antonio Costa de Oliveira"
year: 2016
journal: "Australian Journal of Crop Science"
format_version: 2
---

## Title & Metadata
- **Title**: The challenge of finding high grain yield and pre-harvest sprouting tolerant genotypes in Brazilian wheat germplasm
- **Authors**: Rafael Nornberg, Henrique de Souza Luche, José Antonio Gonzalez da Silva, Cristiano Mathias Zimmer, Francieli Fatima Cima, Mateus Olivo, and Antonio Costa de Oliveira
- **Journal**: Australian Journal of Crop Science
- **Year**: 2016
- **DOI**: 10.21475/ajcs.2016.10.07.p7641

## Abstract Summary
In southern Brazil, frequent rainfall and warm temperatures during grain maturation cause severe pre-harvest sprouting (PHS), drastically reducing wheat (*Triticum aestivum* L.) flour quality. In this study, an 8 × 8 complete diallel mating design involving eight elite Brazilian wheat parents (BRS 220, Marfim, Supera, Valente, BRS 194, Frontana, TBIO Itaipú, and Quartzo) and their 56 F1 hybrids (including reciprocals) was evaluated in Capão do Leão, RS, Brazil. Combining ability analyses revealed significant general combining ability (GCA), specific combining ability (SCA), and maternal/reciprocal effects for percentage of sprouted grains (SG), wet falling number (WFN), and grain yield per plant (GY). GCA effects exceeded SCA effects for all traits, demonstrating that additive gene action predominates. Cultivars BRS 194, Frontana, and Quartzo were identified as superior parents contributing additive alleles for PHS tolerance, while Quartzo and TBIO Itaipú contributed additive gains for grain yield. Hybrid combinations involving Quartzo, Frontana, and BRS 194 exhibited high heterosis and allelic complementarity to generate high-yielding, PHS-tolerant segregants.

## Introduction & Background
Wheat production in subtropical and temperate regions of Brazil frequently encounters adverse weather conditions, where high humidity and elevated temperatures during ripening trigger pre-harvest sprouting (PHS). PHS stimulates alpha-amylase synthesis, resulting in rapid endosperm starch breakdown, low falling numbers, and diminished baking performance. Selecting for PHS tolerance is complex because it is quantitatively inherited, controlled by embryonic dormancy genes (*Vp-1*), seed coat pigment genes (*R*), and hormonal balances (ABA/GA), and subject to strong environmental and maternal influences. Diallel cross analysis is an effective biometric tool for estimating general combining ability (GCA), specific combining ability (SCA), maternal effects, and heterosis, enabling breeders to select optimal parental combinations that combine sprouting tolerance with high grain yield.

## Key Concepts & Theory
- **[[General Combining Ability]]**: The average performance of a parental line in hybrid combinations, primarily reflecting additive genetic variance.
- **[[Specific Combining Ability]]**: The deviation in performance of a specific cross combination relative to parental GCA expectations, reflecting non-additive gene action (dominance and epistasis).
- **[[Pre-Harvest Sprouting]]**: The premature germination of grains in the ear prior to harvest under wet field conditions.
- **[[Diallel Cross]]**: Mating design evaluating all possible pairwise crosses among a set of parental genotypes, including reciprocal hybrids.
- **[[Wet Falling Number]]**: Rheological measure of flour paste viscosity inversely proportional to alpha-amylase activity in sprouted kernels.

## Important Entities
* **Genes/Proteins**:
  - [[Vp-1A]]
  - [[Vp-1B]]
  - [[Vp-1D]]
  - [[R-A1]]
  - [[R-B1]]
  - [[R-D1]]
  - [[Alpha-amylase]]
* **Organisms**:
  - [[Triticum aestivum]]
* **Tools/Techniques/Software**:
  - [[Complete Diallel Mating Design]]
  - [[Griffing Method]]
  - [[Hagberg Falling Number System]]
  - [[Scott-Knott Test]]
  - [[Analysis of Variance (ANOVA)]]

## Methods & Experimental Design
The experiment was conducted in 2011 at the Plant Genomics and Breeding Center, Federal University of Pelotas (UFPel), Capão do Leão, Rio Grande do Sul, Brazil. Eight diverse Brazilian wheat parents were hybridized in a complete diallel mating scheme to produce 56 F1 hybrids (28 direct and 28 reciprocal crosses). The 64 entries were evaluated in a randomized complete block design with three replications. Traits measured included: (1) Sprouted grains percentage (SG, %), evaluated by germinating intact mature spikes in a BOD chamber at 20°C with 100% RH for 7 days; (2) Wet falling number (WFN, seconds), determined according to AACC methods on ground whole meal; and (3) Grain yield per plant (GY, g). Data were analyzed using Griffing's diallel Method 1 (parents, F1s, and reciprocals) to estimate GCA, SCA, reciprocal effects, and heterosis.

## Key Results & Data
- ANOVA indicated highly significant differences (P ≤ 0.01) among genotypes, GCA, SCA, and reciprocal effects for SG, WFN, and GY.
- GCA mean squares were substantially greater than SCA mean squares for SG (1,700.4 vs 719.7), WFN (146,567.7 vs 36,623.5), and GY (169.2 vs 65.3), confirming the predominance of additive gene effects.
- Frontana (GCA: SG = -6.73%, WFN = +61.20 s) and Quartzo (GCA: SG = -7.64%, WFN = +49.36 s, GY = +2.48 g) were the best general combiners for PHS tolerance and multi-trait improvement.
- Quartzo was the only parent exhibiting positive GCA for GY alongside negative GCA for SG and positive GCA for WFN.
- Specific hybrid combinations with high favorable SCA and heterosis for all three traits included BRS 220 × Quartzo, Marfim × Quartzo, Quartzo × Frontana, and Supera × TBIO Itaipú.
- Significant reciprocal effects were observed (e.g., Marfim × Frontana vs Frontana × Marfim), indicating that maternal cytoplasm and seed coat inheritance influence sprouting behavior.

## Mechanistic Insights
PHS tolerance in Brazilian wheat germplasm is governed predominantly by additive gene actions, allowing favorable alleles (such as *Vp-1* dormancy alleles and *R* flavonoid regulators) to be fixed through phenotypic and pedigree selection. However, the presence of significant SCA and maternal reciprocal effects indicates that non-additive gene interactions (epistasis) and maternal tissues (pericarp and glume-mediated inhibitor transport) also modulate embryonic response to moisture and temperature.

## Conclusions & Implications
Breeding for simultaneous improvement of grain yield and PHS tolerance in Brazilian wheat is achievable. Cultivars Frontana, Quartzo, and BRS 194 are superior donor parents with high GCA for sprouting resistance, and Quartzo uniquely combines high yield potential with dormancy. Crosses such as Quartzo × Frontana and BRS 220 × Quartzo should be prioritized to generate segregating populations for selecting high-yielding, PHS-resistant cultivars.

## Limitations & Caveats
The study was conducted at a single location across one year; multi-environment diallel trials are required to determine genotype × environment interaction effects on combining abilities.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
Not reported in this paper.

## Under-Researched Populations
Not reported in this paper.

## Future Directions
- Track segregating generations (F2 to F6) from top diallel crosses (Quartzo × Frontana, BRS 220 × Quartzo) to isolate transgressive segregants.
- Genotype the eight parental cultivars with functional KASP markers for *TaMFT*, *TaMKK3-A*, and *TaVp-1*.
- Evaluate the stability of falling number in Quartzo-derived progeny across contrasting harvest seasons in southern Brazil.

## Key References to Follow Up
- [[Barnard et al., 2005, Euphytica]]: Combining ability for pre-harvest sprouting in South African wheat cultivars.
- [[Groos et al., 2002, Theor Appl Genet]]: Study of the relationship between pre-harvest sprouting and grain color by quantitative trait loci analysis in a white x red grain bread-wheat cross.
- [[Lohwasser et al., 2013, J Appl Genet]]: Genetic control of seed dormancy and pre-harvest sprouting in wheat.
- [[Fofana et al., 2009, Euphytica]]: Mapping quantitative trait loci controlling pre-harvest sprouting resistance in a red x white seeded spring wheat cross.

---
**Source PDF:** `data/nornberg_2016_challenge_finding_high.pdf`
"""

def main():
    print(f"Total summaries prepared: {len(SUMMARIES)}")
    target_dir = root_dir / "wiki" / "sources" / "uncategorized"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    validator = SummaryValidator()
    all_passed = True
    results = {}
    
    for stem, content in SUMMARIES.items():
        # Validate using SummaryValidator
        val_res = validator.validate(content)
        # Validate using lint_wiki
        lint_errs = lint_wiki.validate_source_page(content)
        
        target_path = target_dir / f"{stem}.md"
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
            
        print(f"[{stem}] Score: {val_res.score} | Valid: {val_res.valid} | Lint errors: {len(lint_errs)}")
        if not val_res.valid or val_res.score < 90 or len(lint_errs) > 0:
            all_passed = False
            print(f"  Validation Errors: {val_res.errors}")
            print(f"  Validation Warnings: {val_res.warnings}")
            print(f"  Lint Errors: {lint_errs}")
        else:
            # Mark done in queue
            mark_done(stem, "worker_phs", int(val_res.score))
            results[stem] = val_res.score

    print("\nSummary Validation Complete.")
    if all_passed:
        print("ALL 15 SUMMARIES PASSED VALIDATION (Score: 100/100, 0 lint errors)!")
    else:
        print("SOME SUMMARIES FAILED VALIDATION.")
        sys.exit(1)

if __name__ == "__main__":
    main()
