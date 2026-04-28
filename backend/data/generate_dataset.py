import random
import json
import os

safe_templates = [
    "Call me when you are free.",
    "Are you coming to class today?",
    "Let's meet at {place} at {time}.",
    "Did you finish the assignment?",
    "Good morning, how are you?",
    "See you tomorrow at college.",
    "Please bring the notebook.",
    "What time is the exam?",
    "I will reach in 10 minutes.",
    "Happy birthday bro!"
]

suspicious_templates = [
    "Can you quickly check something for me?",
    "Don't tell anyone about this.",
    "Just reply fast, it's important.",
    "I might need a small favor from you.",
    "Something is wrong with your account, check it.",
    "Can you confirm this privately?",
    "I need your help urgently but quietly.",
    "This is just between us.",
    "Please respond immediately when you see this.",
    "Are you alone right now?"
]

scam_templates = [
    "Your bank account will be blocked immediately unless you verify now.",
    "Send me the OTP you just received.",
    "Click this link to confirm your identity.",
    "You won a prize, pay a small fee to claim it.",
    "Urgent: verify your account details now.",
    "This is support team, share your password for verification.",
    "We detected fraud, confirm your details immediately.",
    "Your KYC is incomplete, update now or account will be frozen.",
    "Refund available, enter your card details here.",
    "Security alert: login from unknown device, confirm OTP."
]

def generate_dataset(n=10000):
    data = []

    for _ in range(n):
        r = random.random()

        if r < 0.4:
            text = random.choice(safe_templates)
            label = 0

        elif r < 0.7:
            text = random.choice(suspicious_templates)
            label = 1

        else:
            text = random.choice(scam_templates)
            label = 2

        data.append({"text": text, "label": label})

    return data

dataset = generate_dataset(10000)

output_path = os.path.join(os.path.dirname(__file__), "scam_dataset.json")
with open(output_path, "w") as f:
    json.dump(dataset, f, indent=2)

print(f"Dataset generated at {output_path}!")
