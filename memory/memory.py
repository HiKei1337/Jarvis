from memory.database import Database



class Memory:


    def __init__(self):

        self.db=Database()



    def remember(self,user,answer):

        self.db.save(
            user,
            answer
        )