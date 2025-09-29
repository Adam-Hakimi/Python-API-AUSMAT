import random

print("What is your name:")
name = input()

adjectives = ["golden", 'big', 'lucky', 'prosperous', 'timid', 'grand']
animals = ['dragon', 'monkey', 'sparrow', 'eagle', 'rat', 'tiger']

x = random.choice(adjectives)
y = random.choice(animals)
z = random.randrange(0,101)
print(f"{name}, your codename is : {x} {y}")
print(f"Your lucky number is {z}")