#!/usr/bin/env python3
import os
import sys
from colorama import init, Fore, Style

# Import the modules for each tool
import downloader
import stem_splitter

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the app header."""
    clear_screen()
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
    print(f"{Fore.CYAN}           AUDIO TOOLBOX             {Style.RESET_ALL}")
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
    print()

def print_menu():
    """Print the main menu options."""
    print(f"{Fore.GREEN}[1] {Style.RESET_ALL}Download song from YouTube/SoundCloud")
    print(f"{Fore.GREEN}[2] {Style.RESET_ALL}Split song into stems")
    print(f"{Fore.GREEN}[3] {Style.RESET_ALL}Download and split song (combined)")
    print(f"{Fore.GREEN}[0] {Style.RESET_ALL}Exit")
    print()

def get_user_choice():
    """Get the user's menu choice."""
    while True:
        try:
            choice = input(f"{Fore.YELLOW}Enter your choice (0-3): {Style.RESET_ALL}")
            choice = int(choice)
            if 0 <= choice <= 3:
                return choice
            else:
                print(f"{Fore.RED}Invalid choice. Please enter a number between 0 and 3.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter a number.{Style.RESET_ALL}")

def main():
    """Main function to run the app."""
    init()  # Initialize colorama

    while True:
        print_header()
        print_menu()
        choice = get_user_choice()

        if choice == 0:
            print(f"{Fore.CYAN}Thank you for using Audio Toolbox. Goodbye!{Style.RESET_ALL}")
            sys.exit(0)
        
        elif choice == 1:
            print_header()
            print(f"{Fore.CYAN}Download Song{Style.RESET_ALL}")
            print(f"{Fore.CYAN}-------------{Style.RESET_ALL}")
            url = input(f"{Fore.YELLOW}Enter YouTube or SoundCloud URL: {Style.RESET_ALL}")
            audio_path = downloader.download_song(url)
            
            if audio_path:
                print(f"{Fore.GREEN}Song downloaded successfully to {audio_path}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Failed to download song.{Style.RESET_ALL}")
            
            # Ask if user wants to split the downloaded song
            if audio_path:
                split_now = input(f"{Fore.YELLOW}Would you like to split this song into stems now? (y/n): {Style.RESET_ALL}").lower()
                if split_now == 'y' or split_now == 'yes':
                    output_dir = stem_splitter.split_stems(audio_path)
                    if output_dir:
                        print(f"{Fore.GREEN}Stems split successfully to {output_dir}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}Failed to split stems.{Style.RESET_ALL}")
            
            input(f"{Fore.YELLOW}Press Enter to return to the main menu...{Style.RESET_ALL}")
        
        elif choice == 2:
            print_header()
            print(f"{Fore.CYAN}Split Song into Stems{Style.RESET_ALL}")
            print(f"{Fore.CYAN}-------------------{Style.RESET_ALL}")
            
            audio_path = input(f"{Fore.YELLOW}Enter path to audio file: {Style.RESET_ALL}")
            if os.path.exists(audio_path):
                output_dir = stem_splitter.split_stems(audio_path)
                if output_dir:
                    print(f"{Fore.GREEN}Stems split successfully to {output_dir}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Failed to split stems.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}File not found: {audio_path}{Style.RESET_ALL}")
            
            input(f"{Fore.YELLOW}Press Enter to return to the main menu...{Style.RESET_ALL}")
        
        elif choice == 3:
            print_header()
            print(f"{Fore.CYAN}Download and Split Song{Style.RESET_ALL}")
            print(f"{Fore.CYAN}---------------------{Style.RESET_ALL}")
            
            url = input(f"{Fore.YELLOW}Enter YouTube or SoundCloud URL: {Style.RESET_ALL}")
            
            # First download the song
            audio_path = downloader.download_song(url)
            
            if audio_path:
                print(f"{Fore.GREEN}Song downloaded successfully to {audio_path}{Style.RESET_ALL}")
                
                # Modified: Store the last processed audio file path so we don't need to ask for it again
                last_processed_audio = audio_path
                
                # Then automatically proceed to split the stems without asking
                proceed = True
                while proceed:
                    # Split the stems using the saved audio path
                    output_dir = stem_splitter.split_stems(last_processed_audio)
                    
                    if output_dir:
                        print(f"{Fore.GREEN}Stems split successfully to {output_dir}{Style.RESET_ALL}")
                        
                        # Ask if user wants to extract another stem
                        another = input(f"{Fore.YELLOW}Would you like to extract another stem? (y/n): {Style.RESET_ALL}").lower()
                        if another != 'y' and another != 'yes':
                            proceed = False
                    else:
                        print(f"{Fore.RED}Failed to split stems.{Style.RESET_ALL}")
                        proceed = False
            else:
                print(f"{Fore.RED}Failed to download song.{Style.RESET_ALL}")
            
            input(f"{Fore.YELLOW}Press Enter to return to the main menu...{Style.RESET_ALL}")


if __name__ == "__main__":
    main()