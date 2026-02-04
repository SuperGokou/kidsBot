#!/usr/bin/env python3
"""
KidBot - Child Companion Robot

Main entry point that orchestrates all components:
- Memory (RAG) for knowledge retrieval
- LLM (DeepSeek) for response generation
- Audio I/O for voice interaction
"""

import sys
from pathlib import Path

from core.memory_rag import MemoryManager
from core.llm_client import DeepSeekClient
from core.voice_security import VoiceGatekeeper
from core.registration import check_owner_registered, register_owner_from_audio, get_owner_embedding_path
from core.utils import load_config, safe_remove_file, format_banner, format_divider, EXIT_PHRASES
from interfaces.audio_io import AudioManager


def print_banner(robot_name: str):
    """Print startup banner."""
    print(format_banner(f"{robot_name} - Child Companion Robot"))
    print("  Commands:")
    print("    - Speak naturally to interact")
    print("    - Press Ctrl+C to exit")
    print(format_divider() + "\n")


def run_registration_mode(config: dict, audio_manager, encoder) -> bool:
    """
    Run the owner registration flow.

    Args:
        config: Configuration dictionary
        audio_manager: AudioManager instance for voice I/O
        encoder: Resemblyzer VoiceEncoder for voice embedding

    Returns:
        True if registration succeeded, False otherwise
    """
    robot_name = config["robot"]["name"]
    embedding_path = get_owner_embedding_path(config)
    temp_audio_path = "temp_registration.wav"

    # Announce registration mode
    registration_prompt = (
        "Hello! I don't have an owner yet. "
        "Please say something so I can remember your voice. "
        "Speak clearly for about 5 seconds."
    )
    print(f"\n{robot_name}: {registration_prompt}")
    audio_manager.speak(registration_prompt)

    # Listen for owner's voice (longer duration for better embedding)
    print("\nListening for registration...")
    user_text, audio_path = audio_manager.listen_and_save(temp_audio_path)

    if not audio_path or not Path(audio_path).exists():
        error_msg = "I couldn't hear you clearly. Please try again."
        print(f"\n{robot_name}: {error_msg}")
        audio_manager.speak(error_msg)
        return False

    # Register the voice
    print("Registering voice...")
    success = register_owner_from_audio(encoder, audio_path, embedding_path)

    # Clean up temp file
    safe_remove_file(audio_path)

    if success:
        success_msg = "Nice to meet you! I've remembered your voice. I'll only listen to you from now on!"
        print(f"\n{robot_name}: {success_msg}")
        audio_manager.speak(success_msg)
        return True
    else:
        fail_msg = "Sorry, I couldn't save your voice. Please try again."
        print(f"\n{robot_name}: {fail_msg}")
        audio_manager.speak(fail_msg)
        return False


def main():
    """Main application loop."""

    # Load configuration
    print("Loading configuration...")
    config = load_config()

    if not config:
        print("Error: Configuration file not found: config.yaml")
        print("Please create config.yaml with your settings.")
        sys.exit(1)

    robot_name = config.get("robot", {}).get("name", "Bobo")
    print_banner(robot_name)

    # Initialize components
    print("Initializing components...")

    # Memory Manager (RAG)
    print("  [1/4] Memory Manager...")
    memory_manager = MemoryManager(config)

    # LLM Client
    print("  [2/4] LLM Client...")
    llm_client = DeepSeekClient(config)

    # Audio Manager
    print("  [3/4] Audio Manager...")
    audio_manager = AudioManager(config)

    # Voice Security
    voice_security_enabled = config.get("voice_security", {}).get("enabled", False)
    gatekeeper = None
    classifier = None

    if voice_security_enabled:
        print("  [4/4] Voice Security...")

        # Check if owner is registered
        owner_registered = check_owner_registered(config)

        if not owner_registered:
            # Load Resemblyzer encoder for registration (same as voice_security.py)
            from resemblyzer import VoiceEncoder

            print("  Loading voice encoder for registration...")
            classifier = VoiceEncoder()

            # Run registration mode
            print(format_banner("REGISTRATION MODE"))

            registration_success = run_registration_mode(config, audio_manager, classifier)

            if not registration_success:
                print("\nRegistration failed. Please restart and try again.")
                audio_manager.cleanup()
                sys.exit(1)

            # Reload gatekeeper with new owner embedding
            print("\nReloading voice security with new owner...")

        # Initialize gatekeeper (will load the owner embedding)
        gatekeeper = VoiceGatekeeper(config)

        if not gatekeeper.is_ready():
            print("\n  WARNING: Voice security enabled but not configured.")
            print("  This should not happen after registration.")
    else:
        print("  [4/4] Voice Security... (disabled)")

    # Temp audio path for voice verification
    temp_audio_path = "temp_input.wav"

    # Startup check - ensure knowledge base is up to date
    print("\nChecking knowledge base...")
    memory_manager.ingest_data()

    # Print knowledge base stats
    stats = memory_manager.get_stats()
    print(f"Knowledge base ready: {stats['total_documents']} documents")

    # Startup greeting
    greeting = f"Hello! I'm {robot_name}! I'm so happy to see you! What would you like to talk about?"
    print(f"\n{robot_name}: {greeting}")
    audio_manager.speak(greeting)

    # Main interaction loop
    print("\n" + format_divider())

    try:
        while True:
            # Listen for user input (with audio saving for verification)
            print("\nListening...")
            if gatekeeper:
                user_text, audio_path = audio_manager.listen_and_save(temp_audio_path)
            else:
                user_text = audio_manager.listen()
                audio_path = None

            # Skip if nothing recognized
            if not user_text:
                continue

            print(f"You said: {user_text}")

            # Verify speaker if voice security is enabled
            if gatekeeper and audio_path:
                is_owner = gatekeeper.verify_user(audio_path)
                if not is_owner:
                    rejection = "Sorry, I can only chat with my owner."
                    print(f"\n{robot_name}: {rejection}")
                    audio_manager.speak(rejection)
                    safe_remove_file(audio_path)
                    continue

            # Check for exit commands
            if any(phrase in user_text.lower() for phrase in EXIT_PHRASES):
                farewell = "Bye bye! It was so fun talking to you! See you next time!"
                print(f"\n{robot_name}: {farewell}")
                audio_manager.speak(farewell)
                break

            # Retrieve relevant context from memory
            print("Thinking...")
            context_chunks = memory_manager.query_memory(user_text, n_results=3)

            if context_chunks:
                print(f"  (Found {len(context_chunks)} relevant memories)")

            # Generate response
            response = llm_client.get_response(user_text, context_chunks)

            # Output response
            print(f"\n{robot_name}: {response}")
            audio_manager.speak(response)

            # Clean up temp audio
            if audio_path:
                safe_remove_file(audio_path)

    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        print("\n\nShutting down...")
        farewell = "Goodbye friend! See you soon!"
        print(f"{robot_name}: {farewell}")

        try:
            audio_manager.speak(farewell)
        except Exception:
            pass

    finally:
        # Cleanup
        audio_manager.cleanup()
        print("Goodbye!")


if __name__ == "__main__":
    main()
