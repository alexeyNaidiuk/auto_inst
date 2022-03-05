def get_agemt():
    with open('user-agents_instagram-app.txt') as file:
        agets = file.read().splitlines()[::-1]
        for i in agets:
            yield i

print(next(get_agemt()))