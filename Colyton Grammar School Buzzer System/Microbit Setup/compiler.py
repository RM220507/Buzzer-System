import uflash
from os import path
import re
import python_minifier

def input_int(prompt : str, min_val : float = float("-inf"), max_val : float = float("inf")) -> int:
    input_val = ""
    valid = False
    while not valid:
        input_val = input(prompt)
        
        if input_val.isdigit() and min_val <= int(input_val) <= max_val:
            valid = True
        else:
            print("Not a valid input. Try again.")
            
    return int(input_val)

def input_bool(prompt : str, condition_val : str) -> bool:
    input_val = input(prompt)

    return input_val.strip().upper() == condition_val.upper()

def flash_file(microbit_name : str, file_path : str):
    input(f"Connect the {microbit_name} Micro:Bit. Press ENTER when ready.")
    if path.isfile(file_path):
        uflash.flash(path_to_python=file_path)
        print(f"Finished flashing {microbit_name} Micro:Bit.")
    else:
        raise FileNotFoundError(f"Required file '{file_path}' was not found.")
        
def search_for_tag(lines : list, tag : str):
    for i in range(len(lines) - 1, -1, -1):
        matched = re.search(f'.*{tag}.*', lines[i])
        if matched is not None:
            tag_line = i
            break
    else:
        tag_line = None
        
    return tag_line
        
def flash_buzzers(start : int, end : int, file_path : str):
    if path.isfile(file_path):
        with open(file_path) as f:
            python_data = f.readlines()
    else:
        raise FileNotFoundError(f"Required file '{file_path}' was not found.")
        
    tag_line = search_for_tag(python_data, '"#REPLACE#"')
    
    for i in range(start, end + 1):
        input(f"Connect the Micro:Bit for Buzzer {i}. Press ENTER when ready.")
        file_to_flash = python_data.copy()
        if tag_line is not None:
            file_to_flash[tag_line] = file_to_flash[tag_line].replace('"#REPLACE#"', str(i))
            
        file_to_flash = "\n".join(file_to_flash)
        file_to_flash = python_minifier.minify(file_to_flash, rename_locals=True, rename_globals=True)
        
        uflash.flash(python_script=file_to_flash.encode("utf-8"))
        print(f"Finished flashing Buzzer {i} to Micro:Bit.")
        
def main():
    print("Buzzer System - Micro:Bit Setup Aid")
    print("Ryan Mitcham 2024")
    print("---------------------------------------")
    
    # Get the values of what to flash
    print("Initial Setup:")
    flash_controller = not input_bool("Flash controller? [Y/N] ", "N")
    flash_host_buzzer = not input_bool("Flash host buzzer? [Y/N] ", "N")
    
    start = input_int("Start from which index? [0-15] ", 0, 15)
    end = input_int(f"End at which index? [{start}-15] ", start, 15)
    #flash_test = not input_bool("Flash buzzers with test script? [Y/N]", "N")
    
    # Flash controller and host buzzer
    print("---------------------------------------")
    print("Flash Controller & Host Buzzer:")
    if flash_controller:
        flash_file("Controller", "src/controller.py")
    
    if flash_host_buzzer:
        flash_file("Host Buzzer", "src/buzzer_host.py")
    
    # Flash buzzers
    print("---------------------------------------")
    print("Flash Buzzers:")
    flash_buzzers(start, end, "src/buzzer.py")
    
    # End
    print("---------------------------------------")
    print("Finished flash operation.")
    
if __name__ == "__main__":
    main()
