import argparse
import random
from core.utils.s3.handlers import BaseS3CommandHandler
from tasks5.utils.s3 import get_quote, save_quote_to_s3

class InspireHandler(BaseS3CommandHandler):
    """Handles fetching and optionally saving inspirational quotes."""

    def execute(self, args: argparse.Namespace):
        """
        Executes the quote fetching process using the provided arguments.
        """
        author = args.author if hasattr(args, 'author') else None
        success, quote_data = get_quote(author)
        
        if not success:
            print("Failed to fetch quote. Please check your internet connection and try again.")
            return
            
        if isinstance(quote_data, dict):
            if 'quote' in quote_data:
                author = quote_data['quote']['author']['name']
                quote = quote_data['quote']['content']
                print(f"\"{quote}\"")
                print(f"- {author}")
            elif 'data' in quote_data:
                if not quote_data:
                    print(f"No quotes found for author: '{author}'")
                    return
                quote = random.choice(quote_data['data'])['content']
                print(f'\"{quote}\"')
                print(f"- {author}")

        quote_data = {
            'author': author,
            'quote': quote
        }
            
        if hasattr(args, 'save') and args.save and hasattr(args, 'bucket_name') and args.bucket_name:
            save_success, filename = save_quote_to_s3(self.client, quote_data, args.bucket_name, author)
            
            if save_success:
                print(f"Quote saved to s3://{args.bucket_name}/{filename}")
            else:
                print(f"Failed to save quote to bucket '{args.bucket_name}'.")
