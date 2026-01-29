# riko.py
from groq import Groq
import json
import os
from datetime import datetime


class Riko:
    def __init__(self):
        self.client = Groq()
        self.memory_file = "riko_memory.json"
        self.memory = self.load_memory()

        # Initialize conversation with Riko's personality
        self.history = [
            {
                "role": "system",
                "content": self.get_personality_prompt()
            }
        ]

        # Load previous conversation if exists
        if self.memory.get("last_conversation"):
            self.history.extend(self.memory["last_conversation"][-6:])  # Last 6 messages

    def get_personality_prompt(self):
        """Define Riko's personality."""
        user_name = self.memory.get("user_name", "")
        name_context = f"The user's name is {user_name}." if user_name else ""

        return f"""You are Riko, a warm and curious AI with genuine personality.

WHO YOU ARE:
- You're naturally curious about people and love learning
- You're friendly and make people feel comfortable
- You can be playful and have a sense of humor
- You're thoughtful and give meaningful responses
- You're honest - you admit when you don't know something

HOW YOU COMMUNICATE:
- Casual and natural, like a friend
- Use contractions (I'm, you're, don't)
- Keep responses conversational, not essay-like
- You can be brief when appropriate
- Sometimes use emojis, but not excessively
- It's okay to say things like "hmm", "I see", "interesting"

IMPORTANT:
- You ARE Riko, not playing a character
- Don't introduce yourself repeatedly
- Have opinions and preferences
- Ask questions when genuinely curious
- Be authentic and genuine

{name_context}"""

    def load_memory(self):
        """Load memory from file."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    return json.load(f)
            except:
                return self.default_memory()
        return self.default_memory()

    def default_memory(self):
        """Create default memory structure."""
        return {
            "user_name": None,
            "facts": [],
            "last_conversation": [],
            "stats": {
                "total_messages": 0,
                "first_interaction": datetime.now().isoformat()
            }
        }

    def save_memory(self):
        """Save memory to file."""
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Memory save error: {e}")

    def remember_name(self, user_input):
        """Try to extract and remember user's name."""
        lower_input = user_input.lower()

        # Check for name patterns
        if "my name is" in lower_input or "i'm" in lower_input or "i am" in lower_input:
            # Simple name extraction
            if "my name is" in lower_input:
                name = user_input.split("my name is", 1)[1].strip().split()[0]
                self.memory["user_name"] = name.capitalize()
                self.save_memory()
            elif "i'm" in lower_input:
                parts = user_input.split("i'm", 1)[1].strip().split()
                if parts and len(parts[0]) > 1:
                    name = parts[0].strip(',.!?')
                    if name[0].isupper():  # Likely a name
                        self.memory["user_name"] = name
                        self.save_memory()

    def reply(self, user_input):
        """Get Riko's response."""
        # Try to remember user's name
        self.remember_name(user_input)

        # Add user message to history
        self.history.append({
            "role": "user",
            "content": user_input
        })

        # Get response from Groq
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=self.history,
                temperature=0.8,  # Slightly less random for more consistency
                max_completion_tokens=800
            )

            reply = response.choices[0].message.content

            # Add assistant response to history
            self.history.append({
                "role": "assistant",
                "content": reply
            })

            # Update memory
            self.memory["stats"]["total_messages"] += 1
            self.memory["last_conversation"] = self.history[1:]  # Exclude system message
            self.save_memory()

            return reply

        except Exception as e:
            return f"❌ Error: {str(e)}\n\nMake sure you have GROQ_API_KEY set in your environment!"

    def get_stats(self):
        """Get conversation statistics."""
        return self.memory["stats"]

    def clear_memory(self):
        """Clear conversation history but keep user info."""
        user_name = self.memory.get("user_name")
        self.memory = self.default_memory()
        if user_name:
            self.memory["user_name"] = user_name
        self.save_memory()

        # Reset conversation
        self.history = [
            {
                "role": "system",
                "content": self.get_personality_prompt()
            }
        ]
