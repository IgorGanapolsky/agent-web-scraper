"""Command-line interface for the Google web scraper."""
import os
import click
import asyncio
from typing import Optional, Dict
from pathlib import Path
from ..web.app import extract_headers_with_undetected_chrome


@click.group()
def cli():
    """Google Web Scraper CLI - A powerful tool for scraping Google search results."""
    pass


# Expose the cli as app for compatibility with tests and other modules
app = cli


async def _scrape_google_async(
    query: str,
    output: Optional[str],
    headless: bool,
    verbose: bool
) -> Dict[str, str]:
    """Async implementation of the Google scrape command."""
    try:
        if verbose:
            click.echo(f"Searching Google for: {query}")
        
        # Build the Google search URL
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        
        # Extract headers from the search results
        headers = extract_headers_with_undetected_chrome(
            search_url,
            tags=["h1", "h2", "h3", "title"]
        )
        
        if output:
            output_path = Path(output)
            if output_path.suffix.lower() == '.json':
                import json
                with open(output_path, 'w') as f:
                    json.dump(headers, f, indent=2)
                if verbose:
                    click.echo(f"Results saved to {output}")
            else:
                click.echo(f"Unsupported output format: {output_path.suffix}")
                return {}
        
        return headers
        
    except Exception as e:
        if verbose:
            import traceback
            traceback.print_exc()
        click.echo(f"Error: {str(e)}", err=True)
        return {}


@cli.command()
@click.argument('query')
@click.option('--output', '-o', type=click.Path(), help='Output file (JSON)')
@click.option('--headless/--no-headless', default=True, help='Run browser in headless mode')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def search(query: str, output: Optional[str], headless: bool, verbose: bool):
    """Search Google and extract headers from the results."""
    if verbose:
        click.echo(f"Starting Google search for: {query}")
        click.echo(f"Headless mode: {'enabled' if headless else 'disabled'}")
    
    # Set headless mode in environment
    os.environ['CHROME_HEADLESS'] = str(headless).lower()
    
    # Run the async function
    loop = asyncio.get_event_loop()
    
    try:
        if loop.is_running():
            # If we're in an async context, run the coroutine directly
            async def run():
                try:
                    return await _scrape_google_async(query, output, headless, verbose)
                except Exception as e:
                    click.echo(f"Error: {str(e)}", err=True)
                    return {}
            
            return asyncio.create_task(run())
    except RuntimeError:
        # No running event loop, use asyncio.run()
        return asyncio.run(_scrape_google_async(query, output, headless, verbose))


if __name__ == '__main__':
    cli()
