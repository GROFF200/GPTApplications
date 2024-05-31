To use the application:

1. Set the duration to however long you want the recording to be.  Don't exceed 60 seconds (default is 20)
2. Make sure to select the voice you want to use for playback via the "Select Voice" drop-down on the bottom left
2. When you are ready, press "Record".  The application will become unresponsive as it records input from your mic for the specified time interval.
3. After the recording finishes, a transcription request is sent to GPT.   The transcription will appear in the "Audio Transcription" textbox on the left side of the panel.
4. Edit it if necessary.  Otherwise, press "Send" to send the text GPT.
5. GPT is prompted to examine what you send it and determine if a native speaker can understand it.  If not, it tells you what the native speaker should have said.  Then it will respond to what you were
   trying to say to it.
6. The text response from GPT is displayed in the "GPT Response" text area in the right textbox.
7. A request is sent to convert the GPT text to audio.  It will start playing back when ready
8. Once playback is finished, you can start the "Record" process again.


To run this script you need:

1.  Python 3.11.8 or higher
2.  Run this to install the required dependencies:  pip install sounddevice numpy scipy pygame openai
