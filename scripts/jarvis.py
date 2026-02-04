#!/usr/bin/env python3
"""
Jarvis Mode - Continuous Conversation for KidBot

This is a standalone desktop script that provides true hands-free
continuous conversation. It automatically:
1. Listens for speech
2. Verifies the voice
3. Processes and gets a response
4. Speaks the response
5. Loops back to listening

Run from project root: python -m scripts.jarvis
Or from scripts dir: python jarvis.py
Press Ctrl+C to stop.
"""

import os
import sys
import tempfile
import time
from pathlib import Path

# Add parent directory to path for imports when run directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import load_config
from core.registration import check_owner_registered


def _check_owner_registered_compat(config: dict) -> bool:
    """Compatibility wrapper for check_owner_registered."""
    return check_owner_registered(config)


# Keep legacy function name for backward compatibility
def check_owner_registered_legacy(config: dict) -> bool:
    """Check if owner is registered (legacy)."""
    path = config.get("voice_security", {}).get(
        "owner_embedding_path",
        "data/voice_prints/owner_embedding.npy"
    )
    return Path(path).exists()


class JarvisMode:
    """Continuous conversation handler."""

    def __init__(self, config: dict):
        self.config = config
        self.robot_name = config.get("robot", {}).get("name", "VV")
        self.running = False

        # Initialize components
        print(f"[Jarvis] Initializing {self.robot_name}...", flush=True)

        # Import audio manager (no streamlit dependency)
        from interfaces.audio_io import AudioManager
        self.audio_manager = AudioManager(config)

        # Initialize voice gatekeeper directly
        print("[Jarvis] Loading voice security...", flush=True)
        from resemblyzer import VoiceEncoder
        import numpy as np
        self.voice_encoder = VoiceEncoder()
        owner_path = config.get("voice_security", {}).get(
            "owner_embedding_path", "data/voice_prints/owner_embedding.npy"
        )
        self.owner_embedding = np.load(owner_path)
        self.similarity_threshold = config.get("voice_security", {}).get("threshold", 0.25)

        # Initialize memory manager directly (without streamlit caching)
        print("[Jarvis] Loading memory system...", flush=True)
        import chromadb
        from sentence_transformers import SentenceTransformer
        vector_store_path = config.get("memory", {}).get("vector_store_path", "data/vector_store")
        print("[Jarvis] Loading embedding model...", flush=True)
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[Jarvis] Connecting to ChromaDB...", flush=True)
        self.chroma_client = chromadb.PersistentClient(path=vector_store_path)
        print("[Jarvis] Getting collection...", flush=True)
        self.collection = self.chroma_client.get_or_create_collection(
            name="kidbot_memory",
            metadata={"hnsw:space": "cosine"}
        )
        print("[Jarvis] Memory system ready.", flush=True)

        # Initialize LLM client
        print("[Jarvis] Loading LLM client...", flush=True)
        from dotenv import load_dotenv
        from openai import OpenAI
        load_dotenv()
        api_key = os.getenv("DEEPSEEK_API_KEY")
        api_config = config.get("api", {}).get("deepseek", {})
        self.llm_client = OpenAI(
            api_key=api_key,
            base_url=api_config.get("base_url", "https://api.deepseek.com")
        )
        self.llm_model = api_config.get("model", "deepseek-chat")
        self.personality = config.get("robot", {}).get("personality", "friendly and helpful")

        # Set continuous mode
        self.audio_manager.set_continuous_mode(True)

        print(f"[Jarvis] {self.robot_name} is ready!", flush=True)

    def verify_voice(self, audio_path: str) -> bool:
        """Verify if the voice matches the owner."""
        import numpy as np
        from resemblyzer import preprocess_wav

        try:
            wav = preprocess_wav(audio_path)
            if len(wav) < 1600:  # Too short
                return False
            embedding = self.voice_encoder.embed_utterance(wav)
            similarity = np.dot(embedding, self.owner_embedding)
            print(f"[Jarvis] Voice similarity: {similarity:.3f} (threshold: {self.similarity_threshold})")
            return similarity >= self.similarity_threshold
        except Exception as e:
            print(f"[Jarvis] Voice verification error: {e}")
            return False

    def query_memory(self, query: str, n_results: int = 3) -> list:
        """Query the memory for relevant context."""
        try:
            query_embedding = self.embedding_model.encode(query).tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            if results and results.get("documents"):
                return results["documents"][0]
            return []
        except Exception as e:
            print(f"[Jarvis] Memory query error: {e}")
            return []

    def get_response(self, user_input: str, mode: str = "chat") -> str:
        """Get response from the bot."""
        # Query memory for context
        context_chunks = self.query_memory(user_input)

        # Build system prompt based on mode
        mode_prompts = {
            "chat": f"You are {self.robot_name}, a friendly companion for a young child. Personality: {self.personality}. Speak in simple, short sentences. Be warm and encouraging. Keep responses brief (2-4 sentences).",
            "story": f"You are {self.robot_name} the Storyteller. Create short, imaginative fairy tales for kids. Use vivid but simple language. Keep stories to 3-5 short paragraphs. Never include scary content.",
            "learning": f"You are {self.robot_name} the Teacher. Explain facts simply using real-world examples. After explaining, ask a fun quiz question. Celebrate correct answers!",
            "game": f"You are {self.robot_name} the Game Master. Play word games like 20 Questions, I Spy, Word Chain. Keep turns short and be encouraging."
        }
        system_prompt = mode_prompts.get(mode, mode_prompts["chat"])

        # Add context if available
        user_message = user_input
        if context_chunks:
            context_text = "\n".join(f"[Info]: {c}" for c in context_chunks)
            user_message = f"{user_input}\n\n[Context from memory]:\n{context_text}"

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=256
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[Jarvis] LLM error: {e}")
            return "Hmm, my brain got a little confused. Can you say that again?"

    def run(self, mode: str = "chat"):
        """Run the continuous conversation loop."""
        self.running = True

        # Greeting
        greeting = f"Hi! I'm {self.robot_name}. I'm listening. Say something!"
        print(f"\n[{self.robot_name}] {greeting}")
        self.audio_manager.speak(greeting)

        while self.running:
            try:
                # Phase 1: Listening
                print("\n[Jarvis] Listening...", flush=True)

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name

                try:
                    text, audio_path = self.audio_manager.listen_and_save(tmp_path)

                    if not text:
                        # No speech detected, continue listening
                        continue

                    print(f"[You] {text}")

                    # Phase 2: Verify voice
                    if audio_path and not self.verify_voice(audio_path):
                        print("[Jarvis] Voice not recognized. Waiting for my friend...")
                        self.audio_manager.speak("I don't recognize that voice.")
                        continue

                    # Phase 3: Process and get response
                    print("[Jarvis] Thinking...")
                    response = self.get_response(text, mode)
                    print(f"[{self.robot_name}] {response}")

                    # Phase 4: Speak response
                    self.audio_manager.speak(response)

                finally:
                    # Clean up temp file
                    try:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                    except Exception:
                        pass

            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                print(f"[Jarvis] Error: {e}")
                time.sleep(1)

    def stop(self):
        """Stop the conversation loop."""
        self.running = False
        print(f"\n[Jarvis] {self.robot_name} is going to sleep. Goodbye!")
        self.audio_manager.speak("Goodbye!")
        self.audio_manager.cleanup()


def main():
    """Main entry point."""
    print("=" * 50)
    print("  Jarvis Mode - Continuous Conversation")
    print("=" * 50)
    print("\nPress Ctrl+C to stop.\n")

    # Load config
    config = load_config()

    if not config:
        print("Error: config.yaml not found!")
        sys.exit(1)

    if not check_owner_registered(config):
        print("Error: Owner not registered!")
        print("Please run: python register_owner.py")
        sys.exit(1)

    # Parse command line args for mode
    mode = "chat"
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode not in ["chat", "story", "learning", "game"]:
            print(f"Unknown mode: {mode}")
            print("Available modes: chat, story, learning, game")
            sys.exit(1)

    print(f"Mode: {mode}")

    # Run Jarvis
    jarvis = JarvisMode(config)

    try:
        jarvis.run(mode=mode)
    except KeyboardInterrupt:
        jarvis.stop()


if __name__ == "__main__":
    main()
