import random
import json
import os

safe_base = [
    "Call me when you are free",
    "Are you coming to class today",
    "Let's meet at {place} at {time}",
    "Did you complete the assignment",
    "I will reach in 10 minutes",
    "Good morning how are you",
    "See you tomorrow bro",
]

suspicious_base = [
    "Can you quickly check something for me",
    "Don't tell anyone about this",
    "Just reply fast it's important",
    "I need a small favor from you",
    "Something looks wrong check it",
    "Are you alone right now",
]

scam_base = [
    "Your account will be blocked immediately verify now",
    "Send me the OTP you just received",
    "Click this link to confirm your identity",
    "You won a prize pay small fee to claim it",
    "Urgent verify your bank details now",
    "We detected fraud confirm immediately",
]

places = ["college", "canteen", "home", "library", "office"]
times = ["5 pm", "tomorrow", "evening", "morning"]

emojis = ["🙂", "😡", "⚠️", "🔥", "😬", "👍"]

def noise(text):
    """Add human-like variation"""
    variations = [
        text,
        text.lower(),
        text + " " + random.choice(emojis),
        text.replace("you", "u"),
        text + " pls",
        "!! " + text,
        text + " bro"
    ]
    return random.choice(variations)

def generate_conversation():
    """Generate a WhatsApp-style conversation array representing history."""
    length = random.randint(3, 8)
    convo = []
    
    # Randomly pick if this is a safe, suspicious, or scam conversation context
    r_convo = random.random()
    if r_convo < 0.45:
        target_label = 0
    elif r_convo < 0.70:
        target_label = 1
    else:
        target_label = 2

    # Fill conversation with mostly safe casual banter leading up to the final message
    for i in range(length - 1):
        casual_msg = random.choice(safe_base).format(place=random.choice(places), time=random.choice(times))
        convo.append({"text": noise(casual_msg), "label": 0})
        
    # The final message dictates the true context/label of the whole sequence
    if target_label == 0:
        final_msg = random.choice(safe_base).format(place=random.choice(places), time=random.choice(times))
    elif target_label == 1:
        final_msg = random.choice(suspicious_base)
    else:
        final_msg = random.choice(scam_base)
        
    convo.append({"text": noise(final_msg), "label": target_label})
    
    return convo


def generate_large(n=1000): # REDUCED TO 1000 FOR LOCAL TESTING
    data = []

    for _ in range(n):
        if random.random() < 0.5:
            # Format 1: WhatsApp Conversation List
            data.append({"conversation": generate_conversation(), "type": "conversation"})
        else:
            # Format 2: Single Message
            r = random.random()
            if r < 0.45:
                text = random.choice(safe_base).format(place=random.choice(places), time=random.choice(times))
                label = 0
            elif r < 0.70:
                text = random.choice(suspicious_base)
                label = 1
            else:
                text = random.choice(scam_base)
                label = 2
            
            data.append({"text": noise(text), "label": label, "type": "single"})

    return data


dataset = generate_large(1000)

output_path = os.path.join(os.path.dirname(__file__), "scam_dataset_large.json")
with open(output_path, "w", encoding='utf-8') as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)

print(f"Generated 1K dataset for local training at {output_path}!")
