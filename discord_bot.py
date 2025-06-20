import os
import discord
from dotenv import load_dotenv

# --- Import our existing AI logic ---
# We will call the functions from your original assistant.py script
from assistant import create_and_load_database, query_assistant

# --- Configuration ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("Discord token not found. Please set it in the .env file.")

# Set up required "intents" for the bot to read messages
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# This will hold our AI's "brain" (the database connection)
db_collection = None

@client.event
async def on_ready():
    """This function runs once when the bot successfully connects to Discord."""
    global db_collection
    print(f'Logged in as {client.user}')
    print('---')
    
    # Load the AI database into memory when the bot starts
    print("Loading AI knowledge base...")
    db_collection = create_and_load_database()
    print("AI is fully loaded and ready for questions.")
    print('---')


@client.event
async def on_message(message):
    """This function runs every time a message is sent in any channel the bot can see."""
    # Ignore messages sent by the bot itself to prevent loops
    if message.author == client.user:
        return

    # Check if the bot was mentioned (e.g., "@AutomationFlow AI Assistant how do I...")
    if client.user.mentioned_in(message):
        
        # Show a "typing..." indicator for a better user experience
        async with message.channel.typing():
            # Get the user's question, removing the bot mention part
            question = message.content.replace(f'<@{client.user.id}>', '').strip()
            
            print(f"Received question from {message.author}: '{question}'")
            
            # Get the answer from our AI assistant function
            # Make sure the database is loaded before querying
            if db_collection:
                answer = query_assistant(question, db_collection)
            else:
                answer = "Sorry, my knowledge base is not loaded yet. Please try again in a moment."

            # Send the AI's answer back to the channel
            await message.channel.send(answer)

# --- Start the bot ---
client.run(DISCORD_TOKEN)