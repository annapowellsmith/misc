import csv
import math
import sys
import urllib2
from pyquery import PyQuery as pq

all_products = []
# Set up the log file. 
logfile = open('log.txt','w')

def scrape_product(section, url, results):
  '''
  Given a URL, scrape ratings etc for a particular product, 
  and write the results to our CSV file. 
  '''
  e = pq(url=url)
  
  # Name and price. 
  recs = e('#bopRight p.ratingOutOf')
  name = e('h1.productTitle strong').text()
  if not name:
    name = ''
  price = e('#bopRight div.sgPrice p.typicalPrice:first')
  if not price: 
    price = e('#bopRight p.typicalPrice:first')    
  reduced_price = price('span.nowPrice')
  def tidy_price(p):
    if 'Typical price' in p: 
      p = p.replace('Typical price', '').strip()
      if 'p' in p:
        p = int(float(p.replace('p', '').strip()))
      else:
        p = int(float(p.strip())*100)
    elif 'p' in p:
      p = int(p.replace('p', '').strip())      
    else: 
      p = int(float(p)*100)
    return p
  if reduced_price:
    price = reduced_price.text().strip().encode('ascii','ignore')
    price = tidy_price(price)
  else:
    if price.text(): 
      price = price.text().strip().encode('ascii','ignore')
      price = tidy_price(price)
    else: 
      price = 0
      
  # Product categories. 
  categories = e('#bopBottom ul.categories li:first')
  if categories: 
    primary_category = categories.text().strip().encode('ascii', 'ignore')
  else: 
    primary_category = ''
    
  # Rating numbers. 
  if recs.text():
    ratings = recs.text().split("customers")[0].strip()
    ratings = ratings.split(" out of ")
    positive_ratings = int(ratings[0])
    total_ratings = int(ratings[1].replace(" out of ",""))
  else:
    positive_ratings = 0
    total_ratings = 0
    
  # Review distribution. 
  review_distribution = []
  stars = e('ul.snapshotList li span.reviewsCount')
  for star in stars: 
    review_distribution.append(int(star.text.strip()))
  total = 0
  num_reviews = 0
  
  # Reverse the order of ratings - 1 to 5 not 5 to 1. 
  review_distribution = review_distribution[::-1]
  for i, n in enumerate(review_distribution): 
    total += (i+1)*n
    num_reviews += n
  if num_reviews != 0:
    mean_rating = float(total) / float(num_reviews)
    sum_of_squares = 0.0
    for i, count in enumerate(review_distribution): 
      for j in range(0,count):
        dist_from_mean = (i+1) - mean_rating
        sum_of_squares += math.pow(dist_from_mean,2)
    if num_reviews != 1:
      variance = sum_of_squares / float(num_reviews-1)
      std_dev = "%.3f" % math.sqrt(variance)
    else: 
      std_dev = "0.0"
    mean_rating = "%.2f" % mean_rating
  else: 
    mean_rating = "0.0"
    std_dev = "0.0"
    
  if total_ratings != num_reviews:
    print 'Total ratings found not equal to Ocado total, for %s' % url
    
  result = [section, name.encode('ascii','ignore'), price]
  result += [positive_ratings, total_ratings, url]
  result += [primary_category, mean_rating]
  result += review_distribution + [std_dev]
  #logfile.write(result + "\n")
  
  results.writerow(result)
  
#testurl = 'http://www.ocado.com/webshop/product/Green-Baby-Natural-Short-Sleeve-Wrap/79904011'
#scrape_product(testurl, '')
#sys.exit()

def get_raw_ratings():
  '''
  Scrape the Ocado site for *all* products and ratings. 
  Write results to ocado-results.csv.
  '''
  avoid_duplicates = []
  
  # Define our desired categories. 
  DOMAIN = 'http://ocado.com'
  categories = { 
    '20002': "Fresh", 
    '20424': "Food Cupboard", 
    "25189": "Bakery",
    "20911": "Frozen", 
    "30930": "Speciality", 
    "30489": "Organic", 
    "20977": "Drinks"
  } 
  
  # Scrape each category in turn. 
  j = 0

  for cat in categories: 
    j += 1
    section = categories[cat]
    
    # Set up the output file. 
    results = csv.writer(open('ocado-results-%s.csv' % cat, 'wb'))
    headings = ['Section', 'Name', 'Price', 'Positive Ratings', 'Total Ratings', 'URL']
    headings += ['Category', 'Mean Rating']
    headings += ['1-Star Reviews', '2-Star Reviews', '3-Star Reviews']
    headings += ['4-Star Reviews', '5-Star Reviews', 'Standard Deviation']
    results.writerow(headings)
    
    msg = 'Scraping category %s of %s: %s' % (j, len(categories.keys()), section)
    print '#########################################################'
    print '############ %s ############' % msg
    print '#########################################################'
    base_url = DOMAIN + '/webshop/getCategories.do?tags=%s' % cat
    d = pq(url=base_url)
    
    # Calculate how many pages to scrape. 
    num_results = d("#productCount span em")
    num_results = num_results.text().strip().replace(" products","") 
    results_per_page = len(d("li.productDetails"))
    max_pages = int(num_results) // results_per_page
    print "%s total results, %s pages" % (int(num_results), max_pages)
    results_count = 0
    init = 0
    
    # Scrape each page in turn. 
    for i in range(init, max_pages):
      page_url = base_url + "&index=%s" % str(i)
      print "---------- Scraping %s of %s pages -----------" % (i, max_pages)
      logfile.write("%s\n" % page_url) 
      d = pq(url=page_url)
      num_products = len(d("li.productDetails"))
      results_count += num_products
      
      # Scrape each product in turn. 
      for i, product in enumerate(d("li.productDetails")):
        logfile.write('Getting product %s of %s\n' % (i, num_products)) 
        product_url = pq(product)('h3.productTitle a').attr('href').split("?")[0]
        logfile.write("%s\n" % product_url) 
        product_url = DOMAIN + product_url.split("?")[0]
        
        # Keep a list of canonical URLs, so we can avoid dupes. 
        if product_url not in avoid_duplicates:
          avoid_duplicates.append(product_url)
          
        # Handle timeouts. 
        try:
          scrape_product(section, product_url, results)
        except urllib2.URLError:
          try:
            sleep(20)
            scrape_product(section, product_url, results)
          except urllib2.URLError:
            sleep(20)
            scrape_product(section, product_url, results)
            
    # Note where we have an unexpected number of results. 
    if results_count != num_results:
      print '----------------'
      print 'Expected %s results in category, actually found %s' % (num_results, results_count)
    else:
      print '----------------'
      print 'Expected number of results found in category - yay!'
   
get_raw_ratings() 
