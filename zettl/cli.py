# cli.py
import click
import os
from datetime import datetime
import time
from typing import Optional
from zettl.notes import Notes
from zettl.graph import NoteGraph
from zettl.llm import LLMHelper
from zettl.config import APP_NAME, APP_VERSION
from zettl.formatting import ZettlFormatter,Colors
import re

# Initialize the notes manager, graph manager and LLM helper
notes_manager = Notes()
graph_manager = NoteGraph()
llm_helper = LLMHelper()

# Define the function that both commands will use
def create_new_note(content, tag, link=None):
    """Create a new note with the given content and optional tags."""
    try:
        note_id = notes_manager.create_note(content)
        click.echo(f"Created note #{note_id}")
        
        # Add tags if provided
        if tag:
            for t in tag:
                try:
                    notes_manager.add_tag(note_id, t)
                    click.echo(f"Added tag '{t}' to note #{note_id}")
                except Exception as e:
                    click.echo(f"Warning: Could not add tag '{t}': {str(e)}", err=True)
        
        # Create link if provided
        if link:
            try:
                notes_manager.create_link(note_id, link)
                click.echo(f"Created link from #{note_id} to #{link}")
            except Exception as e:
                click.echo(f"Warning: Could not create link to note #{link}: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Error creating note: {str(e)}", err=True)


@click.group()
@click.version_option(version=APP_VERSION)
def cli():
    """A Zettelkasten-style note-taking CLI tool."""
    pass

@cli.command()
def commands():
    """Show all available commands with examples."""
    commands = [
        {
            "name": "workflow",
            "description": "Show an example workflow of using zettl",
            "example": "zettl workflow"
        },
        {
            "name": "new",
            "description": "Create a new note with the given content",
            "example": "zettl new \"This is a new note about an interesting concept\"\n"
                    "zettl new \"Note with tag and link\" --tag concept --link 22a4b"
        },
        {
            "name": "list",
            "description": "List recent notes",
            "example": "zettl list --limit 5\n"
                    "zettl list --full  # Shows full content with tags"
        },
        {
            "name": "show",
            "description": "Display note content",
            "example": "zettl show 22a4b"
        },
        {
            "name": "link",
            "description": "Create link between notes",
            "example": "zettl link 22a4b 18c3d"
        },
        {
            "name": "tags",
            "description": "Show or add tags to a note",
            "example": "zettl tags 22a4b\nzettl tags 22a4b \"concept\""
        },
        {
            "name": "search",
            "description": "Search for notes containing text",
            "example": "zettl search \"concept\"\n"
                    "zettl search -t concept --full  # Search by tag with full content\n"
                    "zettl search \"concept\" +t done  # Exclude notes with 'done' tag"
        },
        {
            "name": "related",
            "description": "Show notes connected to this note",
            "example": "zettl related 22a4b"
        },
        {
            "name": "graph",
            "description": "Generate a graph visualization of notes",
            "example": "zettl graph 22a4b --output graph.json --depth 2"
        },
        {
            "name": "llm",
            "description": "Use Claude AI to analyze and enhance notes",
            "example": "zettl llm 22a4b --action summarize  # Summarize a note\n"
                    "zettl llm 22a4b --action connect    # Find connections to other notes\n"
                    "zettl llm 22a4b --action tags       # Suggest tags for a note\n"
                    "zettl llm 22a4b --action expand     # Create expanded version of a note\n"
                    "zettl llm 22a4b --action concepts   # Extract key concepts from a note\n"
                    "zettl llm 22a4b --action questions  # Generate questions based on a note\n"
                    "zettl llm 22a4b --action critique   # Get constructive feedback on a note"
        },
        {
            "name": "todos",
            "description": "List all notes tagged with 'todo' grouped by category",
            "example": "zettl todos  # Show active todos\n"
                    "zettl todos --all  # Show all todos (active and completed)\n"
                    "zettl todos --donetoday  # Show todos completed today\n"
                    "zettl todos --cancel  # Show canceled todos\n"
                    "zettl todos --tag work  # Filter todos by tag"
        },
        {
            "name": "delete",
            "description": "Delete a note and its associated data",
            "example": "zettl delete 22a4b\nzettl delete 22a4b --keep-tags"
        },
        {
            "name": "untag",
            "description": "Remove a tag from a note",
            "example": "zettl untag 22a4b \"concept\""
        },
        {
            "name": "unlink",
            "description": "Remove a link between two notes",
            "example": "zettl unlink 22a4b 18c3d"
        }
    ]
    
    # Terminal colors for better readability
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    header = f"{GREEN}{BOLD}{APP_NAME} v{APP_VERSION}{RESET} - A Zettelkasten-style note-taking CLI tool"
    
    # Calculate the width of the terminal
    try:
        # Try to get terminal width, fallback to 80 if not available
        import shutil
        terminal_width = shutil.get_terminal_size().columns
    except:
        terminal_width = 80
    
    # Print header with decorative border
    click.echo("=" * terminal_width)
    click.echo(header.center(terminal_width))
    click.echo("=" * terminal_width)
    click.echo("")
    
    # Group commands by type
    click.echo(f"{BOLD}Getting Started:{RESET}")
    starter_commands = ["workflow"]
    
    click.echo(f"{BOLD}Core Commands:{RESET}")
    core_commands = ["new", "list", "show", "search"]
    
    click.echo(f"{BOLD}Connection Commands:{RESET}")
    connection_commands = ["link", "related", "graph"]
    
    click.echo(f"{BOLD}Organizational Commands:{RESET}")
    org_commands = ["tags"]
    
    click.echo(f"{BOLD}AI-Powered Commands:{RESET}")
    ai_commands = ["llm"]
    
    # Function to display command details
    def display_command(cmd_name):
        cmd = next((cmd for cmd in commands if cmd["name"] == cmd_name), None)
        if cmd:
            cmd_header = f"{YELLOW}{BOLD}{cmd['name']}{RESET} - {cmd['description']}"
            click.echo(f"  {cmd_header}")
            examples = cmd["example"].split("\n")
            for example in examples:
                click.echo(f"    {BLUE}→{RESET} {example}")
            click.echo("")
    
    # Display commands by group
    for cmd_name in starter_commands:
        display_command(cmd_name)

    for cmd_name in core_commands:
        display_command(cmd_name)
        
    for cmd_name in connection_commands:
        display_command(cmd_name)
        
    for cmd_name in org_commands:
        display_command(cmd_name)
        
    for cmd_name in ai_commands:
        display_command(cmd_name)
        
    # Display footer
    click.echo("=" * terminal_width)
    click.echo(f"{BOLD}For more details, run:{RESET} zettl COMMAND --help")
    click.echo("=" * terminal_width)

@cli.command()
@click.argument('content')
@click.option('--tag', '-t', multiple=True, help='Tag(s) to add to the new note')
@click.option('--link', '-l', help='Note ID to link this note to')
def new(content, tag, link):
    """Create a new note with the given content and optional tags."""
    create_new_note(content, tag, link)


@cli.command()
@click.argument('content')
@click.option('--tag', '-t', multiple=True, help='Tag(s) to add to the new note')
@click.option('--link', '-l', help='Note ID to link this note to')
def add(content, tag, link):
    """Create a new note with the given content and optional tags. Alias for 'new'."""
    create_new_note(content, tag, link)

# Update the list command
@cli.command()
@click.option('--limit', '-l', default=10, help='Number of notes to display')
@click.option('--full', '-f', is_flag=True, help='Show full content of notes')
@click.option('--compact', '-c', is_flag=True, help='Show very compact list (IDs only)')
def list(limit, full, compact):
    """List recent notes with formatting options."""
    try:
        notes = notes_manager.list_notes(limit)
        if not notes:
            click.echo("No notes found.")
            return
            
        click.echo(ZettlFormatter.header(f"Recent Notes (showing {len(notes)} of {len(notes)})"))
        
        for note in notes:
            note_id = note['id']
            created_at = notes_manager.format_timestamp(note['created_at'])
            
            if compact:
                # Very compact mode - just IDs
                click.echo(ZettlFormatter.note_id(note_id))
            elif full:
                # Full content mode
                click.echo(ZettlFormatter.format_note_display(note, notes_manager))
                
                # Add tags if there are any
                try:
                    tags = notes_manager.get_tags(note_id)
                    if tags:
                        click.echo(f"Tags: {', '.join([ZettlFormatter.tag(t) for t in tags])}")
                except Exception:
                    pass
                
                click.echo()  # Extra line between notes
            else:
                # Default mode - ID, timestamp, and preview
                formatted_id = ZettlFormatter.note_id(note_id)
                formatted_time = ZettlFormatter.timestamp(created_at)
                content_preview = note['content'][:50] + "..." if len(note['content']) > 50 else note['content']
                click.echo(f"{formatted_id} [{formatted_time}]: {content_preview}")
    except Exception as e:
        click.echo(ZettlFormatter.error(str(e)), err=True)

@cli.command()
@click.argument('note_id')
def show(note_id):
    """Display note content."""
    try:
        note = notes_manager.get_note(note_id)
        click.echo(ZettlFormatter.format_note_display(note, notes_manager))
        
        # Show tags if any
        try:
            tags = notes_manager.get_tags(note_id)
            if tags:
                click.echo(f"Tags: {', '.join(tags)}")
        except Exception:
            pass
    except Exception as e:
        click.echo(ZettlFormatter.error(str(e)), err=True)

@cli.command()
@click.argument('source_id')
@click.argument('target_id')
@click.option('--context', '-c', default="", help='Optional context for the link')
def link(source_id, target_id, context):
    """Create link between notes."""
    try:
        notes_manager.create_link(source_id, target_id, context)
        click.echo(f"Created link from #{source_id} to #{target_id}")
    except Exception as e:
        click.echo(f"Error creating link: {str(e)}", err=True)

@cli.command()
@click.argument('note_id', required=False)
@click.argument('tag', required=False)
def tags(note_id, tag):
    """Show or add tags to a note. If no note_id is provided, list all tags."""
    try:
        # If no note_id is provided, list all tags
        if not note_id:
            tags_with_counts = notes_manager.get_all_tags_with_counts()
            if tags_with_counts:
                click.echo(ZettlFormatter.header(f"All Tags (showing {len(tags_with_counts)})"))
                for tag_info in tags_with_counts:
                    formatted_tag = ZettlFormatter.tag(tag_info['tag'])
                    click.echo(f"{formatted_tag} ({tag_info['count']} notes)")
            else:
                click.echo(ZettlFormatter.warning("No tags found."))
            return
            
        # If a tag was provided, add it
        if tag:
            notes_manager.add_tag(note_id, tag)
            click.echo(f"Added tag '{tag}' to note #{note_id}")
            
        # Show all tags for the note
        tags = notes_manager.get_tags(note_id)
        if tags:
            click.echo(f"Tags for note #{note_id}: {', '.join([ZettlFormatter.tag(t) for t in tags])}")
        else:
            click.echo(f"No tags for note #{note_id}")
    except Exception as e:
        click.echo(ZettlFormatter.error(str(e)), err=True)

@cli.command()
@click.argument('query', required=False)
@click.option('--tag', '-t', help='Search for notes with this tag')
@click.option('--exclude-tag', '+t', help='Exclude notes with this tag')
@click.option('--full', '-f', is_flag=True, help='Show full content of matching notes')
def search(query, tag, exclude_tag, full):
    """Search for notes containing text or with specific tag."""
    try:
        results = []
        
        if tag:
            # Search by tag inclusion
            notes = notes_manager.get_notes_by_tag(tag)
            if not notes:
                click.echo(ZettlFormatter.warning(f"No notes found with tag '{tag}'"))
                return
                
            click.echo(ZettlFormatter.header(f"Found {len(notes)} notes with tag '{tag}':"))
            results = notes
        elif query:
            # Search by content
            notes = notes_manager.search_notes(query)
            if not notes:
                click.echo(ZettlFormatter.warning(f"No notes found containing '{query}'"))
                return
                
            click.echo(ZettlFormatter.header(f"Found {len(notes)} notes containing '{query}':"))
            results = notes
        else:
            # No search criteria specified, use a larger set
            results = notes_manager.list_notes(limit=50)
            click.echo(ZettlFormatter.header(f"Listing notes (showing {len(results)}):"))
        
        # Filter out excluded tags if specified
        if exclude_tag:
            # Get IDs of notes with the excluded tag
            excluded_notes = notes_manager.get_notes_by_tag(exclude_tag)
            excluded_ids = {note['id'] for note in excluded_notes}
            
            # Filter out notes with the excluded tag
            original_count = len(results)
            results = [note for note in results if note['id'] not in excluded_ids]
            
            # Inform user about filtering
            if original_count != len(results):
                click.echo(ZettlFormatter.warning(f"Excluded {original_count - len(results)} notes with tag '{exclude_tag}'"))
        
        # Display the final results
        if not results:
            click.echo(ZettlFormatter.warning("No notes match your criteria after filtering."))
            return
            
        for note in results:
            if full:
                # Full content mode
                click.echo(ZettlFormatter.format_note_display(note, notes_manager))
                
                # Add tags if there are any
                try:
                    tags = notes_manager.get_tags(note['id'])
                    if tags:
                        click.echo(f"Tags: {', '.join([ZettlFormatter.tag(t) for t in tags])}")
                except Exception:
                    pass
                
                click.echo()  # Extra line between notes
            else:
                # Preview mode
                content_preview = note['content'][:50] + "..." if len(note['content']) > 50 else note['content']
                if query:
                    # Highlight the query in the preview
                    pattern = re.compile(re.escape(query), re.IGNORECASE)
                    content_preview = pattern.sub(f"{Colors.YELLOW}\\g<0>{Colors.RESET}", content_preview)
                
                formatted_id = ZettlFormatter.note_id(note['id'])
                click.echo(f"{formatted_id}: {content_preview}")
    except Exception as e:
        click.echo(ZettlFormatter.error(str(e)), err=True)

@cli.command()
@click.argument('note_id')
@click.option('--full', '-f', is_flag=True, help='Show full content of related notes')
def related(note_id, full):
    """Show notes connected to this note with improved formatting."""
    try:
        # First, show the source note
        try:
            source_note = notes_manager.get_note(note_id)
            click.echo(ZettlFormatter.header(f"Source Note"))
            click.echo(ZettlFormatter.format_note_display(source_note, notes_manager))
            click.echo("\n")  # Extra space after source note
        except Exception as e:
            click.echo(ZettlFormatter.warning(f"Could not display source note: {str(e)}"))
        
        # Now show related notes
        related_notes = notes_manager.get_related_notes(note_id)
        if not related_notes:
            click.echo(ZettlFormatter.warning(f"No notes connected to note #{note_id}"))
            return
            
        click.echo(ZettlFormatter.header(f"Connected Notes ({len(related_notes)} total)"))
        
        for note in related_notes:
            if full:
                # Full content mode
                click.echo(ZettlFormatter.format_note_display(note, notes_manager))
                click.echo()  # Extra line between notes
            else:
                # Preview mode
                content_preview = note['content'][:50] + "..." if len(note['content']) > 50 else note['content']
                formatted_id = ZettlFormatter.note_id(note['id'])
                click.echo(f"{formatted_id}: {content_preview}")
    except Exception as e:
        click.echo(ZettlFormatter.error(str(e)), err=True)

@cli.command()
@click.argument('note_id', required=False)
@click.option('--output', '-o', default='zettl_graph.json', help='Output file for graph data')
@click.option('--depth', '-d', default=2, help='How many levels of connections to include')
def graph(note_id, output, depth):
    """Generate a graph visualization of notes and their connections."""
    try:
        file_path = graph_manager.export_graph(output, note_id, depth)
        click.echo(f"Graph data exported to {file_path}")
        click.echo("You can visualize this data using a graph visualization tool.")
    except Exception as e:
        click.echo(f"Error generating graph: {str(e)}", err=True)

@cli.command()
@click.argument('note_id')
@click.option('--action', '-a', 
              type=click.Choice(['summarize', 'connect', 'tags', 'expand', 'concepts', 'questions', 'critique']), 
              default='summarize', 
              help='LLM action to perform')
@click.option('--count', '-c', default=3, help='Number of results to return for tags/connections/concepts/questions')
@click.option('--show-source', '-s', is_flag=True, help='Show the source note before analysis')
def llm(note_id, action, count, show_source):
    """Use Claude AI to analyze and enhance notes."""
    try:
        # Show the source note if requested
        if show_source:
            try:
                source_note = notes_manager.get_note(note_id)
                click.echo(ZettlFormatter.header("Source Note"))
                click.echo(ZettlFormatter.format_note_display(source_note, notes_manager))
                click.echo("\n")  # Extra space after source note
            except Exception as e:
                click.echo(ZettlFormatter.warning(f"Could not display source note: {str(e)}"))
        
        if action == 'summarize':
            click.echo(ZettlFormatter.header(f"AI Summary for Note #{note_id}"))
            # Show a spinner while the LLM is working
            with click.progressbar(length=100, label='Generating summary') as bar:
                for i in range(100):
                    bar.update(1)
                    time.sleep(0.01)
                summary = llm_helper.summarize_note(note_id)
            
            click.echo(f"\n{Colors.YELLOW}{summary}{Colors.RESET}")
            
        elif action == 'connect':
            click.echo(ZettlFormatter.header(f"AI-Suggested Connections for Note #{note_id}"))
            
            # Show a spinner while the LLM is working
            with click.progressbar(length=100, label='Finding connections') as bar:
                for i in range(100):
                    bar.update(1)
                    time.sleep(0.01)
                connections = llm_helper.generate_connections(note_id, count)
            
            if not connections:
                click.echo(ZettlFormatter.warning("No potential connections found."))
                return
                
            for conn in connections:
                conn_id = conn['note_id']
                formatted_id = ZettlFormatter.note_id(conn_id)
                click.echo(f"\n{formatted_id}")
                click.echo(f"  {Colors.YELLOW}{conn['explanation']}{Colors.RESET}")
                
                # Try to show a preview of the connected note
                try:
                    conn_note = notes_manager.get_note(conn_id)
                    content_preview = conn_note['content'][:100] + "..." if len(conn_note['content']) > 100 else conn_note['content']
                    click.echo(f"  {Colors.CYAN}Preview:{Colors.RESET} {content_preview}")
                    
                    # Add option to link notes
                    if click.confirm(f"\nCreate link from #{note_id} to #{conn_id}?"):
                        notes_manager.create_link(note_id, conn_id, conn['explanation'])
                        click.echo(ZettlFormatter.success(f"Created link from #{note_id} to #{conn_id}"))
                except Exception:
                    pass
            
        elif action == 'tags':
            click.echo(ZettlFormatter.header(f"AI-Suggested Tags for Note #{note_id}"))
            
            # Show a spinner while the LLM is working
            with click.progressbar(length=100, label='Generating tags') as bar:
                for i in range(100):
                    bar.update(1)
                    time.sleep(0.01)
                tags = llm_helper.suggest_tags(note_id, count)
            
            if not tags:
                click.echo(ZettlFormatter.warning("No tags suggested."))
                return
                
            click.echo("\nSuggested tags:")
            for tag in tags:
                formatted_tag = ZettlFormatter.tag(tag)
                click.echo(f"{formatted_tag}")
                
            # Ask if user wants to add these tags
            if click.confirm("\nWould you like to add these tags to the note?"):
                for tag in tags:
                    try:
                        notes_manager.add_tag(note_id, tag)
                        click.echo(ZettlFormatter.success(f"Added tag '{tag}' to note #{note_id}"))
                    except Exception as e:
                        click.echo(ZettlFormatter.error(f"Error adding tag '{tag}': {str(e)}"), err=True)

        elif action == 'expand':
            click.echo(ZettlFormatter.header(f"AI-Expanded Version of Note #{note_id}"))
            
            # Show a spinner while the LLM is working
            with click.progressbar(length=100, label='Expanding note') as bar:
                for i in range(100):
                    bar.update(1)
                    time.sleep(0.01)
                expanded_content = llm_helper.expand_note(note_id)
            
            click.echo(f"\n{Colors.YELLOW}{expanded_content}{Colors.RESET}")
            
            # Ask if user wants to create a new note with the expanded content
            if click.confirm("\nCreate a new note with this expanded content?"):
                try:
                    # Create new note with expanded content
                    new_note_id = notes_manager.create_note(expanded_content)
                    click.echo(ZettlFormatter.success(f"Created expanded note #{new_note_id}"))
                    
                    # Create link from original to expanded note
                    notes_manager.create_link(note_id, new_note_id, "Expanded version")
                    click.echo(ZettlFormatter.success(f"Linked original #{note_id} to expanded #{new_note_id}"))
                    
                    # Copy tags from original note to new note
                    try:
                        original_tags = notes_manager.get_tags(note_id)
                        for tag in original_tags:
                            notes_manager.add_tag(new_note_id, tag)
                        if original_tags:
                            click.echo(ZettlFormatter.success(f"Copied {len(original_tags)} tags to new note"))
                    except Exception:
                        pass
                except Exception as e:
                    click.echo(ZettlFormatter.error(f"Error creating expanded note: {str(e)}"), err=True)
        
        elif action == 'concepts':
            click.echo(ZettlFormatter.header(f"Key Concepts from Note #{note_id}"))
            
            # Show a spinner while the LLM is working
            with click.progressbar(length=100, label='Extracting concepts') as bar:
                for i in range(100):
                    bar.update(1)
                    time.sleep(0.01)
                concepts = llm_helper.extract_key_concepts(note_id, count)
            
            if not concepts:
                click.echo(ZettlFormatter.warning("No key concepts identified."))
                return
                
            for i, concept in enumerate(concepts, 1):
                click.echo(f"\n{Colors.BOLD}{Colors.CYAN}{i}. {concept['concept']}{Colors.RESET}")
                click.echo(f"   {Colors.YELLOW}{concept['explanation']}{Colors.RESET}")
                
                # Ask if user wants to create a new note for this concept
                if click.confirm(f"\nCreate a new note for the concept '{concept['concept']}'?"):
                    try:
                        # Prepare content for the new note
                        concept_content = f"{concept['concept']}\n\n{concept['explanation']}"
                        
                        # Create new note
                        new_note_id = notes_manager.create_note(concept_content)
                        click.echo(ZettlFormatter.success(f"Created concept note #{new_note_id}"))
                        
                        # Create link from original to concept note
                        notes_manager.create_link(note_id, new_note_id, f"Concept: {concept['concept']}")
                        click.echo(ZettlFormatter.success(f"Linked original #{note_id} to concept #{new_note_id}"))
                    except Exception as e:
                        click.echo(ZettlFormatter.error(f"Error creating concept note: {str(e)}"), err=True)
        
        elif action == 'questions':
            click.echo(ZettlFormatter.header(f"Thought-Provoking Questions from Note #{note_id}"))
            
            # Show a spinner while the LLM is working
            with click.progressbar(length=100, label='Generating questions') as bar:
                for i in range(100):
                    bar.update(1)
                    time.sleep(0.01)
                questions = llm_helper.generate_question_note(note_id, count)
            
            if not questions:
                click.echo(ZettlFormatter.warning("No questions generated."))
                return
                
            for i, question in enumerate(questions, 1):
                click.echo(f"\n{Colors.BOLD}{Colors.CYAN}{i}. {question['question']}{Colors.RESET}")
                click.echo(f"   {Colors.YELLOW}{question['explanation']}{Colors.RESET}")
                
                # Ask if user wants to create a new note for this question
                if click.confirm(f"\nCreate a new note for this question?"):
                    try:
                        # Prepare content for the new note
                        question_content = f"{question['question']}\n\n{question['explanation']}"
                        
                        # Create new note
                        new_note_id = notes_manager.create_note(question_content)
                        click.echo(ZettlFormatter.success(f"Created question note #{new_note_id}"))
                        
                        # Create link from original to question note
                        notes_manager.create_link(note_id, new_note_id, "Question derived from this note")
                        click.echo(ZettlFormatter.success(f"Linked original #{note_id} to question #{new_note_id}"))
                    except Exception as e:
                        click.echo(ZettlFormatter.error(f"Error creating question note: {str(e)}"), err=True)
        
        elif action == 'critique':
            click.echo(ZettlFormatter.header(f"AI Critique of Note #{note_id}"))
            
            # Show a spinner while the LLM is working
            with click.progressbar(length=100, label='Analyzing note') as bar:
                for i in range(100):
                    bar.update(1)
                    time.sleep(0.01)
                critique = llm_helper.critique_note(note_id)
            
            # Display strengths
            if critique['strengths']:
                click.echo(f"\n{Colors.BOLD}{Colors.GREEN}Strengths:{Colors.RESET}")
                for strength in critique['strengths']:
                    click.echo(f"  • {strength}")
            
            # Display weaknesses
            if critique['weaknesses']:
                click.echo(f"\n{Colors.BOLD}{Colors.YELLOW}Areas for Improvement:{Colors.RESET}")
                for weakness in critique['weaknesses']:
                    click.echo(f"  • {weakness}")
            
            # Display suggestions
            if critique['suggestions']:
                click.echo(f"\n{Colors.BOLD}{Colors.CYAN}Suggestions:{Colors.RESET}")
                for suggestion in critique['suggestions']:
                    click.echo(f"  • {suggestion}")
            
            # If no structured feedback was generated
            if not (critique['strengths'] or critique['weaknesses'] or critique['suggestions']):
                click.echo(ZettlFormatter.warning("Could not generate structured feedback for this note."))
                
    except Exception as e:
        click.echo(ZettlFormatter.error(str(e)), err=True)

@cli.command()
@click.argument('note_id')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt')
@click.option('--keep-links', is_flag=True, help='Keep links to and from this note')
@click.option('--keep-tags', is_flag=True, help='Keep tags associated with this note')
def delete(note_id, force, keep_links, keep_tags):
    """Delete a note and its associated data."""
    try:
        # First get the note to show what will be deleted
        try:
            note = notes_manager.get_note(note_id)
            
            # Get related data counts for information
            try:
                tags = notes_manager.get_tags(note_id)
                related_notes = notes_manager.get_related_notes(note_id)
                tag_count = len(tags)
                link_count = len(related_notes)
            except Exception:
                tag_count = 0
                link_count = 0
                
            # Show preview of what will be deleted
            click.echo(ZettlFormatter.header(f"Note to delete: #{note_id}"))
            content_preview = note['content'][:100] + "..." if len(note['content']) > 100 else note['content']
            click.echo(f"Content: {content_preview}")
            click.echo(f"Associated tags: {tag_count}")
            click.echo(f"Connected notes: {link_count}")
            
        except Exception as e:
            if not force:
                click.echo(ZettlFormatter.warning(f"Could not retrieve note: {str(e)}"))
                if not click.confirm("Continue with deletion anyway?"):
                    click.echo("Deletion cancelled.")
                    return
        
        # Confirm deletion if not forced
        if not force and not click.confirm(f"Delete note #{note_id}?"):
            click.echo("Deletion cancelled.")
            return
        
        # Determine cascade setting based on flags
        cascade = not (keep_links and keep_tags)
        
        # Delete with custom handling if specific items should be kept
        if cascade and (keep_links or keep_tags):
            # Custom deletion flow
            if not keep_tags:
                notes_manager.delete_note_tags(note_id)
                click.echo(f"Deleted tags for note #{note_id}")
            
            if not keep_links:
                notes_manager.delete_note_links(note_id)
                click.echo(f"Deleted links for note #{note_id}")
            
            # Now delete the note itself (with cascade=False since we handled dependencies)
            notes_manager.delete_note(note_id, cascade=False)
        else:
            # Standard cascade deletion
            notes_manager.delete_note(note_id, cascade=cascade)
        
        click.echo(ZettlFormatter.success(f"Deleted note #{note_id}"))
        
    except Exception as e:
        click.echo(ZettlFormatter.error(f"Error deleting note: {str(e)}"), err=True)

@cli.command()
@click.argument('note_id')
@click.argument('tag')
def untag(note_id, tag):
    """Remove a tag from a note."""
    try:
        notes_manager.delete_tag(note_id, tag)
        click.echo(ZettlFormatter.success(f"Removed tag '{tag}' from note #{note_id}"))
    except Exception as e:
        click.echo(ZettlFormatter.error(f"Error removing tag: {str(e)}"), err=True)

@cli.command()
@click.argument('source_id')
@click.argument('target_id')
def unlink(source_id, target_id):
    """Remove a link between two notes."""
    try:
        notes_manager.delete_link(source_id, target_id)
        click.echo(ZettlFormatter.success(f"Removed link from note #{source_id} to note #{target_id}"))
    except Exception as e:
        click.echo(ZettlFormatter.error(f"Error removing link: {str(e)}"), err=True)

@cli.command()
@click.option('--donetoday', '-dt', is_flag=True, help='List todos that were completed today')
@click.option('--all', '-a', is_flag=True, help='Show all todos (both active and completed)')
@click.option('--cancel', '-c', is_flag=True, help='Show canceled todos')
@click.option('--tag', '-t', multiple=True, help='Filter todos by one or more additional tags')
def todos(donetoday, all, cancel, tag):
    """List all notes tagged with 'todo' grouped by category."""
    try:
        # If --all is specified, force done=True to include completed todos
        done = all
            
        # Get all notes tagged with 'todo'
        todo_notes = notes_manager.get_notes_by_tag('todo')
        
        if not todo_notes:
            click.echo(ZettlFormatter.warning("No todos found."))
            return
            
        # Get notes with 'done' tag added today
        done_today_ids = set()
        if donetoday:
            from datetime import datetime, timedelta
            today = datetime.now().date()
            
            # We need to directly query the tags table to check when the 'done' tag was added
            try:
                # Query tags table for 'done' tags created today
                tags_result = notes_manager.db.client.table('tags').select('note_id, created_at').eq('tag', 'done').execute()
                
                if tags_result.data:
                    for tag_data in tags_result.data:
                        note_id = tag_data.get('note_id')
                        created_at = tag_data.get('created_at', '')
                        
                        if note_id and created_at:
                            try:
                                # Parse the ISO format date
                                tag_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                                
                                # Check if tag was created today
                                if tag_date == today:
                                    done_today_ids.add(note_id)
                            except Exception:
                                # If date parsing fails, skip this tag
                                pass
            except Exception as e:
                click.echo(ZettlFormatter.warning(f"Could not determine todos completed today: {str(e)}"))
        
        # Apply filters if specified
        if tag:
            filters = [f.lower() for f in tag]
            filtered_notes = []
            
            for note in todo_notes:
                note_id = note['id']
                note_tags = [t.lower() for t in notes_manager.get_tags(note_id)]
                
                # Check if all filters are in the note's tags
                has_all_filters = True
                for f in filters:
                    if f not in note_tags:
                        has_all_filters = False
                        break
                
                if has_all_filters:
                    filtered_notes.append(note)
                    
            todo_notes = filtered_notes
            
            if not todo_notes:
                filter_str = "', '".join(tag)
                click.echo(ZettlFormatter.warning(f"No todos found with all tags: '{filter_str}'."))
                return
        
        # Group notes by their tags (categories)
        active_todos_by_category = {}
        done_todos_by_category = {}
        donetoday_todos_by_category = {}
        canceled_todos_by_category = {}  # New dict for canceled todos
        uncategorized_active = []
        uncategorized_done = []
        uncategorized_donetoday = []
        uncategorized_canceled = []  # New list for uncategorized canceled todos
        
        # Track unique note IDs to count them at the end
        unique_active_ids = set()
        unique_done_ids = set()
        unique_donetoday_ids = set()
        unique_canceled_ids = set()  # New set for canceled todos
        
        for note in todo_notes:
            note_id = note['id']
            # Get all tags for this note
            note_tags = notes_manager.get_tags(note_id)
            tags_lower = [t.lower() for t in note_tags]
            
            # Check if this is a done todo
            is_done = 'done' in tags_lower
            
            # Check if this is a canceled todo
            is_canceled = 'cancel' in tags_lower
            
            # Check if this is done today
            is_done_today = note_id in done_today_ids
            
            # Skip done todos if not explicitly included, unless they're done today and we want those
            if is_done and not done and not (is_done_today and donetoday):
                continue
                
            # Skip canceled todos if not explicitly requested
            if is_canceled and not cancel:
                continue
                
            # Track unique IDs
            if is_canceled:
                unique_canceled_ids.add(note_id)
            elif is_done_today and donetoday:
                unique_donetoday_ids.add(note_id)
            elif is_done:
                unique_done_ids.add(note_id)
            else:
                unique_active_ids.add(note_id)
            
            # Find category tags (everything except 'todo', 'done', and the filter tags)
            excluded_tags = ['todo', 'done', 'cancel']  # Added 'cancel' to exclusion list
            if tag:
                excluded_tags.extend([f.lower() for f in tag])
                
            categories = [t for t in note_tags if t.lower() not in excluded_tags]
            
            if not categories:
                # This todo has no category tags
                if is_canceled:
                    uncategorized_canceled.append(note)
                elif is_done_today and donetoday:
                    uncategorized_donetoday.append(note)
                elif is_done:
                    uncategorized_done.append(note)
                else:
                    uncategorized_active.append(note)
            else:
                # Add this note to each of its categories
                for category in categories:
                    if is_canceled:
                        if category not in canceled_todos_by_category:
                            canceled_todos_by_category[category] = []
                        canceled_todos_by_category[category].append(note)
                    elif is_done_today and donetoday:
                        if category not in donetoday_todos_by_category:
                            donetoday_todos_by_category[category] = []
                        donetoday_todos_by_category[category].append(note)
                    elif is_done:
                        if category not in done_todos_by_category:
                            done_todos_by_category[category] = []
                        done_todos_by_category[category].append(note)
                    else:
                        if category not in active_todos_by_category:
                            active_todos_by_category[category] = []
                        active_todos_by_category[category].append(note)
        
        # Build the header message
        header_parts = ["Todos"]
        if tag:
            filter_str = "', '".join(tag)
            header_parts.append(f"tagged with '{filter_str}'")
        
        # Display todos by category
        if (not active_todos_by_category and not uncategorized_active and 
            (not done or (not done_todos_by_category and not uncategorized_done)) and
            (not donetoday or (not donetoday_todos_by_category and not uncategorized_donetoday)) and
            (not cancel or (not canceled_todos_by_category and not uncategorized_canceled))):
            click.echo(ZettlFormatter.warning("No todos match your criteria."))
            return
            
        # Helper function to display a group of todos
        def display_todos_group(category_dict, uncategorized_list, header_text):
            if header_text:
                click.echo(header_text)
            
            if category_dict:
                for category, notes in sorted(category_dict.items()):
                    click.echo(f"\n{ZettlFormatter.tag(category)} ({len(notes)})")
                    
                    for note in notes:
                        formatted_id = ZettlFormatter.note_id(note['id'])
                        
                        # Format with indentation
                        content_lines = note['content'].split('\n')
                        click.echo(f"  {formatted_id}: {content_lines[0]}")
                        if len(content_lines) > 1:
                            for line in content_lines[1:]:
                                click.echo(f"      {line}")
                        click.echo("")  # Add an empty line between notes
            
            if uncategorized_list:
                click.echo("\nUncategorized")
                for note in uncategorized_list:
                    formatted_id = ZettlFormatter.note_id(note['id'])
                    
                    # Format with indentation
                    content_lines = note['content'].split('\n')
                    click.echo(f"  {formatted_id}: {content_lines[0]}")
                    if len(content_lines) > 1:
                        for line in content_lines[1:]:
                            click.echo(f"      {line}")
                    click.echo("")  # Add an empty line between notes
        
        # Display active todos first
        if active_todos_by_category or uncategorized_active:
            active_header = ZettlFormatter.header(f"Active {' '.join(header_parts)} ({len(unique_active_ids)} total)")
            display_todos_group(active_todos_by_category, uncategorized_active, active_header)
        
        # Display done today todos if requested
        if donetoday:
            if donetoday_todos_by_category or uncategorized_donetoday:
                donetoday_header = ZettlFormatter.header(f"Completed Today {' '.join(header_parts)} ({len(unique_donetoday_ids)} total)")
                click.echo(f"\n{donetoday_header}")
                display_todos_group(donetoday_todos_by_category, uncategorized_donetoday, "")
            else:
                click.echo(f"\n{ZettlFormatter.warning('No todos were completed today.')}")
        
        # Display all done todos if requested
        if done and (done_todos_by_category or uncategorized_done):
            # Exclude today's completed todos since they're shown in their own section
            if donetoday:
                # Filter out notes that are done today from the regular done section
                for category in list(done_todos_by_category.keys()):
                    done_todos_by_category[category] = [
                        note for note in done_todos_by_category[category] 
                        if note['id'] not in done_today_ids
                    ]
                    # Remove empty categories
                    if not done_todos_by_category[category]:
                        del done_todos_by_category[category]
                
                # Filter uncategorized done notes too
                uncategorized_done = [
                    note for note in uncategorized_done 
                    if note['id'] not in done_today_ids
                ]
            
            # Only show this section if there are notes to display after filtering
            if done_todos_by_category or uncategorized_done:
                done_header = ZettlFormatter.header(f"Completed {' '.join(header_parts)} ({len(unique_done_ids - unique_donetoday_ids)} total)")
                click.echo(f"\n{done_header}")
                display_todos_group(done_todos_by_category, uncategorized_done, "")
        
        # Display canceled todos if requested
        if cancel and (canceled_todos_by_category or uncategorized_canceled):
            canceled_header = ZettlFormatter.header(f"Canceled {' '.join(header_parts)} ({len(unique_canceled_ids)} total)")
            click.echo(f"\n{canceled_header}")
            display_todos_group(canceled_todos_by_category, uncategorized_canceled, "")
                
    except Exception as e:
        click.echo(ZettlFormatter.error(str(e)), err=True)

@cli.command()
def workflow():
    """Show an example workflow of using zettl."""
    # Colors for better readability
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    click.echo(f"\n{BOLD}{GREEN}Example Zettl Workflow{RESET}\n")
    click.echo("This guide demonstrates a typical Zettl workflow.\n")
    
    steps = [
        {
            "title": "Create a new note",
            "command": "zettl new \"The Feynman Technique is a mental model to convey information using concise thoughts and simple language.\"",
            "explanation": "This creates a new note and returns a unique ID (let's call it 22a4b)."
        },
        {
            "title": "Create another related note",
            "command": "zettl new \"Spaced repetition is a learning technique that involves increasing intervals of time between subsequent review of previously learned material.\"",
            "explanation": "This creates another note (let's call it 18c3d)."
        },
        {
            "title": "Create a note with a direct link",
            "command": "zettl new \"Using spaced repetition with the Feynman Technique enhances recall.\" --tag learning --link 22a4b",
            "explanation": "This creates a new note with a tag and links it directly to the Feynman Technique note."
        },
        {
            "title": "Link these two notes",
            "command": "zettl link 22a4b 18c3d",
            "explanation": "This creates a connection between the Feynman Technique note and the Spaced Repetition note."
        },
        {
            "title": "Add tags to your notes",
            "command": "zettl tags 22a4b \"learning-technique\"",
            "explanation": "This adds a tag to the first note for better organization."
        },
        {
            "title": "View note details",
            "command": "zettl show 22a4b",
            "explanation": "This displays the full content of the note, along with any tags."
        },
        {
            "title": "List all recent notes with full content",
            "command": "zettl list --full",
            "explanation": "This shows all your recent notes with their full content and tags."
        },
        {
            "title": "Find related notes",
            "command": "zettl related 22a4b",
            "explanation": "This shows notes connected to the Feynman Technique note."
        },
        {
            "title": "Generate AI suggestions",
            "command": "zettl llm 22a4b --action tags",
            "explanation": "This uses Claude AI to suggest relevant tags for your note."
        },
        {
            "title": "Visualize your note network",
            "command": "zettl graph --output my_notes.json",
            "explanation": "This exports a graph of your notes and their connections, which you can visualize with various tools."
        },
        {
            "title": "Search your notes with tags",
            "command": "zettl search \"technique\" --full",
            "explanation": "This finds all notes containing the word 'technique' and shows full content including tags."
        },
        {
            "title": "Manage todos with filtering",
            "command": "zettl todos --all --tag learning",
            "explanation": "This shows all todos (active and completed) that have the 'learning' tag."
        }
    ]
    
    for i, step in enumerate(steps, 1):
        click.echo(f"{BOLD}{YELLOW}Step {i}: {step['title']}{RESET}")
        click.echo(f"  {BLUE}Command:{RESET} {CYAN}{step['command']}{RESET}")
        click.echo(f"  {BLUE}What it does:{RESET} {step['explanation']}")
        click.echo("")
    
    click.echo(f"{BOLD}{GREEN}Additional Tips:{RESET}")
    click.echo("• Use the AI capabilities to find connections between notes you might have missed")
    click.echo("• Keep notes atomic - one idea per note")
    click.echo("• Focus on creating meaningful connections between notes")
    click.echo("• Use tags sparingly for high-level categorization")
    click.echo("• Regularly review and refine your note network")
    
if __name__ == '__main__':
    cli()