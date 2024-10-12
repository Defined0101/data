from NutrDataHandler.data_handler import handler_main
from EmptyDataHandler.data_parser import parser_main
import time

def main():
    start_time = time.time()
    handler_main()
    print(f"Nutrition dataset processing completed in {time.time() - start_time:.2f} seconds")

    start_time = time.time()
    parser_main()
    print(f"Empty dataset processing completed in {time.time() - start_time:.2f} seconds")

# Execute the main function when the script is run
if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"Total processing completed in {time.time() - start_time:.2f} seconds")
