# arr-tagsync

A Python application that synchronizes tags from Radarr/Sonarr to Emby media server.

## Features

- ✅ Sync tags from Radarr (movies) or Sonarr (TV shows) to Emby
- ✅ Docker support with environment variable configuration
- ✅ Dry-run mode to preview changes without applying them
- ✅ Batch processing for large libraries
- ✅ One-time sync optimized for Kubernetes CronJobs
- ✅ Comprehensive logging and error handling
- ✅ Unit tests included
- ✅ Configurable via environment variables
- ✅ Health checks and connection testing

## Quick Start

### Using Docker (Recommended)

1. Clone this repository:

```bash
git clone https://github.com/your-username/arr-tagsync.git
cd arr-tagsync
```

2. Copy and edit the docker-compose.yml file:

```bash
cp docker-compose.yml docker-compose.override.yml
```

3. Edit `docker-compose.override.yml` with your configuration:

```yaml
version: "3.8"

services:
  arr-tagsync:
    environment:
      TAGSYNC_ARR_TYPE: "radarr" # or "sonarr"
      TAGSYNC_ARR_URL: "http://your-radarr:7878"
      TAGSYNC_ARR_API_KEY: "your_radarr_api_key"
      TAGSYNC_EMBY_URL: "http://your-emby:8096"
      TAGSYNC_EMBY_API_KEY: "your_emby_api_key"
      TAGSYNC_DRY_RUN: "true" # Start with dry-run to test
```

4. Run the application:

```bash
# Test connections first
docker-compose run --rm arr-tagsync test

# Run a dry-run sync
docker-compose run --rm arr-tagsync sync --dry-run

# Run actual sync
docker-compose run --rm arr-tagsync sync
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
   export TAGSYNC_ARR_TYPE="radarr"
   export TAGSYNC_ARR_URL="http://localhost:7878"
   export TAGSYNC_ARR_API_KEY="your_api_key"
   export TAGSYNC_EMBY_URL="http://localhost:8096"
   export TAGSYNC_EMBY_API_KEY="your_api_key"
   ```

5. Run the application:

```bash
# Test connections first
python main.py test

# Run a dry-run sync
python main.py sync --dry-run

# Run actual sync
python main.py sync
```

export TAGSYNC_EMBY_URL="http://localhost:8096"
export TAGSYNC_EMBY_API_KEY="your_api_key"

python main.py sync --dry-run

````

## Configuration

All configuration is done via environment variables with the `TAGSYNC_` prefix. You can set these variables directly in your environment or use a `.env` file for convenience.

### Using .env File

Create a `.env` file in the project root directory:

```bash
cp .env.example .env
````

Edit the `.env` file with your configuration:

```env
# Application settings
TAGSYNC_LOG_LEVEL=INFO
TAGSYNC_DRY_RUN=false

# Emby settings
TAGSYNC_EMBY_URL=http://your-emby-server:8096
TAGSYNC_EMBY_API_KEY=your-emby-api-key

# Arr service settings
TAGSYNC_ARR_TYPE=radarr
TAGSYNC_ARR_URL=http://your-radarr-server:7878
TAGSYNC_ARR_API_KEY=your-radarr-api-key

# Sync settings
TAGSYNC_BATCH_SIZE=50
```

### Required Variables

| Variable               | Description             | Example                 |
| ---------------------- | ----------------------- | ----------------------- |
| `TAGSYNC_ARR_TYPE`     | Type of Arr service     | `radarr` or `sonarr`    |
| `TAGSYNC_ARR_URL`      | URL of your Arr service | `http://localhost:7878` |
| `TAGSYNC_ARR_API_KEY`  | API key for Arr service | `1234567890abcdef`      |
| `TAGSYNC_EMBY_URL`     | URL of your Emby server | `http://localhost:8096` |
| `TAGSYNC_EMBY_API_KEY` | API key for Emby server | `abcdef1234567890`      |

### Optional Variables

| Variable               | Default | Description                             |
| ---------------------- | ------- | --------------------------------------- |
| `TAGSYNC_EMBY_USER_ID` | (none)  | Specific Emby user ID                   |
| `TAGSYNC_DRY_RUN`      | `false` | Enable dry-run mode                     |
| `TAGSYNC_LOG_LEVEL`    | `INFO`  | Log level (DEBUG, INFO, WARNING, ERROR) |
| `TAGSYNC_BATCH_SIZE`   | `50`    | Batch size for processing items         |

## Usage

The application provides several commands:

### sync

Perform a one-time synchronization:

```bash
# Basic sync
python main.py sync

# Dry-run mode (preview changes)
python main.py sync --dry-run

# With custom log level
python main.py sync --log-level DEBUG
```

### test

Test connections to Radarr/Sonarr and Emby:

```bash
python main.py test
```

## Kubernetes CronJob

This application is designed to run as a Kubernetes CronJob. Here's an example configuration:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: arr-tagsync
spec:
  schedule: "0 */6 * * *" # Run every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: arr-tagsync
              image: your-registry/arr-tagsync:latest
              env:
                - name: TAGSYNC_ARR_TYPE
                  value: "radarr"
                - name: TAGSYNC_ARR_URL
                  value: "http://radarr:7878"
                - name: TAGSYNC_ARR_API_KEY
                  valueFrom:
                    secretKeyRef:
                      name: arr-tagsync-secrets
                      key: arr-api-key
                - name: TAGSYNC_EMBY_URL
                  value: "http://emby:8096"
                - name: TAGSYNC_EMBY_API_KEY
                  valueFrom:
                    secretKeyRef:
                      name: arr-tagsync-secrets
                      key: emby-api-key
              command: ["python", "main.py", "sync"]
          restartPolicy: OnFailure
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
export TAGSYNC_LOG_LEVEL=DEBUG
python main.py sync --dry-run
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, guidelines, and how to contribute to the project.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Radarr](https://radarr.video/) and [Sonarr](https://sonarr.tv/) for their excellent APIs
- [Emby](https://emby.media/) for media server functionality
