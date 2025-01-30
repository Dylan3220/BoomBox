from mfrc522 importSimpleMFRC522
import time
reader = SimpleMFRC522()

while True:
  reader.write("MFRC_TRIGGER")
  id, text = reader.read()
  print("id:{id}")
  print("text:{text}")
  time.sleep(1)
  
