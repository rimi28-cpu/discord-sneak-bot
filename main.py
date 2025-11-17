from bot import bot
import os

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ Please set DISCORD_TOKEN in your Replit Secrets!")
        exit(1)
    
    bot.run(token)
