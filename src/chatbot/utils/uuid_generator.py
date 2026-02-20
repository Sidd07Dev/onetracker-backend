import uuid


def get_uuid():
    try:
        id = uuid.uuid4()
        if not id:
           print("UUID generation error...")
           return None
        return id
    except Exception as e:
      print(str(e))
      return None