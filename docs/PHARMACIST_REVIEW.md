# Pharmacist review checklist (AI drafts)

> **These tables are AI-generated DRAFT rules for hackathon demo use only.**
> Every numeric limit and interaction must be corrected by a licensed pharmacist before any clinical use.
> `verified_by_pharmacist` is currently `false` and `status` is `DRAFT` for all rows.
> Mark each row `[ ] correct` or write the corrected value in the last column.

---

## Max daily dose limits

| id | ingredient | adult_max_mg_day | pediatric_mg_per_kg_day | renal severe/KF | elderly_note | source_url | [ ] correct / corrected value |
|---|---|---|---|---|---|---|---|
| MAX-001 | paracetamol | 4000 | 60 | None/None | Consider lower total daily dose in frail elderly; avoid multiple paracetamol-con | https://www.fda.gov/drugs | [ ] |
| MAX-002 | ibuprofen | 3200 | 30 | avoid/avoid | Prefer lowest effective dose and shortest duration; higher GI/renal risk in elde | https://www.fda.gov/drugs | [ ] |
| MAX-003 | diclofenac | 150 | None | avoid/avoid | Use lowest effective dose; cardiovascular and GI risk increase with age. | https://www.fda.gov/drugs | [ ] |
| MAX-004 | aceclofenac | 200 | None | avoid/avoid | Caution in elderly due to NSAID class risks. | https://www.fda.gov/drugs | [ ] |
| MAX-005 | nimesulide | 200 | None | avoid/avoid | Hepatic risk; avoid prolonged use. | https://www.ema.europa.eu | [ ] |
| MAX-006 | mefenamic acid | 1500 | None | avoid/avoid | NSAID caution in elderly. | https://www.fda.gov/drugs | [ ] |
| MAX-007 | aspirin | 4000 | None | None/None | Higher bleed risk; antiplatelet doses are much lower than analgesic max. | https://www.fda.gov/drugs | [ ] |
| MAX-008 | tramadol | 400 | None | None/None | Start low; fall and seizure risk. | https://www.fda.gov/drugs | [ ] |
| MAX-009 | cetirizine | 10 | None | 5/None | Sedation risk; consider lower dose in renal impairment. | https://www.fda.gov/drugs | [ ] |
| MAX-010 | levocetirizine | 5 | None | None/avoid | Adjust for renal function. | https://www.fda.gov/drugs | [ ] |
| MAX-011 | domperidone | 30 | None | None/None | QT prolongation risk; avoid with interacting drugs. | https://www.ema.europa.eu | [ ] |
| MAX-012 | pantoprazole | 40 | None | None/None |  | https://www.fda.gov/drugs | [ ] |
| MAX-013 | omeprazole | 40 | None | None/None |  | https://www.fda.gov/drugs | [ ] |
| MAX-014 | metformin | 2550 | None | avoid/avoid | Assess renal function; risk of lactic acidosis if eGFR low. | https://www.fda.gov/drugs | [ ] |
| MAX-015 | amoxicillin | None | None | None/None |  | https://www.fda.gov/drugs | [ ] |
| MAX-016 | azithromycin | None | None | None/None |  | https://www.fda.gov/drugs | [ ] |
| MAX-017 | atorvastatin | 80 | None | None/None | Myopathy risk rises with dose and interacting drugs. | https://www.fda.gov/drugs | [ ] |
| MAX-018 | amlodipine | 10 | None | None/None | Start lower in elderly (edema, hypotension). | https://www.fda.gov/drugs | [ ] |
| MAX-019 | ondansetron | 24 | None | None/None | QT prolongation risk. | https://www.fda.gov/drugs | [ ] |
| MAX-020 | montelukast | 10 | None | None/None | Neuropsychiatric adverse-effect warnings apply. | https://www.fda.gov/drugs | [ ] |

## Curated interactions (override DDInter)

| id | A | B | tier | mechanism | recommended_action | source_url | [ ] correct / corrected value |
|---|---|---|---|---|---|---|---|
| CUR-INT-001 | warfarin | aspirin | critical | Additive antiplatelet/anticoagulant effect increases bleeding risk. | Avoid combination unless specialist-directed; monitor INR and bleeding closely. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-002 | warfarin | ibuprofen | critical | NSAIDs increase GI bleeding risk and may displace warfarin protein binding. | Prefer alternative analgesic (e.g. paracetamol within limits); monitor INR if unavoidable. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-003 | warfarin | diclofenac | critical | NSAID-related GI mucosal injury plus anticoagulation elevates bleeding risk. | Avoid; use non-NSAID analgesia if possible and seek clinician advice. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-004 | ibuprofen | diclofenac | review | Two NSAIDs together increase GI, renal, and cardiovascular adverse-effect risk without added benefit | Use a single NSAID at the lowest effective dose; avoid stacking NSAIDs. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-005 | ibuprofen | aceclofenac | review | Duplicate NSAID exposure increases adverse-effect risk. | Do not combine two NSAIDs; choose one agent. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-006 | diclofenac | nimesulide | review | NSAID duplication increases GI and hepatic risk. | Avoid concurrent NSAIDs; review indication and duration. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-007 | ibuprofen | ramipril | review | NSAIDs may reduce ACE-inhibitor antihypertensive effect and worsen renal function. | Limit NSAID duration; monitor BP, creatinine, and potassium. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-008 | diclofenac | ramipril | review | NSAID + ACE inhibitor can precipitate renal impairment, especially in volume depletion. | Avoid prolonged NSAID use; check renal function if co-prescribed. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-009 | ibuprofen | enalapril | review | NSAID may blunt ACE-inhibitor effect and increase acute kidney injury risk. | Prefer short NSAID courses; monitor renal function and BP. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-010 | diclofenac | enalapril | review | Combined renal afferent/efferent effects raise AKI risk. | Avoid if possible; hydrate and monitor creatinine/potassium. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-011 | ibuprofen | telmisartan | review | NSAID + ARB can impair renal autoregulation and raise potassium. | Limit NSAID; monitor renal function and electrolytes. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-012 | diclofenac | telmisartan | review | NSAID + ARB increases risk of renal adverse effects. | Avoid prolonged NSAID therapy; check creatinine. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-013 | ibuprofen | losartan | review | NSAID may reduce ARB efficacy and worsen kidney function. | Use lowest NSAID dose/shortest duration; monitor labs. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-014 | clopidogrel | omeprazole | critical | Omeprazole inhibits CYP2C19 activation of clopidogrel, potentially reducing antiplatelet effect. | Prefer a PPI with less CYP2C19 inhibition if gastroprotection is needed; seek clinician advice. | https://www.fda.gov/drugs/drug-safety-and-availability/fda-reminder-avoid-concomitant-use-plavix-clopidogrel-and-omeprazole | [ ] |
| CUR-INT-015 | clopidogrel | esomeprazole | critical | Strong CYP2C19 inhibition may reduce clopidogrel activation. | Avoid combination when possible; discuss PPI choice with prescriber. | https://www.fda.gov/drugs/drug-safety-and-availability/fda-reminder-avoid-concomitant-use-plavix-clopidogrel-and-omeprazole | [ ] |
| CUR-INT-016 | tramadol | ondansetron | review | Both affect serotonergic pathways; ondansetron may also reduce tramadol analgesic effect. | Monitor efficacy and serotonin-related symptoms; consider alternatives if needed. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-017 | ramipril | spironolactone | critical | Dual renin–angiotensin–aldosterone blockade increases hyperkalemia and renal failure risk. | Monitor potassium and renal function closely; ensure indication is appropriate. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-018 | enalapril | spironolactone | critical | ACE inhibitor + potassium-sparing diuretic raises hyperkalemia risk. | Check K+ and creatinine; avoid potassium supplements unless directed. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-019 | warfarin | nimesulide | critical | NSAID increases bleeding risk with anticoagulants. | Avoid NSAID with warfarin when possible. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-020 | aspirin | ibuprofen | review | Ibuprofen may interfere with aspirin's antiplatelet effect and increase GI bleeding risk. | If both needed, separate dosing per clinician advice; watch for GI symptoms. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-021 | metformin | diclofenac | review | NSAID-related renal impairment can increase metformin accumulation and lactic acidosis risk. | Use NSAIDs cautiously; hold metformin if acute renal risk (sick day rules). | https://www.fda.gov/drugs | [ ] |
| CUR-INT-022 | lithium | ibuprofen | critical | NSAIDs reduce lithium clearance and can cause lithium toxicity. | Avoid NSAIDs or monitor lithium levels closely if unavoidable. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-023 | methotrexate | ibuprofen | critical | NSAIDs can reduce methotrexate clearance and increase toxicity. | Avoid concurrent high-dose methotrexate with NSAIDs unless specialist-supervised. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-024 | ciprofloxacin | warfarin | review | Fluoroquinolones may potentiate anticoagulant effect. | Monitor INR during and after antibiotic course. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-025 | azithromycin | warfarin | review | Macrolides may alter warfarin response in some patients. | Consider INR check if co-administered. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-026 | sertraline | tramadol | critical | Additive serotonergic effects increase serotonin syndrome and seizure risk. | Avoid combination when possible; monitor closely if used. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-027 | fluoxetine | tramadol | critical | SSRI + tramadol raises serotonin syndrome risk; CYP2D6 interactions may alter tramadol activation. | Prefer alternative analgesic; escalate if agitation, tremor, or hyperreflexia occur. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-028 | simvastatin | clarithromycin | critical | CYP3A4 inhibition markedly increases simvastatin exposure and myopathy risk. | Avoid combination; hold or switch statin per local guidance. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-029 | atorvastatin | clarithromycin | review | CYP3A4 inhibition can increase statin levels and muscle toxicity risk. | Consider temporary statin hold or dose review during macrolide course. | https://www.fda.gov/drugs | [ ] |
| CUR-INT-030 | potassium | spironolactone | critical | Additive hyperkalemia risk with potassium-sparing diuretic plus potassium salts. | Avoid unsupervised potassium supplements; monitor serum K+. | https://www.fda.gov/drugs | [ ] |

## Top 60 DDInter Major pairs (among brand-dataset ingredients)

| # | ingredient_a | ingredient_b | level | tier | source | [ ] correct / corrected value |
|---|---|---|---|---|---|---|
| 1 | abacavir | leflunomide | major | critical | DDInter 2.0 | [ ] |
| 2 | abacavir | teriflunomide | major | critical | DDInter 2.0 | [ ] |
| 3 | abatacept | adalimumab | major | critical | DDInter 2.0 | [ ] |
| 4 | abatacept | baricitinib | major | critical | DDInter 2.0 | [ ] |
| 5 | abatacept | cladribine | major | critical | DDInter 2.0 | [ ] |
| 6 | abatacept | etanercept | major | critical | DDInter 2.0 | [ ] |
| 7 | abatacept | fingolimod | major | critical | DDInter 2.0 | [ ] |
| 8 | abatacept | golimumab | major | critical | DDInter 2.0 | [ ] |
| 9 | abatacept | infliximab | major | critical | DDInter 2.0 | [ ] |
| 10 | abatacept | leflunomide | major | critical | DDInter 2.0 | [ ] |
| 11 | abatacept | natalizumab | major | critical | DDInter 2.0 | [ ] |
| 12 | abatacept | teriflunomide | major | critical | DDInter 2.0 | [ ] |
| 13 | abatacept | tocilizumab | major | critical | DDInter 2.0 | [ ] |
| 14 | abatacept | tofacitinib | major | critical | DDInter 2.0 | [ ] |
| 15 | abciximab | acalabrutinib | major | critical | DDInter 2.0 | [ ] |
| 16 | abciximab | alteplase | major | critical | DDInter 2.0 | [ ] |
| 17 | abciximab | apixaban | major | critical | DDInter 2.0 | [ ] |
| 18 | abciximab | ardeparin | major | critical | DDInter 2.0 | [ ] |
| 19 | abciximab | cabozantinib | major | critical | DDInter 2.0 | [ ] |
| 20 | abciximab | clopidogrel | major | critical | DDInter 2.0 | [ ] |
| 21 | abciximab | dalteparin | major | critical | DDInter 2.0 | [ ] |
| 22 | abciximab | dasatinib | major | critical | DDInter 2.0 | [ ] |
| 23 | abciximab | deferasirox | major | critical | DDInter 2.0 | [ ] |
| 24 | abciximab | dipyridamole | major | critical | DDInter 2.0 | [ ] |
| 25 | abciximab | enoxaparin | major | critical | DDInter 2.0 | [ ] |
| 26 | abciximab | eptifibatide | major | critical | DDInter 2.0 | [ ] |
| 27 | abciximab | fondaparinux | major | critical | DDInter 2.0 | [ ] |
| 28 | abciximab | heparin | major | critical | DDInter 2.0 | [ ] |
| 29 | abciximab | ibrutinib | major | critical | DDInter 2.0 | [ ] |
| 30 | abciximab | prasugrel | major | critical | DDInter 2.0 | [ ] |
| 31 | abciximab | ramucirumab | major | critical | DDInter 2.0 | [ ] |
| 32 | abciximab | regorafenib | major | critical | DDInter 2.0 | [ ] |
| 33 | abciximab | reteplase | major | critical | DDInter 2.0 | [ ] |
| 34 | abciximab | rivaroxaban | major | critical | DDInter 2.0 | [ ] |
| 35 | abciximab | streptokinase | major | critical | DDInter 2.0 | [ ] |
| 36 | abciximab | tenecteplase | major | critical | DDInter 2.0 | [ ] |
| 37 | abciximab | ticlopidine | major | critical | DDInter 2.0 | [ ] |
| 38 | abciximab | tinzaparin | major | critical | DDInter 2.0 | [ ] |
| 39 | abciximab | tirofiban | major | critical | DDInter 2.0 | [ ] |
| 40 | abciximab | urokinase | major | critical | DDInter 2.0 | [ ] |
| 41 | abciximab | warfarin | major | critical | DDInter 2.0 | [ ] |
| 42 | abemaciclib | adalimumab | major | critical | DDInter 2.0 | [ ] |
| 43 | abemaciclib | atazanavir | major | critical | DDInter 2.0 | [ ] |
| 44 | abemaciclib | baricitinib | major | critical | DDInter 2.0 | [ ] |
| 45 | abemaciclib | carbamazepine | major | critical | DDInter 2.0 | [ ] |
| 46 | abemaciclib | ceritinib | major | critical | DDInter 2.0 | [ ] |
| 47 | abemaciclib | cladribine | major | critical | DDInter 2.0 | [ ] |
| 48 | abemaciclib | clarithromycin | major | critical | DDInter 2.0 | [ ] |
| 49 | abemaciclib | clozapine | major | critical | DDInter 2.0 | [ ] |
| 50 | abemaciclib | conivaptan | major | critical | DDInter 2.0 | [ ] |
| 51 | abemaciclib | deferiprone | major | critical | DDInter 2.0 | [ ] |
| 52 | abemaciclib | enzalutamide | major | critical | DDInter 2.0 | [ ] |
| 53 | abemaciclib | etanercept | major | critical | DDInter 2.0 | [ ] |
| 54 | abemaciclib | fingolimod | major | critical | DDInter 2.0 | [ ] |
| 55 | abemaciclib | fosphenytoin | major | critical | DDInter 2.0 | [ ] |
| 56 | abemaciclib | golimumab | major | critical | DDInter 2.0 | [ ] |
| 57 | abemaciclib | indinavir | major | critical | DDInter 2.0 | [ ] |
| 58 | abemaciclib | infliximab | major | critical | DDInter 2.0 | [ ] |
| 59 | abemaciclib | itraconazole | major | critical | DDInter 2.0 | [ ] |
| 60 | abemaciclib | ketoconazole | major | critical | DDInter 2.0 | [ ] |
