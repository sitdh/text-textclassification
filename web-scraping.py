import requests, logging
from bs4 import BeautifulSoup
from lxml import html

def counting_movie_entity(content):

  soup = BeautifulSoup(content, 'html.parser')

  content = soup.find('div', id='content-2-wide')
  description = content.find('div', class_='desc')

  counting, entity = description.find('span').text.split(' of ')

  counting = int(counting.split('-')[-1].strip().replace(',', ''))
  entity = int(entity.replace(',', '').replace('titles.', '').strip())

  return counting, entity

def extract_movie_title(title_list):
  soup = BeautifulSoup(title_list, 'html.parser')

  movie_titles = soup.find_all('div', class_='lister-item mode-advanced')

  movie_extract = []

  for movie_title in movie_titles:
    _, title, year = movie_title.find('h3', class_='lister-item-header').text.strip().split("\n")

    year = year.replace(')', '').replace('(', '').split(' ')[-1]
    year = year.split('–')[-1] if '–' in year else year
    year = int(year)

    run_time_minute = int(movie_title.find('span', class_='runtime').text.replace('min', '').strip())
    movie_genre = movie_title.find('span', class_='genre').text.strip()

    movie_rate = None
    try:
      movie_rate = movie_title.find('span', class_='certificate').text.strip()
    except:
      pass

    movie_rating = float(movie_title.find('div', class_='ratings-bar').text.strip().split("\n")[0])

    meta_score = 0
    try:
      meta_score = int(movie_title.find('span', class_='metascore favorable').text.strip())
    except:
      pass

    movie_desc = movie_title.find_all('p', class_='text-muted')[-1].text.strip()

    directors, starts = [m.strip() for m in movie_title.find('p', class_='').text.strip().split('Stars:')]
    if 'Director:' in directors:
      directors = directors.replace('Director:', '').replace('|', '').strip()
    else:
      directors = '+'.join(s.strip() for s in directors.replace('Directors:', '').replace('|', '').strip().split(','))

    directors = directors.strip() if len(directors) else None

    starts = '+'.join(s.strip() for s in starts.replace(" \n", '').split(','))

    movie_vote_gross = movie_title.find('p', class_='sort-num_votes-visible').text.strip().split("\n")
    movie_vote = movie_vote_gross[1]
    movie_gross = movie_vote_gross[-1] if len(movie_vote_gross) > 2 else None 

    movie_vote = int(movie_vote.replace(',', ''))

    movie_extract.append({
      'title': title,
      'year': year,
      'movie_rate': movie_rate,
      'runtime': run_time_minute,
      'genre': movie_genre,
      'rating': movie_rating,
      'metascore': meta_score,
      'description': movie_desc,
      'directors': directors,
      'starts': starts,
      'vote': movie_vote,
      'gross': movie_gross,
    })

  return movie_extract

def store_data(movie_list, corpus_location="movie_corpus.csv", sep="|"):
  import csv

  movie = movie_list[-1]
  movie_keys = list(movie.keys())

  print('Open file', corpus_location, end=' ')

  with open(corpus_location, 'w') as f:
    writer = csv.DictWriter(
      f,
      fieldnames=movie_keys,
      delimiter=sep,
      dialect=csv.unix_dialect
    )

    try:
      writer.writeheader()
      writer.writerows(movie_list)
      print('Data wrote')
    except:
      print('Fail')
      corpus_location = None

  return corpus_location

def start_scrape():
  import math, time, random

  url_template = url_template = "https://www.imdb.com/search/title/?release_date=2010&sort=num_votes,desc&page={page_number}"
  imdb_url = url_template.format(page_number=1)
  response = requests.get(imdb_url)

  response_text = response.text

  title_per_page, title_count = counting_movie_entity(response_text)

  page_range = math.ceil(title_count / title_per_page)
  print("Number of page", page_range, "All title", title_count)

  movie_store = []

  error_pages = []
  for i in range(1, page_range+1):

    print('Executing page number', i, end=" ")

    try:
      imdb_url = url_template.format(page_number=i)
      response = requests.get(imdb_url)
      response_text = response.text

      movie_store += extract_movie_title(response_text)

      print('Done')
    except:
      print('Error')
      error_pages.append(i)

    waiting = random.randint(0, 3) + random.random()
    print(f"Waiting for", waiting, 'sec.')
    time.sleep(waiting)

  if len(error_pages):
    print('Error pages:', ', '.join(error_pages))

  return movie_store

if '__main__' == __name__:
  movie_copus = start_scrape()
  file_name = store_data(movie_copus)
  print("Done", file_name)
