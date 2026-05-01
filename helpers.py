
import sys

# Reads a text file and returns a list of the tokens in the file, ignoring stopwords
# A token is a sequence of alphanumerical characters as specified by isalnum
def tokenize(text: str, stopwords: set[str]) -> list[str]:

    tokens: list[str] = []

    # Split the text by whitespace
    words: list[str] = text.split()

    # Split each whitespace separated word (in case it contains special chars)
    for word in words:

        # Skip whitespace separated stopwords and single char words
        if word.strip() not in stopwords and len(word.strip()) > 1:
            
            splitWords: list[str] = tokenizeWord(word)

            # Don't add empty token lists or stopwords that are separated by non-alphanumeric chars
            if(len(splitWords) > 0 and not set(splitWords).issubset(stopwords)): 
                tokens += splitWords

    # Return the list of tokens, even if the file was not read
    return tokens


# Helper function to split a word that may contain non-alphanumeric characters
def tokenizeWord(rawWord: str) -> list[str]:

    words: list[str] = []
    word: str = ""

    for letter in rawWord:

        # Add the character to the word if it's alphanumeric and an English char
        if letter.isalnum() and letter.isascii():
            word += letter

        # Else, end the word, convert to lowercase, and add it to words
        else:
            if len(word) > 0: # Don't add empty words
                words.append(word.lower())
                word = ""

    # Add the last word, if any
    if len(word) > 0:
        words.append(word.lower())

    return words
            

# Counts the number of occurences of each token in a list of tokens
def computeWordFrequencies(tokens: list[str], frequencies: dict[str, int]) -> None:

    for token in tokens:
        if token in frequencies:
            frequencies[token] += 1
        else:
            frequencies[token] = 1


