"""
Test Watson CLI: Simple CLI interface for testing IBM Granite functionality
"""

import click
import os
from langchain_ibm import WatsonxLLM
from rich.console import Console
from rich.prompt import Prompt
from dotenv import load_dotenv

console = Console()

def initialize_model():
    """Initialize the Granite model with environment settings"""
    load_dotenv()
    
    model_parameters = {
        "decoding_method": "greedy",
        "max_new_tokens": 1000,
        "min_new_tokens": 1,
        "temperature": 0.7,
        "repetition_penalty": 1.1
    }
    
    # Updated to match pydantic validation requirements
    model = WatsonxLLM(
        model_id="ibm/granite-3-8b-instruct",
        url=os.getenv("WATSONX_URL"),
        apikey=os.getenv("IBM_API_KEY"),
        project_id=os.getenv("PROJECT_ID"),
        params=model_parameters
    )
    
    return model

@click.group()
def cli():
    """Test Watson CLI: Test IBM Granite language model capabilities"""
    pass

@cli.command()
def chat():
    """Start an interactive chat session with the Granite model"""
    console.print("[bold green]Initializing IBM Granite model...[/]")
    try:
        model = initialize_model()
        console.print("[bold green]Model initialized! Start chatting (type 'exit' to quit)[/]")
        
        while True:
            query = Prompt.ask("\n[bold blue]You")
            if query.lower() == 'exit':
                break
                
            with console.status("[bold yellow]Thinking..."):
                response = model.invoke(query)
            
            console.print(f"\n[bold purple]Assistant[/]: {response}")
            
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/]")

@cli.command()
@click.argument('prompt')
def single_query(prompt):
    """Send a single query to the Granite model"""
    console.print("[bold green]Initializing IBM Granite model...[/]")
    try:
        model = initialize_model()
        
        with console.status("[bold yellow]Thinking..."):
            response = model.invoke(prompt)
            
        console.print(f"\n[bold purple]Assistant[/]: {response}")
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/]")

if __name__ == '__main__':
    cli()