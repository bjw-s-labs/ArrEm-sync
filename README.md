# ArrEm-sync

A Python application that synchronizes tags from Radarr/Sonarr to Emby media server.

## Features

- ✅ Sync tags from multiple Radarr/Sonarr instances to Emby
- ✅ Additive tag sync: tags from Arr are added in Emby; existing Emby tags are preserved (never removed)
- ✅ Support for mixing Radarr and Sonarr instances
- ✅ Dry-run mode to preview changes without applying them
- ✅ Batch processing for large libraries
- ✅ Configurable via environment variables

## Quick Start

### Using Docker (Recommended)

Run it directly using the pre-built container image:

```bash
# Test connections first
docker run --rm \
   -e ARREM_ARR_1_TYPE="radarr" \
   -e ARREM_ARR_1_URL="http://your-radarr:7878" \
   -e ARREM_ARR_1_API_KEY="your_radarr_api_key" \
   -e ARREM_ARR_1_NAME="Main Radarr" \
   -e ARREM_EMBY_URL="http://your-emby:8096" \
   -e ARREM_EMBY_API_KEY="your_emby_api_key" \
   ghcr.io/bjw-s-labs/arrem-sync:rolling test

# Run a dry-run sync to preview changes (dry-run is the default)
docker run --rm \
   -e ARREM_ARR_1_TYPE="radarr" \
   -e ARREM_ARR_1_URL="http://your-radarr:7878" \
   -e ARREM_ARR_1_API_KEY="your_radarr_api_key" \
   -e ARREM_ARR_1_NAME="Main Radarr" \
   -e ARREM_EMBY_URL="http://your-emby:8096" \
   -e ARREM_EMBY_API_KEY="your_emby_api_key" \
   ghcr.io/bjw-s-labs/arrem-sync:rolling

# Run actual sync (disable dry-run mode)
docker run --rm \
   -e ARREM_ARR_1_TYPE="radarr" \
   -e ARREM_ARR_1_URL="http://your-radarr:7878" \
   -e ARREM_ARR_1_API_KEY="your_radarr_api_key" \
   -e ARREM_ARR_1_NAME="Main Radarr" \
   -e ARREM_EMBY_URL="http://your-emby:8096" \
   -e ARREM_EMBY_API_KEY="your_emby_api_key" \
   ghcr.io/bjw-s-labs/arrem-sync:rolling --no-dry-run
```

**Using environment file:**

For convenience, you can create an environment (`.env`) file:

```bash
cp .env.example .env
# Edit .env with your values, then run:
docker run --rm --env-file .env ghcr.io/bjw-s-labs/arrem-sync:rolling
```

**Multiple Arr instances:**

```
# First Radarr instance (regular movies)
ARREM_ARR_1_TYPE=radarr
ARREM_ARR_1_URL=http://radarr:7878
ARREM_ARR_1_API_KEY=your_radarr_api_key
ARREM_ARR_1_NAME=Radarr

# Second Radarr instance (4K movies)
ARREM_ARR_2_TYPE=radarr
ARREM_ARR_2_URL=http://radarr4k:7878
ARREM_ARR_2_API_KEY=your_radarr4k_api_key
ARREM_ARR_2_NAME=Radarr 4K

# Sonarr instance
ARREM_ARR_3_TYPE=sonarr
ARREM_ARR_3_URL=http://sonarr:8989
ARREM_ARR_3_API_KEY=your_sonarr_api_key
ARREM_ARR_3_NAME=Sonarr

# Emby configuration
ARREM_EMBY_URL=http://your-emby:8096
ARREM_EMBY_API_KEY=your_emby_api_key
ARREM_DRY_RUN=false
```

### Manual Installation

1. Install Python 3.13+ and a package manager (uv recommended, or pip)
2. Clone this repository
3. Install dependencies:

   Using uv (recommended):

   ```bash
   uv sync
   ```

   Or using pip:

   ```bash
   python -m pip install .
   ```

4. Configure the application (choose one option):

   **Option A: Using .env file**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

   **Option B: Using environment variables**

   ```bash
   export ARREM_ARR_1_TYPE="radarr"
   export ARREM_ARR_1_URL="http://localhost:7878"
   export ARREM_ARR_1_API_KEY="your_api_key"
   export ARREM_ARR_1_NAME="Main Radarr"
   export ARREM_EMBY_URL="http://localhost:8096"
   export ARREM_EMBY_API_KEY="your_api_key"
   ```

5. Run the application:

   Using uv:

   ```bash
   # Test connections first
   uv run arrem-sync test

   # Run a dry-run sync (default behavior)
   uv run arrem-sync

   # Run actual sync (disable dry-run mode)
   uv run arrem-sync --no-dry-run
   ```

   Or using the installed CLI directly (pip install .):

   ```bash
   # Test connections first
   arrem-sync test

   # Dry-run sync (default)
   arrem-sync

   # Actual sync
   arrem-sync --no-dry-run
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

# First Arr instance
ARREM_ARR_1_TYPE=radarr
ARREM_ARR_1_URL=http://your-radarr-server:7878
ARREM_ARR_1_API_KEY=your-radarr-api-key
ARREM_ARR_1_NAME=Main Radarr

# Second Arr instance (optional)
ARREM_ARR_2_TYPE=sonarr
ARREM_ARR_2_URL=http://your-sonarr-server:8989
ARREM_ARR_2_API_KEY=your-sonarr-api-key
ARREM_ARR_2_NAME=Main Sonarr

# Sync settings
ARREM_BATCH_SIZE=50
```

### Required Variables

| Variable              | Description                    | Example                 |
| --------------------- | ------------------------------ | ----------------------- |
| `ARREM_ARR_N_TYPE`    | Type of Arr service (N=1,2...) | `radarr` or `sonarr`    |
| `ARREM_ARR_N_URL`     | URL of your Arr service        | `http://localhost:7878` |
| `ARREM_ARR_N_API_KEY` | API key for Arr service        | `1234567890abcdef`      |
| `ARREM_ARR_N_NAME`    | Friendly name for instance     | `Main Radarr`           |
| `ARREM_EMBY_URL`      | URL of your Emby server        | `http://localhost:8096` |
| `ARREM_EMBY_API_KEY`  | API key for Emby server        | `abcdef1234567890`      |

**Note:** Replace `N` with numbers starting from 1. You can configure multiple Arr instances by using `ARREM_ARR_1_*`, `ARREM_ARR_2_*`, etc.

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
# Basic sync (dry-run by default)
arrem-sync

# Disable dry-run mode to make actual changes
arrem-sync --no-dry-run

# With custom log level
ARREM_LOG_LEVEL=DEBUG arrem-sync
```

### test

Test connections to Radarr/Sonarr and Emby:

```bash
arrem-sync test
```

## How It Works

1. **Connection**: The app connects to your Radarr/Sonarr instance and Emby server using their APIs
2. **Fetch Data**: It retrieves all movies/shows from Radarr/Sonarr along with their tags
3. **Match Items**: For each item, it finds the corresponding item in Emby using:
   - TMDb ID (preferred)
   - IMDb ID
   - TVDB ID (for TV shows)
4. **Sync Tags**: It adds any missing tags from Radarr/Sonarr to the Emby item. Existing tags in Emby are preserved and are never removed by this tool.
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
arrem-sync
```

## Contributing

Contributions are welcomed! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, guidelines, and how to contribute to the project.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Radarr](https://radarr.video/) and [Sonarr](https://sonarr.tv/) for their excellent APIs
- [Emby](https://emby.media/) for media server functionality
