# Skills Collection

Claude Code skills for building AI-powered workflows.

## Skills

| # | Skill | Description | Version | Status |
|---|-------|-------------|---------|--------|
| 1 | [ai-agent-builder](./ai-agent-builder/) | Build, update, and refine AI agents/assistants with structured artifact generation | 1.0.0 | Released |
| 2 | [youtube-transcript-ytdlp](./youtube-transcript-ytdlp/) | Fetch YouTube transcripts locally via yt-dlp — free, offline, no API credits | 1.0.0 | Released |

## Installation

Each skill can be installed at user level (`~/.claude/skills/`) to be available across all projects:

```bash
# Copy a skill to your user skills directory
cp -r ai-agent-builder ~/.claude/skills/
```

Or clone the whole repo and symlink:

```bash
git clone https://github.com/Serg1kk/skills.git ~/skills
ln -s ~/skills/ai-agent-builder ~/.claude/skills/ai-agent-builder
```

## Structure

Each skill follows the standard Claude Code skill anatomy:

```
skill-name/
├── SKILL.md              # Main skill file (instructions + workflow)
├── README.md             # Skill documentation (what it does, how to use)
└── references/           # Bundled resources
    ├── scripts/          # Executable code (if needed)
    ├── references/       # Documentation loaded into context
    └── assets/           # Files used in output (templates, etc.)
```

## License

MIT
