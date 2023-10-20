import os
from utils import get_paths, read_create_historical_data, get_samples, play_and_save

#Paths
PATH = os.getcwd()
PATH_HISTORY = PATH + '\\history.csv'
NEXT_SOUND_PATH = PATH + '\\next_sound\\'

#Parameters
FORMAT = '.mp3' #format of files
DOUBLECLICK_SLEEP = 0.5 #seconds to wait for the next click to be by accident
MOVE_AGAIN_BY = 5 #if answered wrongly, by how many phrases it should be moved
NUM_SAMPLES_REPEAT = 5 #number of samples from history to play
NUM_SAMPLES_NEW = 3 #number of new samples to play

#Get all file paths
file_paths = get_paths(PATH, FORMAT, next_sound = False)

#Read/create historical answers file
history = read_create_historical_data(PATH_HISTORY)

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
