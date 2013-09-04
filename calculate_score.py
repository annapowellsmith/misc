import csv
import math
import sys

# For our purposes, we only care about positive or negative ratings. 
def ci_lower_bound(pos, n, confidence):
  '''
  This answers the question:
  'Given the ratings I have, there is a 95 percent hance that 
  the "real" fraction of positive ratings is at least what?'
  pos = number of positive ratings
  n = total number of ratings
  confidence = confidence level
  (the z-score is always 1.96 at 95% confidence, so you can hard-code this)
  '''
  if n == 0:
    return 0
  #z = Statistics2.pnormaldist(1-(1-confidence)/2)
  z = 1.96
  if n == 0.0:
    return 0.0
  # print pos, n
  phat = pos/n
  # print 'phat', phat
  # print ( phat * (1-phat) + z*z / (4*n) ) / n
  # print math.sqrt( (phat*(1-phat)+z*z/(4*n))/n)
  return ( phat + z*z/(2*n) - z * math.sqrt( (phat*(1-phat)+z*z/(4*n))/n) ) / (1+z*z/n)

def get_ci():
  ''' 
  Calculate lower bounds for positive and negative ratings, to 
  a 95 per cent conflidence interval. 
  '''
  print 'get_ci'
  results = csv.DictReader(open('all.csv', 'rU'))
  headings = results.fieldnames
  headings.append('Proportion positive to 95% confidence')
  headings.append('Proportion negative to 95% confidence')
  full_results = csv.DictWriter(open('all-with-intervals.csv', 'wb'), fieldnames=headings)
  full_results.writeheader()
  for r in results:
    if r['Section'] == "Section": 
      continue
    print r['Name']
    positive_ratings = float(r['Positive Ratings'])
    total_ratings = float(r['Total Ratings'])
    # print positive_ratings, total_ratings
    # There are occasional bugs on the Ocado pages, whereby
    # there are more people who would recommend the product
    # than have actually reviewed it! Look out for these. 
    if positive_ratings > total_ratings: 
      positive_ratings = float(r['4-Star Reviews']) + float(r['5-Star Reviews'])
      total_ratings = float(r['1-Star Reviews']) + float(r['2-Star Reviews']) + \
          float(r['3-Star Reviews']) + float(r['4-Star Reviews']) + float(r['5-Star Reviews'])
    negative_ratings = total_ratings - positive_ratings
    lower_bound = ci_lower_bound(positive_ratings, total_ratings, 0.95)
    lower_negative_bound = ci_lower_bound(negative_ratings, total_ratings, 0.95)
    r['Proportion positive to 95% confidence'] = "%.6f" % lower_bound
    r['Proportion negative to 95% confidence'] = "%.6f" % lower_negative_bound
    full_results.writerow(r)
    
def remove_duplicates():
  '''
  Remove duplicate URLs. 
  '''
  print 'remove_duplicates'
  results = csv.DictReader(open('all-with-intervals.csv', 'rU'))
  headings = results.fieldnames
  full_results = csv.DictWriter(open('FINAL.csv', 'wb'), fieldnames=headings)
  full_results.writeheader()
  non_duplicate_urls = []
  non_duplicates = []
  for r in results:
    # print r
    url = r['URL']
    if url not in non_duplicate_urls:
        non_duplicate_urls.append(url)
        non_duplicates.append(r)
  for non_dupe in non_duplicates:
    full_results.writerow(non_dupe)
    
get_ci()
remove_duplicates()
