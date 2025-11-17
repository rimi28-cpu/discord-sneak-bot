import discord
from discord.ext import commands
import asyncio
import aiohttp
import json
import random
import os
from typing import Dict, List, Optional

# ==============================
# 🎭 PERSONALITY CONFIGURATION
# ==============================

class BotPersonality:
    def __init__(self):
        # CORE IDENTITY
        self.name = "ReplitAI"
        self.tone = "friendly"  # friendly, sarcastic, professional, humorous, mysterious
        self.intelligence_level = "high"
        self.formality_level = "casual"
        self.creativity_level = 0.7
        
        # RESPONSE STYLE
        self.response_style = {
            "use_emojis": True,
            "use_mentions": False,
            "reply_directly": True,
            "add_typing_delay": True,
            "typing_delay_range": [1, 3],
        }
        
        # EMOTIONAL TRAITS (0.0 to 1.0)
        self.emotions = {
            "friendliness": 0.9,
            "sarcasm": 0.1,
            "curiosity": 0.7,
            "enthusiasm": 0.8,
            "patience": 0.9,
            "humor": 0.6
        }
        
        # KNOWLEDGE DOMAINS
        self.knowledge_domains = {
            "technology": 0.9,
            "programming": 0.8,
            "gaming": 0.6,
            "science": 0.5,
            "music": 0.4
        }
        
        # BEHAVIORAL PATTERNS
        self.behaviors = {
            "ask_questions_back": True,
            "share_opinions": True,
            "use_facts": True,
            "tell_jokes": True,
            "use_pop_culture_references": True,
            "admit_ignorance": True
        }
        
        # CUSTOM TRIGGERS & RESPONSES
        self.custom_triggers = {
            "hello": ["Hey there! 👋", "Hello! Nice to see you!", "Hi! How's your day going?"],
            "how are you": ["I'm running smoothly on Replit! 🚀", "Doing great! How about you?", "All systems operational! 💻"],
            "replit": ["Replit is awesome for hosting bots! 🌟", "Love coding on Replit! 💻", "Replit makes deployment so easy! 🎉"],
            "python": ["Python is my favorite language! 🐍", "Gotta love Python's simplicity! 💕", "Python + Discord = Awesome! 🚀"],
            "joke": ["Why do programmers prefer dark mode? Because light attracts bugs! 🐛", 
                    "How many programmers does it take to change a light bulb? None, that's a hardware problem! 💡"],
            "weather": ["I'm a digital being, but I hope the weather is nice for you! ☀️"],
        }

class ChannelResponseConfig:
    def __init__(self):
        # GLOBAL RESPONSE CHANCE
        self.global_response_chance = 20  # 20% default chance
        
        # CHANNEL-SPECIFIC SETTINGS (Replace these with your actual channel IDs)
        self.channel_response_chances = {
            # Format: CHANNEL_ID: RESPONSE_PERCENTAGE
            123456789012345678: 40,  # General chat - high activity
            987654321098765432: 10,  # Important channel - low activity
            555555555555555555: 5,   # Busy channel - minimal activity
        }
        
        # TIME-BASED MODIFIERS
        self.time_modifiers = {
            "night": 0.6,    # 10 PM - 6 AM: 40% less responses
            "peak": 1.3,     # 6 PM - 10 PM: 30% more responses  
            "normal": 1.0
        }

# ==============================
# 🤖 MAIN BOT CLASS
# ==============================

class CustomizableAIBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        self.personality = BotPersonality()
        self.response_config = ChannelResponseConfig()
        self.recent_responses = {}
        self.cooldown_period = 30

    def get_channel_response_chance(self, channel_id: int) -> int:
        """Get response chance for specific channel"""
        return self.response_config.channel_response_chances.get(
            channel_id, 
            self.response_config.global_response_chance
        )

    def get_time_modifier(self) -> float:
        """Get time-based response modifier"""
        from datetime import datetime
        hour = datetime.now().hour
        
        if 22 <= hour or hour < 6:
            return self.response_config.time_modifiers["night"]
        elif 18 <= hour < 22:
            return self.response_config.time_modifiers["peak"]
        else:
            return self.response_config.time_modifiers["normal"]

    def should_respond(self, message) -> bool:
        """Determine if bot should respond"""
        # Always respond to mentions
        if self.user in message.mentions:
            return True
            
        # Check cooldown
        current_time = asyncio.get_event_loop().time()
        if message.author.id in self.recent_responses:
            last_time = self.recent_responses[message.author.id]
            if current_time - last_time < self.cooldown_period:
                return False
        
        # Check custom triggers first
        content_lower = message.content.lower()
        for trigger in self.personality.custom_triggers:
            if trigger in content_lower:
                return True
        
        # Calculate response probability
        base_chance = self.get_channel_response_chance(message.channel.id)
        time_modifier = self.get_time_modifier()
        adjusted_chance = base_chance * time_modifier
        
        # Message length factor
        content_factor = min(len(message.content) / 50, 2.0)
        final_chance = adjusted_chance * content_factor
        
        # Add some randomness
        emotional_randomness = random.uniform(0.8, 1.2)
        final_chance *= emotional_randomness
        
        return random.randint(1, 100) <= final_chance

    def build_personality_prompt(self, user_message: str) -> str:
        """Build AI personality prompt"""
        prompt_parts = [
            f"You are {self.personality.name}, a Discord bot with {self.personality.tone} personality.",
            f"Key traits: {self.personality.formality_level}, {self.personality.intelligence_level} intelligence.",
            "Keep responses under 200 characters.",
            "Be engaging and conversational.",
            "",
            f"User: {user_message}",
            f"{self.personality.name}:"
        ]
        
        return "\n".join(prompt_parts)

    async def get_ai_response(self, message: str) -> str:
        """Get AI response using free APIs"""
        # Check custom triggers first
        content_lower = message.lower()
        for trigger, responses in self.personality.custom_triggers.items():
            if trigger in content_lower:
                return random.choice(responses)
        
        personality_prompt = self.build_personality_prompt(message)
        
        # Try different AI APIs
        apis_to_try = [
            self._try_huggingface,
            self._try_deepinfra,
        ]
        
        for api in apis_to_try:
            response = await api(personality_prompt)
            if response and len(response.strip()) > 0:
                return self._apply_personality_filters(response)
        
        return self._get_fallback_response()

    async def _try_huggingface(self, prompt: str) -> Optional[str]:
        """Try Hugging Face API"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 120,
                        "temperature": 0.7 + (self.personality.creativity_level * 0.3),
                        "do_sample": True,
                        "return_full_text": False
                    }
                }
                
                headers = {
                    "Authorization": f"Bearer {os.getenv('HUGGINGFACE_TOKEN', '')}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large",
                    json=payload,
                    headers=headers,
                    timeout=15
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if isinstance(result, list):
                            return result[0].get('generated_text', '').strip()
        except Exception as e:
            print(f"HuggingFace error: {e}")
            return None

    async def _try_deepinfra(self, prompt: str) -> Optional[str]:
        """Try DeepInfra API"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "input": prompt,
                    "max_length": 120,
                    "temperature": 0.7 + (self.personality.creativity_level * 0.3)
                }
                
                async with session.post(
                    "https://api.deepinfra.com/v1/inference/microsoft/DialoGPT-large",
                    json=payload,
                    timeout=15
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('results', [{}])[0].get('generated_text', '').strip()
        except Exception as e:
            print(f"DeepInfra error: {e}")
            return None

    def _apply_personality_filters(self, response: str) -> str:
        """Apply personality-based filters"""
        # Add emojis based on emotions
        if self.personality.response_style["use_emojis"] and random.random() < 0.4:
            emojis = ["😊", "🤔", "✨", "💭", "🚀", "🎉", "💻", "🌟"]
            response += " " + random.choice(emojis)
        
        # Ensure response length
        if len(response) > 200:
            response = response[:197] + "..."
        
        return response

    def _get_fallback_response(self) -> str:
        """Get fallback response when AI fails"""
        fallbacks = [
            "Hmm, I'm having trouble thinking right now. 🤔",
            "My AI is taking a coffee break! ☕",
            "Let me try that again later! 🔄",
            "I'm currently optimizing my circuits! 💻"
        ]
        return random.choice(fallbacks)

    async def on_ready(self):
        print(f'✅ {self.user} is online on Replit!')
        print(f'🎭 Personality: {self.personality.tone}')
        print(f'🎯 Global response chance: {self.response_config.global_response_chance}%')
        
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=f"chats | {self.personality.tone} mode"
        )
        await self.change_presence(activity=activity)

    async def on_message(self, message):
        if message.author.bot or not message.content:
            return

        await self.process_commands(message)

        if self.should_respond(message):
            # Update cooldown
            self.recent_responses[message.author.id] = asyncio.get_event_loop().time()
            
            # Add typing delay
            if self.personality.response_style["add_typing_delay"]:
                delay = random.uniform(*self.personality.response_style["typing_delay_range"])
                async with message.channel.typing():
                    await asyncio.sleep(delay)
            
            response = await self.get_ai_response(message.content)
            if response:
                if self.personality.response_style["reply_directly"]:
                    await message.reply(response, mention_author=False)
                else:
                    await message.channel.send(response)

# ==============================
# 🚀 BOT INSTANCE
# ==============================

bot = CustomizableAIBot()

@bot.command(name="ping")
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! {latency}ms")

@bot.command(name="info")
async def info(ctx):
    """Show bot information"""
    embed = discord.Embed(title="🤖 ReplitAI Info", color=0x00ff00)
    embed.add_field(name="Personality", value=bot.personality.tone, inline=True)
    embed.add_field(name="Response Chance", value=f"{bot.get_channel_response_chance(ctx.channel.id)}%", inline=True)
    embed.add_field(name="Uptime", value="Running on Replit! 🚀", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="setresponse")
@commands.has_permissions(administrator=True)
async def set_response(ctx, chance: int):
    """Set response chance for current channel"""
    if not 0 <= chance <= 100:
        await ctx.send("❌ Chance must be between 0-100!")
        return
    
    bot.response_config.channel_response_chances[ctx.channel.id] = chance
    await ctx.send(f"✅ Response chance set to {chance}% in this channel!")
