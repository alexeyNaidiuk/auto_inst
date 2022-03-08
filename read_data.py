import pickle

with open('roman_ketkov_followers.pickle', 'rb') as file:
    data = pickle.load(file)

for i in data:
    print(i.__dict__)
