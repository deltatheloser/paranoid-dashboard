# Dashboard — terminal system monitor

Minimal terminal dashboard that shows CPU, memory, disk, processes, network connections and (optional) GPU stats using `rich` and `plotext`.

**Quick Summary:**

- Simple terminal dashboard that show some system info, along with a bunch of useless "logs"

## Features

Shows:

- System info (OS, uptime, host, IP)
- CPU / Memory usage
- Disk usage visualization
- Simple process list
- Active network connections (ESTABLISHED)
- Fake / demo log events (customizable)
- Optional GPU monitoring (NVIDIA via `pynvml` or AMD via sysfs)

## Requirements

- Python 3.10+ recommended
- pip packages: `rich`, `psutil`, `plotext`
- Optional for NVIDIA GPU: `pynvml`

## Install

```powershell
git clone https://github.com/deltatheloser/paranoid-dashboard.git
cd paranoid-dashboard

pip install -r requirements.txt
```

## Usage

```powershell
python main.py
```

### Notes

This project was done as a simple way to learn more about rich and the terminal environment. It's not meant to be a full-featured system monitor, but rather a fun demo with some random log messages. And the code quality is pretty rough...

There's probably some bugs and other problems, specially with the gpu monitoring, since I don't have much experience with that. But it should work on most systems (hopefully).

Also I probably should split the main script into more modules (UI rendering/data collection/etc), but I wrote this a year ago and I feel too lazy to refactor it now..