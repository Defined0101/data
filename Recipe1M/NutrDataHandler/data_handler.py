from NutrDataHandler.data_parser import parser_main
from NutrDataHandler.data_reader import reader_main
import time

def handler_main():
    start_time = time.time()
    reader_main()
    print(f"Reading completed in {time.time() - start_time:.2f} seconds")

    start_time = time.time()
    parser_main()
    print(f"Parsing completed in {time.time() - start_time:.2f} seconds")

# Execute the main function when the script is run
if __name__ == "__main__":
    start_time = time.time()
    handler_main()
    print(f"Total processing completed in {time.time() - start_time:.2f} seconds")
