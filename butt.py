import random
from collections import namedtuple
from pprint import pprint
import re

Word = namedtuple('Word', ['text', 'index'])

def buttify(text, do_print=True):

	if text.startswith('!'):
		return text

	if 'http://' in text or 'https://' in text or '@' in text:
		return text

	words = re.split('(\W)', text)
	if do_print:
		print('words=')
		pprint(words)

	words_tuples = []

	for index, word_text in enumerate(words):
		# eliminates empty texts and special chars only texts
		# also eliminates words that are already butt
		if not all(not char.isalnum() for char in word_text) and word_text.lower() != 'butt':
			words_tuples.append(Word(word_text, index))

	if do_print:
		print('words_tuples=')
		pprint(words_tuples)

	if len(words_tuples) == 0:
		return text

	words_tuples_by_length = sorted(words_tuples,
		key=lambda x: len(x.text),
		reverse=True)

	if do_print:
		print('words_tuples_by_length=')
		pprint(words_tuples_by_length)

	population = []
	weights = []

	for i, word in enumerate(words_tuples_by_length):
		population.append(word.index)

		w = (len(words_tuples_by_length) - i) * 2
		weights.append(w)

	if do_print:
		print('population=')
		pprint(population)
		print('weights=')
		pprint(weights)

	index_chosen = random.choices(population, weights=weights)[0]

	if do_print:
		print('index_chosen=')
		pprint(index_chosen)

	meme = 'butt'
	if words[index_chosen].isupper():
		meme = 'BUTT'
	elif words[index_chosen][0].isupper():
		meme = 'Butt'

	words[index_chosen] = meme

	butt_text = ''.join(words)
	return butt_text

if __name__ == '__main__':
	while True:
		pprint(buttify(input()))