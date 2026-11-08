# TacticLens user study (protocol)

**Question.** Does TacticLens help people spot influence tactics, and do they find it usable and trustworthy?

## Design
- **Participants:** 12–15 students or staff, over 18, who give informed consent. No personal data is collected beyond the answers.
- **Within-subject design:** each person judges 8 short texts, 4 without the tool and then 4 with it. The two halves use matched sets (A/B), counterbalanced: half the people see A without the tool, the other half see B without it.
- **The texts:** written for the study, like those in `src/tacticlens/serve/examples.py`. Each set has 1 persuasion, 1 manipulation, 1 scam SMS and 1 neutral text. Two people agree the "correct" tactics beforehand.
- **Running the tool:** run it locally with feedback logging:
  `python -m tacticlens.cli ui --feedback-log reports/study_feedback.csv`
  The log stores ratings and a hash of the input, never the text.

## Per text, the participant answers
1. Which category is it: persuasion, manipulation, scam or neutral?
2. Which tactics are used? (Tick the 10 tactic names, with short definitions on the sheet.)
3. How confident are you? (1–5)

## After the tool half
- **SUS** (System Usability Scale, 10 items, 1–5).
- **Trust and usefulness** (1–5 each):
  - "The highlighted evidence made the result easier to check."
  - "I would use this before replying to a suspicious message."
  - "The tool's mistakes were easy to notice."
- **Open question:** what was confusing or missing?

## Analysis
- **Accuracy:** category accuracy and tactic F1 against the agreed answers, without vs with the tool, using a Wilcoxon signed-rank test per participant.
- **Confidence:** mean confidence, without vs with the tool.
- **Usability:** the SUS score (0–100; 68 is the usual "average" mark).
- **Feedback:** helpful / not helpful counts from `reports/study_feedback.csv`.
- **Reporting:** report effect sizes and say plainly that the sample is small.

## Ethics
- **Approval:** check whether your department needs approval for a minimal-risk study.
- **Wording:** tell participants the tool is a research prototype that can be wrong.
- **Content:** do not use real messages from anyone's phone.
