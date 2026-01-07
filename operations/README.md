# Operations

This directory contains operational scripts for the Context Engineering MCP platform.

## Miyabi - Autonomous Development

[Miyabi](https://github.com/ShunsukeHayashi/Miyabi) provides autonomous development capabilities.

### Quick Start

```bash
# Check system health
npm run miyabi:doctor

# Start autonomous development
npm run miyabi:run

# Check status
npm run miyabi:status
```

### Using the Operations Script

```bash
# Run autonomous development
./operations/miyabi-ops.sh run

# Check status
./operations/miyabi-ops.sh status

# Health check
./operations/miyabi-ops.sh doctor
```

### Prerequisites

- Node.js 18+
- GitHub authentication (run `gh auth login` or set `GITHUB_TOKEN`)

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub personal access token | Yes (or use `gh auth login`) |
| `GEMINI_API_KEY` | Gemini API key for AI features | Yes |

### Troubleshooting

Run `npm run miyabi:doctor` to diagnose issues:

- **GITHUB_TOKEN not set**: Run `gh auth login` or export `GITHUB_TOKEN`
- **Network issues**: Check your internet connection
- **Node version**: Ensure Node.js 18+ is installed
