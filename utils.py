import os
import random
import re
import numpy as np
import pandas as pd
import pygame  # To run sound samples
from datetime import datetime, timedelta
import time
from win32api import GetKeyState  # To get mouse click type


def get_paths(path_dir: str,
              file_format: str,
              next_sound: bool = False) -> list:
    """
    Get all paths with a provided extension from a given directory and its
    subfolders.
    
    Args:
        path_dir (str): A main directory path
        file_format (str): An extension of file names to iterate over
        next_sound (bool): [Not implemented yet] Specifies if sound from
            'next_sound' directory should be played (True) to signal that next
            phrase has just started. Defaults to False (don't use sound signal)
    Returns:
        paths (list): All paths within the given directory
    """
    paths = []
    for root, dirs, files in os.walk(path_dir):
        # Next_sound functionality isn't implemented yet, so False should be
        # used all the time
        if not next_sound:
            # Keep paths that aren't from 'next_sound' directory
            dirs[:] = [d for d in dirs if d not in ['next_sound']]
        for file in files:
            full_path = os.path.join(root, file)
            if full_path.endswith(file_format):
                # Append the file name to the list
                paths.append(os.path.join(root, file))
    return paths


def read_create_historical_data(path_history: str) -> pd.DataFrame:
    """
    Read historical answers or create a file if there is no history.
    
    Args:
        path_history (str): A path where historical answers are stored
    Returns:
        df (pd.DataFrame): A DataFrame with historical answers
    """
    if os.path.exists(path_history):
        # Read history if exists
        df = pd.read_csv(path_history)
    else:
        # Create a CSV file with historical answers only for the first time if
        # it wasn't created yet
        df = pd.DataFrame(columns=['Expression',
                                   'File',
                                   'Last used',
                                   'Next use',
                                   'Days to next',
                                   'Good count',
                                   'Again count'])
        df.to_csv(path_history, index=False)
    return df


def get_samples(history: pd.DataFrame,
                next_use_col: str,
                file_paths: list,
                num_samples_new: int,
                num_samples_repeat: int) -> list: 
    """
    Get a list of samples to play. The samples are chosen randomly.
    
    Args:
        history (pd.DataFrame): A DataFrame with historical answers
        next_use_col (str): A column indicating when samples should be played
            again at the earliest
        file_paths (str): Paths to sound samples
        num_samples_new (int): How many new samples should be played
        num_samples_repeat (int): How many historical samples should be played
    Returns:
        samples (list): A list of samples to play
    """
    # Assign True if file path was in history
    idxs_with_history = [x in list(history.File) for x in file_paths]
    # Get indexes of file paths from history
    idxs_with_history = np.where(idxs_with_history)[0]
    # Create a list with paths without history
    paths_without_history = list(np.delete(file_paths, idxs_with_history))

    # For historical data, only rows with 'Next use' date no greater than today
    # should be used.
    to_repeat = history[pd.to_datetime(history[next_use_col]) <=
                        pd.to_datetime(datetime.now())]
    # Assign True if file path was in historical to repeat
    idxs_repeat = [x in list(to_repeat.File) for x in file_paths]
    # Get indexes of file paths from historical to repeat
    idxs_repeat = np.where(idxs_repeat)[0]
    # Create a list with paths from historical to repeat
    paths_with_history = list(np.array(file_paths)[idxs_repeat])

    # Sample from file paths
    if len(paths_without_history) >= num_samples_new:
        # Sample num_samples_new
        samples_new = random.sample(paths_without_history, num_samples_new)
    else:
        # Samples as much as possible if less rows than num_samples_new
        samples_new = random.sample(paths_without_history,
                                    len(paths_without_history))
    if len(paths_with_history) >= num_samples_repeat:
        samples_hist = random.sample(paths_with_history, num_samples_repeat)
    else:
        samples_hist = random.sample(paths_with_history, len(paths_with_history))

    # Add a column that indicates if the sample was already played in the past
    # (True) of if the sample is new (False)
    samples_new = [(x, False) for x in samples_new]
    samples_hist = [(x, True) for x in samples_hist]

    # Merge lists. Historical first, then new
    samples = samples_hist + samples_new
    return samples


def left_right_mouse_click() -> str:
    """
    Check what button is clicked on a computer mouse.
    
    Returns:
        mouse_button (str): Clicked mouse button (left/right). The middle
            button functionality is provided in a comment, though it isn't yet
            used
    """
    while True:
        left_button = GetKeyState(0x01)
        if left_button < 0:
            mouse_button = 'left'
            break
        right_button = GetKeyState(0x02)
        if right_button < 0:
            mouse_button = 'right'
            break
        # middle_button = GetKeyState(0x04)
        # if middle_button < 0:
        #     mouse_button = 'middle'
        #     break
    return mouse_button


def get_next_number_fibonacci(prev_num: int) -> int:
    """
    Get the next number from the Fibonacci sequence. It is used to calculate
    when the sample should be run again at the earliest.
    
    Args:
        prev_num (int): A previous number of days when the sample should be
            run again, at the time when the sequence was last run
    Returns:
        next_num (int): A next number from the Fibonacci sequence indicating
            when the sample should be run again
    """
    next_num = round(prev_num * (1 + np.sqrt(5))/2)
    # Next number should be not less than 3
    next_num = max(next_num, 3)
    return next_num


def play_and_save(samples: list,
                  history: pd.DataFrame,
                  file_format: str,
                  move_again_by: int,
                  doubleclick_sleep: float,
                  path_history: str):
    """
    Play samples and save results based on the correctness of answers.
    
    Args:
        samples (list): A list of samples to play
        history (pd.DataFrame): A DataFrame with historical answers
        file_format (str): An extension of file names
        move_again_by (int): if answered wrongly, by how many phrases
            the sample should be moved in the queue to be run again
        doubleclick_sleep (float): Seconds to wait between mouse clicks to
            avoid accidental double clicks
        path_history (str): A path to historical answers        
    """
    at_least_once_wrong = []
    # Initialize pygame for playing a sound
    mixer = pygame.mixer
    mixer.init()
    while len(samples) > 0:
        print(f'{len(samples)} left')
        # Get today's date
        date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        sample = samples[0][0]
        in_history = samples[0][1]

        # Print word to learn
        word = sample.split('\\')[-1]
        word = re.findall(rf'\d*\s*(.*)\s*{file_format}', word)[0]
        print('Phrase:', word)
        print('Path:', sample)

        # Play a sound sample
        pygame.mixer.music.load(sample)
        pygame.mixer.music.play()

        # If left mouse click - answered correctly,
        # if right mouse click - has to be played again
        mouse_click = left_right_mouse_click()
        if mouse_click == 'left':
            correct_answer = True
            # Remove from the list as answered correctly
            print('Good')
            samples.pop(0)
        else:
            correct_answer = False
            print('Again')
            # Move to the nth element of the list to be played again
            # (or to last if less than 5 elements in the samples list)
            samples.insert(move_again_by, (sample, True))
            samples.pop(0)
            # Keep track of phrases that have to be repeated at least once
            at_least_once_wrong.append(sample)
        while pygame.mixer.music.get_busy():
            continue
        time.sleep(doubleclick_sleep)  # to avoid double-clicks

        # If sample from history
        if in_history:
            good = history.loc[history.File == sample,
                               'Good count'].iloc[0] + int(correct_answer)
            again = history.loc[history.File == sample,
                                'Again count'].iloc[0] + 1 - int(correct_answer)
            if correct_answer:
                # Find next Fibonacci number
                prev_num = history.loc[history['File'] == sample,
                                       'Days to next'].iloc[0]
                if sample in at_least_once_wrong:
                    # If finally correct but at least once wrong, set to 2 days
                    days_to_next = 2
                else:
                    # Set to the next number from the Fibonacci sequence
                    days_to_next = get_next_number_fibonacci(prev_num)
            else:
                # If not answered correctly, set to 1 day
                days_to_next = 1
        else:
            good = int(correct_answer)
            again = 1 - int(correct_answer)
            # New samples should be run again after 1 day (if still wasn't
            # answered correctly) or 3 days (if answered correctly)
            if correct_answer:
                days_to_next = 3
            else:
                days_to_next = 1

        # Get a date when the sample should be run again (today +
        # number of days to the next run in YYYY-MM-DD format)
        next_use = (pd.to_datetime(date) + timedelta(days=days_to_next)).\
            strftime('%Y-%m-%d')

        # Row to add/update in the history
        new_row = {'Expression': word,
                   'File': sample,
                   'Last used': date,
                   'Next use': next_use,
                   'Days to next': days_to_next,
                   'Good count': good,
                   'Again count': again}
        if in_history:
            # Update values
            history[history.File == sample] = new_row.values()
        else:
            # Append row if the sample was run for the first time
            history = pd.concat([history,
                                 pd.DataFrame.from_records([new_row])],
                                ignore_index=True)
        # Save history after every sample. This way, the progress will be
        # saved even if the program is stopped after a few samples.
        history.to_csv(path_history, index=False)
    # Sort history by 'Last used' column and save final results
    history = history.sort_values('Last used').reset_index(drop=True)
    history.to_csv(path_history, index=False)
