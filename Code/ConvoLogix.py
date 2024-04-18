
from moviepy.editor import *
from IPython.display import Audio
from spleeter.separator import Separator
import speech_recognition as sr
# import spacy
# from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from heapq import nlargest

from pydub import AudioSegment

from gensim import *
from numpy import bool_

import textsum as t

from sumy.summarizers import luhn
from sumy.utils import get_stop_words
from sumy.nlp.stemmers import Stemmer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer as sumytoken
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer

#from punctuator import Punctuator

# import nltk
# nltk.download('punkt')


#class Convologix11:


def Convologix11(self, vid):

  video =VideoFileClip(vid)
  Summary=""
    # Extract audio from video
  output_path = "D:\ConvoLogix-Project\Extracted Audio\example.mp3"  # Provide the full path where you want to save the file
  video.audio.write_audiofile(output_path)
  #video.audio.write_audiofile("example.mp3")


  #wn = Audio('example.mp3', autoplay=True)
  #display(wn)



  

  # Define the input audio file path
  audio_file = 'D:/ConvoLogix-Project/Extracted Audio/example.mp3'

  # Load the audio file
  audio = AudioSegment.from_file(audio_file)

  # Split the audio into vocals and accompaniment
  vocals = audio  # Placeholder for vocals (not separated by pydub)
  accompaniment = audio  # Placeholder for accompaniment (not separated by pydub)

  # Export vocals and accompaniment to separate files
  vocals.export('D:/ConvoLogix-Project/Extracted Audio/Noise less/vocals.wav', format='wav')
# accompaniment.export('D:/ConvoLogix-Project/Extracted Audio/Noise less/accompaniment.wav', format='wav')  # Uncomment if you want to export accompaniment separately

  # # Initialize the separator
  # separator = Separator('spleeter:2stems')  # 'spleeter:2stems' separates vocals and accompaniment.

  # # Provide the input audio file
  # audio_file = 'D:\ConvoLogix-Project\Extracted Audio\example.mp3'

  # # Separate vocals and accompaniment
  # separator.separate_to_file(audio_file, 'D:/ConvoLogix-Project/Extracted Audio/Noise less/vocals.wav')

  




    # Initialize the recognizer
  recognizer = sr.Recognizer()

    # Load the audio file
  audio_file = "D:/ConvoLogix-Project/Extracted Audio/Noise less/vocals.wav"
  # Load the pre-trained model
  #punctuator_model = Punctuator('D:/ConvoLogix-Project/Required Files/Demo-Europarl-EN.pcl')
  text=""
  with sr.AudioFile(audio_file) as source:
        # Adjust for ambient noise and record the audio
      recognizer.adjust_for_ambient_noise(source)
      audio = recognizer.record(source)

        # Use Google Web Speech API to recognize the audio
      try:
          text = recognizer.recognize_google(audio)
          #output_text = punctuator_model.punctuate(text)
          print("#"*50)
          print("Transcription: " + text)
          Summary=t.sum(text)
      except sr.UnknownValueError:
        print("Google Web Speech API could not understand the audio.")
      except sr.RequestError as e:
        print("Could not request results from Google Web Speech API; {0}".format(e))
  
  # LANGUAGE = "english"
  # SENTENCES_COUNT = 1
  # parser = PlaintextParser.from_string((text), sumytoken(LANGUAGE))
  # stemmer = Stemmer(LANGUAGE)


  # print ("\n","*"*30, "LEXRANK SUMMARIZER", "*"*30)
  # summarizer_LexRank = LexRankSummarizer(stemmer)
  # summarizer_LexRank.stop_words = get_stop_words(LANGUAGE)
  # print("#"*10)
  # for sentence in summarizer_LexRank(parser.document, SENTENCES_COUNT):

  #    print (sentence)
  #    print("#"*10)
  return Summary
  

