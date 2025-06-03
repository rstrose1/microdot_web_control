#https://github.com/peterhinch/micropython-async/blob/master/v3/primitives/queue.py
# may need to manually get the queue class it seems.

from collections import deque

msg = []
my_deque = deque(msg, 20)
print(my_deque)  # deque([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

my_deque.append("my messaage")
my_deque.append("my second message")
print(my_deque)
first = my_deque.popleft()  # Pops the 9.
second = my_deque.popleft()  # Pops the 8.

print(first)
print(second)  # deque([2, 3, 4, 5, 6, 7])

while len(my_deque) > 0:
	my_deque.pop()
print(my_deque)  # deque([])