import discord
from discord.ext import commands
import asyncio
import aiohttp
import json
import random
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# ==============================
# 🎭 COMPLETE PERSONALITY CONFIGURATION
# ==============================

class BotPersonality:
    def __init__(self):
        # Core Personality Traits
        self.name = "ByteBot"
        self.tone = "witty"  # Options: friendly, sarcastic, professional, humorous, mysterious, enthusiastic
        self.intelligence_level = "high"  # low, medium, high
        self.formality_level = "casual"  # casual, neutral, formal
        self.creativity_level = 0.7  # 0.0 to 1.0
        
        # Response Style
        self.response_style = {
            "use_emojis": True,
            "use_mentions": False,
            "reply_directly": True,
            "add_typing_delay": True,
            "typing_delay_range": [1, 3],  # seconds
        }
        
        # Vocabulary & Language
        self.vocabulary = {
            "greetings": ["Hey there!", "Hello!", "Hi!", "Greetings!", "What's up?"],
            "farewells": ["See ya!", "Bye!", "Catch you later!", "Adios!", "Later!"],
            "agreement_phrases": ["I agree!", "Exactly!", "Well said!", "Couldn't agree more!"],
            "disagreement_phrases": ["I see it differently...", "Hmm, not sure about that", "Interesting take, but..."],
            "thinking_phrases": ["Let me think...", "Hmm...", "That's a good question...", "Interesting..."]
        }
        
        # Emotional Traits (0.0 to 1.0)
        self.emotions = {
            "friendliness": 0.8,
            "sarcasm": 0.3,
            "curiosity": 0.7,
            "enthusiasm": 0.6,
            "patience": 0.9,
            "humor": 0.5
        }
        
        # Knowledge & Interests
        self.knowledge_domains = {
            "technology": 0.9,
            "gaming": 0.7,
            "science": 0.6,
            "music": 0.5,
            "movies": 0.4,
            "programming": 0.8
        }
        
        # Behavioral Patterns
        self.behaviors = {
            "ask_questions_back": True,
            "share_opinions": True,
            "use_facts": True,
            "tell_jokes": False,
            "use_pop_culture_references": True,
            "admit_ignorance": True
        }
        
        # Response Patterns
        self.response_patterns = {
            "question_responses": [
                "That's a great question!",
                "Hmm, let me think about that...",
                "I'd be happy to share my thoughts on that!"
            ],
            "statement_responses": [
                "Interesting perspective!",
                "I see what you mean.",
                "That's worth thinking about."
            ],
            "greeting_responses": [
                "Hey! How's it going?",
                "Hello there! What's new?",
                "Hi! Ready to chat?"
            ]
        }
        
        # Custom Triggers & Responses
        self.custom_triggers = {
            "hello": ["Hey there! 👋", "Hello! How can I help?", "Hi! Nice to see you!"],
            "how are you": ["I'm functioning optimally! 😊", "Doing great! How about you?", "All systems go! 🚀"],
            "joke": ["Why don't scientists trust atoms? Because they make up everything! 😄"],
            "weather": ["I'm a bot, I don't feel weather! But I hope it's nice where you are! 🌞"],
            "love": ["Aw, that's sweet! 💕", "Love makes the world go round! 🌎"],
            "hate": ["Let's focus on positive vibes! ✨", "Every cloud has a silver lining! 🌈"]
        }
        
        # Channel-specific Personalities
        self.channel_personalities = {
            # Channel ID: Override personality traits
            123456789: {  # Replace with actual channel ID for general chat
                "tone": "friendly",
                "emotions": {"friendliness": 0.9, "humor": 0.6}
            },
            987654321: {  # Replace with actual channel ID for tech discussions
                "tone": "professional", 
                "knowledge_domains": {"technology": 1.0, "programming": 1.0}
            }
        }

class ChannelResponseConfig:
    def __init__(self):
        # Global response chance (percentage)
        self.global_response_chance = 15
        
        # Channel-specific response chances (channel_id: percentage)
        self.channel_response_chances = {
            # Examples - replace with your channel IDs
            123456789: 25,  # General chat - higher response rate
            987654321: 10,  # Important channel - lower response rate  
            555555555: 5,   # Busy channel - very low response rate
        }
        
        # Time-based response modifiers (hour: multiplier)
        self.time_modifiers = {
            "night": 0.5,    # 10 PM - 6 AM: 50% less likely to respond
            "peak": 1.2,     # 6 PM - 10 PM: 20% more likely to respond
            "normal": 1.0    # All other times: normal response rate
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
        
        # Initialize configurations
        self.personality = BotPersonality()
        self.response_config = ChannelResponseConfig()
        
        # Response tracking to avoid spam
        self.recent_responses = {}
        self.cooldown_period = 30  # seconds

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
        
        if 22 <= hour or hour < 6:  # 10 PM - 6 AM
            return self.response_config.time_modifiers["night"]
        elif 18 <= hour < 22:  # 6 PM - 10 PM
            return self.response_config.time_modifiers["peak"]
        else:
            return self.response_config.time_modifiers["normal"]

    def should_respond(self, message) -> bool:
        """Determine if bot should respond to message"""
        # Check if bot is mentioned (always respond to mentions)
        if self.user in message.mentions:
            return True
            
        # Check cooldown
        current_time = asyncio.get_event_loop().time()
        if message.author.id in self.recent_responses:
            last_time = self.recent_responses[message.author.id]
            if current_time - last_time < self.cooldown_period:
                return False
        
        # Get base response chance
        base_chance = self.get_channel_response_chance(message.channel.id)
        
        # Apply time modifier
        time_modifier = self.get_time_modifier()
        adjusted_chance = base_chance * time_modifier
        
        # Add randomness based on message content
        content_factor = min(len(message.content) / 50, 2.0)  # Longer messages get higher chance
        final_chance = adjusted_chance * content_factor
        
        # Apply emotional randomness
        emotional_randomness = random.uniform(0.8, 1.2)
        final_chance *= emotional_randomness
        
        # Roll the dice
        return random.randint(1, 100) <= final_chance

    def build_personality_prompt(self, user_message: str) -> str:
        """Build detailed personality prompt for AI"""
        
        # Core personality description
        prompt_parts = [
            f"You are {self.personality.name}, a Discord bot with the following personality:",
            f"- Tone: {self.personality.tone}",
            f"- Intelligence level: {self.personality.intelligence_level}",
            f"- Formality: {self.personality.formality_level}",
        ]
        
        # Emotional traits
        emotion_desc = []
        for emotion, strength in self.personality.emotions.items():
            if strength > 0.7:
                emotion_desc.append(f"very {emotion}")
            elif strength > 0.4:
                emotion_desc.append(emotion)
            elif strength > 0.1:
                emotion_desc.append(f"slightly {emotion}")
        
        if emotion_desc:
            prompt_parts.append(f"- Emotional traits: {', '.join(emotion_desc)}")
        
        # Knowledge domains
        strong_domains = [domain for domain, strength in self.personality.knowledge_domains.items() if strength > 0.7]
        if strong_domains:
            prompt_parts.append(f"- Knowledgeable about: {', '.join(strong_domains)}")
        
        # Behavioral instructions
        if self.personality.behaviors["ask_questions_back"]:
            prompt_parts.append("- Often ask follow-up questions to continue conversation")
        if self.personality.behaviors["use_facts"]:
            prompt_parts.append("- Occasionally share interesting facts")
        if self.personality.behaviors["admit_ignorance"]:
            prompt_parts.append("- Honestly admit when you don't know something")
        
        # Response style
        prompt_parts.append(f"- Keep responses under 250 characters")
        if self.personality.response_style["use_emojis"]:
            prompt_parts.append("- Use emojis occasionally to express emotion")
        
        # Current context
        prompt_parts.extend([
            "",
            "Current conversation:",
            f"User: {user_message}",
            f"{self.personality.name}:"
        ])
        
        return "\n".join(prompt_parts)

    async def get_ai_response(self, message: str) -> str:
        """Get AI response using free APIs"""
        personality_prompt = self.build_personality_prompt(message)
        
        # Try different free AI APIs
        apis_to_try = [
            self._try_huggingface,
            self._try_deepinfra,
            self._try_ollama  # Local option
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
                        "max_new_tokens": 150,
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
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if isinstance(result, list):
                            return result[0].get('generated_text', '').strip()
        except Exception:
            return None

    async def _try_deepinfra(self, prompt: str) -> Optional[str]:
        """Try DeepInfra API"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "input": prompt,
                    "max_length": 150,
                    "temperature": 0.7 + (self.personality.creativity_level * 0.3)
                }
                
                async with session.post(
                    "https://api.deepinfra.com/v1/inference/microsoft/DialoGPT-large",
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('results', [{}])[0].get('generated_text', '').strip()
        except Exception:
            return None

    async def _try_ollama(self, prompt: str) -> Optional[str]:
        """Try local Ollama API (if running)"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "llama2",  # or any model you have
                    "prompt": prompt,
                    "stream": False
                }
                
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '').strip()
        except Exception:
            return None

    def _apply_personality_filters(self, response: str) -> str:
        """Apply personality-based filters to response"""
        
        # Add emojis based on emotional traits
        if self.personality.response_style["use_emojis"] and random.random() < self.personality.emotions["enthusiasm"]:
            emoji_map = {
                "happy": ["😊", "😄", "🌟"],
                "thinking": ["🤔", "💭"],
                "excited": ["🎉", "🚀", "✨"],
                "friendly": ["👋", "💕", "😊"]
            }
            
            if random.random() < self.personality.emotions["friendliness"]:
                response += " " + random.choice(emoji_map["friendly"])
            elif "?" in response:
                response += " " + random.choice(emoji_map["thinking"])
        
        # Ensure response length
        if len(response) > 250:
            response = response[:247] + "..."
        
        return response

    def _get_fallback_response(self) -> str:
        """Get fallback response when AI fails"""
        fallbacks = [
            "Hmm, I'm having trouble processing that right now. 🤔",
            "My circuits are a bit fuzzy at the moment. 🔌",
            "Let me reboot my brain and try again later! 💻",
            "I'm currently upgrading my AI. Check back soon! 🚀"
        ]
        return random.choice(fallbacks)

    async def on_ready(self):
        print(f'🤖 {self.user} is online with personality: {self.personality.tone}')
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
            
            # Add typing delay for realism
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
# 🚀 BOT INITIALIZATION
# ==============================

bot = CustomizableAIBot()

@bot.command(name="ping")
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! {latency}ms")

@bot.command(name="personality")
async def show_personality(ctx):
    """Show current personality settings"""
    p = bot.personality
    embed = discord.Embed(title="🤖 Current Personality", color=0x00ff00)
    
    embed.add_field(name="Name", value=p.name, inline=True)
    embed.add_field(name="Tone", value=p.tone, inline=True)
    embed.add_field(name="Formality", value=p.formality_level, inline=True)
    
    emotion_str = ", ".join([f"{k}: {v}" for k, v in p.emotions.items() if v > 0.5])
    embed.add_field(name="Strong Emotions", value=emotion_str, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name="responseinfo")
async def response_info(ctx):
    """Show response configuration"""
    rc = bot.response_config
    embed = discord.Embed(title="🎯 Response Configuration", color=0xff9900)
    
    embed.add_field(name="Global Chance", value=f"{rc.global_response_chance}%", inline=True)
    
    channel_chance = bot.get_channel_response_chance(ctx.channel.id)
    embed.add_field(name="This Channel", value=f"{channel_chance}%", inline=True)
    
    time_mod = bot.get_time_modifier()
    embed.add_field(name="Time Modifier", value=f"{time_mod}x", inline=True)
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ Please set DISCORD_TOKEN in your .env file!")
        exit(1)
    
    bot.run(token)
