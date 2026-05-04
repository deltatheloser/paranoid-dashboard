import platform
import os

try:
    import pynvml
    HAS_NVIDIA = True
except (ImportError, pynvml.NVMLError):
    HAS_NVIDIA = False


AMD_LOAD_PATH = "/sys/class/drm/card0/device/gpu_busy_percent"
AMD_VRAM_USED = "/sys/class/drm/card0/device/mem_info_vram_used"
AMD_VRAM_TOTAL = "/sys/class/drm/card0/device/mem_info_vram_total"

class GPUReader:
    def __init__(self):
        self.mode = "NONE"

        if HAS_NVIDIA:
            try:
                pynvml.nvmlInit()
                self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                self.mode = "NVIDIA"
                return
            except Exception:
                pass
        
        if os.path.exists(AMD_LOAD_PATH):
            self.mode = "AMD_FILE"
            return
    
    def get_stats(self):
        if self.mode == "NVIDIA":
            try:
                mem = pynvml.nvmlDeviceGetMemoryInfo(self.handle)
                total = mem.total / (1024**2)
                used = mem.used / (1024**2)

                util = pynvml.nvmlDeviceGetUtilizationRates(self.handle)

                return {
                "load": util.gpu,
                "vram_used": int(used),
                "vram_total": int(total),
                "name": "NVIDIA"
            }
            except Exception:
                return {"load ": 0, "vram_used": 0, "vram_total": 0, "name": "ERR"}
        elif self.mode == "AMD_FILE":
            try:
                with open(AMD_LOAD_PATH, "r") as f:
                    load = int(f.read().strip())
                with open(AMD_VRAM_USED, "r") as f:
                    used = int(f.read().strip())
                with open(AMD_VRAM_TOTAL, "r") as f:
                    total = int(f.read().strip())

                return {
                    "load": load,
                    "vram_used": int(used),
                    "vram_total": int(total),
                    "name": "AMD"
                }
            except Exception:
                return {"load ": 0, "vram_used": 0, "vram_total": 0, "name": "ERR"}
        
        else:
            return {"load ": 0, "vram_used": 0, "vram_total": 0, "name": "???"}