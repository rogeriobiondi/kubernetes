import time
from datetime import datetime

def main():    
    print(f"{datetime.now().isoformat()} The Job is running...")    
    time.sleep(5)
    print(f"{datetime.now().isoformat()} The Job has finished.")

if __name__ == "__main__":
    main()