"""Build the gold directory from compact claim specs. Spans are located by exact text in the stored section."""

import json
import re
import sqlite3
import sys
from pathlib import Path

RUN = Path(__file__).parent
GOLD = RUN / "gold"
db = sqlite3.connect(RUN / "dossier.db")

W = {  # short name -> (work id, domain)
    "resnet": ("work_4627097f8362928c", "COMPUTER_SCIENCE"),
    "crispr_review": ("work_551d55b26e0cb4a5", "BIOLOGY"),
    "ipconazole": ("work_5c58342a230665a3", "BIOLOGY"),
    "adam": ("work_6d41d2f09c026403", "COMPUTER_SCIENCE"),
    "warts": ("work_8c83c39cd1afa399", "BIOLOGY"),
    "transformer": ("work_a1a0262a54cd0bbc", "COMPUTER_SCIENCE"),
    "cas9_msm": ("work_ecdc742ad2d21fbc", "BIOLOGY"),
    "vitd_oil": ("work_f911b46a09ec5d13", "BIOLOGY"),
}


def C(key, study, ctype, text, subj, pred, outcome, system, method, comp, meas, direction,
      span, value=None, unit=None, sig=None, p=None):
    return dict(key=key, study=study, ctype=ctype, text=text, subj=subj, pred=pred, outcome=outcome,
                system=system, method=method, comp=comp, meas=meas, direction=direction, span=span,
                value=value, unit=unit, sig=sig, p=p)


CLAIMS = {
    "resnet": [
        C("c1", "resnet-imagenet", "PERFORMANCE", "An ensemble of residual nets achieves 3.57% error on the ImageNet test set.",
          "ensemble of residual nets", "achieves", "error", "ImageNet", "residual nets", None, "error", "OBSERVED",
          "An ensemble of these residual nets achieves 3.57% error on the ImageNet test set", 3.57, "%"),
        C("c2", "resnet-coco", "PERFORMANCE", "Extremely deep representations gave a 28% relative improvement on COCO object detection.",
          "deep residual representations", "improves", "object detection performance", "COCO", "residual nets", None,
          "object detection performance", "IMPROVED",
          "we obtain a 28% relative improvement on the COCO object detection dataset", 28.0, "% relative"),
        C("c3", "resnet-imagenet", "COMPARISON", "Residual networks are easier to optimize.",
          "residual networks", "are easier to optimize", "optimization", None, "residual networks", None, None, "IMPROVED",
          "residual networks are easier to optimize"),
        C("c4", "resnet-imagenet", "SCALING", "Residual networks gain accuracy from considerably increased depth.",
          "residual networks", "gain accuracy from", "accuracy", None, "residual networks", None, "accuracy", "INCREASED",
          "can gain accuracy from considerably increased depth"),
        C("c5", "resnet-imagenet", "COMPARISON", "A 152-layer residual net has lower complexity than the 8x shallower VGG nets.",
          "152-layer residual nets", "have lower complexity than", "complexity", "ImageNet", "residual nets", "VGG nets", "complexity",
          "DECREASED",
          "residual nets with a depth of up to 152 layers---8x deeper than VGG nets but still having lower complexity"),
        C("c6", "resnet-ilsvrc", "PERFORMANCE", "The ensemble won 1st place on the ILSVRC 2015 classification task.",
          "ensemble of residual nets", "won", "ILSVRC 2015 classification", "ILSVRC 2015", "residual nets", None, None, "OBSERVED",
          "This result won the 1st place on the ILSVRC 2015 classification task"),
        C("c7", "resnet-competitions", "PERFORMANCE", "Deep residual nets won 1st place on ImageNet detection, ImageNet localization, COCO detection and COCO segmentation.",
          "deep residual nets", "won", "ILSVRC and COCO 2015 competition tasks", "ILSVRC and COCO 2015", "residual nets", None, None, "OBSERVED",
          "we also won the 1st places on the tasks of ImageNet detection, ImageNet localization, COCO detection, and COCO segmentation"),
    ],
    "crispr_review": [],
    "ipconazole": [
        C("c1", "ipc-larvae", "EFFECT", "Ipconazole reduced the locomotive activity of zebrafish larvae during early development.",
          "ipconazole", "reduced", "locomotive activity", "zebrafish larvae", "ipconazole exposure", None, "locomotive activity",
          "DECREASED", "locomotive activity of ipconazole-exposed zebrafish larvae was reduced during early development"),
        C("c2", "ipc-larvae", "EFFECT", "Ipconazole exposure produced no detected morphological abnormalities.",
          "ipconazole", "did not cause", "morphological abnormalities", "zebrafish larvae", "ipconazole exposure", None,
          "morphological abnormalities", "NOT_OBSERVED", "even when morphological abnormalities were undetected"),
        C("c3", "ipc-embryos", "EFFECT", "Ipconazole reduced the mitochondrial antioxidants SOD1 and SOD2 in embryos.",
          "ipconazole", "reduced", "superoxide dismutases 1 and 2", "zebrafish embryos", "ipconazole treatment", None,
          "superoxide dismutase expression", "DECREASED",
          "the mitochondrial-specific antioxidants, superoxide dismutases 1 and 2"),
        C("c4", "ipc-embryos", "EFFECT", "Ipconazole reduced the genes for mitochondrial genome maintenance and function in embryos.",
          "ipconazole", "reduced", "mitochondrial genome maintenance and function genes", "zebrafish embryos", "ipconazole treatment", None,
          "gene expression", "DECREASED",
          "the genes essential for mitochondrial genome maintenance and functions were specifically reduced in ipconazole-treated (0.02 μg/mL) embryos"),
        C("c5", "ipc-embryos", "EFFECT", "Ipconazole reduced hsp70 expression.",
          "ipconazole", "reduced", "hsp70 expression", "zebrafish embryos", "ipconazole treatment", None, "hsp70 expression",
          "DECREASED", "substantially reduced hsp70 expression"),
        C("c6", "ipc-embryos", "EFFECT", "Ipconazole increased ERK1/2 phosphorylation in a dose-dependent manner.",
          "ipconazole", "increased", "ERK1/2 phosphorylation", "zebrafish embryos", "ipconazole treatment", None,
          "ERK1/2 phosphorylation", "INCREASED", "increased ERK1/2 phosphorylation in a dose-dependent manner"),
        C("c7", "ipc-embryos", "EFFECT", "Ipconazole dysregulated GABAergic inhibitory neurons at 0.02 ug/mL.",
          "ipconazole", "dysregulated", "GABAergic inhibitory neurons", "zebrafish embryos", "ipconazole treatment", None,
          "gad1b expression", "UNKNOWN",
          "Interrupted gad1b expression confirmed that GABAergic inhibitory neurons were dysregulated at 0.02 μg/mL ipconazole"),
        C("c8", "ipc-embryos", "EFFECT", "Glutamatergic excitatory and dopaminergic neurons were unaffected by ipconazole.",
          "ipconazole", "did not affect", "glutamatergic excitatory and dopaminergic neurons", "zebrafish embryos", "ipconazole treatment", None,
          None, "UNCHANGED", "glutamatergic excitatory and dopaminergic neurons remained unaffected"),
        C("c9", "ipc-embryos", "EFFECT", "Ipconazole at 2 ug/mL produced caspase-independent cell death.",
          "ipconazole", "caused", "caspase-independent cell death", "zebrafish embryos", "ipconazole treatment", None, "cell death",
          "INCREASED", "ipconazole-treated (2 μg/mL) embryos exhibited caspase-independent cell death"),
        C("c10", "ipc-embryos", "MECHANISM", "Ipconazole may alter neurodevelopment by dysregulating mitochondrial homeostasis.",
          "ipconazole", "may alter neurodevelopment by dysregulating", "mitochondrial homeostasis", "zebrafish", "ipconazole treatment", None,
          None, "UNKNOWN",
          "ipconazole has the potential to alter neurodevelopment by dysregulating mitochondrial homeostasis"),
    ],
    "adam": [
        C("c1", "adam-empirical", "COMPARISON", "Adam works well in practice and compares favorably to other stochastic optimization methods.",
          "Adam", "compares favorably to", "optimization performance", None, "Adam", "other stochastic optimization methods", None,
          "IMPROVED", "Adam works well in practice and compares favorably to other stochastic optimization methods"),
        C("c2", "adam-theory", "PERFORMANCE", "Adam has a regret bound comparable to the best known results under online convex optimization.",
          "Adam", "has a regret bound comparable to", "convergence rate", "online convex optimization", "Adam",
          "best known results", "regret bound", "UNCHANGED",
          "a regret bound on the convergence rate that is comparable to the best known results under the online convex optimization framework"),
    ],
    "warts": [
        C("c1", "warts-rct", "COMPARISON", "Intralesional vitamin D3 led to more complete resolution of warts than cryotherapy.",
          "intralesional vitamin D3", "was related to more", "complete resolution of warts", "cutaneous warts", "intralesional vitamin D3",
          "cryotherapy", "complete resolution of warts", "IMPROVED",
          "Vitamin D3 was statistically significantly related to complete resolution of warts as compared to cryotherapy (p-value<0.05)",
          sig=True, p="<0.05"),
        C("c2", "warts-rct", "PROPERTY", "Plantar warts were the commonest wart type, 41 of 50 patients (82%).",
          "plantar warts", "were the commonest type", "wart type", "cutaneous warts", None, None, None, "OBSERVED",
          "Planter warts 41 (82%) were the commonest type according to the site of warts", 82.0, "%"),
    ],
    "transformer": [
        C("c1", "tf-wmt-ende", "PERFORMANCE", "The Transformer achieves 28.4 BLEU on WMT 2014 English-to-German, over 2 BLEU above the best existing results.",
          "Transformer", "achieves", "BLEU", "WMT 2014 English-to-German", "Transformer", "existing best results, including ensembles", "BLEU",
          "IMPROVED",
          "Our model achieves 28.4 BLEU on the WMT 2014 English-to-German translation task, improving over the existing best results, including ensembles by over 2 BLEU",
          28.4, "BLEU"),
        C("c2", "tf-wmt-enfr", "PERFORMANCE", "The Transformer sets a single-model state of the art of 41.8 BLEU on WMT 2014 English-to-French.",
          "Transformer", "establishes", "BLEU", "WMT 2014 English-to-French", "Transformer", "previous single-model results", "BLEU",
          "IMPROVED",
          "our model establishes a new single-model state-of-the-art BLEU score of 41.8 after training for 3.5 days on eight GPUs",
          41.8, "BLEU"),
        C("c3", "tf-wmt-ende", "COMPARISON", "The Transformer requires significantly less time to train.",
          "Transformer", "requires less", "training time", "machine translation", "Transformer", None, "training time",
          "DECREASED", "requiring significantly less time to train"),
        C("c4", "tf-wmt-ende", "COMPARISON", "The Transformer is more parallelizable.",
          "Transformer", "is more", "parallelizability", "machine translation", "Transformer", None, None, "IMPROVED",
          "being more parallelizable"),
        C("c5", "tf-parsing", "PERFORMANCE", "The Transformer applies successfully to English constituency parsing with large and limited training data.",
          "Transformer", "applies successfully to", "English constituency parsing", "English constituency parsing", "Transformer", None,
          None, "OBSERVED",
          "applying it successfully to English constituency parsing both with large and limited training data"),
    ],
    "cas9_msm": [
        C("c1", "msm-cas9", "MECHANISM", "A model is proposed for the synergy between Gln768 and Arg976 in Cas9.",
          "Gln768 and Arg976", "act synergistically in", "Cas9 configurational space", "Cas9", "MD-MSM-ML scheme", None, None, "UNKNOWN",
          "A model for the synergy between those two residues is proposed"),
    ],
    "vitd_oil": [
        C("c1", "vitd-rct", "EFFECT", "Vitamin D supplement raised serum 25(OH)D more than control.",
          "vitamin D supplement", "increased", "serum 25(OH)D", "healthy adults aged 18-30", "1000 IU vitamin D supplement", "control",
          "serum 25(OH)D", "INCREASED", "Serum 25(OH)D increased more in the vitamin D supplement group compared to the controls (P = 0.001)",
          sig=True, p="= 0.001"),
        C("c2", "vitd-rct", "EFFECT", "In vitamin D sufficient participants, supplement and fortified oil raised serum 25(OH)D more than control.",
          "vitamin D supplement and fortified oil", "increased", "serum 25(OH)D", "vitamin D sufficient subgroup",
          "vitamin D supplement and fortified oil", "control", "serum 25(OH)D", "INCREASED",
          "serum 25(OH)D increased more in both vitamin D supplement group and vitamin D fortified oil group, compared to the controls (P = 0.001 for both)",
          sig=True, p="= 0.001"),
        C("c3", "vitd-rct", "EFFECT", "PTH, BAP and CTX did not differ among the study groups.",
          "vitamin D supplement and fortified oil", "did not change", "PTH, BAP and CTX", "healthy adults aged 18-30",
          "vitamin D supplement and fortified oil", "control", "bone turnover markers", "UNCHANGED",
          "The mean differences of PTH, BAP, and CTX were not significantly different among the study groups", sig=False),
    ],
}


def term(text):
    return {"original": text, "canonical": text}


def build(name):
    work_id, domain = W[name]
    doc_id = f"{work_id}_v1"
    ((sid, stext),) = db.execute("select id, text from sections where document_id=?", (doc_id,)).fetchall()
    claims = []
    for c in CLAIMS[name]:
        pattern = re.compile(r"[ \u00a0]".join(re.escape(w) for w in c["span"].split(" ")))
        hits = list(pattern.finditer(stext))
        if len(hits) != 1:
            sys.exit(f"{name} {c['key']}: span found {len(hits)} times: {c['span'][:50]}")
        start = hits[0].start()
        c = {**c, "span": hits[0].group()}
        claim = {
            "gold_key": c["key"], "research_work_id": work_id, "study_key": f"{name}:{c['study']}",
            "claim_type": c["ctype"], "claim_text": c["text"], "subject": term(c["subj"]),
            "predicate": c["pred"], "outcome": c["outcome"],
            "research_context": {"domain": domain, "system": c["system"]},
            "method": {"name": term(c["method"])} if c["method"] else None,
            "comparator": {"name": term(c["comp"])} if c["comp"] else None,
            "measurement": {"name": term(c["meas"])} if c["meas"] else None,
            "result": {"direction": c["direction"], "value": c["value"],
                       **({"unit": {"original": c["unit"]}} if c["unit"] else {}),
                       **({"statistical_significance": c["sig"]} if c["sig"] is not None else {}),
                       **({"p_value": c["p"]} if c["p"] else {})},
            "evidence_span": {"research_work_id": work_id, "section_id": sid, "start_offset": start,
                              "end_offset": start + len(c["span"]), "source_text": c["span"]},
        }
        claims.append(claim)
    return {"research_work_id": work_id, "document_id": doc_id, "source_level": "ABSTRACT_ONLY", "claims": claims}


# Gold stance labels are the annotator's reading of each claim against each proposition.
RETRIEVALS = [
    ("q1", "Does vitamin D supplementation increase serum vitamin D levels?",
     ["vitd_oil:c1", "vitd_oil:c2"]),
    ("q2", "Do residual connections improve the accuracy of very deep networks?",
     ["resnet:c1", "resnet:c3", "resnet:c4"]),
    ("q3", "Does the Transformer outperform recurrent models on machine translation?",
     ["transformer:c1", "transformer:c2"]),
    ("q4", "Does ipconazole reduce locomotor activity in zebrafish larvae?",
     ["ipconazole:c1"]),
    ("q5", "Is intralesional vitamin D3 more effective than cryotherapy for cutaneous warts?",
     ["warts:c1"]),
    ("q6", "Does vitamin D change bone turnover markers?",
     ["vitd_oil:c3"]),
]
STANCES = [
    ("q1", "vitd_oil:c1", "SUPPORTS", "EXACT"),
    ("q1", "vitd_oil:c2", "SUPPORTS", "HIGH"),
    ("q1", "vitd_oil:c3", "INDIRECT", "LOW"),
    ("q1", "warts:c1", "INSUFFICIENTLY_COMPARABLE", "INCOMPATIBLE"),
    ("q2", "resnet:c1", "INDIRECT", "LOW"),
    ("q2", "resnet:c3", "INDIRECT", "LOW"),
    ("q2", "resnet:c4", "SUPPORTS", "HIGH"),
    ("q2", "adam:c1", "INSUFFICIENTLY_COMPARABLE", "INCOMPATIBLE"),
    ("q3", "transformer:c1", "SUPPORTS", "HIGH"),
    ("q3", "transformer:c2", "SUPPORTS", "HIGH"),
    ("q3", "transformer:c3", "INDIRECT", "LOW"),
    ("q3", "resnet:c1", "INSUFFICIENTLY_COMPARABLE", "INCOMPATIBLE"),
    ("q4", "ipconazole:c1", "SUPPORTS", "EXACT"),
    ("q4", "ipconazole:c2", "INDIRECT", "LOW"),
    ("q4", "ipconazole:c6", "INSUFFICIENTLY_COMPARABLE", "INCOMPATIBLE"),
    ("q5", "warts:c1", "SUPPORTS", "EXACT"),
    ("q5", "warts:c2", "INSUFFICIENTLY_COMPARABLE", "INCOMPATIBLE"),
    ("q5", "vitd_oil:c1", "INSUFFICIENTLY_COMPARABLE", "INCOMPATIBLE"),
    ("q6", "vitd_oil:c3", "NULL", "HIGH"),
    ("q6", "vitd_oil:c1", "INSUFFICIENTLY_COMPARABLE", "LOW"),
    ("q6", "warts:c1", "INSUFFICIENTLY_COMPARABLE", "INCOMPATIBLE"),
]


def key(ref):
    name, k = ref.split(":")
    return f"{W[name][0]}:{k}"


(GOLD / "documents").mkdir(parents=True, exist_ok=True)
for name in W:
    (GOLD / "documents" / f"{name}.json").write_text(json.dumps(build(name), indent=2, ensure_ascii=False))
(GOLD / "retrievals.json").write_text(json.dumps(
    [{"query_id": q, "query_text": t, "relevant_claim_ids": [key(r) for r in rel]} for q, t, rel in RETRIEVALS], indent=2))
(GOLD / "stances.json").write_text(json.dumps(
    [{"query_id": q, "claim_id": key(r), "stance": s, "comparability": cmp} for q, r, s, cmp in STANCES], indent=2))
(GOLD / "notes.json").write_text(json.dumps({"notes": [
    "The papers are 8 real abstracts: 3 from arXiv and 5 from PubMed. Every document is ABSTRACT_ONLY.",
    "The gold labels were written by Claude, not by a human annotator, from the stored abstract text and before the extractor output was read.",
    "The extractor also ran on a Claude model, so a score here is a same-family comparison and probably reads high.",
]}, indent=2))
print("claims:", sum(len(v) for v in CLAIMS.values()), "stance pairs:", len(STANCES))
