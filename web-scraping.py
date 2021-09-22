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

  next_url = soup.find('a', text='Next »')
  if next_url:
    next_page_url = f"https://www.imdb.com{next_url['href']}"
  else:
    raise Exception('Reach the last page')

  movie_titles = soup.find_all('div', class_='lister-item mode-advanced')

  movie_extract = []

  for movie_title in movie_titles:
    title_spliting = movie_title.find('h3', class_='lister-item-header').text.strip().split("\n")

    year = title_spliting[-1]
    year = year.replace(')', '').replace('(', '').replace('I', '').strip().split(' ')[0]
    year = year.split('–')[0] if '–' in year else year

    title = title_spliting[1].strip()
    print(title, end=', ')

    runtime_minute = None
    try:
      runtime_minute = int(movie_title.find('span', class_='runtime').text.replace('min', '').strip())
    except:
      pass 

    movie_genre = None
    try:
      movie_genre = movie_title.find('span', class_='genre').text.strip()
    except:
      pass

    movie_rate = None
    try:
      movie_rate = movie_title.find('span', class_='certificate').text.strip()
    except:
      pass

    movie_rating = None
    try:
      movie_rating = float(movie_title.find('div', class_='ratings-bar').text.strip().split("\n")[0])
    except:
      pass

    meta_score = 0
    try:
      meta_score = int(movie_title.find('span', class_='metascore favorable').text.strip())
    except:
      pass

    movie_desc = movie_title.find_all('p', class_='text-muted')[-1].text.strip()
    movie_desc = None if 'Add a Plot' in movie_desc else movie_desc

    crews = movie_title.find('p', class_='').text.strip().replace('Star:', 'Stars:').strip()
    stars = None
    if 'Stars:' in crews:
      directors, stars = [m.strip() for m in crews.split('Stars:')]
      stars = '+'.join(s.strip() for s in stars.replace('Stars:', '').replace("\n", '').split(','))
    else:
      directors, stars = crews, None

    if 'Director:' in directors:
      directors = directors.replace('Director:', '').replace('|', '').strip()
    else:
      directors = '+'.join(s.strip() for s in directors.replace('Directors:', '').replace('|', '').strip().split(','))

    directors = directors.strip() if len(directors) else None

    movie_vote = None
    movie_gross = None

    movie_vote_gross = movie_title.find('p', class_='sort-num_votes-visible')
    if movie_vote_gross:
      movie_vote_gross = movie_vote_gross.text.strip().split("\n")
      movie_gross = movie_vote_gross[-1] if len(movie_vote_gross) > 2 else None 
      if movie_gross:
        movie_gross = movie_gross.lower().replace('$', '').replace('m', '')

        movie_vote_gross = movie_vote_gross.text.strip().split("\n")
        movie_vote = movie_vote_gross[1]
        movie_vote = int(movie_vote.replace(',', ''))

    movie_extract.append({
      'title': title,
      'year': year,
      'movie_rate': movie_rate,
      'runtime': runtime_minute,
      'genre': movie_genre,
      'rating': movie_rating,
      'metascore': meta_score,
      'description': movie_desc,
      'directors': directors,
      'starts': stars,
      'vote': movie_vote,
      'gross': movie_gross,
    })

  return next_page_url, movie_extract

def store_data(movie_list, corpus_location="movie_corpus.csv", sep="|"):
  import csv, os

  if None == movie_list or 0 == len(movie_list):
    return

  fields = ['title', 'year', 'movie_rate', 'runtime', 'genre', 'rating', 'metascore', 'description', 'directors', 'starts', 'vote', 'gross']
  if not os.path.isfile(corpus_location):
    with open(corpus_location, 'w') as f:
      writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter=sep,
        dialect=csv.unix_dialect
      )
      writer.writeheader()
      f.write("\n")

  print('Open file', corpus_location, end=' ')

  with open(corpus_location, 'a') as f:
    writer = csv.DictWriter(
      f,
      fieldnames=fields,
      delimiter=sep,
      dialect=csv.unix_dialect
    )

    try:
      writer.writerows(movie_list)
      print('Data wrote')
    except Exception as e:
      print('Fail', e)
      corpus_location = None

  return corpus_location

def start_scrape():
  import math, time, random

  imdb_url = "https://www.imdb.com/search/title/?release_date=2000&sort=num_votes,desc&page=1"
  response = requests.get(imdb_url)

  response_text = response.text

  title_per_page, title_count = counting_movie_entity(response_text)

  page_range = math.ceil(title_count / title_per_page)
  print("Number of page", page_range, "All title", title_count)

  movie_store = []
  error_pages = []

  i = 1
  imdb_url = 'https://www.imdb.com/search/title/?release_date=2000-01-01,2000-12-31&sort=num_votes,desc&after=Wy05MjIzMzcyMDM2ODU0Nzc1ODA4LCJ0dDM4NjU1MzYiLDM4MzUxXQ%3D%3D'
  while imdb_url:

    print('Executing page number', i)
    print("Open", imdb_url)

    # try:
    response = requests.get(imdb_url)
    response_text = response.text

    imdb_url, movie_extracted = extract_movie_title(response_text)
    if imdb_url:
      movie_store += movie_extracted

    print(': Done')
    # except Exception as e:
    #   if str(e) == 'Reach the last page':
    #     print(e)
    #     break

    #   print(e)
    #   error_pages.append(i)

    waiting = random.randint(0, 1) + random.random()

    print(f"Waiting for", waiting, 'sec.')
    i += 1

    f = store_data(movie_list=movie_store)
    if f:
      print('Update for', f)

    movie_store = []

    time.sleep(waiting)

  if len(error_pages):
    print('Error pages:', ', '.join(error_pages))

  return movie_store

if '__main__' == __name__:
  movie_copus = start_scrape()