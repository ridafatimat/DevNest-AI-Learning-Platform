# import time
# from fastapi import HTTPException

# class RateLimiter:
#     def __init__(self, limit=20):
#         self.limit = limit
#         self.calls = {}

#     def check(self, user):
#         now = time.time()
#         window = 60
#         arr = self.calls.get(user, [])
#         arr = [t for t in arr if now - t < window]

#         if len(arr) >= self.limit:
#             raise HTTPException(429, "Rate limit exceeded")

#         arr.append(now)
#         self.calls[user] = arr

# limiter = RateLimiter(limit=20)




import time
from fastapi import HTTPException

class RateLimiter:
    def __init__(self, limit=20):
        self.limit = limit
        self.calls = {}

    def check(self, user):
        now = time.time()
        window = 60
        arr = self.calls.get(user, [])
        arr = [t for t in arr if now - t < window]

        if len(arr) >= self.limit:
            raise HTTPException(429, "Rate limit exceeded")

        arr.append(now)
        self.calls[user] = arr

# Make sure this is at the bottom of the file
limiter = RateLimiter(limit=20)
