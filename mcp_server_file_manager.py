import os
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server with configuration
mcp = FastMCP(
    "File manager",  # Name of the MCP server
    instructions="You are a local file manager that can operate on the local file system.",
    host="0.0.0.0",  # Host address (0.0.0.0 allows connections from any IP)
    port=8006,  # Port number for the server
)

# Get default base path from environment variable or use current directory
BASE_PATH = os.environ.get("BASE_PATH", os.getcwd())
print(f"File Manager initialized with BASE_PATH: {BASE_PATH}")

# Get list of files and directories in a specified path
@mcp.tool()
async def get_local_file_list(path: str) -> str:
    try:
        if not path:
            return "Error: Path parameter is required. Please specify a path (use '.' for current directory)."
            
        # Resolve path relative to BASE_PATH for security
        if path == ".":
            full_path = BASE_PATH
        else:
            # Convert relative paths to absolute, but keep them within BASE_PATH
            # This prevents directory traversal attacks
            full_path = os.path.normpath(os.path.join(BASE_PATH, path))
            if not full_path.startswith(BASE_PATH):
                return f"Error: Path '{path}' is outside of allowed directory"

        if not os.path.exists(full_path):
            return f"Error: Path '{full_path}' does not exist"

        file_list = []
        file_list.append(f"Listing contents of: {full_path}")
        file_list.append("-" * 80)

        # Collect file/directory information
        for entry in os.scandir(full_path):
            stats = entry.stat()
            size = stats.st_size
            modified_time = datetime.fromtimestamp(stats.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # Convert size unit
            size_str = f"{size:,} bytes"
            if size > 1024 * 1024 * 1024:
                size_str = f"{size/(1024*1024*1024):.2f} GB"
            elif size > 1024 * 1024:
                size_str = f"{size/(1024*1024):.2f} MB"
            elif size > 1024:
                size_str = f"{size/1024:.2f} KB"

            # File/directory distinction
            type_str = "[DIR]" if entry.is_dir() else "[FILE]"

            # Generate result string
            file_info = f"{type_str} {entry.name:<50} {size_str:<15} {modified_time}"
            file_list.append(file_info)

        # Sort and return results
        return "\n".join(sorted(file_list[2:], key=lambda x: (not x.startswith("[DIR]"), x)))

    except Exception as e:
        return f"Error: {str(e)}"


# Write specified text to a file
@mcp.tool()
async def write_text_to_file(file_name: str, text: str) -> str:
    try:
        # Use BASE_PATH for file operations to keep files in the allowed area
        path = os.path.normpath(os.path.join(BASE_PATH, file_name))
        
        # Security check to prevent directory traversal
        if not path.startswith(BASE_PATH):
            return f"Error: Cannot write to '{file_name}' - outside of allowed directory"

        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

        result_text = f"Successfully wrote to file: {path}\n{text}"
        return result_text
    except Exception as e:
        return f"Error: {str(e)}"


# Read content of a file
@mcp.tool()
async def read_file_content(file_name: str) -> str:
    try:
        # Use BASE_PATH for file operations to keep files in the allowed area
        path = os.path.normpath(os.path.join(BASE_PATH, file_name))
        
        # Security check to prevent directory traversal
        if not path.startswith(BASE_PATH):
            return f"Error: Cannot read '{file_name}' - outside of allowed directory"
            
        if not os.path.exists(path):
            return f"Error: File '{file_name}' does not exist"
            
        if not os.path.isfile(path):
            return f"Error: '{file_name}' is not a file"

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return f"Content of '{file_name}':\n\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


if __name__ == "__main__":
    # Start the MCP server with stdio transport
    mcp.run(transport="stdio")