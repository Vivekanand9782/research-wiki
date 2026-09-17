import json
import re

raw_path = "/Users/vivekanandsirohi/Desktop/antigravity/research-wiki/raw/papers/vpc_transgene_free/Ana_Luisa_Garcia-Oliveira_2025_The_importance_of_genotyping_within_the_climate-smart_plant_breeding_value_chain_3c3050f9fd.md"
with open(raw_path) as f:
    raw_text = f.read()

def check_quote(quote, label="Quote"):
    if quote in raw_text:
        print(f"PASS: {label}")
        return True
    else:
        print(f"FAIL: {label}")
        print("  Looking for:", repr(quote[:60]))
        return False

# Let's verify our selected quotes
quotes_to_verify = {
    # Methods & Experimental Design
    "methods_uom_wheat": "The University of Minnesota’s (UoM, St. Paul, Minnesota, USA) Wheat Improvement Program uses markers in three main ways: 1) Parental genotyping to facilitate crossing decisions, 2) Enrichment of 3-way crosses for favourable marker alleles prior to generation advancement, and 3) Marker-assisted line purification during advanced breeding stages.",
    "methods_cip_potato": "In the breeding program of the International Potato Center (CIP, Lima, Peru), for the vegetatively propagated potato, DArTag markers (Endelman et al., 2024) are being used for genomic selection (GS), diversity analysis, and selection based on trait markers.",
    "methods_iita_yam": "In Yam at the International Institute of Tropical Agriculture (IITA, Ibadan, Nigeria) KASP SNP markers are being used to distinguish different yam species (Diascorea alata, D. rotundata, D. praehensilis, D. cayenensis and D. abyssinica, and also tagged markers with the economically important traits such as plant vigour, sex distinguishing, flowering intensity, yam mosaic virus, among others",
    "methods_simsenseq": "For the detection of rare point mutations in plant genomes the use of NGS still presents challenges. As an alternative, the Simple, Multiplexed, PCR-based bar-coding of DNA (SiMsenseq) system is an opportunity for selective mutation detection using sequencing, as it detects variants at or below 0.1% frequency with low DNA input",
    "methods_find_it": "With this method libraries of 500,000 knockout barley mutant individuals, can be screened within only two weeks (Knudsen et al., 2021; Madsen et al., 2024). Contrary to CRISPR methodology, FIND-IT is not subjected to governmental regulations as a nonGM technique.",

    # Key Results & Data
    "results_rice_gs3": "the nonsense-mutated GS3 gene, represented by the gs3 allele in the rice cultivar ‘Akita 63’, enhances yield production and grain size in rice, thereby improving harvest index and NUE in rice.",
    "results_wheat_tamlo": "In hexaploid wheat, the TALEN-generated Tamlo-R32 mutant targets the three wheat MLO1 genes (TaMLO-A1, TaMLO-B1 and TaMLO-D1) and is characterised by a 300kb pair targeted deletion in the MLO-B1 locus that retains crop growth and yields while conferring resistance to powdery mildew.",
    "results_rice_multiplex_gw": "In rice, noteworthy examples of precision editing include the knockout of three seed weight-related genes, namely GW2, GW5, and TGW6, which lead to an increase in grain weight (Xu et al., 2016).",
    "results_tomato_sp": "In tomato (Solanum lycopersicum L.), the multiplexing of the coding regions of SELF-PRUNING and SELF-PRUNING 5G, together with cis-regulatory regions of CLV3 and WUS or open reading frames (ORFs) of GGP1, allowed the generation of tomato fruits with compact plant architecture, synchronized fruit ripening, day length insensitivity, enlarged fruit size and increased vitamin C levels",
    "results_potato_s_genes": "More recently, in potatoes (Solanum tuberosum L.), the functional knockouts of several S-genes, namely StDND1, StCHL1, and DMG400000582 (StDDMR6-1), lead to the generation of tetraploid potatoes with increased resistance against late blight (Kieu et al., 2021).",
    "results_rice_apomixis": "Through simultaneous editing of REC8, PAIR1, OSD1, and MTL genes, researchers have been able to fix the favourable F1 traits (Wang et al., 2019). When REC8, PAIR1, and OSD1 genes were knocked down simultaneously, and meiosis was replaced by mitosis, it was enabled the production of asexual hybrid rice seeds and the preservation of the hybrid vigour",
    "results_haploid_matl": "In wheat CRISPR/Cas9mediated targeting of the MATL gene led to an inheritance rate of 18.9% haploid progeny (Liu et al., 2019a, b) while targeting maize DMP – gene resulted in maternal haploids with an efficacy range of about 0.1 0.3%",
    "results_strawberry_fvesep3": "In strawberry, fvesep3 mutated using CRISPR/Cas9 has produced the desirable trait of parthenocarpic fruits, which is highly sought in strawberry breeding programs",
    "results_rice_acc1": "In addition, various mutations in the acetyl-coenzyme A carboxylase 1(OsACC1) gene, have been discovered, resulting in herbicide resistance",
    "results_cas12a_mirna": "Zheng et al. (2024) demonstrated in rice that CRISPR Cas12a is a more efficient tool compared to its Cas9 counterpart for generating knockout mutants of a miRNA gene. With this improvement, it seems possible to achieve editing efficiencies of up to 100%.",

    # Mechanistic Insights
    "mech_ips1_pho2": "Franco-Zorrilla et al. (2007) identified an endogenous long non-protein coding gene INDUCED BY PHOSPHATE STARVATION 1 (IPS1) which altered the protein levels of PHOSPHATE2 (PHO2) by modulating the effects of miR399 in Arabidopsis.",
    "mech_etm_bulge": "It was observed that both IPS1 and PHO2 had highly conserved sequence motifs that contain complementary binding site for the phosphate (Pi) starvation–induced miRNA miR399. However, IPS1 showed three additional nucleotides bases, which provoke central mismatches in the miR399 binding site by forming of central “bulge” opposite the expected miRNA cleavage site, thus avoiding miR399-guided cleavage but instead sequesters of miR399.",
    "mech_tatmt3b": "Through epigenetic changes, this mutant exhibits a significant upregulation of TaTMT3B (Tonoplast monosaccharide transporter 3) locus transcript expression. The use of the CRISPR/Cas9 tool demonstrated that this genetic arrangement counteracts the negative effects associated with mlo mutations while maintaining strong disease resistance in wheat",
    "mech_mir168_mir395": "miRNAs OsmiR168 and OSmiR395, targeting the Ago1 and ATP sulfurylase (OsAPS1) genes which enhanced the resistance and broad-spectrum resistance to rice blast fungus (Magnaporthe oryzae L.) and both pathovars Xanthomonas oryzae pv.oryzae (Xoo) and X. oryzae pv. oryzicola (Xoc), causing bacterial blight and leaf streak diseases in rice, respectively",
    "mech_mir156_spl": "The miR156 not only was found to module flooding tolerance by regulating physiological processes and SnRK1 gene expression (Feyissa et al., 2021) but also to influence heat, cold and drought tolerances by downregulating the SPL gene",
    "mech_prime_editing": "Prime-editing combines the Cas9 nuclease with an engineered reverse transcriptase and a prime editing RNA (pegRNA), which enables targeted base editing, insertions, deletions, and combinations without the need for double-stranded breaks or donor templates.",
    "mech_dmr6_divergence": "The mutation of DMR6 homologues indicates that StDMR6-1 and StDMR6-2 have two different biological functions, with the first involved in pathogen resistance whereas the second involved in plant growth."
}

all_pass = True
for k, v in quotes_to_verify.items():
    if not check_quote(v, k):
        all_pass = False

print("All quotes verified:", all_pass)
