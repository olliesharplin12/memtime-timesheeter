def ask_question(question: str) -> bool:
    while True:
        res = input(f'{question} [y/n]: ').lower()
        if res == 'y':
            return True
        elif res == 'n':
            return False
