# Docker Deployment Guide

This guide explains how to build and run the voice assistant in Docker, ensuring it works on any platform (Windows, Mac, Linux).

---

## 🐳 Quick Start with Docker

### Option 1: Using Docker Compose (Recommended)

```bash
cd "/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"

# Build and run
docker-compose up

# To rebuild after changes
docker-compose up --build

# Stop the container
docker-compose down
```

### Option 2: Using Docker CLI

```bash
cd "/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"

# Build the image
docker build -t voice-assistant .

# Run in interactive mode
docker run -it voice-assistant

# Run with custom calendar ID
docker run -it voice-assistant python main.py --text --calendar-id your_team_id
```

---

## 📋 What's Included in the Docker Image

- **Base**: Python 3.11 (slim)
- **System packages**: ffmpeg, espeak-ng, git, curl
- **Python packages**: All dependencies from requirements.txt
- **Application**: Complete voice assistant with all modules
- **Default mode**: Text mode (works on all platforms)

---

## 🔧 Configuration

### Set Your Team's Calendar ID

**Method 1: Environment Variable**
```bash
docker run -it -e calenderid=your_team_id voice-assistant
```

**Method 2: Command Line Argument**
```bash
docker run -it voice-assistant python main.py --text --calendar-id your_team_id
```

**Method 3: Docker Compose**
Edit `docker-compose.yml`:
```yaml
environment:
  - calenderid=your_team_unique_id
command: ["python", "main.py", "--text", "--calendar-id", "your_team_unique_id"]
```

---

## 🖥️ Platform-Specific Instructions

### macOS

```bash
# Build
docker build -t voice-assistant .

# Run
docker run -it voice-assistant

# For Apple Silicon (M1/M2/M3)
docker build --platform linux/amd64 -t voice-assistant .
docker run --platform linux/amd64 -it voice-assistant
```

### Linux

```bash
# Build
docker build -t voice-assistant .

# Run
docker run -it voice-assistant

# For voice mode (requires audio device)
docker run -it --device /dev/snd voice-assistant python main.py
```

### Windows

Using PowerShell:
```powershell
# Build
docker build -t voice-assistant .

# Run
docker run -it voice-assistant
```

Using Command Prompt:
```cmd
rem Build
docker build -t voice-assistant .

rem Run
docker run -it voice-assistant
```

---

## 📊 Verify the Build

### Check Image Size
```bash
docker images voice-assistant
```

Expected size: ~2-3 GB (includes PyTorch and Whisper model)

### Test the Container
```bash
# Quick test
docker run voice-assistant python -c "print('Hello from Docker!')"

# Check Python version
docker run voice-assistant python --version

# List installed packages
docker run voice-assistant pip list
```

---

## 🐛 Troubleshooting

### Issue: Build fails with "no space left on device"

**Solution**: Clean up Docker images
```bash
docker system prune -a
docker volume prune
```

### Issue: Container exits immediately

**Solution**: Run in interactive mode
```bash
docker run -it voice-assistant
```

### Issue: Module not found errors

**Solution**: Rebuild without cache
```bash
docker build --no-cache -t voice-assistant .
```

### Issue: Whisper model download fails

**Solution**: The model will download on first run. Ensure internet connection:
```bash
docker run -it voice-assistant python -c "import whisper; whisper.load_model('base')"
```

### Issue: Permission denied on logs directory

**Solution**: Create logs directory with proper permissions
```bash
mkdir -p logs
chmod 777 logs
docker-compose up
```

---

## 📁 Volume Mounting

### Save Conversation Logs
```bash
# Create logs directory
mkdir -p logs

# Run with volume mount
docker run -it -v $(pwd)/logs:/app/logs voice-assistant
```

### Use Local Whisper Model Cache
```bash
# Mount cache directory to avoid re-downloading
docker run -it \
  -v ~/.cache:/root/.cache \
  voice-assistant
```

---

## 🚀 Advanced Usage

### Run Specific Commands

**Test Weather API**:
```bash
docker run voice-assistant python modules/weather_api.py
```

**Test Calendar API**:
```bash
docker run voice-assistant python modules/calendar_api.py
```

**Run NLU Tests**:
```bash
docker run voice-assistant python modules/nlu.py
```

### Interactive Shell Inside Container
```bash
# Start container with shell
docker run -it voice-assistant /bin/bash

# Then inside container
python main.py --text
```

### Run Test Suite
```bash
docker run voice-assistant python test_commands.py
```

---

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: Build and Test
on: [push]
jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker image
        run: docker build -t voice-assistant .
      - name: Test
        run: docker run voice-assistant python test_commands.py
```

### GitLab CI Example
```yaml
build:
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t voice-assistant .
    - docker run voice-assistant python test_commands.py
```

---

## 📦 Export and Import Image

### Export Image (for sharing)
```bash
docker save voice-assistant > voice-assistant.tar
```

### Import Image (on another machine)
```bash
docker load < voice-assistant.tar
```

### Push to Docker Hub (optional)
```bash
# Tag the image
docker tag voice-assistant username/voice-assistant:latest

# Push to Docker Hub
docker push username/voice-assistant:latest
```

---

## 🏗️ Multi-Stage Build (Optional Optimization)

For a smaller final image, you can use multi-stage builds:

```dockerfile
# Builder stage
FROM python:3.11 as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY main.py .
COPY modules/ ./modules/
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "main.py", "--text"]
```

---

## ✅ Submission Checklist for Docker

Before submitting:

- [ ] Image builds successfully: `docker build -t voice-assistant .`
- [ ] Container runs: `docker run -it voice-assistant`
- [ ] All tests pass: `docker run voice-assistant python test_commands.py`
- [ ] Unique calendar ID configured
- [ ] Image size is reasonable (<5GB)
- [ ] No hardcoded credentials or sensitive data
- [ ] README includes Docker instructions
- [ ] Dockerfile is documented

---

## 📝 Notes

- **Text mode** is the default and works on all platforms
- **Voice mode** requires audio device access (not available in standard Docker)
- **Model caching**: Whisper model (~150MB) downloads on first run
- **Network**: Container needs internet access for API calls
- **Storage**: Ensure at least 5GB free space for Docker image

---

## 🎯 Production Deployment

For production use:

1. **Use specific tags** instead of `latest`
2. **Set resource limits**:
   ```bash
   docker run -it --memory="2g" --cpus="2" voice-assistant
   ```
3. **Use docker-compose** for easier management
4. **Mount volumes** for persistent logs
5. **Set restart policies**:
   ```yaml
   restart: unless-stopped
   ```

---

**The Docker container is platform-independent and works on Windows, Mac, and Linux!** 🎉
