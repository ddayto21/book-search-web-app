import os
from dotenv import load_dotenv
from abc import ABC, abstractmethod

import httpx  # For making asynchronous HTTP requests
import asyncio  # For running asynchronous code
import json  # For parsing JSON responses
import requests  # For making synchronous HTTP requests

from typing import AsyncGenerator, Generator, List, Dict, Optional


# -----------------------------------------------------------------------------
# A client designed to interact with the DeepSeek API.
# It supports both asynchronous and synchronous streaming of model responses.
# -----------------------------------------------------------------------------
class DeepSeekAPIClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com/v1/chat/completions",
    ):

        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not provided or set in DEEPSEEK_API_KEY environment variable"
            )
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def get_token_balance(self) -> dict:
        """
        Query the available token balance from the DeepSeek API.

        Returns:
            dict: A dictionary containing the token balance information.
        """

        balance_url = "https://api.deepseek.com/user/balance"

        try:
            response = requests.get(balance_url, headers=self.headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()  # Return the JSON response
        except requests.exceptions.RequestException as e:
            print(f"Error querying token balance: {e}")
            return {"error": str(e)}

    async def async_stream(
        self, model: str, messages: List[Dict], temperature: float
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronous generator that streams responses from the DeepSeek API.

        This method sends a POST request to the DeepSeek API with the specified
        model, messages, and temperature parameters. It then listens for the streamed
        response, processes each incoming line, and yields chunks of text as they
        arrive.

        Args:
            model (str): The DeepSeek model identifier (e.g., "deepseek-chat").
            messages (List[Dict]): A list of messages forming the conversation history.
                                   Each message is a dict with keys like "role" and "content".
            temperature (float): Controls the randomness of the model's response.

        Yields:
            str: Chunks of generated text from the API as they arrive, plus a final "[DONE]" message
                 when the stream has finished.


        """
        # Create an asynchronous HTTP client to manage the connection.

        async with httpx.AsyncClient(
            http2=True,
            timeout=httpx.Timeout(connect=10.0, read=None, write=10.0, pool=10.0),
        ) as client:
            # Send a POST request with streaming enabled. The API will send back lines of data.
            async with client.stream(
                "POST",
                self.base_url,
                headers=self.headers,
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "stream": True,  # Enable streaming mode in the request.
                },
            ) as response:
                # Raise an error if the request was unsuccessful.
                response.raise_for_status()

                # Read each line in the streamed response.
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            # Strip the "data: " prefix and parse JSON.
                            json_data = json.loads(line[6:])
                            # Extract 'content' from the first choice's delta.
                            chunk = json_data["choices"][0]["delta"].get("content", "")
                            if chunk:
                                yield chunk
                        except json.JSONDecodeError:
                            # If parsing fails, skip this line.
                            continue
                yield "[DONE]"  # Signal the end of the stream.

    def sync_stream(
        self, model: str, messages: List[Dict], temperature: float
    ) -> Generator[str, None, None]:
        """
        Synchronous generator that streams responses from DeepSeek.
        Yields:
            str: Chunks of generated text as they arrive.
        """
        # Make a POST request with streaming enabled using the synchronous requests library.
        with requests.post(
            self.base_url,
            headers=self.headers,
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": True,  # Request a streaming response.
            },
            stream=True,
        ) as response:
            response.raise_for_status()  # Raise an error if the request fails.
            # Iterate over each line in the streaming response.
            for line in response.iter_lines():
                if line:
                    # Convert bytes to string.
                    decoded_line = line.decode("utf-8")
                    if decoded_line.startswith("data: "):
                        try:
                            # Parse the JSON data in the line.
                            json_data = json.loads(decoded_line[6:])
                            #  Extract the text content from the response payload.
                            chunk = json_data["choices"][0]["delta"].get("content", "")
                            if chunk:
                                yield chunk  # Yield the chunk.
                        except json.JSONDecodeError:
                            # Skip any lines that are not valid JSON.
                            continue


# -----------------------------------------------------------------------------
# Helper function to read a multi-line prompt.
# The user can type multiple lines. When finished, they type '/send' on a new line.
# -----------------------------------------------------------------------------
def read_multiline_prompt() -> str:
    """
    Read multi-line input from the user until '/send' is entered on a new line.
    Returns:
        The full prompt as a single string.
    """
    print("Enter your prompt (type '/send' on a new line when finished):")
    lines = []
    while True:
        line = input()
        # When user types '/send', end the input collection.
        if line.strip() == "/send":
            break
        lines.append(line)
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Main program entry point.
# This section sets up an interactive REPL so you can ask multiple questions.
#
# Example to run the program in the terminal:
#   python3 app/clients/llm_client.py --model deepseek-chat --temperature 0.9 --async-mode
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import sys

    def parse_args():
        """
        Parse command-line arguments.
        Options:
            --model: Select the DeepSeek model (default: deepseek-chat).
            --temperature: Set the temperature (default: 0.7).
            --async-mode: Use asynchronous streaming (requires Python 3.7+).
        """
        parser = argparse.ArgumentParser(
            description="DeepSeek CLI Client - Chat with DeepSeek models"
        )
        parser.add_argument(
            "--model",
            type=str,
            default="deepseek-chat",
            help="Model to use (default: deepseek-chat)",
        )
        parser.add_argument(
            "--temperature",
            type=float,
            default=0.7,
            help="Temperature parameter (default: 0.7)",
        )
        parser.add_argument(
            "--async-mode",
            action="store_true",
            help="Use asynchronous mode (requires Python 3.7+)",
        )
        return parser.parse_args()

    # Load environment variables from the .env file.
    load_dotenv()
    args = parse_args()

    # Prompt the user to enter a prompt interactively in the terminal.
    # user_prompt = input("Enter your prompt: ")
    # # Build the messages list expected by the API.
    # messages = [{"role": "user", "content": user_prompt}]

    # Create an instance of the DeepSeekAPIClient.
    # The API key is loaded from the environment if not provided.
    client = DeepSeekAPIClient()
    # Query and display the token balance
    token_balance = client.get_token_balance()
    print(f"Token Balance: {token_balance}")
    try:
        # If asynchronous mode is enabled, run the async REPL.
        if args.async_mode:

            async def run_async_repl():
                while True:
                    # Prompt the user to enter their question.
                    # user_input = input("Enter your prompt (or type 'quit' to exit): ")
                    user_input = read_multiline_prompt()
                    if user_input.strip().lower() == "quit":
                        print("Exiting interactive session.")
                        break
                    # Build the messages list expected by the API.
                    messages = [{"role": "user", "content": user_input}]
                    print("\n--- Answer ---")
                    # Stream the response asynchronously, printing each chunk as it arrives.
                    async for chunk in client.async_stream(
                        model=args.model,
                        messages=messages,
                        temperature=args.temperature,
                    ):
                        print(chunk, end="", flush=True)
                    print("\n--------------\n")

            asyncio.run(run_async_repl())
        else:
            # Synchronous REPL loop.
            while True:
                try:
                    user_input = input("Enter your prompt (or type 'quit' to exit): ")
                except KeyboardInterrupt:
                    print("\nExiting interactive session.")
                    break
                if user_input.strip().lower() == "quit":
                    print("Exiting interactive session.")
                    break
                messages = [{"role": "user", "content": user_input}]
                print("\n--- Answer ---")
                # Stream the response synchronously, printing each chunk as it arrives.
                for chunk in client.sync_stream(
                    model=args.model, messages=messages, temperature=args.temperature
                ):
                    print(chunk, end="", flush=True)
                print("\n--------------\n")
    except KeyboardInterrupt:
        # If the user presses Ctrl+C, handle the interruption gracefully.
        print("\n\nOperation interrupted by user")
        sys.exit(0)
