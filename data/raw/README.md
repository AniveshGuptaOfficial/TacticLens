# Raw data (not in Git)

Put each downloaded dataset in its own folder here:

- `p4g/`          PersuasionForGood: full_dialog.csv, full_info.csv, 300_dialog.xlsx, 300_info.xlsx
- `mentalmanip/`  mentalmanip_maj.csv (and mentalmanip_con.csv)
- `sms_human/`    Mishra-Soni SMS Phishing (the CSV from Mendeley)
- `sms_llm/`      Munoz & Islam balanced LLM SMS (the CSV from Mendeley)
- `psyscam/`      PsyScam (csv / json / jsonl)

Then run `python -m tacticlens.cli inspect` to check what was found.
