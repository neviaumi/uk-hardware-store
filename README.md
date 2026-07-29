# UK Hardware Store MCP Server

Real-time product search and comparison across major UK hardware retailers via the Model Context Protocol (MCP).

## Value Proposition

Searching for DIY supplies across multiple retailers is notoriously fragmented. This project provides a unified, AI-ready interface to discover, compare, and retrieve product data from the UK's leading hardware stores. By leveraging the **Model Context Protocol (MCP)**, it enables AI assistants like Claude to act as a knowledgeable DIY consultant, capable of finding the right parts at the best prices in seconds.

## Product Definition

The **UK Hardware Store MCP Server** is a high-performance scraping and integration layer. It exposes a suite of tools that allow for:
- **Keyword Search**: Find products across DIY.com, Screwfix, Homebase, Toolstation, and Wickes simultaneously.
- **Deep Detail Retrieval**: Fetch technical specifications, stock status, and current pricing.
- **Unified Schema**: Standardizes disparate retailer data into a consistent format for easy processing.

## Features

- **Multi-Retailer Support**: Built-in crawlers for:
  - **DIY.com (B&Q)**
  - **Screwfix**
  - **Homebase**
  - **Toolstation**
  - **Wickes**
- **Robust Scraping Infrastructure**:
  - TLS Fingerprinting via `curl-cffi` to bypass common bot detection.
  - Dynamic header generation using `browserforge`.
  - Fast, reliable parsing with `parsel`.
- **MCP Native**: Plugs directly into any MCP-compliant client (e.g., Claude Desktop, Zed).

## Project Structure

```text
├── app/                    # Main application source code
│   ├── crawlers/           # Specialized retailer crawlers
│   │   ├── http_client.py  # Centralized robust HTTP client
│   │   ├── utils.py        # Shared parsing and helper utilities
│   │   └── [retailer]_crawler/
│   ├── config.py           # Application configuration
│   ├── mcp_server.py       # MCP Tool definitions and routing
│   └── stdio.py            # MCP stdio interface entry point
├── tests/                  # Robust test suite with mock servers
├── scripts/                # Life-cycle management scripts
│   ├── start.sh            # Development and production server start
│   ├── setup.sh            # Environment initialization
│   ├── lint.sh             # Linting, formatting, and type checks
│   └── test.sh             # Pytest test suite runner
├── pyproject.toml          # Modern dependency management via uv
├── mcp.json                # MCP configuration template
└── GEMINI.md               # Spec Driven Development workflow documentation
```

## Getting Started

### Prerequisites

- **Python 3.12.0** or higher.
- **[uv](https://docs.astral.sh/uv/)**: Fast Python package manager (required).

### Installation

1. **Clone the repository**:
   ```bash
   git clone git@github.com:neviaumi/uk-hardware-store-mcp.git
   cd uk-hardware-store-mcp
   ```

2. **Setup the environment**:
   ```bash
   uv sync
   ```

### Configuration

To use this with an MCP client (like Claude Desktop), add the server to your `mcp_config.json`:

```json
{
  "mcpServers": {
    "uk-hardware-store": {
      "command": "bash",
      "args": ["-c", "cd /path/to/uk-hardware-store-mcp && ./scripts/start.sh --prod"]
    }
  }
}
```

### Usage

#### Development Server
Start the server in development mode (port 8080):
```bash
bash ./scripts/start.sh --dev
```

#### Production Mode
Launch for MCP client integration:
```bash
bash ./scripts/start.sh --prod
```

## Testing and Quality

The project adheres to **Spec Driven Development (SDD)**. For more details, see [GEMINI.md](GEMINI.md).

Run linting and formatting:
```bash
bash ./scripts/lint.sh
```

Run the behavioral test suite:
```bash
bash ./scripts/test.sh
```

## License

This project is released into the public domain under the [Unlicense](LICENSE).
