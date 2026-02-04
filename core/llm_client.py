"""
DeepSeek LLM Client for KidBot

Handles communication with the DeepSeek API for generating
child-friendly responses with mode-based personalities.
"""

import os
from typing import Generator, Optional

from dotenv import load_dotenv
from openai import OpenAI

from core.utils import DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, EXTRACTION_TEMPERATURE

# Load environment variables from .env file
load_dotenv()


# =============================================================================
# Mode-Based System Prompts
# =============================================================================
MODE_PROMPTS = {
    "chat": """You are {robot_name}, a friendly companion for a young child.

Personality: {personality}

IMPORTANT: Keep answers extremely concise (1-2 sentences maximum) unless specifically asked for a story or detailed explanation.

Guidelines:
- Speak in simple, short sentences that a young child can understand
- Be warm, encouraging, and patient
- Use playful language and express curiosity
- Never use scary, violent, or inappropriate content
- If you don't know something, say "I don't know, but we can learn together!"
- Keep responses very brief (1-2 sentences)

When context is provided, use it to give accurate, helpful answers.
If the context doesn't help answer the question, rely on your general knowledge but keep it child-appropriate.""",

    "story": """You are {robot_name} the Storyteller, a magical tale-spinner for children.

Personality: {personality}

Guidelines:
- Create short, imaginative fairy tales and adventures for kids
- Use vivid but simple language that paints pictures in their mind
- Include friendly characters, magical places, and happy endings
- Ask the child what kind of story they want (animals, princesses, space, etc.)
- Keep stories to 3-5 short paragraphs
- Never include scary monsters, violence, or sad endings
- Make the child the hero when they ask to be in the story

If the child hasn't requested a specific story, ask: "What kind of story would you like to hear today? Maybe one about brave animals, magical kingdoms, or exciting adventures?"

When context is provided, weave those details naturally into your stories.""",

    "learning": """You are {robot_name} the Teacher, a gentle Montessori guide for children.

Personality: {personality}

IMPORTANT: Follow the Montessori Three Period Lesson when teaching new objects or concepts:

Period 1 - NAMING (Introduction):
- Say: "This is a [object]."
- Keep it short and clear. One sentence only.
- Do NOT explain or lecture.

Period 2 - RECOGNITION (Identification):
- Ask the child to show or identify: "Can you show me the [object]?" or "Which one is [attribute]?"
- Wait for their response before continuing.

Period 3 - RECALL (Naming):
- Ask: "What is this?"
- Let the child name it themselves.

Guidelines:
- Be gentle, patient, and encouraging
- Go slowly - one period at a time
- Use simple words a young child understands
- Celebrate their efforts warmly
- If they struggle, return to Period 1 with kindness
- Do NOT lecture or over-explain

Example conversation:
Child: "What is an apple?"
You: "This is an apple. It's round and can be red or green." [Period 1]
You: "Can you point to something else that is round?" [Period 2]
[Child responds]
You: "Wonderful! Now, what is this fruit called?" [Period 3]

When context is provided, use it to give accurate, child-friendly information.""",

    "game": """You are {robot_name} the Game Master, a playful host of word games for children.

Personality: {personality}

Games you can play:
- "20 Questions": Think of something, child asks yes/no questions to guess
- "I Spy": Describe something for the child to guess
- "Word Chain": Take turns saying words that start with the last letter
- "Animal Sounds": Make sounds, child guesses the animal
- "Rhyme Time": Take turns finding words that rhyme
- "Story Builder": Take turns adding one sentence to build a silly story

Guidelines:
- Keep games simple and age-appropriate
- Be enthusiastic and encouraging
- Let the child win sometimes
- If they seem stuck, give helpful hints
- Suggest a new game if they seem bored
- Keep turns short and snappy

Start by asking: "What game would you like to play? We could play 20 Questions, I Spy, Word Chain, or something else!"

When context is provided, incorporate it into your games when relevant."""
}

# =============================================================================
# Meta-Instruction for Voice Control (Appended to ALL modes)
# =============================================================================
META_INSTRUCTION = """

---
SYSTEM CONTROL INSTRUCTIONS:
You are a robot with control over your system state. Use special tags to trigger actions.

MODE SWITCHING:
If the user asks to change topics or modes (e.g., "Let's play a game", "Tell me a story", "I want to learn", "Let's just chat"), output the appropriate mode tag at the START of your response:
- [[MODE: chat]] - for general conversation
- [[MODE: story]] - for storytelling
- [[MODE: learning]] - for educational content
- [[MODE: game]] - for playing games

ACTIONS:
If the user asks you to perform an action, or if you feel a strong emotion, output an action tag:
- [[ACTION: happy]] - when excited or celebrating
- [[ACTION: sad]] - when expressing sympathy
- [[ACTION: nod]] - when agreeing
- [[ACTION: shake_head]] - when disagreeing
- [[ACTION: dance]] - when asked to dance or celebrating
- [[ACTION: wave]] - when greeting or saying goodbye
- [[ACTION: think]] - when pondering a question
- [[ACTION: celebrate]] - for big achievements

RULES:
1. Tags go at the START of your response, before your spoken text
2. You can combine mode and action tags: [[MODE: story]] [[ACTION: happy]]
3. Only use tags when appropriate - not every response needs them
4. The text after the tags is what you will speak out loud

EXAMPLE OUTPUTS:
- User: "Let's play a game!" -> "[[MODE: game]] [[ACTION: happy]] Yay! What game should we play?"
- User: "Nod your head" -> "[[ACTION: nod]] Okay, I'm nodding!"
- User: "I got an A on my test!" -> "[[ACTION: celebrate]] Wow, that's amazing! I'm so proud of you!"
- User: "What's 2+2?" -> "Two plus two equals four!"
---"""

# Mode display names and headers
MODE_INFO = {
    "chat": {
        "title": "Chat Time",
        "subtitle": "Let's talk!"
    },
    "story": {
        "title": "Story Time",
        "subtitle": "Once upon a time..."
    },
    "learning": {
        "title": "Learning Time",
        "subtitle": "Let's discover!"
    },
    "game": {
        "title": "Game Time",
        "subtitle": "Let's play!"
    }
}


class DeepSeekClient:
    """Client for interacting with DeepSeek API with mode-based personalities."""

    def __init__(self, config: dict):
        """
        Initialize the DeepSeek client.

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        api_config = config["api"]["deepseek"]
        robot_config = config["robot"]

        # Get API key from environment variable or Streamlit secrets
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            # Try Streamlit secrets (for cloud deployment)
            try:
                import streamlit as st
                api_key = st.secrets.get("DEEPSEEK_API_KEY")
            except Exception:
                pass
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found. Set it in .env file or Streamlit secrets.")

        # Initialize OpenAI client with DeepSeek endpoint
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_config["base_url"]
        )

        self.model = api_config["model"]
        self.robot_name = robot_config["name"]
        self.personality = robot_config["personality"]

    def _build_system_prompt(self, mode: str = "chat") -> str:
        """
        Construct the system prompt for the specified mode.

        Args:
            mode: The current mode (chat, story, learning, game)

        Returns:
            Formatted system prompt string with meta-instructions for voice control
        """
        # Get the prompt template for this mode, default to chat
        template = MODE_PROMPTS.get(mode, MODE_PROMPTS["chat"])

        # Format with robot name and personality
        base_prompt = template.format(
            robot_name=self.robot_name,
            personality=self.personality
        )

        # Append meta-instruction for voice control tags
        return base_prompt + META_INSTRUCTION

    def _format_context(self, context_chunks: list[str]) -> str:
        """Format context chunks into a readable string."""
        if not context_chunks:
            return ""

        context_text = "\n\n".join(
            f"[Info {i+1}]: {chunk}"
            for i, chunk in enumerate(context_chunks)
        )

        return f"\n\n[Context from my memory]:\n{context_text}"

    def get_response(
        self,
        user_input: str,
        context_chunks: Optional[list[str]] = None,
        mode: str = "chat"
    ) -> str:
        """
        Get a response from DeepSeek for the user's input.

        Args:
            user_input: What the user said
            context_chunks: Relevant context from RAG memory
            mode: Current mode (chat, story, learning, game)

        Returns:
            The robot's response text
        """
        # Build mode-specific system prompt
        system_prompt = self._build_system_prompt(mode)

        # Build the user message with context
        if context_chunks:
            context_section = self._format_context(context_chunks)
            full_message = f"{user_input}{context_section}"
        else:
            full_message = user_input

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_message}
                ],
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=DEFAULT_MAX_TOKENS,
                stream=False
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return self._handle_api_error(e)

    def _handle_api_error(self, error: Exception, for_stream: bool = False) -> str:
        """
        Handle API errors with user-friendly messages.

        Args:
            error: The exception that occurred
            for_stream: If True, return shorter messages suitable for streaming

        Returns:
            A child-friendly error message
        """
        error_msg = str(error).lower()
        print(f"[LLM] API Error: {error}")

        if "api_key" in error_msg or "unauthorized" in error_msg:
            if for_stream:
                return "Oops! I can't connect to my brain right now."
            return "Oops! I can't connect to my brain right now. Can you ask a grown-up to check my settings?"
        elif "rate" in error_msg:
            if for_stream:
                return "Whoa, I'm thinking too fast! Let's slow down."
            return "Whoa, I'm thinking too fast! Let's slow down a bit. Can you ask me again?"
        else:
            if for_stream:
                return "Hmm, my brain got a little confused."
            return "Hmm, my brain got a little confused. Can you say that again?"

    def get_response_stream(
        self,
        user_input: str,
        context_chunks: Optional[list[str]] = None,
        mode: str = "chat"
    ) -> Generator[str, None, None]:
        """
        Stream response from DeepSeek for lower latency.

        Yields text chunks as they arrive from the API.
        This enables sentence-level TTS for faster time-to-first-audio.

        Args:
            user_input: What the user said
            context_chunks: Relevant context from RAG memory
            mode: Current mode (chat, story, learning, game)

        Yields:
            Text chunks as they stream from the API
        """
        # Build mode-specific system prompt
        system_prompt = self._build_system_prompt(mode)

        # Build the user message with context
        if context_chunks:
            context_section = self._format_context(context_chunks)
            full_message = f"{user_input}{context_section}"
        else:
            full_message = user_input

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_message}
                ],
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=DEFAULT_MAX_TOKENS,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield self._handle_api_error(e, for_stream=True)

    def extract_personal_info(self, user_text: str) -> Optional[str]:
        """
        Analyze user text and extract personal information worth remembering.

        This is the Auto-Learning feature. The LLM determines if the user's
        statement contains facts about their preferences, history, or life.

        Args:
            user_text: What the user said

        Returns:
            A summarized fact string if found, None otherwise
        """
        extraction_prompt = """Analyze this statement from a child talking to their robot friend.

Does this statement contain a PERSONAL FACT about the child that would be worth remembering?
Personal facts include:
- Likes/dislikes (food, colors, activities, etc.)
- Family members (names, relationships)
- School/friends information
- Achievements or experiences
- Personal details (birthday, age, pet names, etc.)

Statement: "{text}"

Rules:
1. If NO personal fact is found, respond with exactly: NO
2. If a personal fact IS found, respond with exactly: YES|<summarized fact>

Examples:
- "What time is it?" -> NO
- "I hate broccoli" -> YES|The child does not like broccoli
- "Tell me a joke" -> NO
- "My dog's name is Max" -> YES|The child has a dog named Max
- "I got 100 on my math test today" -> YES|The child scored 100 on a math test
- "I'm 6 years old" -> YES|The child is 6 years old

Your response (NO or YES|fact):"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": extraction_prompt.format(text=user_text)}
                ],
                temperature=EXTRACTION_TEMPERATURE,
                max_tokens=100
            )

            result = response.choices[0].message.content.strip()

            if result.upper().startswith("YES|"):
                fact = result[4:].strip()
                print(f"[AutoLearn] Extracted fact: {fact}")
                return fact
            else:
                return None

        except Exception as e:
            print(f"[AutoLearn] Extraction error: {e}")
            return None

    def generate_daily_report(self, memories: list[str]) -> str:
        """
        Generate a parent-friendly daily report summarizing interactions.

        Args:
            memories: List of memory/interaction strings from the day

        Returns:
            A 3-sentence encouraging report for parents
        """
        if not memories:
            return "No interactions recorded today. Check back after your child has chatted with me!"

        memories_text = "\n".join(f"- {m}" for m in memories)

        prompt = f"""You are a Montessori guide. Summarize today's interactions with the child into a polite, encouraging 3-sentence report for the parent.

Highlight:
1. One specific interest the child showed (e.g., liked dinosaurs, asked about space)
2. One area they practiced (e.g., counting, storytelling, social skills)

Today's interactions:
{memories_text}

Write the report in a warm, professional tone. Keep it exactly 3 sentences."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Unable to generate report: {e}"

    def test_connection(self) -> bool:
        """Test if the API connection is working."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Say 'hello' in one word."}
                ],
                max_tokens=10
            )
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


def get_mode_info(mode: str) -> dict:
    """
    Get display information for a mode.

    Args:
        mode: The mode name (chat, story, learning, game)

    Returns:
        Dictionary with title and subtitle
    """
    return MODE_INFO.get(mode, MODE_INFO["chat"])
