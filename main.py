from flask import Flask, render_template, request, redirect, url_for
import pymongo
from pymongo import MongoClient
from datetime import datetime
import json
from password import MONGO_USER, MONGO_PASS

app = Flask(__name__)

@app.route('/')
def main():
	return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
	query = request.form['query']
	if len(query.strip()) > 0:
		return redirect(url_for('results', query=query)) 
	return redirect(url_for('main'))


@app.route('/results/<query>')
def results(query):
	connection = MongoClient("ds063536.mlab.com", port=63536)
	db = connection['articles']
	db.authenticate(MONGO_USER, MONGO_PASS)
	collection = db['all_articles']

	or_pipeline = []
	for part in query.split():
		or_pipeline.append({'keywords': part})
		or_pipeline.append({'title': {'$regex': part,  "$options": "-i"}})
	print or_pipeline

	pipeline = [
		{'$match': {'$or': or_pipeline, 'date': {'$ne': None}} },
		{'$group': {'_id': '$date','articles': {'$push': {'title': '$title', 'url': '$url', 'author': '$authors', 'keywords': '$keywords'} }}},
		{'$sort': {'_id': 1}}
	]


	articles = collection.aggregate(pipeline)

	articles_length = {}
	all_articles = {}

	for article in articles:
		diff = article['_id'] - datetime(2016, 8, 26)
		diff_current = datetime.now() - article['_id'] 
		if diff.days > 0 and diff_current.days >= 0:
			date = article['_id'].strftime("%Y-%m-%d")
			try:
				all_articles[date] = all_articles[date].extend(article['articles'])
				articles_length[date] = articles_length[date] + len(article['articles'])
			except:
				all_articles[date] = article['articles']
				articles_length[date] = len(article['articles'])

	if len(articles_length) > 0: 			
		curr = datetime.now().strftime("%Y-%m-%d")
		if curr not in articles_length:
			articles_length[curr] = 0

	pipeline2 = [
		{'$match': {'$or': or_pipeline, 'date': {'$gte': datetime(2016, 8, 26)}}},
		{'$unwind': '$keywords'},
		{'$group': {'_id': None, 'words': {'$push': {'word': '$keywords'}}}}
	]

	words = collection.aggregate(pipeline2)
	try:
		all_keywords = [item['word'] for item in list(words)[0]['words']]
	except:
		all_keywords = []

	ignore = ['10000', 'hello']
	words_dict = {str(x):all_keywords.count(x) for x in all_keywords if query not in str(x) and len(str(x)) > 3 and str(x) not in ignore }

	all_articles = json.dumps(all_articles)
	return render_template('search.html', articles=all_articles, keywords=words_dict, lengths = articles_length, query=query)

# if __name__ == "__main__":
#    app.run(debug=True)

