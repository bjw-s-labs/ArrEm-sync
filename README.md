# ArrEm-sync

A Python application that synchronizes tags from Radarr/Sonarr to Emby media server.

## Features

- ✅ Sync tags from Radarr (movies) or Sonarr (TV shows) to Emby
- ✅ Dry-run mode to preview changes without applying them
- ✅ Batch processing for large libraries
- ✅ Configurable via environment variables

## Quick Start

### Using Docker (Recommended)

Run it directly using the pre-built container image:

```bash
# Test connections first
docker run --rm \
  -e ARREM_ARR_TYPE="radarr" \
  -e ARREM_ARR_URL="http://your-radarr:7878" \
  -e ARREM_ARR_API_KEY="your_radarr_api_key" \
  -e ARREM_EMBY_URL="http://your-emby:8096" \
  -e ARREM_EMBY_API_KEY="your_emby_api_key" \
  ghcr.io/bjw-s-labs/arrem-sync:rolling test

# Run a dry-run sync to preview changes
docker run --rm \
  -e ARREM_ARR_TYPE="radarr" \
  -e ARREM_ARR_URL="http://your-radarr:7878" \
  -e ARREM_ARR_API_KEY="your_radarr_api_key" \
  -e ARREM_EMBY_URL="http://your-emby:8096" \
  -e ARREM_EMBY_API_KEY="your_emby_api_key" \
  -e ARREM_DRY_RUN="true" \
  ghcr.io/bjw-s-labs/arrem-sync:rolling sync

# Run actual sync (disable dry-run mode)
docker run --rm \
  -e ARREM_ARR_TYPE="radarr" \
  -e ARREM_ARR_URL="http://your-radarr:7878" \
  -e ARREM_ARR_API_KEY="your_radarr_api_key" \
  -e ARREM_EMBY_URL="http://your-emby:8096" \
  -e ARREM_EMBY_API_KEY="your_emby_api_key" \
  ghcr.io/bjw-s-labs/arrem-sync:rolling sync --no-dry-run
```

**Using environment file:**

For convenience, you can create an environment file:

```bash
# Create .env file with your configuration
cat > .env << EOF
ARREM_ARR_TYPE=radarr
ARREM_ARR_URL=http://your-radarr:7878
ARREM_ARR_API_KEY=your_radarr_api_key
ARREM_EMBY_URL=http://your-emby:8096
ARREM_EMBY_API_KEY=your_emby_api_key
ARREM_DRY_RUN=false
EOF

# Run with environment file
docker run --rm --env-file .env ghcr.io/bjw-s-labs/arrem-sync:rolling sync
```

### Manual Installation

1. Install Python 3.11+ and pip
2. Clone this repository
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure the application (choose one option):

   **Option A: Using .env file**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

   **Option B: Using environment variables**

   ```bash
   export ARREM_ARR_TYPE="radarr"
   export ARREM_ARR_URL="http://localhost:7878"
   export ARREM_ARR_API_KEY="your_api_key"
   export ARREM_EMBY_URL="http://localhost:8096"
   export ARREM_EMBY_API_KEY="your_api_key"
   ```

5. Run the application:

```bash
# Test connections first
python main.py test

# Run a dry-run sync (default behavior)
python main.py sync --dry-run

# Run actual sync (disable dry-run mode)
python main.py sync --no-dry-run
```

## Configuration

All configuration is done via environment variables with the `ARREM_` prefix. You can set these variables directly in your environment or use a `.env` file for convenience.

### Using .env File

Create a `.env` file in the project root directory:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
# Application settings
ARREM_LOG_LEVEL=INFO
ARREM_DRY_RUN=true

# Emby settings
ARREM_EMBY_URL=http://your-emby-server:8096
ARREM_EMBY_API_KEY=your-emby-api-key

# Arr service settings
ARREM_ARR_TYPE=radarr
ARREM_ARR_URL=http://your-radarr-server:7878
ARREM_ARR_API_KEY=your-radarr-api-key

# Sync settings
ARREM_BATCH_SIZE=50
```

### Required Variables

| Variable             | Description             | Example                 |
| -------------------- | ----------------------- | ----------------------- |
| `ARREM_ARR_TYPE`     | Type of Arr service     | `radarr` or `sonarr`    |
| `ARREM_ARR_URL`      | URL of your Arr service | `http://localhost:7878` |
| `ARREM_ARR_API_KEY`  | API key for Arr service | `1234567890abcdef`      |
| `ARREM_EMBY_URL`     | URL of your Emby server | `http://localhost:8096` |
| `ARREM_EMBY_API_KEY` | API key for Emby server | `abcdef1234567890`      |

### Optional Variables

| Variable           | Default | Description                             |
| ------------------ | ------- | --------------------------------------- |
| `ARREM_DRY_RUN`    | `true`  | Enable dry-run mode                     |
| `ARREM_LOG_LEVEL`  | `INFO`  | Log level (DEBUG, INFO, WARNING, ERROR) |
| `ARREM_BATCH_SIZE` | `50`    | Batch size for processing items         |

## Usage

The application provides several commands:

### sync

Perform a one-time synchronization:

```bash
# Basic sync (runs in dry-run mode by default for safety)
python main.py sync

# Disable dry-run mode to make actual changes
python main.py sync --no-dry-run

# With custom log level
python main.py sync --log-level DEBUG
```

### test

Test connections to Radarr/Sonarr and Emby:

```bash
python main.py test
```

## How It Works

1. **Connection**: The app connects to your Radarr/Sonarr instance and Emby server using their APIs
2. **Fetch Data**: It retrieves all movies/shows from Radarr/Sonarr along with their tags
3. **Match Items**: For each item, it finds the corresponding item in Emby using:
   - TMDb ID (preferred)
   - IMDb ID
   - TVDB ID (for TV shows)
4. **Sync Tags**: It updates the Emby item's tags to match the Radarr/Sonarr tags
5. **Report**: Provides detailed logging and final statistics

## Troubleshooting

### Common Issues

1. **Connection Failed**:

   - Verify your URLs and API keys
   - Ensure services are running and accessible
   - Check firewall and network settings

2. **No Items Matched**:

   - Ensure your Emby library has been scanned
   - Check that items have proper metadata (TMDb/IMDb IDs)
   - Verify library paths are correctly configured

3. **Permission Denied**:
   - Verify API keys have sufficient permissions
   - Check user permissions in Emby

### Debug Mode

Enable debug logging to get more detailed information:

```bash
export ARREM_LOG_LEVEL=DEBUG
python main.py sync
```

## Contributing

Contributions are welcomed! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, guidelines, and how to contribute to the project.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Radarr](https://radarr.video/) and [Sonarr](https://sonarr.tv/) for their excellent APIs
- [Emby](https://emby.media/) for media server functionality
