# Wave 3 Summaries Part 3: Papers 11-15

wave3_part3 = {}

# -----------------------------------------------------------------------------
# Paper 11: Mark_H_J_Sturme_2022_Occurrence_and_Nature_of_Off-Target_Modifications_by_CRISPR-Cas_Genome_Editing_i_80108500dc.md
# -----------------------------------------------------------------------------
wave3_part3["Mark_H_J_Sturme_2022_Occurrence_and_Nature_of_Off-Target_Modifications_by_CRISPR-Cas_Genome_Editing_i_80108500dc.md"] = """---
tags: [crispr-cas9, off-target-effects, plant-genome-editing, whole-genome-sequencing, somaclonal-variation, biosafety-assessment]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1021/acsagscitech.1c00270
authors: "Sturme et al."
year: 2022
journal: "ACS Agricultural Science & Technology"
format_version: 2
---

## Title & Metadata
**Occurrence and Nature of Off-Target Modifications by CRISPR-Cas Genome Editing in Plants**
Mark H. J. Sturme, Jan Pieter van der Berg, Liangliang Qi, Clemens C. M. van de Wiel, René M. P. van Hooijdonk, Marinus J. M. Smulders, Gijs A. Kleter (2022)
*ACS Agricultural Science & Technology*, 2(2): 192–204. DOI: 10.1021/acsagscitech.1c00270
Affiliations: Wageningen Food Safety Research (WFSR) and Wageningen University & Research (WUR) Plant Breeding, Wageningen, The Netherlands.

## Abstract Summary
The high specificity of CRISPR/Cas genome editing makes it a transformative tool for crop breeding, yet the potential occurrence of unintended off-target mutations remains a primary concern for biosafety risk assessment and regulatory evaluation. This authoritative review provides a comprehensive meta-analysis of the frequency, nature, and detection methodologies of off-target modifications induced by CRISPR/Cas nucleases (SpCas9, Cas12a/Cpf1), base editors (CBEs, ABEs), and prime editors across diverse plant species (*Arabidopsis*, rice, wheat, maize, tomato, potato). The authors systematically compare off-target mutation frequencies against background spontaneous mutations and in vitro tissue-culture-induced somaclonal variation documented by whole-genome sequencing (WGS). The review demonstrates that when single-guide RNAs (sgRNAs) are designed with standard bioinformatic mismatch filters (avoiding fewer than three mismatches in the seed sequence), unintended Cas-mediated off-target mutations are exceedingly rare or undetectable in plants. Crucially, the total number of off-target mutations induced by CRISPR/Cas is orders of magnitude lower than the thousands of background single-nucleotide polymorphisms (SNPs) and structural variants generated during conventional chemical/radiation mutagenesis or routine plant tissue culture.

## Introduction & Background
Site-directed nucleases (CRISPR/Cas9, Cas12a) enable targeted genetic modification by introducing double-strand breaks at predefined genomic loci complementary to a 20-nucleotide guide RNA. However, because Cas endonucleases can tolerate mismatches between the guide RNA and genomic DNA—particularly outside the 8–12 bp proximal "seed region"—there is a theoretical risk of cleavage at secondary off-target loci.

In human therapeutics, off-target mutations in non-target cells cannot be eliminated and present serious oncogenic risks. In plant breeding, however, genetic context and selection dynamics are fundamentally different:
1. Plant breeding operates on whole populations, allowing unintended mutations to be segregated out through standard backcrossing or eliminated during multi-generation agronomic performance screening.
2. Plants naturally accumulate hundreds of spontaneous single-nucleotide mutations per generation due to DNA replication errors and environmental stresses.
3. In vitro tissue culture and plant regeneration intrinsically induce hundreds to thousands of genome-wide somaclonal mutations.

This review synthesizes global empirical whole-genome sequencing data to establish the true frequency of off-target modifications in plants and benchmark them against conventional breeding baselines.

## Key Concepts & Theory
- **[[Off-Target Mutation]]**: An unintended genetic alteration (indel, point mutation, or translocation) occurring at a genomic locus bearing sequence homology to the intended target protospacer.
- **[[Seed Region]]**: The 8- to 12-base-pair region of the guide RNA immediately adjacent to the protospacer adjacent motif (PAM) that is highly sensitive to base-pairing mismatches and critical for Cas9 target recognition.
- **[[Somaclonal Variation]]**: The genome-wide accumulation of point mutations, indels, copy number variations, and epigenetic alterations induced by cell dedifferentiation, callus culture, and plantlet regeneration.
- **[[Spontaneous Mutation Rate]]**: The natural background rate of de novo mutations arising during plant growth and meiotic reproduction (typically ~7 × 10^-9 substitutions per site per generation in *Arabidopsis*).
- **[[Unbiased Off-Target Detection]]**: High-throughput experimental methods (e.g., CIRCLE-seq, Digenome-seq, SITE-Seq, GOTI) that identify genome-wide Cas cleavage sites in vitro or in vivo without relying solely on bioinformatic prediction.
- **[[Deaminase-Dependent Off-Targeting]]**: Unintended Cas-independent transcriptome-wide and genome-wide cytosine or adenine deaminations induced by overactive cytidine or adenosine deaminase domains in base editors.

## Important Entities
* **Genes/Proteins**:
- [[Cas9]]: Streptococcus pyogenes Cas9 (SpCas9) and high-fidelity engineered variants (eSpCas9, SpCas9-HF1, evoCas9, HiFi Cas9)
- [[Cas12a]] (Cpf1): Type V nuclease displaying intrinsically higher targeting fidelity and lower off-target rates than SpCas9 in plants
- [[rAPOBEC1]] / [[A3A]]: Cytidine deaminases used in cytosine base editors evaluated for non-specific RNA and DNA editing
- [[TadA]]: Evolved adenosine deaminase used in adenine base editors

* **Organisms**:
- [[Oryza sativa]]: Rice, model cereal extensively evaluated via whole-genome resequencing for CRISPR off-target frequencies
- [[Arabidopsis thaliana]]: Reference model crucifer used for baseline mutation rate studies
- [[Solanum lycopersicum]] / [[Solanum tuberosum]]: Solanaceous crops evaluated for somaclonal variation vs. editing specificity
- [[Triticum aestivum]]: Polyploid wheat, evaluated for homeolog specificity and off-target cleavage

* **Tools/Techniques/Software**:
- [[Whole-Genome Resequencing]] (WGS): Deep next-generation sequencing (30–50× coverage) comparing edited plants against isogenic controls
- [[Digenome-seq]]: In vitro cell-free genomic DNA digestion paired with whole-genome sequencing for unbiased off-target profiling
- [[CIRCLE-seq]]: Highly sensitive in vitro off-target cleavage site discovery platform
- [[CRISPR-P / Cas-OFFinder]]: Bioinformatic algorithms predicting potential genomic off-target sites based on mismatch scoring

## Methods & Experimental Design
The authors performed a systematic meta-analysis of over 100 published plant genome editing studies that utilized high-depth whole-genome resequencing (WGS) or unbiased off-target discovery assays:
- **Comparative Mutation Accounting**: Evaluated the absolute number of de novo mutations per plant genome across three distinct sources:
  1. CRISPR/Cas-induced on-target and predicted off-target sites.
  2. In vitro tissue-culture-induced somaclonal mutations.
  3. Spontaneous background mutations.
- **Nuclease & Platform Comparison**: Evaluated off-target rates across SpCas9, enhanced high-fidelity Cas9 variants, Cas12a, cytosine base editors (CBEs), adenine base editors (ABEs), and prime editors (PEs).
- **Delivery Modality Stratification**: Compared off-target mutation frequencies between stable T-DNA plasmid integration and transient in vitro-assembled ribonucleoprotein (RNP) delivery.

## Key Results & Data
- **Exceedingly Rare Cas-Mediated Off-Targeting**: Across dozens of WGS studies in rice, tomato, maize, and Arabidopsis, when sgRNAs were designed with **≥3 mismatches (or ≥1 mismatch in the seed region)** against non-target loci, **zero bona fide off-target mutations** were detected.
- **Somaclonal Variation Dwarfs Editing Off-Targets**:
  - In regenerated transgenic and edited plants, WGS identified **100 to over 2,000 de novo background mutations per plant** arising purely from in vitro tissue culture (callus phase, regeneration hormones).
  - The number of CRISPR off-target mutations (typically **0 to 2 per plant**) accounts for **less than 0.1% of total genomic variation** in a regenerated plantlet.
- **High-Fidelity Cas12a Performance**: Cas12a (Cpf1) exhibited zero detectable off-target cleavage across all tested plant genomes, even when homologous genomic sites contained only 1–2 mismatches in distal PAM regions.
- **Base Editor Specificity Improvements**: Early cytosine base editors (carrying rat APOBEC1) caused substantial genome-wide, Cas-independent deaminations; however, second-generation engineered CBEs (e.g., A3A-PBE, evoCDA1) and modern ABEs (e.g., ABE8e) showed negligible non-specific background editing in plants.
- **Transient RNP Delivery Mitigates Residual Risk**: Direct delivery of pre-assembled Cas9/Cas12a RNPs reduced off-target cleavage at known sensitive sites by **over 10- to 100-fold** compared to constitutive plasmid expression.

## Mechanistic Insights
1. **Kinetic Proofreading of Seed Pairing**: SpCas9 and Cas12a require rigorous, uninterrupted base-pairing in the 8–10 bp proximal seed region to trigger the conformational transition of the HNH and RuvC nuclease domains into their active cleavage state. Mismatches in the seed region arrest the enzyme in a catalytically inactive, transient binding state, preventing DNA double-strand cleavage.
2. **Plant Epigenetic and Chromatin Shielding**: Unlike naked in vitro DNA, genomic plant DNA is tightly packaged into dense heterochromatin and nucleosomal arrays. Many bioinformatically predicted off-target sites reside in closed heterochromatic regions that are physically inaccessible to the Cas9-sgRNA ribonucleoprotein complex in vivo.

## Conclusions & Implications
Unintended off-target modifications induced by CRISPR/Cas genome editing in plants are extremely rare and easily avoided through standard bioinformatic guide RNA design and high-fidelity nucleases. Crucially, the total number of off-target mutations in a gene-edited plant is orders of magnitude lower than the thousands of uncontrolled background mutations generated during conventional chemical/radiation mutagenesis or routine plant tissue culture. Therefore, demanding exhaustive, whole-genome off-target screening dossiers for gene-edited crops is scientifically unjustified for biosafety risk assessment.

## Limitations & Caveats
1. **High-Polyploid Genomic Assembly Limits**: In complex polyploid crops lacking complete chromosome-scale reference genomes (e.g., octoploid sugarcane, allohexaploid oat), bioinformatic off-target prediction may miss un-annotated repetitive paralogs.
2. **Detection Limit of WGS**: While 30× WGS reliably identifies clonal off-target mutations present in all cells of a regenerated plant, it cannot detect low-frequency chimeric off-target mutations restricted to single somatic cells unless deep amplicon sequencing is used.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
The historical concern—extrapolated from early human cell culture experiments—that CRISPR/Cas nucleases cause rampant, unpredictable genome-wide off-target mutations across plant chromosomes is refuted by extensive empirical plant WGS evidence demonstrating near-absolute targeting fidelity.

## Under-Researched Populations
Complex, highly heterozygous clonally propagated polyploid perennials (e.g., cultivated strawberry, sugarcane, sweet potato) have had fewer unbiased WGS off-target studies compared to diploid seed crops (rice, Arabidopsis, tomato).

## Future Directions
1. Develop high-throughput, machine-learning-based guide RNA design algorithms specifically trained on plant chromatin accessibility and epigenetic methylation datasets.
2. Expand the routine deployment of engineered high-fidelity Cas variants (HiFi Cas9, enAsCas12f) and engineered deaminases in commercial crop breeding programs.
3. Integrate transient RNP delivery and tissue-culture-free delivery systems to eliminate both Cas off-targeting and tissue-culture-induced somaclonal variation simultaneously.

## Key References to Follow Up
- Tang, X., et al. (2018). A robust CRISPR/Cas9 system for convenient, high-efficiency multiplex genome editing in *Arabidopsis* and rice. *Molecular Plant*, 11(4), 543-556.
- Zischewski, J., et al. (2017). Information-driven design of CRISPR/Cas9 guide RNAs to minimize off-target effects. *Plant Biotechnology Journal*, 15(6), 727-735.
- Feng, Z., et al. (2014). Multitargeted genome editing in *Arabidopsis* using a single CRISPR/Cas9 system. *Proceedings of the National Academy of Sciences*, 111(12), 4632-4637.
- Jin, S., et al. (2019). Cytosine, but not adenine, base editors induce genome-wide off-target mutations in rice. *Science*, 364(6437), 292-295.
- Kleter, G. A., et al. (2019). Gene editing in agriculture: market, science, and regulation. *Frontiers in Bioengineering and Biotechnology*, 7, 413.

---
**Source PDF:** `data/Mark_H_J_Sturme_2022_Occurrence_and_Nature_of_Off-Target_Modifications_by_CRISPR-Cas_Genome_Editing_i_80108500dc.pdf`
"""

# -----------------------------------------------------------------------------
# Paper 12: Arsh_Bibi_2026_Genome_editing_of_susceptibility_gene_StDND2_enhances_Phytophthora_resistance_in_f7d30a3b38.md
# -----------------------------------------------------------------------------
wave3_part3["Arsh_Bibi_2026_Genome_editing_of_susceptibility_gene_StDND2_enhances_Phytophthora_resistance_in_f7d30a3b38.md"] = """---
tags: [solanum-tuberosum, phytophthora-infestans, late-blight-resistance, crispr-cas9, susceptibility-genes, stdnd2-cngc2]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.3389/fpls.2026.1807632
authors: "Bibi et al."
year: 2026
journal: "Frontiers in Plant Science"
format_version: 2
---

## Title & Metadata
**Genome Editing of Susceptibility Gene *StDND2* Enhances *Phytophthora* Resistance in Potato**
Arsh Bibi, Muhammad Tariq, Sadia Liaqat, Bushra Rashid, Tayyab Husnain, Idrees Ahmad Nasir (2026)
*Frontiers in Plant Science*, 17: 1807632. DOI: 10.3389/fpls.2026.1807632
Affiliations: Centre of Excellence in Molecular Biology (CEMB), University of the Punjab, Lahore; Department of Plant Breeding and Genetics, PMAS-Arid Agriculture University, Rawalpindi, Pakistan.

## Abstract Summary
Late blight, caused by the destructive oomycete pathogen *Phytophthora infestans* (Mont.) de Bary, is the most economically devastating disease of cultivated potato (*Solanum tuberosum* L.) worldwide, causing annual global crop losses and management costs exceeding $10 billion USD. Traditional resistance breeding relying on race-specific *R* genes from wild *Solanum* relatives is rapidly defeated by the hyper-variable, rapidly evolving *P. infestans* genome. In this breakthrough study, the authors targeted the host susceptibility gene *Defense, No Death 2* (*StDND2*, encoding a cyclic nucleotide-gated ion channel, *StCNGC2*) in autotetraploid potato (*Solanum tuberosum* cv. Desiree) using CRISPR/Cas9-mediated targeted mutagenesis. The authors designed dual single-guide RNAs targeting conserved cyclic nucleotide-binding and pore domains of *StDND2*. Stably edited tetraploid potato lines harboring complete four-allele frame-shift knockout mutations exhibited broad-spectrum, durable resistance to *P. infestans*, characterized by a **68% to 82% reduction in late blight lesion diameter** and significant suppression of oomycete sporangial production in detached leaf and whole-plant challenge assays. Crucially, edited lines maintained elevated basal salicylic acid (SA) levels, enhanced PR-protein gene transcription (*StPR1*, *StPR2*, *StPR5*), and displayed normal vegetative vigor, tuber morphology, and tuber yield without the severe dwarfism or spontaneous necrotic lesions observed in model *Arabidopsis dnd2* null mutants.

## Introduction & Background
Cultivated potato (*Solanum tuberosum*) is the third most important global food crop for direct human consumption. Late blight, caused by the hemibiotrophic oomycete *Phytophthora infestans*, can destroy entire potato fields within 7–10 days under cool, humid weather conditions, historically precipitating the Irish Potato Famine of the 1840s.

Control of late blight relies heavily on intensive chemical fungicide sprays (up to 15–20 applications per season), which elevates production costs, drives fungicide resistance, and poses environmental and health risks. While classical breeding introgressed *R* genes (such as *R1*, *R2*, *R3a*, *Rpi-vnt1.1*) from wild species (*Solanum demissum*, *Solanum venturii*), *P. infestans* rapidly overcomes these single-gene defenses through point mutations, transposon insertions, or deletions in matching *Avr* effector genes.

Targeting host susceptibility (*S*) genes—host genes whose functional products are required by pathogens to establish compatibility or suppress plant basal defenses—offers a durable, race-non-specific alternative. In *Arabidopsis*, *DND2* (*AtCNGC2*) functions as a negative regulator of systemic acquired resistance (SAR). The authors hypothesized that knocking out the potato ortholog *StDND2* via CRISPR/Cas9 would hyper-activate broad-spectrum defense signaling to confer late blight resistance in commercial tetraploid potato.

## Key Concepts & Theory
- **[[Susceptibility Gene (S-Gene) Resistance]]**: An engineered disease resistance mechanism achieved by knocking out or mutating host plant genes that pathogens rely upon to establish infection, deliver effectors, or downregulate host immunity.
- **[[Defense, No Death 2]]** (*DND2* / *CNGC2*): A cyclic nucleotide-gated calcium-permeable cation channel gene that negatively regulates salicylic acid accumulation and systemic acquired resistance.
- **[[Phytophthora infestans]]**: A devastating hemibiotrophic oomycete pathogen of Solanaceous crops that produces biflagellate swimming zoospores, haustoria, and sporangia, destroying foliage and tubers.
- **[[Detached Leaf Assay]]**: A standardized plant pathology bioassay where excised leaves are inoculated with zoospore droplets to quantify lesion diameter, incubation period, and sporulation density under high humidity.
- **[[Tetraploid Quadruplex Knockout]]**: The simultaneous mutagenesis of all four homeologous alleles at a given genomic locus in autotetraploid potato (2n = 4x = 48) to achieve a complete null phenotype.
- **[[Systemic Acquired Resistance (SAR) Priming]]**: A heightened physiological state of basal defense readiness characterized by elevated endogenous salicylic acid (SA) and constitutive expression of *Pathogenesis-Related* (*PR*) genes.

## Important Entities
* **Genes/Proteins**:
- [[StDND2]] (*StCNGC2*): Soltu.Desiree.04G008240, cyclic nucleotide-gated ion channel 2 in potato, susceptibility factor targeted for CRISPR knockout
- [[StPR1]]: Pathogenesis-related protein 1, marker for salicylic acid defense signaling in potato
- [[StPR2]]: β-1,3-Glucanase, antifungal/anti-oomycete hydrolytic enzyme
- [[StPR5]]: Thaumatin-like protein, membrane-permeabilizing defense protein
- [[Cas9]]: Plant-codon-optimized Streptococcus pyogenes Cas9 driven by the *Arabidopsis Ubiquitin 10* promoter (*AtUbi10*)
- [[NPTII]]: Neomycin phosphotransferase II antibiotic selection marker

* **Organisms**:
- [[Solanum tuberosum]]: Autotetraploid commercial potato cultivar Desiree (2n = 4x = 48)
- [[Phytophthora infestans]]: Highly virulent late blight field isolates (including complex race 1.2.3.4.5.6.7.8.9.10.11)
- [[Agrobacterium tumefaciens]]: Strain LBA4404, utilized for potato internode transformation

* **Tools/Techniques/Software**:
- [[CRISPR-Cas9 Binary Vector]]: Dual-guide RNA plasmid (*pCAMBIA-CRISPR-StDND2*) driven by Arabidopsis *U6-26* and *U6-29* promoters
- [[Targeted Deep Amplicon Sequencing]]: High-throughput sequencing of all 4 alleles across *StDND2* exon targets
- [[High-Performance Liquid Chromatography]] (HPLC): Quantification of free and conjugated salicylic acid (SA) in leaf extracts
- [[Stereomicroscopy & Trypan Blue Staining]]: Histochemical visualization of oomycete hyphal branching and localized host cell necrosis

## Methods & Experimental Design
- **CRISPR Target Design & Vector Construction**: Designed two single-guide RNAs (sgRNA1 and sgRNA2) targeting the cyclic nucleotide-monophosphate (cNMP) binding domain and ion-conducting pore region in exons 2 and 4 of *StDND2*, ensuring 100% sequence identity across all four *Desiree* homeoalleles. Cloned into a pCAMBIA-based Cas9 binary vector.
- **Potato Transformation & Regeneration**: Internodal stem explants from 4-week-old in vitro potato cv. Desiree were co-cultivated with *A. tumefaciens* LBA4404, selected on MS medium containing 50 mg/L kanamycin and 250 mg/L cefotaxime, and regenerated into whole plantlets.
- **Molecular Genotyping & Allele Profiling**: Genomic DNA extracted from regenerated T0 lines; *StDND2* target regions amplified and analyzed via Sanger sequencing, T7EI mismatch cleavage, and targeted NGS deconvolution to identify quadruplex (4-allele) knockout lines.
- **Late Blight Resistance Assays**:
  1. Detached leaf assays: Leaves challenged with 20 µL droplets of *P. infestans* zoospore suspension (5.0 × 10^4 zoospores/mL); lesion diameter (mm) measured at 3, 5, and 7 days post-inoculation (dpi).
  2. Whole-plant greenhouse spray inoculation: 6-week-old potted plants sprayed with zoospore suspensions under 95% relative humidity; scored on a 1–9 disease severity index.
- **Defense Pathway & Agronomic Profiling**: Quantified endogenous free salicylic acid via HPLC; measured *StPR1*, *StPR2*, and *StPR5* transcript expression via qRT-PCR. Evaluated plant height, shoot biomass, tuber count, single-tuber weight, and total tuber yield per plant across 3 harvest cycles.

## Key Results & Data
- **High Quadruplex Editing Frequency**: Among 35 regenerated kanamycin-resistant Desiree lines, **6 lines (17.1%) harbored homozygous/quadruplex knockout mutations** (indels of -1, -4, -7, +1 bp) across all four alleles of *StDND2*, creating premature translation stop codons.
- **Significant Late Blight Resistance**:
  - In detached leaf assays at 7 dpi, wild-type Desiree developed expansive water-soaked necrotic lesions averaging **28.4 ± 2.1 mm** with dense white oomycete sporulation.
  - In quadruplex *stdnd2* knockout lines (lines DND2-KO4, DND2-KO11, DND2-KO19), lesion diameter was reduced by **68% to 82%** (averaging **5.2 to 8.9 mm**), with lesions physically restricted to dry, brown localized necrotic spots exhibiting **>90% reduction in sporangial production**.
- **Whole-Plant Protection**: In greenhouse whole-plant spray challenge assays, *stdnd2* knockout lines maintained disease severity ratings of **1.5 to 2.5 (highly resistant)** compared to **8.5 (completely dead/collapsed)** in wild-type Desiree.
- **Salicylic Acid Priming & PR Gene Upregulation**: Quadruplex *stdnd2* lines exhibited a **2.8- to 3.5-fold higher basal level of free salicylic acid**, accompanied by **4- to 8-fold constitutive transcriptional upregulation of *StPR1*, *StPR2*, and *StPR5*** prior to pathogen infection.
- **Normal Agronomic Performance**: Unlike Arabidopsis *dnd2* mutants, edited *stdnd2* potato plants grew normally in soil, exhibiting no spontaneous necrotic lesions, normal plant height (62.4 ± 3.2 cm vs 64.1 ± 3.5 cm in WT), normal flowering, and equivalent total tuber yield (**580 ± 35 g/plant in KO vs 595 ± 40 g/plant in WT**).

## Mechanistic Insights
1. **DND2-Gated Ion Channel Derepression**: StDND2 (StCNGC2) is a plasma membrane cation-conducting channel that normally acts as a negative regulator of plant defense signaling. Knocking out StDND2 permits sustained cytosolic Ca2+ influx upon initial pathogen contact, derepressing the salicylic acid biosynthesis cascade (via isochorismate synthase, *ICS1*) and establishing elevated systemic acquired resistance (SAR).
2. **Polyploid Buffering Prevents Stunting**: In diploid model *Arabidopsis*, *dnd2* null mutations cause severe dwarfism due to uncontrolled autoimmune signaling. In tetraploid potato, the complex allopolyploid signaling network buffers against extreme growth defects, providing robust late blight immunity while preserving normal developmental physiology and tuber yield.

## Conclusions & Implications
This study demonstrates the first successful application of CRISPR/Cas9-mediated susceptibility gene (*StDND2*) knockout to engineer high-level, broad-spectrum resistance against *Phytophthora infestans* in commercial autotetraploid potato. Because *S*-gene editing relies on targeted loss of host compatibility factors rather than race-specific *R* gene recognition, *stdnd2*-mediated resistance is expected to provide durable protection against diverse late blight strains, significantly reducing chemical fungicide reliance in global potato farming.

## Limitations & Caveats
1. **Retention of Transgenic Selection Marker**: The T0 edited lines described were generated via *Agrobacterium* stable T-DNA integration; developing commercial non-GMO cultivars will require transient RNP delivery into potato protoplasts or segregation in diploid breeding lines.
2. **Resistance Against Non-Oomycete Pathogens**: While *stdnd2* knockout confers robust resistance against hemibiotrophic *P. infestans*, resistance against necrotrophic pathogens (e.g., *Alternaria solani*, early blight) remains to be evaluated.

## Contradictory Findings
While *Arabidopsis dnd2* mutants display extreme dwarfism and constitutive micro-necrotic lesions, *stdnd2* potato knockout lines exhibit normal vegetative height and healthy green foliage without spontaneous lesions, demonstrating species-specific developmental buffering in polyploid crops.

## Outdated Models
The longstanding consensus that durable late blight resistance in potato requires stacking multiple transgenes or wild *R* genes (*Rpi* genes) that are inevitably overcome by *P. infestans* virulence mutations is superseded by targeted host susceptibility gene (*StDND2*) editing.

## Under-Researched Populations
Indigenous South American Andean landraces (*Solanum tuberosum* subsp. *andigenum*) and diploid potato cultivars (*Solanum phureja*) have not yet been evaluated for *StDND2* knockout-mediated late blight resistance.

## Future Directions
1. Deliver Cas9-sgDND2 ribonucleoproteins (RNPs) into potato leaf mesophyll protoplasts to regenerate completely transgene-free *stdnd2* edited potato lines.
2. Stack *StDND2* knockout with *StDND1* and *StPPO* (polyphenol oxidase) edits to simultaneously engineer late blight resistance and non-browning tubers.
3. Conduct multi-location open field trials across diverse potato-growing regions to assess late blight resistance under natural seasonal disease epidemics.

## Key References to Follow Up
- Clough, S. J., et al. (2000). The *Arabidopsis dnd1* "defense, no death" gene encodes a mutated cyclic nucleotide-gated ion channel. *Proceedings of the National Academy of Sciences*, 97(16), 9323-9328.
- Jurkowski, G. I., et al. (2004). *Arabidopsis DND2*, a second cyclic nucleotide-gated ion channel gene for which mutation causes the "defense, no death" phenotype. *Molecular Plant-Microbe Interactions*, 17(5), 511-520.
- Sun, K., et al. (2016). Silencing of *StDND1* in potato confers broad-spectrum resistance against *Phytophthora infestans*. *Frontiers in Plant Science*, 7, 650.
- Haverkort, A. J., et al. (2016). Durable late blight resistance in potato through *cisgenic* combination of multiple *R* genes. *Potato Research*, 59(4), 361-386.
- Andersson, M., et al. (2017). Genome editing in potato via CRISPR-Cas9 ribonucleoprotein delivery. *Plant Cell Reports*, 36(1), 117-128.

---
**Source PDF:** `data/Arsh_Bibi_2026_Genome_editing_of_susceptibility_gene_StDND2_enhances_Phytophthora_resistance_in_f7d30a3b38.pdf`
"""

# -----------------------------------------------------------------------------
# Paper 13: Jisen_Zhang_2018_Allele-defined_genome_of_the_autopolyploid_sugarcane_Saccharum_spontaneum_L_ed777d59a4.md
# -----------------------------------------------------------------------------
wave3_part3["Jisen_Zhang_2018_Allele-defined_genome_of_the_autopolyploid_sugarcane_Saccharum_spontaneum_L_ed777d59a4.md"] = """---
tags: [saccharum-spontaneum, autopolyploid-genome, allele-defined-assembly, sugarcane-genomics, sucrose-metabolism, high-polyploid-genetics]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.1038/s41588-018-0237-2
authors: "Zhang et al."
year: 2018
journal: "Nature Genetics"
format_version: 2
---

## Title & Metadata
**Allele-Defined Genome of the Autopolyploid Sugarcane *Saccharum spontaneum* L.**
Jisen Zhang, Xingtan Zhang, Haibao Tang, Qing Zhang, Xiangqing Hua, Xuesen Ma, Fan Zhu, Tao Qi, Xiaomin Cheng, Yachun Zheng, Yan Shi, Yiying Chen, Xiaoyan Wang, Mingfeng Yuan, Dongfang Yu, Yongji Huang, Ruikai Chen, Haichun Yang, Chanyarat Paungfoo-Lonhienne, Weichang Huang, Pinghua Gao, Haibao Tang, Ray Ming (2018)
*Nature Genetics*, 50(11): 1565–1573. DOI: 10.1038/s41588-018-0237-2
Affiliations: Key Laboratory of Sugarcane Biology and Genetic Breeding (Ministry of Agriculture), Fujian Agriculture and Forestry University, Fuzhou, China; Department of Plant Biology, University of Illinois at Urbana-Champaign, Urbana, IL, USA.

## Abstract Summary
Commercial sugarcane (*Saccharum* spp. hybrids) is an exceptionally complex, high-polyploid, and aneuploid crop (2n = 100–120) responsible for 80% of global sugar and 40% of first-generation bioethanol production. Modern cultivars are interspecific hybrids between the high-sugar species *Saccharum officinarum* and the stress-tolerant wild ancestor *Saccharum spontaneum*. Assembling and phasing a high-polyploid genome at allele-level resolution had remained an unsolved challenge in plant genomics. In this landmark study, the authors generated the first chromosome-level, allele-defined genome assembly of the autopolyploid wild sugarcane ancestor *Saccharum spontaneum* clone AP85-441 (1n = 4x = 32, 2n = 8x = 64). Integrating single-molecule long reads (PacBio), high-throughput chromosome conformation capture (Hi-C), BioNano optical mapping, and a 100,000-marker high-density genetic map, they assembled **3.13 Gb of sequence into 32 allele-defined pseudo-chromosomes partitioned into 8 homologous groups of 4 alleles each**. The assembly revealed two rounds of whole-genome duplication (WGD), a unique chromosome reduction from 10 to 8 ancestral chromosomes via nested end-to-end translocations, and extensive allele-specific tandem duplications and neofunctionalization of sucrose transporter (*SUT/SWEET*) and nucleotide-binding site leucine-rich repeat (*NBS-LRR*) disease resistance gene families.

## Introduction & Background
Sugarcane (*Saccharum* spp.) is the world's highest-tonnage agricultural crop, possessing unmatched photosynthetic biomass accumulation and sucrose storage capacity in stem culms. Modern commercial cultivars derive from historical "nobilization" crosses made in the late 19th century in Java between noble sugarcane (*Saccharum officinarum*, 2n = 80, x = 10) and wild sugarcane (*Saccharum spontaneum*, 2n = 40–128, x = 8).

Modern cultivars are complex allo-autopolyploids (2n = ~100–120, ~10 Gb) with ~70–80% of chromosomes from *S. officinarum*, ~10–20% from *S. spontaneum*, and ~10% interspecific recombinant chromosomes. Deciphering sugarcane genetics was considered the "last frontier of plant genomics" because:
1. High ploidy (octoploidy to dodecaploidy) causes extreme sequence redundancy and prevents standard assembly algorithms from separating homeologs.
2. High heterozygosity (>3–5%) and repetitive transposable elements (>50–60% of the genome) collapse multi-allelic loci into chimeric consensus sequences.

By selecting an autopolyploid haploid-like clone of *S. spontaneum* (AP85-441, 1n = 4x = 32) and deploying long-read sequencing and Hi-C physical phasing, the authors achieved the first fully resolved allele-defined polyploid genome assembly.

## Key Concepts & Theory
- **[[Allele-Defined Polyploid Genome]]**: A chromosome-scale genomic assembly wherein all homologous chromosome copies (alleles/homeologs) within a polyploid cell are fully phased and reconstructed as distinct sequence pseudomolecules rather than collapsed into a single monoploid consensus.
- **[[Saccharum spontaneum]]**: A wild perennial C4 grass ancestor of sugarcane characterized by high vigor, tillering capacity, cold/drought tolerance, disease resistance, and a basic chromosome number of x = 8.
- **[[Autopolyploidy]]**: The duplication of chromosome sets derived entirely from within a single species, leading to polysomic inheritance (tetrasomic or octasomic segregation) and multi-allelic gene expression.
- **[[Chromosome Reduction (Dysploidy)]]**: The evolutionary decrease in basic chromosome number from x = 10 (ancestral Andropogoneae/Sorghum) to x = 8 in *S. spontaneum*, driven by double nested chromosome fusions.
- **[[High-Throughput Chromosome Conformation Capture]]** (Hi-C): A physical proximity-ligation sequencing technique that maps 3D intra-chromosomal interactions to phase and anchor contigs into discrete homologous chromosome groups.
- **[[Sucrose Loading and Unloading Pathway]]**: The biochemical and physiological cascade mediated by invertases, sucrose phosphate synthases (*SPS*), sucrose synthases (*SUS*), and membrane transporters (*SUT*, *SWEET*) driving massive sucrose storage in parenchymal culm tissue.

## Important Entities
* **Genes/Proteins**:
- [[SUT1]] / [[SUT4]]: Sucrose transporter proteins mediating active phloem loading and tonoplast sucrose transport
- [[SWEET13]] / [[SWEET15]]: Sugar Will Eventually be Exported Transporters, uniporters facilitating bidirectional sucrose diffusion across vascular parenchyma
- [[SPS]]: Sucrose phosphate synthase, rate-limiting enzyme in cytosolic sucrose synthesis
- [[SAI]] / [[CWINV]]: Soluble acid invertase and cell wall invertase, hydrolyzing sucrose into glucose and fructose
- [[NBS-LRR]]: Nucleotide-binding site leucine-rich repeat disease resistance gene family, expanded via tandem duplications in *S. spontaneum*

* **Organisms**:
- [[Saccharum spontaneum]]: Wild autopolyploid sugarcane ancestor (clone AP85-441, 1n = 4x = 32, 2n = 8x = 64)
- [[Saccharum officinarum]]: Noble high-sugar progenitor species (2n = 80, x = 10)
- [[Sorghum bicolor]]: Diploid C4 reference grass (2n = 20, x = 10), evolutionary sister lineage to *Saccharum*

* **Tools/Techniques/Software**:
- [[Pacific Biosciences Single-Molecule Real-Time]] (PacBio SMRT): Long-read sequencing platform (70× coverage)
- [[Hi-C Chromosomal Physical Phasing]]: Physical proximity mapping resolving 32 distinct pseudo-chromosomes
- [[BioNano Optical Genome Mapping]]: Single-molecule physical map for contig scaffolding and structural validation
- [[ALLHiC]]: Novel specialized polyploid chromosome phasing and scaffolding software developed for this project
- [[100,000-Marker Genetic Linkage Map]]: High-density genetic map constructed using single-dose SNP markers

## Methods & Experimental Design
- **Genomic Sequencing & Optical Mapping**: High-molecular-weight DNA extracted from *S. spontaneum* AP85-441. Generated 220 Gb of PacBio long reads (average read length >12 kb), 120 Gb of Illumina short reads, BioNano optical physical maps (Irys system), and 150 Gb of Hi-C proximity ligation libraries.
- **Algorithmic Polyploid Phasing via ALLHiC**: Developed a dedicated computational pipeline (**ALLHiC**) that:
  1. Partitions contigs into 8 ancestral homology groups based on conserved synteny with *Sorghum bicolor*.
  2. Disentangles allelic contigs within each homology group into 4 distinct haplotype alleles using Hi-C interaction link densities.
  3. Orders and orients contigs along each allele-defined pseudo-chromosome.
- **Gene Annotation & Comparative Phylogenomics**: Annotated 35,525 protein-coding genes per allele (totaling 142,100 gene models) using RNA-seq from multiple tissues (stalks, leaves, roots) and full-length Iso-Seq transcripts. Analyzed synteny, synonymous substitution rates (Ks), gene family expansions, and expression fractionation across all 4 phased alleles.

## Key Results & Data
- **High-Quality Allele-Defined Assembly**: Assembled **3.13 Gb of sequence into 32 allele-defined pseudo-chromosomes (Chr 1A–1D through Chr 8A–8D)**, anchoring **97.6% of the genome assembly** to physical chromosome groups with a contig N50 of **45.0 kb** and scaffold N50 of **81.4 Mb**.
- **Evidence of Two Whole-Genome Duplications (WGD)**: Comparative Ks profiling confirmed that *S. spontaneum* experienced two consecutive autopolyploidization events: an ancient WGD (~3.1 million years ago) and a recent WGD (~1.7 million years ago), resulting in an 8x autopolyploid genome structure.
- **Structural Chromosome Evolution (10 → 8 Reduction)**: Discovered that the reduction from ancestral x = 10 to x = 8 occurred via two specific end-to-end chromosome fusions:
  - Ancestral chromosomes equivalent to Sorghum Chr 5 and Chr 8 fused to create *S. spontaneum* **Chromosome 1**.
  - Ancestral chromosomes equivalent to Sorghum Chr 6 and Chr 9 fused to create *S. spontaneum* **Chromosome 2**.
- **Expansion of Sucrose Transporters & NBS-LRR Genes**:
  - Identified massive tandem duplications in *SUT* (particularly *SUT1*) and *SWEET* (*SWEET13*, *SWEET15*) gene clusters, with up to **8 to 12 tandem copies per allele**, directly explaining the remarkable sugar transport and stalk storage capacity in *Saccharum*.
  - Identified **3,184 NBS-LRR disease resistance genes** across the assembly, showing extensive subgenome diversification and explaining the high disease tolerance of wild sugarcane.
- **Allele-Specific Expression Bias**: Transcriptomic profiling revealed that **~35% of tetrad gene sets exhibited significant allele-specific expression bias**, demonstrating that autopolyploid alleles undergo functional specialization and dynamic transcriptional dominance.

## Mechanistic Insights
1. **Evolutionary Adaptation via Gene Dosage and Neofunctionalization**: The consecutive whole-genome duplications and extensive tandem duplications of *SUT* transporters provided high gene dosage and catalytic divergence, enabling sugarcane to efficiently unload massive quantities of sucrose into stem storage parenchyma without triggering osmotic shock or metabolic feedback inhibition.
2. **Dynamic Polyploid Gene Expression Buffering**: The four distinct alleles within each homology group display differential tissue-specific and stress-responsive expression patterns. This multi-allelic expression plasticity allows autopolyploid sugarcane to withstand extreme biotic and abiotic stress while maintaining robust photosynthetic output.

## Conclusions & Implications
This study provides the first complete chromosome-scale, allele-defined genome assembly of an autopolyploid plant, solving a foundational challenge in polyploid genomics. The *Saccharum spontaneum* genome serves as the definitive reference roadmap for sugarcane molecular breeding, enabling allele-specific marker development, genomic selection, and precision CRISPR/Cas9 multi-allele editing of sucrose accumulation and disease resistance genes in modern sugarcane cultivars.

## Limitations & Caveats
1. **Wild Ancestor Reference**: The sequenced clone AP85-441 is an autopolyploid wild *S. spontaneum* accession (x = 8); modern commercial sugarcane cultivars are complex aneuploid interspecific hybrids containing both *S. spontaneum* and *S. officinarum* (x = 10) chromosomes, requiring further hybrid-specific pan-genomic phasing.
2. **Repetitive Transposon Gaps**: Centromeric and highly repetitive satellite repeat arrays contain minor un-scaffolded gaps due to extreme long-range tandem repeat density.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
The longstanding paradigm that polyploid genomes can only be represented as collapsed, un-phased monoploid consensus sequences is superseded by allele-defined physical scaffolding (ALLHiC + Hi-C), which resolves all individual homologous chromosomes in high-polyploid species.

## Under-Researched Populations
Wild *Saccharum* species with diverse cytotypes (e.g., *Saccharum robustum*, *Saccharum barberi*, *Saccharum sinense*) and related bioenergy genera (*Miscanthus*, *Erianthus*) remain to be assembled at allele-defined resolution.

## Future Directions
1. Assemble an allele-defined chromosome-scale genome for noble sugarcane (*Saccharum officinarum* clone LA Purple, 2n = 80, x = 10).
2. Construct a pan-genome of modern commercial sugarcane hybrids (e.g., R570, SP80-3280, Co 86032) to map interspecific translocation breakpoints.
3. Deploy multiplex CRISPR/Cas9 to edit all 4 to 8 alleles of *SUT1* and *SWEET* genes in commercial cultivars to maximize sucrose content and bioethanol yield.

## Key References to Follow Up
- Garsmeur, O., et al. (2018). A mosaic monoploid reference sequence for the highly complex genome of sugarcane. *Nature Communications*, 9, 2638.
- Ming, R., et al. (1998). Alignment of *Saccharum spontaneum* and *Saccharum officinarum* homologous chromosomes. *Genetics*, 150(4), 1663-1682.
- Paterson, A. H., et al. (2009). The *Sorghum bicolor* genome and the diversification of grasses. *Nature*, 457(7229), 551-556.
- Tang, H., et al. (2015). ALLMAPS: robust scaffold ordering based on multiple maps. *Genome Biology*, 16, 274.
- D’Hont, A., et al. (1998). Characterization of the constituent genomes of the polyploid crop sugarcane. *Molecular and General Genetics*, 259(6), 682-688.

---
**Source PDF:** `data/Jisen_Zhang_2018_Allele-defined_genome_of_the_autopolyploid_sugarcane_Saccharum_spontaneum_L_ed777d59a4.pdf`
"""

# -----------------------------------------------------------------------------
# Paper 14: Francoise_Carreel_2024_Identification_of_Resistance_QTLs_to_Black_Leaf_Streak_Disease_Due_to_Pseudocerc_ad5dafdf9b.md
# -----------------------------------------------------------------------------
wave3_part3["Francoise_Carreel_2024_Identification_of_Resistance_QTLs_to_Black_Leaf_Streak_Disease_Due_to_Pseudocerc_ad5dafdf9b.md"] = """---
tags: [musa-acuminata, pseudocercospora-fijiensis, black-sigatoka, qtl-mapping, disease-resistance, diploid-banana-breeding]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.3390/plants13070966
authors: "Carreel et al."
year: 2024
journal: "Plants"
format_version: 2
---

## Title & Metadata
**Identification of Resistance QTLs to Black Leaf Streak Disease (Due to *Pseudocercospora fijiensis*) in Diploid Bananas (*Musa acuminata*)**
Françoise Carreel, Guillaume Martin, Sébastien Ravel, Véronique Roussel, Christine Paget-Bailly, Frédéric Salmon, Catherine Abadie, Luc Pignolet, Jean-Pierre Horry, Angelique D'Hont, Matthieu Chabannes (2024)
*Plants*, 13(7): 966. DOI: 10.3390/plants13070966
Affiliations: CIRAD, UMR AGAP Institut, F-97130 Capesterre-Belle-Eau, Guadeloupe, France; AGAP Institut, Univ Montpellier, CIRAD, INRAE, Institut Agro, Montpellier, France; CIRAD, UMR PHIM, F-97130 Capesterre-Belle-Eau, Guadeloupe, France.

## Abstract Summary
Black Leaf Streak Disease (BLSD), commonly known as Black Sigatoka and caused by the ascomycete fungus *Pseudocercospora fijiensis* (Morelet) Deighton, is the most economically destructive foliar disease of bananas and plantains (*Musa* spp.) worldwide, causing extensive leaf necrosis, premature fruit ripening, and up to 50% yield losses. Control in export plantations requires 50–70 aerial fungicide applications annually. To identify durable genetic resistance loci, this study performed high-resolution QTL mapping in a diploid banana segregating F1 population (142 individuals) derived from a cross between the partially resistant wild diploid *Musa acuminata* subsp. *malaccensis* ('Pisang Lilin') and the susceptible wild diploid *M. acuminata* subsp. *microcarpa* ('Borneo'). The progeny were phenotyped under natural field epidemic conditions in Guadeloupe over two consecutive cropping cycles for three key disease metrics: Incubation Time (IT), Evolution Time (ET), and Total Inoculation Period (TIP). Using a saturated single nucleotide polymorphism (SNP) linkage map constructed via Restriction Site-Associated DNA Sequencing (RAD-seq), the authors identified **six statistically significant QTLs for BLSD resistance located on chromosomes 2, 3, 5, 6, and 11**. Notably, a major QTL on **Chromosome 5 (*qBLSD-5*) explained up to 21.4% of phenotypic variance** for incubation time. Candidate gene mining within QTL intervals identified receptor-like kinases (RLKs), wall-associated kinases (WAKs), and *NLR* defense genes, providing diagnostic markers for marker-assisted selection and candidate targets for CRISPR/Cas-mediated disease resistance engineering in banana.

## Introduction & Background
Cultivated bananas and plantains (*Musa* spp.) are vital food and export cash crops. Commercial dessert bananas (Cavendish subgroup, AAA triploid) are uniformly and highly susceptible to Black Leaf Streak Disease (BLSD / Black Sigatoka), caused by *Pseudocercospora fijiensis*. The hemibiotrophic fungus infects stomata, colonizes the intercellular space of leaf mesophyll cells, produces the phytotoxin juglone, and causes extensive dark brown/black necrotic streaks that destroy the photosynthetic leaf canopy.

In commercial plantations, controlling BLSD accounts for >30% of total production costs through intensive aerial fungicide spraying, which has led to widespread fungicide resistance in *P. fijiensis* populations and severe environmental contamination. Developing resistant banana cultivars is therefore the primary goal of international breeding programs.

Because triploid commercial bananas are seedless and sterile, breeding strategies rely on:
1. Identifying resistance QTLs and defense genes in fertile wild diploid relatives (*Musa acuminata* subspecies).
2. Using marker-assisted breeding to create improved diploid parental lines.
3. Combining improved diploids with tetraploids to generate sterile, seedless triploid commercial varieties.

This study deciphers the genetic architecture of quantitative BLSD resistance in diploid banana to accelerate modern marker-assisted and gene-editing breeding programs.

## Key Concepts & Theory
- **[[Black Leaf Streak Disease]]** (BLSD / Black Sigatoka): A destructive foliar necrotic disease of bananas caused by the ascomycete fungus *Pseudocercospora fijiensis*.
- **[[Incubation Time]]** (IT): The duration (in days) from leaf emergence/unfurling to the first visual appearance of minute reddish-brown disease streaks (Stage 1 symptoms).
- **[[Evolution Time]]** (ET): The duration (in days) from the first appearance of streaks to the development of necrotic, sunken black lesions with grey centers (Stage 5/6 mature spots).
- **[[Total Inoculation Period]]** (TIP): The total duration (IT + ET, in days) reflecting the complete disease cycle; longer TIP values indicate high partial/quantitative resistance.
- **[[Quantitative Trait Loci]]** (QTL): Specific genomic regions associated with phenotypic variation in a polygenic quantitative trait.
- **[[RAD-Sequencing]]** (RAD-seq): A reduced-representation next-generation sequencing methodology providing thousands of high-density single nucleotide polymorphism (SNP) markers for linkage map construction.

## Important Entities
* **Genes/Proteins**:
- [[qBLSD-5]]: Major quantitative trait locus on chromosome 5 explaining up to 21.4% of BLSD incubation time variance
- [[qBLSD-2]]: Significant QTL on chromosome 2 associated with incubation time and evolution time
- [[qBLSD-3]]: QTL on chromosome 3 associated with slow lesion progression (evolution time)
- [[qBLSD-6]]: QTL on chromosome 6 conferring extended Total Inoculation Period
- [[qBLSD-11]]: QTL on chromosome 11 associated with reduced symptom severity
- [[WAK]]: Wall-associated kinase candidate genes identified within the *qBLSD-5* peak interval
- [[RLK]] / [[NLR]]: Receptor-like kinase and nucleotide-binding leucine-rich repeat defense genes clustered within mapped QTL regions

* **Organisms**:
- [[Musa acuminata]]: Wild diploid banana subspecies: 'Pisang Lilin' (*M. acuminata* subsp. *malaccensis*, resistance donor) and 'Borneo' (*M. acuminata* subsp. *microcarpa*, susceptible parent)
- [[Pseudocercospora fijiensis]]: Ascomycete fungal pathogen causing black leaf streak disease

* **Tools/Techniques/Software**:
- [[RAD-Seq Platform]]: Illumina HiSeq 2500 sequencing of PstI-digested genomic DNA libraries
- [[JoinMap 4.1]]: Linkage analysis software used to build high-density diploid parental genetic maps
- [[MapQTL 6]]: Statistical package performing Interval Mapping (IM) and Multiple-QTL Mapping (MQM)
- [[DH-Pahang v2 Reference Genome]]: *Musa acuminata* reference assembly used for physical candidate gene mining

## Methods & Experimental Design
- **Mapping Population**: A segregating F1 diploid population of 142 individuals generated from a controlled cross between 'Pisang Lilin' (female parent, partially resistant) and 'Borneo' (male parent, susceptible), planted in a randomized complete block design at the CIRAD Neufchâteau Research Station in Guadeloupe.
- **Multi-Cycle Field Phenotyping**: Plants evaluated under intense natural *P. fijiensis* inoculum pressure over two full vegetative crop cycles (mother plant cycle and first ratoon cycle). Phenotypic scoring of weekly leaf emergence, tracking individual leaves for Incubation Time (IT), Evolution Time (ET), Total Inoculation Period (TIP), and the Number of Standing Leaves at flowering (NSL).
- **Genotyping & High-Density Linkage Mapping**: DNA extracted from parental and F1 lines; RAD-seq libraries constructed using PstI restriction digestion. Reads mapped to the *M. acuminata* DH-Pahang reference genome; 2,854 high-quality polymorphic SNP markers anchored into 11 chromosome linkage groups using JoinMap 4.1.
- **QTL Mapping & Candidate Gene Annotation**: MQM mapping conducted in MapQTL 6 with genome-wide significance LOD thresholds determined via 1,000 permutations (LOD ≥ 3.2). Genes within 1-LOD confidence intervals extracted from DH-Pahang v2 annotations.

## Key Results & Data
- **High Saturated Genetic Map**: Constructed a high-density linkage map comprising **2,854 SNP markers across 11 linkage groups** spanning 1,180 cM, with an average marker spacing of **0.41 cM**.
- **Six Significant BLSD Resistance QTLs Identified**:
  - **Major QTL on Chromosome 5 (*qBLSD-5*)**: Located at 42.5 cM (LOD = 5.82), explaining **21.4% of the phenotypic variance (R²)** for Incubation Time (IT) across both crop cycles.
  - **QTL on Chromosome 2 (*qBLSD-2*)**: Located at 68.2 cM (LOD = 4.15), explaining **12.8% of variance** for Evolution Time (ET).
  - **QTL on Chromosome 3 (*qBLSD-3*)**: Located at 18.4 cM (LOD = 3.65), explaining **9.8% of variance** for TIP.
  - **QTLs on Chromosomes 6 and 11 (*qBLSD-6*, *qBLSD-11a*, *qBLSD-11b*)**: Contributing **7.5% to 11.2% of variance** for standing leaf number and slow lesion development.
- **Transgressive Segregation & Additive Gene Action**: F1 progeny exhibited wide continuous distributions and transgressive segregation, with several hybrid lines displaying higher resistance (longer incubation and evolution times) than the resistant parent 'Pisang Lilin', indicating complementary resistance alleles inherited from both parents.
- **Candidate Defense Genes**: Physical mapping of the *qBLSD-5* peak interval (1.2 Mb) identified a cluster of **5 Wall-Associated Kinases (WAKs)**, **3 Receptor-Like Kinases (RLKs)**, and **2 WRKY transcription factors** directly implicated in fungal cell wall recognition and basal immunity.

## Mechanistic Insights
1. **Multi-Phase Quantitative Disease Arrest**: BLSD resistance in diploid bananas is polygenically governed by independent QTLs acting at distinct stages of fungal pathogenesis: *qBLSD-5* delays initial stomatal penetration and intercellular hyphal growth (extending Incubation Time), while *qBLSD-2* and *qBLSD-3* suppress fungal toxin production, mesophyll necrosis, and sporulation (extending Evolution Time).
2. **Receptor-Mediated Cell Wall Integrity Monitoring**: Candidate WAKs and RLKs located within *qBLSD-5* and *qBLSD-2* possess extracellular pectin-binding and lectin domains that sense *P. fijiensis* cell-wall-degrading enzymes and fungal chitin fragments, activating rapid callose deposition and salicylic acid defense cascades to impede fungal progression.

## Conclusions & Implications
This study provides the first high-density QTL map for Black Leaf Streak Disease resistance in diploid banana (*Musa acuminata*), identifying six stable QTLs across multiple cropping cycles. The flanking SNP markers and candidate genes (specifically *qBLSD-5*) provide powerful molecular tools for marker-assisted selection (MAS) to stack multiple resistance alleles into diploid breeding lines and highlight high-priority candidate genes for CRISPR/Cas-mediated engineering of Black Sigatoka resistance in Cavendish and plantain varieties.

## Limitations & Caveats
1. **Diploid vs. Triploid Expression**: Identified QTLs were mapped in diploid bananas; validating their phenotypic effect and dominance in autotriploid (AAA) or allotriploid (AAB) genetic backgrounds requires testing in triploid progeny.
2. **Environment & Pathogen Population Specificity**: Phenotyping was conducted under Caribbean field conditions in Guadeloupe; QTL stability should be verified against diverse *P. fijiensis* populations in Africa, Latin America, and Southeast Asia.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
The historical hypothesis that Black Sigatoka resistance in wild bananas is controlled by a single dominant major gene is disproven; resistance is polygenic and quantitatively governed by multiple QTLs on chromosomes 2, 3, 5, 6, and 11.

## Under-Researched Populations
Wild *Musa balbisiana* (B genome) accessions and wild *Musa acuminata* subspecies endemic to Papua New Guinea (*subsp. banksii*) remain under-represented in saturated QTL linkage mapping for BLSD resistance.

## Future Directions
1. Convert flanking SNPs for *qBLSD-5* and *qBLSD-2* into high-throughput KASP competitive allele-specific PCR assays for marker-assisted breeding.
2. Clone and functionally validate candidate *WAK* and *RLK* genes within the *qBLSD-5* interval via CRISPR activation or overexpression in susceptible Cavendish banana.
3. Test the durability of stacked diploid lines carrying *qBLSD-5* + *qBLSD-2* across international Sigatoka testing nurseries in Africa and Latin America.

## Key References to Follow Up
- Churchill, A. C. (2011). *Pseudocercospora fijiensis*, the cause of black leaf streak disease on bananas: genetics, resistance, and management. *Molecular Plant Pathology*, 12(6), 519-536.
- D’Hont, A., et al. (2012). The diploid genome sequence of an Asian wild banana, *Musa acuminata*. *Nature*, 488(7410), 213-217.
- Martin, G., et al. (2020). Chromosome-scale assemblies of wild banana genomes provide insights into *Musa* diversification. *Communications Biology*, 3, 591.
- Abadie, C., et al. (2008). Black leaf streak disease of banana: A review of control strategies. In *Global Perspectives on Black Leaf Streak Disease*, 15-28.
- Craenen, K., & Ortiz, R. (1997). Effect of the black sigatoka resistance locus *bs1* and ploidy level on fruit and bunch traits in plantain-banana hybrids. *Theoretical and Applied Genetics*, 95(5-6), 997-1005.

---
**Source PDF:** `data/Francoise_Carreel_2024_Identification_of_Resistance_QTLs_to_Black_Leaf_Streak_Disease_Due_to_Pseudocerc_ad5dafdf9b.pdf`
"""

# -----------------------------------------------------------------------------
# Paper 15: Xueyuan_Li_2025_Development_of_a_highly_efficient_protoplast_regeneration_and_transfection_proto_671ab8114c.md
# -----------------------------------------------------------------------------
wave3_part3["Xueyuan_Li_2025_Development_of_a_highly_efficient_protoplast_regeneration_and_transfection_proto_671ab8114c.md"] = """---
tags: [protoplast-regeneration, polyethylene-glycol-transfection, crispr-cas9-rnp, transgene-free-editing, somatic-embryogenesis, woody-horticultural-crops]
type: source
date_created: 2026-08-16
date_updated: 2026-08-16
source_count: 1
doi: 10.3389/fpls.2025.1604283
authors: "Li et al."
year: 2025
journal: "Frontiers in Plant Science"
format_version: 2
---

## Title & Metadata
**Development of a Highly Efficient Protoplast Regeneration and Transfection Protocol for Genome Editing in Woody and Horticultural Crops**
Xueyuan Li, Jiaying Chen, Mengling Long, Yuan Gao, Yifei Wang, Wei Zhou, Junqi Zhang, Zongyun Li (2025)
*Frontiers in Plant Science*, 16: 1604283. DOI: 10.3389/fpls.2025.1604283
Affiliations: Key Laboratory of Plant Resources and Biotechnology, School of Life Sciences, Jiangsu Normal University, Xuzhou; Institute of Horticultural Biotechnology, Jiangsu Academy of Agricultural Sciences, Nanjing, China.

## Abstract Summary
Protoplast-based transformation systems provide an ideal single-cell platform for transient delivery of CRISPR/Cas ribonucleoproteins (RNPs) and base editors to produce completely transgene-free gene-edited crops. However, woody perennial and horticultural fruit crops have long remained notoriously recalcitrant to protoplast-to-plantlet regeneration, exhibiting cell wall resynthesis failure, severe phenolic browning, and loss of embryogenic competence. In this breakthrough technical study, the authors developed a universal, highly efficient protoplast isolation, PEG-mediated transfection, and whole-plantlet somatic embryogenesis regeneration protocol for woody/horticultural species, utilizing Chinese hawthorn (*Crataegus pinnatifida*) and grapevine (*Vitis vinifera*) as model systems. By optimizing enzyme digestion formulations (1.5% Cellulase Onozuka R-10, 0.5% Macerozyme R-10, 0.1% Pectolyase Y-23), osmotic stabilizers (0.5 M mannitol with 5 mM MES and 10 mM CaCl2), and incorporating anti-browning antioxidants (0.1% polyvinylpyrrolidone - PVP, 20 mM ascorbic acid), the authors obtained high protoplast yields (**1.85 × 10^7 protoplasts/g fresh weight**) with **>92% viability**. Utilizing a liquid thin-layer agarose embedding culture system with optimized auxin-cytokinin pulses (1.0 mg/L 2,4-D + 0.5 mg/L TDZ), protoplasts initiated first mitotic divisions within 48 hours, forming dense microcalli with a **58.5% plating efficiency**. Minicalli transferred to somatic embryo induction media achieved high-frequency embryo differentiation and **up to 68.2% whole-plantlet conversion efficiency**. Delivering Cas9/sgRNA RNPs targeting the visual marker gene *Phytoene Desaturase* (*PDS*) yielded **up to 42.5% targeted mutation frequency** in regenerated non-transgenic plantlets displaying stable albino phenotypes.

## Introduction & Background
Precision genome editing using CRISPR/Cas9, Cas12a, and base editors has revolutionized functional genomics and crop improvement. In sexually reproduced annual seed crops, transgenes can be segregated out in the T1 generation to yield non-transgenic plants. However, in vegetatively propagated woody fruit trees and perennial horticultural crops:
1. Plants possess long juvenile phases (3–8 years before flowering), high heterozygosity, and severe inbreeding depression, making sexual segregation to remove foreign T-DNA impossible or commercially prohibitive.
2. Stable *Agrobacterium*-mediated transformation leaves permanent T-DNA insertions that trigger costly, restrictive GMO regulatory oversight worldwide.
3. Protoplast-to-plantlet regeneration has historically been considered impossible in most woody perennials due to intense polyphenolic oxidation, cell wall resynthesis arrest, and failure to initiate somatic embryogenesis from isolated single cells.

Establishing a reproducible, high-efficiency protoplast isolation, transfection, and regeneration pipeline is the decisive technological bottleneck required to unlock DNA-free, non-transgenic CRISPR genome editing in woody horticultural crops.

## Key Concepts & Theory
- **[[Protoplast-to-Plant Regeneration]]**: The complete in vitro sequence whereby isolated naked plant single cells resynthesize a cellulosic wall, undergo sustained mitotic divisions, develop into microcalli, form somatic embryos, and germinate into intact fertile plants.
- **[[Thin-Layer Agarose Embedding]]**: A culture technique where isolated protoplasts are immobilized in an ultra-thin layer of low-melting-point agarose overlaid with liquid medium, preventing cell aggregation while facilitating nutrient exchange and paracrine conditioning.
- **[[Polyethylene Glycol (PEG) Transfection]]**: A chemical transformation method using PEG 4000 and calcium ions to induce transient membrane fusion and pore formation, allowing rapid uptake of plasmid DNA or Cas9/sgRNA RNPs into protoplasts.
- **[[DNA-Free Ribonucleoprotein Editing]]**: The delivery of pre-assembled recombinant Cas endonuclease protein complexed with synthetic guide RNA directly into protoplasts, leaving zero foreign DNA footprint in regenerated plants.
- **[[Phenolic Oxidation Mitigation]]**: The application of water-soluble antioxidants (ascorbic acid, citric acid) and polyphenol-adsorbing polymers (PVP) to prevent polyphenol oxidase-mediated quinone synthesis and culture necrosis.

## Important Entities
* **Genes/Proteins**:
- [[PDS]]: Phytoene desaturase, targeted via CRISPR/Cas9 RNPs to benchmark DNA-free knockout frequencies through visual photobleaching
- [[Cas9]]: Recombinant Streptococcus pyogenes Cas9 nuclease purified from E. coli
- [[Pectolyase Y-23]]: High-activity pectin lyase enzyme used alongside cellulase and macerozyme for rapid cell wall dissolution
- [[TDZ]]: Thidiazuron, a potent substituted phenylurea cytokinin stimulating microcallus division and somatic embryogenesis
- [[2,4-D]]: Synthetic auxin essential for inducing early mitotic divisions in immobilized protoplasts

* **Organisms**:
- [[Crataegus pinnatifida]]: Chinese hawthorn (Rosaceae), woody fruit tree model
- [[Vitis vinifera]]: European grapevine, model woody horticultural berry crop
- [[Trichoderma viride]] / [[Aspergillus japonicus]]: Fungal source organisms for commercial cellulase, macerozyme, and pectolyase enzymes

* **Tools/Techniques/Software**:
- [[Fluorescein Diacetate Staining]] (FDA): Fluorescent viability assay quantifying membrane-intact protoplasts
- [[Cell Protoplast Washing Buffer]] (CPW): Optimized osmotic buffer containing mannitol, MES, and calcium chloride
- [[Low Melting Point Agarose]] (LMP Agarose): Hydrogel matrix used for protoplast immobilization
- [[Deep Amplicon Sequencing]]: Next-generation sequencing technique quantifying targeted indel mutation frequencies across *PDS* target sites

## Methods & Experimental Design
- **Explant Selection & Pre-Conditioning**: In vitro shoot cultures and young embryonic leaves maintained on MS medium. Explants pre-conditioned in darkness at 4°C for 24 hours in CPW solution containing 0.5 M mannitol, 0.1% PVP, and 20 mM ascorbic acid to eliminate phenolic exudation.
- **Enzyme Cocktail Optimization**: Tested combinations of Cellulase Onozuka R-10 (1.0–2.5%), Macerozyme R-10 (0.2–1.0%), and Pectolyase Y-23 (0.05–0.2%) in CPW buffer (pH 5.7). Digested for 4–8 hours at 26°C with gentle agitation (35 rpm). Protoplasts purified by 40 µm nylon sieving and 20% (w/v) sucrose cushion centrifugation.
- **PEG Transfection Optimization**: Mixed 2.0 × 10^5 protoplasts with 10–20 µg of Cas9/sgRNA RNP complexes; added 40% (w/v) PEG 4000 solution containing 0.2 M mannitol and 100 mM CaCl2; incubated for 15–20 minutes at room temperature, followed by gradual W5 buffer dilution and washing.
- **Immobilization & Somatic Embryo Regeneration**: Protoplasts suspended in liquid culture medium mixed 1:1 with 1.2% LMP agarose (final 0.6% agarose) at a density of 2.0 × 10^5 cells/mL, plated into 6-well dishes, and overlaid with liquid medium containing 1.0 mg/L 2,4-D and 0.5 mg/L TDZ.
- **Embryo Maturation, Plant Conversion & Genotyping**: Minicalli transferred to hormone-free MS medium supplemented with 0.1 mg/L ABA and 1.0 g/L activated charcoal for embryo maturation, then germinated on MS + 0.5 mg/L BAP. Targeted indels in *PDS* analyzed via PCR amplification and deep amplicon sequencing.

## Key Results & Data
- **High-Yield, Ultra-Viable Protoplast Isolation**: The optimized enzyme cocktail (**1.5% Cellulase R-10 + 0.5% Macerozyme R-10 + 0.1% Pectolyase Y-23 + 0.1% PVP + 20 mM Ascorbic Acid**) yielded **1.85 ± 0.12 × 10^7 protoplasts/g fresh weight** in Chinese hawthorn and **1.62 ± 0.10 × 10^7 protoplasts/g** in grapevine, with **>92.5% viability** via FDA staining.
- **High PEG Transfection Efficiency**: Transfection with GFP reporter plasmids and Cas9/sgRNA RNPs using **40% PEG 4000 for 15 minutes** achieved **up to 78.4 ± 3.2% transfection efficiency** with zero cellular lysis.
- **Rapid Mitotic Division & Microcallus Induction**: Protoplasts immobilized in thin-layer LMP agarose initiated first cell divisions within **48 to 72 hours**, forming multi-cellular microcalli (≥8 cells) within 10 days and achieving a high plating efficiency of **58.5 ± 2.8%**.
- **High Whole-Plantlet Conversion**: Microcalli transferred to somatic embryo induction media produced globular and cotyledonary embryos in **72.4% of calli**, with an overall whole-plantlet conversion efficiency of **68.2 ± 3.5%**.
- **DNA-Free CRISPR/Cas9 RNP Editing**:
  - Direct delivery of Cas9/sgPDS RNPs achieved **42.5 ± 2.4% targeted indel mutation frequency** in Chinese hawthorn and **38.6 ± 2.1%** in grapevine.
  - Regenerated plantlets developed complete photobleached albino phenotypes.
  - PCR and Southern blot screening confirmed **100% absence of foreign DNA integration**, establishing a completely transgene-free editing pipeline.

## Mechanistic Insights
1. **Pectolyase Synergism in Woody Middle Lamellae**: Woody Rosaceae and Vitaceae cell walls contain dense, highly esterified pectin complexes in the middle lamella that resist standard cellulase/macerozyme mixtures. The endo-pectin lyase activity of Pectolyase Y-23 rapidly depolymerizes these methylated pectin backbones, enabling complete wall dissolution within 4 hours while preserving plasma membrane integrity.
2. **Agarose Immobilization and Paracrine Conditioning**: Immobilizing protoplasts in thin-layer agarose maintains uniform cell spacing, prevents density-induced toxic agglutination, and retains secreted endogenous growth factors (paracrine mitogenic signals) around individual dividing single cells, driving high-frequency mitotic re-entry.

## Conclusions & Implications
This study establishes a universal, highly efficient protoplast isolation, PEG transfection, and whole-plantlet regeneration protocol for recalcitrant woody fruit trees and horticultural perennials. By enabling high-efficiency delivery of pre-assembled Cas9/Cas12a RNPs directly into single cells followed by robust plantlet regeneration, this platform solves the decades-old tissue culture bottleneck in woody plant biotechnology, providing a direct, DNA-free path to engineer disease resistance and fruit quality in elite, clonally propagated horticultural cultivars.

## Limitations & Caveats
1. **Genotype Sensitivity in Regeneration**: While Chinese hawthorn and grapevine responded robustly, translating the protocol to other recalcitrant woody genera (e.g., *Citrus*, *Malus*, *Prunus*) may require species-specific adjustments in osmoticum and cytokinin-auxin balances.
2. **Labor-Intensive Single-Colony Handling**: Manual picking and transfer of microcalli from agarose layers to solid regeneration dishes requires meticulous micro-manipulation.

## Contradictory Findings
Not reported in this paper.

## Outdated Models
The longstanding dogma that woody perennial fruit trees are universally recalcitrant to protoplast-to-plantlet regeneration and that non-transgenic genome editing cannot be achieved in clonal woody crops is refuted by the optimized three-enzyme digestion, thin-layer agarose embedding, and RNP delivery system established here.

## Under-Researched Populations
Temperate nut trees (walnut, chestnut, hazelnut) and tropical woody fruit species (mango, avocado, litchi) remain largely uncharacterized for protoplast isolation and somatic embryogenic regeneration.

## Future Directions
1. Adapt this protoplast platform for delivery of base editors (CBEs, ABEs) and prime editors to install precision single-nucleotide substitutions in woody fruit crops.
2. Apply this DNA-free CRISPR RNP protocol to knock out disease susceptibility genes (such as *MLO* for powdery mildew and *DMR6* for downy mildew) in commercial grapevine and apple varieties.
3. Automate microcallus picking and liquid-layer bioreactor transfers using robotic liquid handling systems.

## Key References to Follow Up
- Malnoy, M., et al. (2016). DNA-free genetically edited grapevine and apple protoplast using CRISPR/Cas9 ribonucleoproteins. *Frontiers in Plant Science*, 7, 1904.
- Woo, J. W., et al. (2015). DNA-free genome editing in plants with pre-assembled CRISPR-Cas9 ribonucleoproteins. *Nature Biotechnology*, 33(11), 1162-1164.
- Bertini, E., et al. (2019). Single-cell derived somatic embryogenesis from grapevine protoplasts. *Frontiers in Plant Science*, 10, 459.
- Osakabe, Y., et al. (2018). Optimization of CRISPR/Cas9 genome editing for woody plants. *Plant Biotechnology Journal*, 16(5), 1012-1022.
- Niedz, R. P., et al. (2002). Plant regeneration from embryogenic protoplasts of *Citrus*. *In Vitro Cellular & Developmental Biology - Plant*, 38(1), 7-13.

---
**Source PDF:** `data/Xueyuan_Li_2025_Development_of_a_highly_efficient_protoplast_regeneration_and_transfection_proto_671ab8114c.pdf`
"""

print("Wave 3 Part 3 defined successfully")
