import os
from utils import get_paths, read_create_historical_data, get_samples, play_and_save

#Paths
PATH = os.getcwd() #Current working directory
PATH_HISTORY = PATH + '\history.csv' #Path to historical answers
NEXT_SOUND_PATH = PATH + '\next_sound' #Functionality not implemented yet

#Parameters
#Format of files
FORMAT = '.mp3'
#seconds to wait between mouse clicks to avoid accidental double clicks
DOUBLECLICK_SLEEP = 0.5 
#if answered wrongly, by how many phrases it should be moved
MOVE_AGAIN_BY = 5
#Number of samples from history (already answered before) to play
NUM_SAMPLES_REPEAT = 5
#Number of new samples to play
NUM_SAMPLES_NEW = 3

#Get all file paths
file_paths = get_paths(PATH, FORMAT, next_sound = False)

#Read/create historical answers file
history = read_create_historical_data(PATH_HISTORY)

#Add instructions to print
print(f'If you knew the translation for a given phrase, click the left mouse \
button to go to the next sentence. Otherwise, click the right mouse button and \
the next sentence will be played, while the wrongly answered one will appear \
again after {MOVE_AGAIN_BY} sentences')

#Get samples to play
samples = get_samples(history,
                      'Next use',
                      file_paths,
                      NUM_SAMPLES_NEW,
                      NUM_SAMPLES_REPEAT)

#Play samples and update history
play_and_save(samples,
              history,
              FORMAT,
              MOVE_AGAIN_BY,
              DOUBLECLICK_SLEEP,
              PATH_HISTORY)
