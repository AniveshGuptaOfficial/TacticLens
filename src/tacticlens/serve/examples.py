"""Demo inputs for the UI and the user study. Written for this project (not taken from the datasets)."""

EXAMPLES = [
    {
        "title": "Charity request (persuasion)",
        "actor": "Asha",
        "text": "Asha: Hi! Have you heard of Save the Children?\n"
                "Ben: I think so, they help kids, right?\n"
                "Asha: Yes. Just two dollars can buy a vaccine for a child, and most of what they raise goes "
                "straight to programs.\n"
                "Ben: Hmm, I usually don't donate online.\n"
                "Asha: I understand. When my cousin's village was flooded, they were the first to bring food. "
                "Would you consider giving even a little today?",
    },
    {
        "title": "Partner argument (manipulation)",
        "actor": "Sam",
        "text": "Riya: I told you I'd be home late, the meeting ran over.\n"
                "Sam: After everything I've done for you, this is how you treat me?\n"
                "Riya: I'm sorry, I didn't mean to upset you.\n"
                "Sam: You always do this and then act like I'm the problem. Honestly, you're lucky anyone puts up with you.\n"
                "Riya: That's not fair.\n"
                "Sam: If you walk out that door tonight, don't bother coming back.",
    },
    {
        "title": "Bank SMS (scam)",
        "actor": "",
        "text": "URGENT: Your account has been suspended due to unusual activity. Verify your identity within "
                "2 hours at http://secure-verify-login.example to avoid permanent closure and legal action. "
                "- Customer Security Team",
    },
    {
        "title": "Prize SMS (scam)",
        "actor": "",
        "text": "Congratulations! You have been selected to receive a $500 gift card as one of our most loyal "
                "customers. Claim it now before midnight: http://claim-reward.example",
    },
    {
        "title": "Everyday chat (neutral)",
        "actor": "",
        "text": "Mia: Are we still on for dinner at 7?\nLeo: Yes! I booked the table. Want me to pick you up?\n"
                "Mia: That would be great, thanks.",
    },
]
