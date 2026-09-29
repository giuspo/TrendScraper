import typer
from rich.console import Console
from rich.table import Table
from core.database import create_db_and_tables
from modules.mod1_radar.radar import RadarEngine

app = typer.Typer(help="TrendRadar & Sourcing Engine CLI")
console = Console()

@app.command()
def setup():
    """Inizializza il database SQLite locale."""
    console.print("[bold green]Creazione tabelle nel database...[/bold green]")
    create_db_and_tables()
    console.print("[bold green]Setup completato.[/bold green]")

@app.command()
def scan(
    category: str = typer.Option("all", help="Categoria da scansionare"),
    min_margin: float = typer.Option(20.0, help="Override margine minimo operativo"),
    max_weight: float = typer.Option(800.0, help="Override peso massimo in grammi")
):
    """Avvia la scansione e valuta le idee (Radar)."""
    console.print(f"[bold blue]Avvio Scansione...[/bold blue] Categoria: {category} | Margine Min: {min_margin}% | Peso Max: {max_weight}g")
    
    # 1. Lanciamo il Radar (Mod 1)
    radar = RadarEngine()
    candidates = radar.run_scan()
    
    if not candidates:
        console.print("[yellow]Nessun candidato trovato dal radar in questa sessione.[/yellow]")
        return

    # MOCKUP DEI RISULTATI SUCCESSIVI
    # Qui, in futuro, si innescheranno in sequenza:
    # Modulo 2 (Trend), Modulo 3 (Fabbrica), Modulo 4 (Amazon), Modulo 5 (Calcoli)
    
    table = Table(title="Risultati Radar Idee (Anteprima)")
    table.add_column("Sorgente", style="cyan")
    table.add_column("Keyword Candidata", style="magenta")
    table.add_column("Trazione", justify="right", style="green")

    for cand in candidates[:10]: # mostriamo i primi 10
        table.add_row(cand["source"], cand["keyword"][:50] + "...", str(cand["initial_traction_score"]))

    console.print(table)
    console.print(f"\n[bold green]Completato! Elaborate {len(candidates)} idee.[/bold green]")

if __name__ == "__main__":
    app()
