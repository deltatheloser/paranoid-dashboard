import time
import math
import plotext as plt
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.ansi import AnsiDecoder
from rich.align import Align
from rich.console import Group
from rich.table import Table
from rich.bar import Bar
from rich.console import Console
from rich.padding import Padding
from rich.text import Text
import psutil
import types
from gpu_mon import GPUReader
import socket
import random as rd
import platform
from datetime import datetime
import loader
import signal
import sys

HOSTNAME = socket.gethostname()
BOOT_TIME = datetime.fromtimestamp(psutil.boot_time())
EXIT_PHRASES, LOG_PHRASES = loader.load_configs()


try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    IP_ADDRESS = s.getsockname()[0]
    s.close()
except:
    IP_ADDRESS = "127.0.0.1"

OS_INFO = f"{platform.system()} {platform.release()}"
ARCH_INFO = platform.machine()
TZ_INFO = time.tzname[0]

gpu_reader = GPUReader()
gpu_stats = gpu_reader.get_stats()
HAS_READABLE_GPU = 1 if (gpu_stats['name'] != "ERR" and gpu_stats['name'] != "???") else 0

event_log_history = []

_cache_procs = None
_cache_net = None
_cache_disk = None

def make_plotext_graph(phase_shift, width, height):
    y_data = [math.sin((i / 5) + phase_shift) for i in range(60)]

    plt.clear_data()
    plt.clear_figure()
    
    w = max(10, int(width) - 4)
    h = max(5, int(height) - 2)

    plt.plotsize(width=w, height=h) 
    plt.theme("dark")
    plt.ylim(-1.5, 1.5)
    plt.frame(True)
    plt.grid(False, False)
    plt.yticks([])
    plt.xticks([])

    plt.plot(y_data, color="cyan", marker="braille")
    
    graph_str = plt.build()
    decoder = AnsiDecoder()
    renderable = decoder.decode(graph_str)

    if isinstance(renderable, types.GeneratorType):
        items = list(renderable)
        renderable = Group(*items)

    return Panel(Align.center(renderable), title="", border_style="blue")



def system_res_use():
    table = Table(expand=True, border_style="blue", title_style="bold blue")
    table.add_column("Resources", justify="left", style="cyan", no_wrap=True)
    table.add_column("Usage", justify="right", style="magenta")

    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory()

    cpu_bar_color = "red" if cpu > 80 else "yellow" if cpu > 50 else "green"
    mem_bar_color = "red" if mem.percent > 80 else "yellow" if mem.percent > 50 else "green"
    cpu_bar = Bar(size=100, begin=0, end=cpu, color=cpu_bar_color)
    mem_bar = Bar(size=100, begin=0, end=mem.percent, color=mem_bar_color)
    
    cpu_color = "[red]" if cpu > 80 else "[yellow]" if cpu > 50 else "[green]"
    mem_color = "[red]" if mem.percent > 80 else "[yellow]" if mem.percent > 50 else "[green]"

    cpu_text = f"{cpu_color}{cpu}%[/]"
    mem_text = f"{mem_color}{mem.percent}%[/]"

    combined_cpu = Table.grid(expand=True)
    combined_cpu.add_column()
    combined_cpu.add_column(justify="right")
    combined_cpu.add_row(cpu_bar, cpu_text)
    
    combined_mem = Table.grid(expand=True)
    combined_mem.add_column()
    combined_mem.add_column(justify="right")
    combined_mem.add_row(mem_bar, mem_text)

    table.add_row("CPU Usage", combined_cpu)
    table.add_row("Memory Total", f"[green]{round(mem.total / (1024**3), 2)} GB[/]")
    table.add_row("Memory Usage", combined_mem)
    
    if HAS_READABLE_GPU:
        g_stats = gpu_reader.get_stats()

        if g_stats['load'] > 80:
            gpu_color = "[red]"
        elif g_stats['load'] > 50:
            gpu_color = "[yellow]"
        else:
            gpu_color = "[green]"
            
        total_vram = g_stats['vram_total'] if g_stats['vram_total'] > 0 else 1
        
        if (g_stats['vram_used'] / total_vram * 100) > 80:
            vram_color = "[red]"
        else:
            vram_color = "[green]"

        table.add_row(f"GPU Load", f"{gpu_color}{g_stats['load']}%[/]")
        table.add_row(f"GPU VRAM Used", f"{vram_color}{g_stats['vram_used'] / 1024:.2f} GB[/]")
        table.add_row(f"GPU VRAM Total", f"{vram_color}{g_stats['vram_total'] / 1024:.2f} GB[/]")
    return table

def system_processes(force_update=False):
    global _cache_procs
    
    if _cache_procs and not force_update:
        return _cache_procs

    cpu_count = psutil.cpu_count()
    processes = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            if p.info['pid'] < 10 or p.info['name'] == 'System Idle Process':
                continue
            
            raw_cpu = p.info['cpu_percent']
            normalized_cpu = raw_cpu / cpu_count

            processes.append({
                'pid': p.info['pid'],
                'name': p.info['name'],
                'cpu_percent': normalized_cpu,
                'memory_percent': p.info['memory_percent']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    top_processes = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)[:20]

    table = Table(expand=True, border_style="blue", title_style="bold blue")
    table.add_column("PID", style="cyan", no_wrap=True, width=6)
    table.add_column("Name", style="cyan", no_wrap=True, width=25)
    table.add_column("CPU %", justify="right", style="cyan")
    table.add_column("Memory %", justify="right", style="cyan")

    for p in top_processes[:16]:
        cpu_color = "red" if p['cpu_percent'] > 50 else "yellow" if p['cpu_percent'] > 20 else "green"
        table.add_row(
            str(p['pid']),
            p['name'][:25],
            f"{p['cpu_percent']:.1f}",
            f"{p['memory_percent']:.1f}"
        )

    _cache_procs = Panel(table, title="Current Processes", border_style="blue")
    return _cache_procs


def system_storage(force_update=False):
    global _cache_disk
    if _cache_disk and not force_update:
        return _cache_disk

    disk = psutil.disk_usage('/')
    total_block = 50
    used_blocks = int((disk.used / disk.total) * total_block)
    free_blocks = total_block - used_blocks
    total_gb = disk.total / (1024**3)
    free_gb = disk.free / (1024**3)

    block_list = ["[green]■[/]"] * used_blocks + ["[dim]□[/]"] * free_blocks
    block_grid = Table.grid(padding=(0, 0))

    for _ in range(25):
        block_grid.add_column(width=1,justify="left")

    for i in range(0, len(block_list), 25):
        rows_cells = [Text.from_markup(b) for b in block_list[i:i+25]]
        block_grid.add_row(*rows_cells)

    header = Text.assemble(
        ("Drive (C:)\n", "bold"),
        (f"{disk.percent}% Used\n", "bold white")
    )
    footer = Text(f"\nTotal: {total_gb:.0f} GB  |  Free: {free_gb:.0f} GB", style="dim")
    content_group = Group(header, block_grid, footer)
    indented_content = Padding(content_group, (1, 1, 1, 4))
    
    _cache_disk = Panel(indented_content, title="Storage", border_style="green")
    return _cache_disk

def base_info():
    now = datetime.now()
    uptime = now - BOOT_TIME
    up_str = str(uptime).split('.')[0] 
    
    try:
        batt = psutil.sensors_battery()
        batt_pct = f"{batt.percent}%" if batt else 'N/A'
    except:
        batt_pct = "N/A"

    sys_info_text = f"""
    [cyan]OS:[/]      {OS_INFO}
    [cyan]Uptime:[/]  {up_str}
    [cyan]Boot:[/]    {BOOT_TIME.strftime("%Y-%m-%d %H:%M")}
    [cyan]Arch:[/]    {ARCH_INFO}
    [cyan]Host:[/]    {HOSTNAME}
    [cyan]IP Address:[/] {IP_ADDRESS}
    [cyan]Battery:[/] {batt_pct}
    [cyan]Time Zone:[/] {TZ_INFO}
    """
    return Panel(sys_info_text, title="Base Info", border_style="cyan")

def netstat(force_update=False):
    global _cache_net
    if _cache_net and not force_update:
        return _cache_net
    
    try:
        connections = psutil.net_connections(kind='inet')
        active_conns = [c for c in connections if c.status == "ESTABLISHED"]
        
        table = Table(expand=True, border_style="blue", title_style="bold blue")
        table.add_column("Local Port", style="cyan", no_wrap=True)
        table.add_column("Remote IP", style="cyan", no_wrap=True)
        table.add_column("Remote Port", style="cyan", no_wrap=True)
        
        for conn in active_conns[-11:]:
            local_port = str(conn.laddr.port)
            if conn.raddr:
                remote_ip = conn.raddr.ip
                remote_port = str(conn.raddr.port)
            else:
                remote_ip = "*"
                remote_port = "*"
            table.add_row(local_port, remote_ip, remote_port)
        
        _cache_net = Panel(table, title="NetStat Monitor", border_style="blue")
        return _cache_net
    except:
        return Panel("Access Denied", title="NetStat", border_style="red")


def system_logs():
    global event_log_history

    if rd.random() < 0.05:
        now_str = datetime.now().strftime("%H:%M:%S")
        level, msg = rd.choice(LOG_PHRASES)
        if "PID" in msg and "Daemon" in msg:
            msg = f"Daemon active: PID {rd.randint(1000,9999)}"
        elif "PID" in msg and "Zombie" in msg:
            msg = f"Zombie process found: PID {rd.randint(1000,9999)}"

        event_log_history.append(f"[dim]{now_str}[/] {level} {msg}")

        if len(event_log_history) > 18:
            event_log_history.pop(0)
    
    table = Table(expand=True, border_style="blue", box=None, padding=(0,1))
    table.add_column("Time", style="dim", width=8)
    table.add_column("Lvl", width=6)
    table.add_column("Message")

    for log in event_log_history:
        parts = log.split(" ", 2)
        if len(parts) == 3:
            table.add_row(parts[0], parts[1], parts[2])

    return Panel(table, title="Logs", border_style="blue")

layout = Layout()
layout.split_column(
    Layout(name="header", size=3),
    Layout(name="body"),
    Layout(name="footer", size=3),
)

layout["body"].split_row(
    Layout(name="left"),
    Layout(name="right"),
)

layout["right"].split_column(
    Layout(name="wave_section", size=10),
    Layout(name="bottom_right",)
)

layout["left"].split_column(
    Layout(name="system_usage", size=10),
    Layout(name="middle_row", size=14),
    Layout(name="system_logs"),
)

layout["middle_row"].split_row(
    Layout(name="system_storage"),
    Layout(name="base_info"),
)

layout["header"].update(
    Panel(f"ROOT@{HOSTNAME}", title="", border_style="purple")
)

layout["bottom_right"].split_column(
    Layout(name="system_processes", size=22),
    Layout(name="NetStat_Monitor"),
)

layout["footer"].update(f"[purple]System: [green]ONLINE[/] | Mode: [green bold]MONITORING[/] | Press [bold cyan]Ctrl+C[/] to [bold italic red]Exit[/]")



is_shutting_down = False
def shutdown(signum=None, frame=None):
    try:
        final_message = rd.choice(EXIT_PHRASES)
        end_layout = Layout()
        end_layout.update(
            Panel(
                Align.center(
                    f"[bold white]{final_message}[/]",
                    vertical="middle"
                ),
                border_style="black",
                style="on black"
            )
        )
        global live
        global is_shutting_down
        
        if is_shutting_down:
            return
        is_shutting_down = True
        
        if live:
            live.update(end_layout)
            live.refresh()
            time.sleep(2)
            live.stop()
    except Exception:
        pass
    finally:
        sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown)
    try:
        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGBREAK, shutdown)
    except AttributeError:
        pass
    global live
    
    phase = 0
    console = Console()
    tick = 0

    with Live(layout, refresh_per_second=10, screen=True, console=console) as live:
        while True:
            try:
                tick += 1
                
                if tick % 10 == 0:
                    term_width = console.size.width
                    term_height = console.size.height
                    if term_width < 100 or term_height < 25:
                        continue

                right_column_width = console.size.width / 2

                layout["wave_section"].update(make_plotext_graph(phase, right_column_width, 10))
                layout["system_usage"].update(system_res_use())
                layout["system_logs"].update(system_logs())
                layout["base_info"].update(base_info())

                
                if tick % 50 == 0:
                    layout["system_storage"].update(system_storage(force_update=True))
                elif tick == 1:
                    layout["system_storage"].update(system_storage(force_update=True))

                if tick % 20 == 0:
                    layout["system_processes"].update(system_processes(force_update=True))
                elif tick == 1:
                    layout["system_processes"].update(system_processes(force_update=True))

                if tick % 30 == 0:
                    layout["NetStat_Monitor"].update(netstat(force_update=True))
                elif tick == 1:
                    layout["NetStat_Monitor"].update(netstat(force_update=True))
                
                phase += 0.5
                
                time.sleep(0.25)
                
                if tick > 1000: tick = 0

            except Exception as e:
                layout["footer"].update(Panel(f"ERROR: {e}", style="bold red"))
                time.sleep(5)
                break