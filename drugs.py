import requests
import json
import os
import webbrowser
import secret_drugs

def find_by_drug(drug_name):

    reactionList = {}
    reactionList = check_cache(drug_name)

    fda_url_base = "https://api.fda.gov/drug/event.json?api_key="
    api_key = secret_drugs.FDA_API_KEY
    fda_search = "&search=patient.drug.openfda.brand_name:" + drug_name
    limit = '&limit=1000'

    output = requests.get(fda_url_base + api_key + fda_search + limit)
    reaction_results = json.loads(output.text)
    test = reaction_results['results']

    test_list = []
    for i in range(len(test)):
        for x in range(len(test[i]['patient']['reaction'])):
            reaction = test[i]['patient']['reaction'][x]['reactionmeddrapt']
            if reaction not in test_list:
                test_list.append(reaction)

    print(test_list)
    print(len(test_list))

    with open('output_test.txt', 'w') as testfile:
        json.dump(test, testfile, indent=2)

    '''

    search by either brand name first, if not found, then search generic.
    if nothing found, then print apologies and ask to try another drug search
    SEARCH FORMAT: https://api.fda.gov/drug/event.json?api_key=yourAPIKeyHere&search=...
    #fda_url_search =
    #https://api.fda.gov/drug/event.json?search=patient.drug.openfda.brand_name:%22BONIVA%22
    #search=patient.drug.openfda.generic_name:"FOO+BAR"

    If not found in check_cache, add_to_cache(drug_name, reactionList)
    '''

    return reactionList
    pass


def find_by_reaction(reaction):

    drug_list = {}
    drug_list = check_cache(reaction)

    fda_url_base = "https://api.fda.gov/drug/event.json?"
    api_key = FDA_API_KEY

    '''
    sample searches:
    SEARCH FORMAT: https://api.fda.gov/drug/event.json?api_key=yourAPIKeyHere&search=...
    https://api.fda.gov/drug/event.json?search=patient.reaction.reactionmeddrapt:%22vomiting%22
    '''

    return drug_list
    pass


def check_cache(key):
    '''
    Checks the cache to see if the data has already been run
    and stored in cache.  Returns value if found.

    Parameters:
    -----------
    key: string
        key from key,value pair in cache

    Returns:
    --------
    value: string
        content of key in dict, if found
    '''
    if key in json_cache:
        #print('Using cache')
        return json_cache[key]
    else:
        #print('Fetching')
        return None


def add_to_cache(key, value):
    '''
    Adds key, value pair to json_cache file

    Parameters:
    -----------
    key: string
        key from key,value pair in cache

    value: string
        contents of key

    Returns:
    --------
    None
    '''
    # creating key,value pair for cache file
    json_cache[key] = value

    # writing new key,value pair to cache file
    with open("drugs_cache.json", "w") as cache:
        json.dump(json_cache, cache)

# Initializing setup of cache
json_cache = {}
path = 'drugs_cache.json'

# if the cache file exist, read from that file
if os.path.isfile(path):
    with open('drugs_cache.json') as f:
        json_cache = json.load(f)


if __name__ == "__main__":
    # interactive search should go here
    find_by_drug("celebrex")