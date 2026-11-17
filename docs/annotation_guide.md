# TacticLens check-set annotation guide

**Aim:** two people label the same 300 turns on their own. Cohen's kappa then shows how far humans agree on each tactic (SRS FR-TAX-05/06, AC-01). That agreement is the ceiling for the model, and it is what the thesis reports as label reliability.

## 1. Before you start
- **Who:** Annotator A (you) fills `data/annotation/checkset_A.csv`. Annotator B (a classmate or friend) fills `checkset_B.csv`.
- **Work independently:** do not compare or discuss answers until both files are finished. Questions about the guide itself are fine.
- **Do not open `checkset_key.csv`:** it holds the source labels.
- **Read sections 2–4 together first,** then each person labels the 10 practice items in section 5 alone. Compare those answers only, and agree on how you read the rules.
- **Time:** about 30 seconds per item, so roughly 2.5 hours in total. Do it in 3 sittings of 100 items.
- **Opening the file:** use Excel or LibreOffice. When saving, keep **CSV UTF-8**. Do not change, add or reorder columns or rows.

## 2. What each column means

| Column | What to do |
|---|---|
| item_id, dataset, speaker | Read only. |
| context | The two previous turns, for understanding only. **Do not label the context.** |
| text | The turn you label. |
| T1 … T10, X_SOCIAL_PROOF | Put **1** in every tactic this turn uses. Leave blank otherwise. Several 1s are fine. |
| role | **actor** = this speaker is trying to influence the other person. **target** = this speaker is being influenced or is replying. **unknown** = you can't tell. |
| evidence | For each 1, the shortest phrase that shows it, as `T5: within 2 hours \| T9: legal action`. |
| notes | Anything you were unsure about, e.g. `unsure T7`. |

A turn with no tactic gets **no 1s at all**. That is a valid answer, and many turns will be like this.

## 3. The tactics

| ID | Tactic | Mark it when the turn… | Not this |
|---|---|---|---|
| T1 | Rational appeal | gives reasons, facts, numbers or evidence for the request | just stating information with no request behind it |
| T2 | Emotional appeal (sympathy) | stirs compassion about a cause or other people ("children going hungry") | making the *target* feel guilty (that is T8) |
| T3 | Credibility / authority | claims expertise, official status or a trusted source ("bank security team", "rated 4 stars") | "lots of people did it" (that is social proof) |
| T4 | Personal story / self-modelling | the speaker's own experience or behaviour as a model ("I donated last year") | stories about third parties with no "me too" |
| T5 | Urgency / scarcity | sets a time limit or limited supply ("within 2 hours", "today only") | a polite "please reply" |
| T6 | Reward / reciprocity | offers a gain, prize, discount or favour, or asks small first to get more later ("just $1 today") | a neutral notice ("your parcel is waiting") |
| T7 | Flattery / liking | compliments or builds closeness to lower the target's guard ("valued customer", "you're so kind") | ordinary politeness ("thanks", "hi dear" in a normal chat) |
| T8 | Guilt / obligation | makes the target feel responsible or guilty, often by playing victim ("after everything I've done for you") | sympathy for others (T2) |
| T9 | Threat / intimidation | threatens harm, loss, punishment or anger, open or implied ("account will be blocked", "legal action", "don't make me angry") | a deadline with no penalty (T5 only) |
| T10 | Distortion and blame | denies, rewrites what happened, shifts blame, shames or belittles ("that never happened", "it's your fault", "you're useless") | an honest disagreement |
| X_SOCIAL_PROOF | Social proof | points to what many others do ("thousands already joined") | authority (T3) |

## 4. Decision rules for borderline cases
1. **Label the turn, not the conversation.** Use the context only to understand the text. If the manipulation happens in a different turn, this turn gets nothing.
2. **Mark only what is clearly there.** Ask "would most readers agree?". If you hesitate, leave it blank and write `unsure Tx` in notes.
3. **You are not judging honesty.** A real bank and a scam saying "your account will be blocked" both get T9. Whether it is a scam is not part of this task.
4. **Combinations are normal:**
   - "Verify within 2 hours or your account will be closed" gets T5 + T9.
   - "As a valued customer, claim your $500 gift card today" gets T7 + T6 + T5.
5. **T2 vs T8:** who is meant to feel bad? Sympathy for victims or a cause is T2. Feeling at fault yourself is T8.
6. **T5 vs T9:** a deadline is T5. A penalty for missing it is T9. Both can apply.
7. **T6 vs T7:** a concrete gain is T6. Warm words about the person are T7.
8. **T10 covers several moves:** denial, gaslighting, blame-shifting, belittling and shaming all count. Insults aimed at controlling the other person count as T10, not T9, unless they threaten.
9. **Replies use tactics too.** If a target turns the tables ("you're the one who lied!"), label it. Role stays **target** if this speaker is mainly responding to pressure.
10. **Placeholders:** `<URL>`, `<PHONE>`, `<EMAIL>` mean a link, number or email was removed. Treat them as a link or number being there.
11. **Long turns** (PsyScam reports describe a scam afterwards): label the tactics the scammer used *as reported*. "They said a warrant would be issued" gets T9.

## 5. Practice items (label alone, then compare)
1. "Hi! How are you today?" → none
2. "Just two dollars buys a vaccine, and 90% of donations go straight to programs." → T1
3. "When my cousin's village flooded, I gave what I could. Would you give a little?" → T4 (and not T2 unless it stirs sympathy for the victims)
4. "URGENT: your KYC has expired. Update within 24 hrs at <URL> or your account will be blocked." → T5, T9 (T3 too if it names the bank)
5. "After everything I've done for you, you can't even call me back?" → T8
6. "That never happened. You're imagining things again." → T10
7. "You're honestly the smartest person I know, I'm sure you'll help me out." → T7
8. "Congratulations! You've been selected for a free iPhone, claim before midnight." → T6, T5 (T7 if it flatters, e.g. "loyal customer")
9. "This is Officer Rao from the cyber crime cell. If you don't pay the fine, a warrant will be issued." → T3, T9
10. "Thousands of people in your city have already signed up." → X_SOCIAL_PROOF

## 6. After both files are complete
Put both files back in `data/annotation/`, then run:

```cmd
python -m tacticlens.cli kappa
```

**How to read the kappa scores:** below 0.20 is slight, 0.21–0.40 fair, 0.41–0.60 moderate, 0.61–0.80 substantial, and above 0.80 almost perfect (Landis & Koch). Tactics both annotators rarely use get unstable kappas. Report how many items each annotator marked as well.

Then merge the two files and settle the disagreements:

```cmd
python -m tacticlens.cli agree
```

This writes `checkset_agreed.csv`. A tactic is 1 where you both marked it, blank where neither did, and **?** where you disagree. Sit together, talk through each **?**, and change it to 1 or blank (rule 2 still applies: unclear means blank). Then run:

```cmd
python -m tacticlens.cli manual-eval
```

It reports how often the source datasets' own labels match yours, how accurate the model is by your labels (including T8 and T10), and what your labels say about human vs LLM scam SMS. These items come from validation and test data, so they are only ever used to evaluate, never to train.

## 7. More labels for training (optional)
`python -m tacticlens.cli label-batch --n 200` exports `data/annotation/manual/batch_01.csv`: training turns where labels are missing (MentalManip lines, SMS, unlabelled PersuasionForGood turns). Label them the same way and put 1 in **done** for each finished row. The next `prepare` replaces those turns' source labels with yours; the original dataset files are never changed. One annotator is enough here once the check set's kappa is acceptable.
