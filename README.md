# Montessori Intelligence Nexus (MIN)

**Building AI for Montessori Education**

MIN is the AI operating system for Montessori education. We turn AMS-standard Montessori methods into a replicable AI teaching engine, delivered through software-led, hardware-supported, classroom-proven systems -- so every school can consistently deliver high-quality Montessori education.

## Author
Ming Xia

## Vision

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Montessori Intelligence Nexus                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│   │   Phase 1   │───▶│   Phase 2   │───▶│   Phase 3   │            │
│   │  SOFTWARE   │    │  HARDWARE   │    │  ROBOTICS   │            │
│   │             │    │             │    │             │            │
│   │ • AI Engine │    │ • Screen    │    │ • Robot Arms│            │
│   │ • RAG KB    │    │ • Mic/Cam   │    │ • Generative│            │
│   │ • Voice I/O │    │ • Speaker   │    │   Demos     │            │
│   └─────────────┘    └─────────────┘    └─────────────┘            │
│         │                  │                  │                     │
│         ▼                  ▼                  ▼                     │
│   ┌─────────────────────────────────────────────────────┐          │
│   │              AMS-Certified Montessori               │          │
│   │                  Knowledge Base                     │          │
│   │         (Exclusive FMAE Training Data)              │          │
│   └─────────────────────────────────────────────────────┘          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## The Problem We Solve

| Challenge | Impact | MIN Solution |
|-----------|--------|--------------|
| Great teachers are hard to replicate | Inconsistent quality | AI teaching engine with certified methods |
| Quality varies classroom to classroom | Parent frustration | Standardized, replicable curriculum delivery |
| High costs due to labor | Limited accessibility | Scalable software reduces per-student cost |
| Parents disconnected from daily learning | Broken learning loop | Real-time engagement and progress tracking |

## Architecture

```
                         ┌──────────────────┐
                         │   MIN Platform   │
                         │   (main.py)      │
                         └────────┬─────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  core/          │    │  core/          │    │  interfaces/    │
│  memory_rag.py  │    │  llm_client.py  │    │  audio_io.py    │
│                 │    │                 │    │                 │
│  Montessori     │    │  DeepSeek API   │    │  Voice I/O      │
│  Knowledge Base │    │  Child-safe AI  │    │  edge-tts       │
└────────┬────────┘    └─────────────────┘    └────────┬────────┘
         │                                             │
         ▼                                             ▼
┌─────────────────┐                         ┌─────────────────┐
│    ChromaDB     │                         │  Raspberry Pi   │
│  Vector Store   │                         │  (Future HW)    │
│  384-dim embed  │                         │  Screen/Mic/Cam │
└─────────────────┘                         └─────────────────┘
```

## Features

### AI Teaching Engine (VV)
- **Montessori-aligned responses** using RAG with certified curriculum
- **Child-appropriate personality** -- friendly, curious, encouraging
- **Context-aware teaching** -- retrieves relevant knowledge for each question
- **AMS-standard methods** encoded into replicable AI behavior

### Knowledge Base (RAG)
- **500MB+ Montessori content** ingestion supported
- **Memory-efficient processing** using generators (no RAM overflow)
- **Semantic search** with sentence-transformers embeddings
- **Duplicate detection** via file hashing (skip unchanged files)

### Voice Interaction
- **Real-time speech recognition** with silence detection
- **Natural TTS** using Microsoft Edge Neural voices
- **Child-friendly voice** (Ana Neural - US English)
- **Cross-platform** -- works on PC, Mac, Raspberry Pi

### Classroom Ready
- **Raspberry Pi 5 deployment** for hardware integration
- **Offline-capable** vector database (ChromaDB)
- **Low-latency responses** for natural conversation
- **Scalable architecture** for multi-classroom deployment

## Project Structure

```
MIN/
├── main.py                 # Application entry point
├── config.yaml             # Robot settings and paths
├── config.yaml.example     # Template (safe to commit)
├── requirements.txt        # Python dependencies
├── ingest_data.py          # Standalone data ingestion
├── .env                    # API keys (gitignored)
├── .env.example            # Template (safe to commit)
│
├── core/
│   ├── __init__.py
│   ├── memory_rag.py       # MemoryManager (ChromaDB + embeddings)
│   └── llm_client.py       # DeepSeekClient (LLM API)
│
├── interfaces/
│   ├── __init__.py
│   └── audio_io.py         # AudioManager (STT + TTS)
│
└── data/
    ├── raw_docs/           # Montessori curriculum files (.txt, .md)
    └── vector_store/       # ChromaDB persistent storage
```

## Tech Stack

| Category | Technology | Purpose |
|----------|------------|---------|
| LLM | DeepSeek V3 API | Child-safe response generation |
| Vector DB | ChromaDB | Persistent semantic search |
| Embeddings | all-MiniLM-L6-v2 | Lightweight (22MB), Pi-compatible |
| TTS | edge-tts | Microsoft Edge neural voices |
| STT | SpeechRecognition | Google Speech Recognition |
| Audio | pygame | Cross-platform MP3 playback |
| Config | PyYAML + dotenv | Secure settings management |

## Getting Started

### Prerequisites

- Python 3.10+
- Microphone and speakers
- DeepSeek API key ([get one here](https://platform.deepseek.com/))

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/MIN.git
   cd MIN
   ```

2. Create conda environment
   ```bash
   conda create -n min python=3.10
   conda activate min
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Configure API key
   ```bash
   cp .env.example .env
   # Edit .env with your DeepSeek API key
   ```

5. Configure robot settings
   ```bash
   cp config.yaml.example config.yaml
   # Customize name, personality, voice
   ```

6. Add Montessori curriculum
   ```bash
   # Copy your certified Montessori content to data/raw_docs/
   cp /path/to/montessori/materials/*.txt data/raw_docs/
   ```

7. Run MIN
   ```bash
   python main.py
   ```

## Configuration

### config.yaml

| Section | Key | Description |
|---------|-----|-------------|
| `api.deepseek` | `base_url`, `model` | LLM endpoint |
| `paths` | `raw_docs`, `vector_store` | Data directories |
| `robot` | `name`, `personality` | AI companion identity |
| `rag` | `chunk_size`, `chunk_overlap` | Text splitting params |
| `audio` | `tts_voice`, `listen_timeout` | Voice settings |

### Robot Personality (Default: VV)

```yaml
robot:
  name: "VV"
  personality: "A 6-year-old curious and friendly robot who loves
    to learn and play. Speaks in simple, cheerful sentences that
    children can understand. Always positive and encouraging."
```

## Business Model

| Metric | Value |
|--------|-------|
| Subscription | $3,500 / school / month |
| Revenue Share | 15% of incremental tuition |
| CAC | $24,500 per school |
| LTV | $286,000 per school |
| Payback Period | 14 months |
| Gross Margin | 75%+ (SaaS), ~30% (hardware) |

## Go-to-Market Strategy

```
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│  Phase 1: 0→1  │───▶│  Phase 2: 1→10 │───▶│ Phase 3: 10→100│
│                │    │                │    │                │
│  Internal      │    │  AMS Partner   │    │  National      │
│  Pilots        │    │  Industry Std  │    │  Scale         │
│                │    │                │    │                │
│  • Prove ROI   │    │  • Adoption    │    │  • Tech-in-Box │
│  • Efficiency  │    │  • Not sales   │    │  • Upgrades    │
│  • Parent val  │    │  • Certified   │    │  • Family prod │
└────────────────┘    └────────────────┘    └────────────────┘
```

## Technology Roadmap

### Phase 1: Software MVP (Current)
- [x] Voice input/output with edge-tts
- [x] RAG-based knowledge retrieval
- [x] DeepSeek LLM integration
- [x] Cross-platform support
- [x] Montessori personality encoding

### Phase 2: Hardware Integration
- [ ] Raspberry Pi 5 deployment
- [ ] Screen display for visual aids
- [ ] Camera for child engagement detection
- [ ] LED status indicators
- [ ] Physical button controls

### Phase 3: Advanced Robotics
- [ ] Robotic arms for demonstrations
- [ ] Generative material manipulation
- [ ] Multi-modal teaching (visual + audio + physical)
- [ ] Classroom-scale deployment

## Our Moat

Built on **FMAE** with four operating Montessori kindergartens:

| Advantage | Description |
|-----------|-------------|
| Official Certification | Direct access to AMS Montessori certification |
| Real Classrooms | Experiment and validate in actual environments |
| Exclusive Data | High-quality Montessori materials for AI training |
| Domain Expertise | Founding team includes experienced Montessori principals |

## Seed Round Fundraising

| Item | Value |
|------|-------|
| **Target** | $8.5M |
| **Pre-money Valuation** | $45M |
| R&D | 35% |
| Compliance & Certification | 25% |
| Pilot Deployment & Data | 20% |
| Talent | 15% |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `DEEPSEEK_API_KEY not found` | Check `.env` file contains your API key |
| `Speech synthesis error: Permission denied` | Restart the application |
| `No microphone found` | Check system audio permissions |
| `No module named 'xxx'` | Run `pip install -r requirements.txt` |

## Dependencies

```
openai>=1.12.0
chromadb>=0.4.22
sentence-transformers>=2.3.0
edge-tts>=6.1.9
pygame>=2.5.0
SpeechRecognition>=3.10.0
pyaudio>=0.2.14
pyyaml>=6.0
python-dotenv>=1.0.0
tqdm>=4.66.0
```

## Team

Our core founding team comes from **Stanford**, **UPenn**, **Harvard**, and includes an **experienced Montessori school principal** with 4 operating Montessori schools.

## License

Proprietary - Montessori Intelligence Nexus

## Contact

For partnership inquiries, pilot programs, or investment opportunities, please contact the MIN team.

---

*MIN is building the AI operating system for Montessori education.*
