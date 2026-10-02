# -*- coding: utf-8 -*-
import sys
from dotenv import load_dotenv
load_dotenv()

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import typer
from rich.console import Console
from rich.table import Table
import logging
import time
import random
from modules.mod1_radar.radar import RadarEngine
from modules.mod2_trend.trend_engine import TrendEngine
from modules.mod3_sourcing.aliexpress_scraper import AliExpressScraper
from modules.mod4_benchmark.amazon_scraper import AmazonBenchmarkEngine

logging.basicConfig(level=logging.WARNING)

app = typer.Typer(help="TrendRadar & Sourcing Engine CLI")
console = Console()

def human_delay(min_sec=3, max_sec=6, message="Attesa per non sovraccaricare il server..."):
    delay = random.uniform(min_sec, max_sec)
    with console.status(f"[dim]{message} ({delay:.1f}s)[/dim]", spinner="dots"):
        time.sleep(delay)

@app.command()
def setup():
    pass

@app.command()
def scan(
    category: str = typer.Option("all", "--category", "-c", help="Es: informatica, casa, giardinaggio"),
    limit: int = typer.Option(3, "--limit", "-l", help="Quanti prodotti massimi analizzare")
):
    console.print(f"[bold blue]Avvio Pipeline Completa a 4 Stadi (Safe & Slow)...[/bold blue] (Cat: {category})")
    
    console.print(f"\n[yellow]Fase 1: Scansione Radar per '{category}'...[/yellow]")
    radar = RadarEngine()
    candidates = radar.run_scan(category=category)
    if not candidates:
        console.print(f"[bold red]Nessun candidato trovato. Esco.[/bold red]")
        return
        
    console.print(f"\n[yellow]Fase 2: Validazione Google Trends per {min(len(candidates), limit)} candidati...[/yellow]")
    trend_engine = TrendEngine()
    credits_left = trend_engine.get_remaining_credits()
    console.print(f" -> [bold yellow]Crediti SerpApi Rimasti:[/bold yellow] [bold green]{credits_left}[/bold green]")
    if credits_left <= 10:
        console.print("[bold red]Operazione annullata per crediti insufficienti (rimasti <= 10).[/bold red]")
        raise typer.Exit(1)
    trend_engine = TrendEngine()
    valid_candidates = []
    for i, c in enumerate(candidates[:limit]):
        if i > 0: human_delay(3, 5, "Pausa anti-bot Google Trends")
        console.print(f" -> Controllo trend per: [cyan]{c['keyword']}[/cyan]")
        trend_res = trend_engine.evaluate_keyword(c['keyword'])
        c['trend_score'] = trend_res.get('trend_score', 0.0)
        valid_candidates.append(c)
        
    console.print(f"\n[yellow]Fase 3: Ricerca costi fabbrica (AliExpress)...[/yellow]")
    sourcing_engine = AliExpressScraper()
    for i, c in enumerate(valid_candidates):
        if i > 0: human_delay(3, 6, "Pausa anti-bot AliExpress")
        console.print(f" -> Cerco costo cinese per: [cyan]{c['keyword']}[/cyan]")
        sourcing_res = sourcing_engine.estimate_sourcing_cost(c['keyword'])
        c['base_cost'] = sourcing_res.get('estimated_cost_usd', 0.0)
        
    console.print(f"\n[yellow]Fase 4: Benchmark prezzo di vendita (Amazon)...[/yellow]")
    amazon_engine = AmazonBenchmarkEngine()
    for i, c in enumerate(valid_candidates):
        if i > 0: human_delay(2, 4, "Pausa anti-bot Amazon")
        console.print(f" -> Cerco prezzo di mercato per: [cyan]{c['keyword']}[/cyan]")
        amazon_res = amazon_engine.estimate_selling_price(c['keyword'])
        c['sell_price'] = amazon_res.get('estimated_price_eur', 0.0)
        
        if c['sell_price'] > 0 and c['base_cost'] > 0:
            margin = ((c['sell_price'] - c['base_cost']) / c['sell_price']) * 100
            c['margin_percent'] = round(margin, 1)
        else:
            c['margin_percent'] = 0.0
            
    # L'utente ha ragione: il Trend comanda! Ordiniamo per Trend decrescente.
    valid_candidates.sort(key=lambda x: (x.get('trend_score', 0.0), x.get('margin_percent', 0.0)), reverse=True)
        
    console.print("\n")
    table = Table(title=f"--- RISULTATI FINALI TRENDSCRAPER ({category.upper()}) ---")
    table.add_column("Keyword", style="magenta")
    table.add_column("Trend", justify="right", style="bold green")
    table.add_column("Costo (Ali)", justify="right", style="yellow")
    table.add_column("Prezzo (Amz)", justify="right", style="cyan")
    table.add_column("Margine Lordo", justify="right", style="green")
    
    for cand in valid_candidates:
        cost_str = f"€{cand['base_cost']:.2f}" if cand['base_cost'] > 0 else "N/A"
        sell_str = f"€{cand['sell_price']:.2f}" if cand['sell_price'] > 0 else "N/A"
        marg_str = f"{cand['margin_percent']}%" if cand['margin_percent'] > 0 else "N/A"
        
        table.add_row(cand["keyword"][:30], str(round(cand['trend_score'], 1)), cost_str, sell_str, marg_str)
        
    console.print(table)

if __name__ == "__main__":
    app()
