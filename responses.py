def get_reponse(user_input: str) -> str:                # placeholder
    lowered: str = user_input.lower()

    if lowered == '':
        return 'Well, you\'re awfully silent...'
    elif 'hello' in lowered:
        return 'Hello there!'
    else:
        return 'This isn\'t a map!'