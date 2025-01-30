from mfrc522 importSimpleMFRC522
import time
reader = SimpleMFRC522()

while True:
  reader.write("MFRC_TRIGGER")
  id, text = reader.read()
  print(f"id:{id}")
  print(f"text:{text}")
  time.sleep(1)
  
