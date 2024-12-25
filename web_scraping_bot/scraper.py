import asyncio
import csv
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from web_scraping_bot import WebScrapingBot
import pandas as pd
import requests

logger = logging.getLogger(__name__)

class ScrapingChatbot:
    def __init__(self):
        """Initialize the scraping chatbot."""
        self.console = Console()
        self.bot = WebScrapingBot()
        self.current_content = None
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
    async def init_bot(self):
        """Initialize the WebScrapingBot asynchronously."""
        await self.bot.init_session()
        
    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape a URL and return the content."""
        try:
            logger.info(f"Initializing scraping for URL: {url}")
            await self.init_bot()
            
            if not url.startswith(('http://', 'https://')):
                raise ValueError("URL must start with http:// or https://")
            
            logger.info("Fetching webpage content...")
            page_source = await self.bot.scrape_webpage(url)
            if not page_source:
                raise Exception("Failed to get page content")
            
            logger.info("Extracting content from webpage...")
            self.current_content = self.bot._extract_main_content(page_source)
            if not self.current_content:
                raise Exception("Failed to extract content from page")
            
            logger.info("Content extraction successful")
            return self.current_content
            
        except ValueError as e:
            logger.error(f"Invalid URL format: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            if self.bot:
                try:
                    await self.bot.close_session()
                except Exception as close_error:
                    logger.error(f"Error closing session: {str(close_error)}")
            raise Exception(f"Failed to scrape URL: {str(e)}")
        
    def chat_with_groq(self, question: str) -> str:
        """Chat with Groq about the scraped content."""
        if not self.current_content:
            return "Please scrape a webpage first before asking questions."
            
        if not self.groq_api_key:
            return "Please set the GROQ_API_KEY environment variable."
            
        # Combine relevant content for context
        context = ""
        if self.current_content.get('paragraphs'):
            context += " ".join(self.current_content['paragraphs'])
        if self.current_content.get('lists'):
            for list_type in ['ordered', 'unordered']:
                for lst in self.current_content['lists'][list_type]:
                    context += " " + " ".join(lst)
                    
        if not context:
            return "No content available to answer questions."
            
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""Based on the following content, please answer the question. If the answer cannot be found in the content, say so.

Content: {context[:15000]}  # Limit context to 15k chars to avoid token limits

Question: {question}

Please provide a detailed, accurate answer based only on the content provided."""

            payload = {
                "model": "mixtral-8x7b-32768",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that provides accurate, detailed answers based on the given content."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1000,
                "top_p": 0.9
            }

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
            return "Failed to get a response from Groq."

        except Exception as e:
            return f"Error getting answer: {str(e)}"
        
    def export_data(self, data: List[Dict[str, Any]], format: str = 'csv') -> str:
        """Export scraped data to a file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'csv':
            filename = f'scraped_data_{timestamp}.csv'
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if data and len(data) > 0:
                    fieldnames = set()
                    for item in data:
                        fieldnames.update(self._flatten_dict(item).keys())
                    
                    writer = csv.DictWriter(f, fieldnames=list(fieldnames))
                    writer.writeheader()
                    for item in data:
                        writer.writerow(self._flatten_dict(item))
        else:
            filename = f'scraped_data_{timestamp}.xlsx'
            df = pd.DataFrame([self._flatten_dict(item) for item in data])
            df.to_excel(filename, index=False)
            
        return filename
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten a nested dictionary."""
        items: List = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                if v and isinstance(v[0], dict):
                    for i, item in enumerate(v):
                        items.extend(self._flatten_dict(item, f"{new_key}_{i}", sep=sep).items())
                else:
                    items.append((new_key, ', '.join(map(str, v))))
            else:
                items.append((new_key, v))
        return dict(items)
    
    async def run_interactive_session(self):
        """Run an interactive scraping session with enhanced UI."""
        try:
            rprint("[bold green]Welcome to the Web Scraping Chatbot![/bold green]")
            rprint("[yellow]Commands:[/yellow]")
            rprint("  [cyan]1. Enter a URL[/cyan] to scrape a webpage")
            rprint("  [cyan]2. Ask questions[/cyan] about the scraped content")
            rprint("  [cyan]3. Type 'exit'[/cyan] to quit\n")

            while True:
                try:
                    user_input = input("\n[bold blue]Enter URL, question, or command:[/bold blue] ")
                    
                    if user_input.lower() == 'exit':
                        rprint("[green]Thank you for using the Web Scraping Chatbot. Goodbye![/green]")
                        break

                    if user_input.startswith(('http://', 'https://')):
                        rprint("[yellow]Scraping webpage... Please wait.[/yellow]")
                        try:
                            content = await self.scrape_url(user_input)
                            
                            if content:
                                rprint("[green]✓ Content scraped successfully![/green]")
                                self._display_content(content)
                                
                                # Ask if user wants to export the data
                                export_choice = input("\nWould you like to export this data? (y/n): ")
                                if export_choice.lower() == 'y':
                                    format_choice = input("Choose export format (csv/excel) [default: csv]: ").lower() or 'csv'
                                    if format_choice in ['csv', 'excel']:
                                        filename = self.export_data([content], format_choice)
                                        rprint(f"[green]Data exported to: {filename}[/green]")
                                    else:
                                        rprint("[red]Invalid format choice. Skipping export.[/red]")
                                        
                                rprint("\n[yellow]You can now ask questions about the content![/yellow]")
                            else:
                                rprint("[red]✗ No content found on the webpage.[/red]")
                                
                        except Exception as e:
                            rprint(f"[red]Error while scraping: {str(e)}[/red]")
                    else:
                        # Treat input as a question
                        answer = self.chat_with_groq(user_input)
                        rprint(answer)

                except KeyboardInterrupt:
                    rprint("\n[yellow]Operation cancelled by user.[/yellow]")
                    continue
                except Exception as e:
                    rprint(f"[red]An error occurred: {str(e)}[/red]")
                    continue

        finally:
            if self.bot:
                await self.bot.close_session()
            
    def _display_content(self, content: Dict[str, Any]):
        """Display scraped content in a formatted way."""
        # Display title and meta description
        if content['title']:
            rprint(f"\n[bold cyan]Title:[/bold cyan] {content['title']}")
        if content['meta_description']:
            rprint(f"[bold cyan]Description:[/bold cyan] {content['meta_description']}")

        # Display headings
        if content['headings']:
            rprint("\n[bold magenta]Headings:[/bold magenta]")
            for level, headings in content['headings'].items():
                for heading in headings:
                    rprint(f"[cyan]{level}:[/cyan] {heading}")

        # Display paragraphs
        if content['paragraphs']:
            table = Table(title="[bold magenta]Main Content[/bold magenta]")
            table.add_column("Text", style="white", overflow="fold")
            for p in content['paragraphs'][:10]:
                table.add_row(p[:200] + '...' if len(p) > 200 else p)
            self.console.print(table)

        # Display other content based on user request
        rprint("\n[yellow]Available content sections:[/yellow]")
        sections = []
        if content['images']: sections.append("images")
        if content['links']: sections.append("links")
        if content['lists']['ordered'] or content['lists']['unordered']: sections.append("lists")
        if content['tables']: sections.append("tables")
        if any(content['contact_info'].values()): sections.append("contact_info")
        if content['social_links']: sections.append("social_links")
        
        rprint(f"[cyan]Type 'show <section>' to view: {', '.join(sections)}[/cyan]")

async def main():
    """Main execution function."""
    chatbot = ScrapingChatbot()
    await chatbot.run_interactive_session()

if __name__ == "__main__":
    asyncio.run(main())
