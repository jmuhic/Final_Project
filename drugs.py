import requests
import json
import os
import webbrowser
import secret_drugs
import plotly


def find_by_drug(drug_name):
    '''
    Returns a list of rections reported to the FDA
    for the drug entered by the user.  Will return
    data from cache, if found.  Otherwise, will use
    FDA API to retrieve the information.

    Parameters:
    -----------
    drug_name: string
        name of drug entered by user

    Returns:
    --------
    reactionDict: dictionary
        dictionary containing the name of the reaction (key)
        and the number of times the reaction was reported (value)
        for the user-specified drug
    '''

    drug_dict = {}
    drug_dict = check_cache(drug_name)

    if drug_dict:
        reactions_dict = {}
        reactions = drug_dict['results']
        for i in range(len(reactions)):
            for x in range(len(reactions[i]['patient']['reaction'])):
                drug_reaction = reactions[i]['patient']['reaction'][x]['reactionmeddrapt']
                if drug_reaction not in reactions_dict:
                    reactions_dict[drug_reaction] = 1
                else:
                    reactions_dict[drug_reaction] += 1

            # Sorting the results by most frequently report reactions to least frequent
            reactionDict = dict(sorted(reactions_dict.items(), key=lambda kv: kv[1], reverse=True))
    elif drug_dict is None:
        fda_url_base = "https://api.fda.gov/drug/event.json?api_key="
        api_key = secret_drugs.FDA_API_KEY
        #fda_search_brand = "&search=patient.drug.openfda.brand_name:" + drug_name
        limit = '&limit=1000'

        # More generalized search appears to be most effective for brand/generic/substance_name
        #output_brand = requests.get(fda_url_base + api_key + fda_search_brand + limit)
        output = requests.get(fda_url_base + api_key + '&search=' + drug_name + limit)
        reaction_results = json.loads(output.text)
        try:
            reactions = reaction_results['results']
            add_to_cache(drug_name, reaction_results)

        # Building a dictionary to list reporting reactions and number of occurrences
            reactions_dict = {}
            for i in range(len(reactions)):
                for x in range(len(reactions[i]['patient']['reaction'])):
                    drug_reaction = reactions[i]['patient']['reaction'][x]['reactionmeddrapt']
                    if drug_reaction not in reactions_dict:
                        reactions_dict[drug_reaction] = 1
                    else:
                        reactions_dict[drug_reaction] += 1

            # Sorting the results by most frequently report reactions to least frequent
            reactionDict = dict(sorted(reactions_dict.items(), key=lambda kv: kv[1], reverse=True))
            #add_to_cache(drug_name, reactionDict)

        except:
            print('Drug not found in FDA database. Please try another search.')
            return None

    #### SHOULD I LIST ONLY THE TOP TEN TO THE USER? ####

    return reactionDict



def find_by_reaction(user_reaction):
    '''
    Returns a list of rections reported to the FDA
    for the drug entered by the user.  Will return
    data from cache, if found.  Otherwise, will use
    FDA API to retrieve the information.

    Parameters:
    -----------
    user_reaction: string
        name of reaction entered by user

    Returns:
    --------
    drugDict: dictionary
        dictionary containing the name of the drug name (key)
        and the number of times the drug was reported for the
        user-specified reaction (value)
    '''
    # Can use the same base as 'find_my_drug' probably, but search
    # for different values in 'output'
    reaction_dict = {}
    reaction_dict = check_cache(user_reaction)

    if reaction_dict:
        drugs_dict = {}
        drugs = reaction_dict['results']
        for i in range(len(drugs)):
            for x in range(len(drugs[i]['patient']['drug'])):
                found_drug = drugs[i]['patient']['drug'][x]['medicinalproduct'].replace('  ','')
                if found_drug not in drugs_dict:
                    drugs_dict[found_drug] = 1
                else:
                    drugs_dict[found_drug] += 1
                ### PICK UP FROM HERE ### NOT FINISHSED ###

        drugsDict = dict(sorted(drugs_dict.items(), key=lambda kv: kv[1], reverse=True))
    elif reaction_dict is None:
        fda_url_base = "https://api.fda.gov/drug/event.json?api_key="
        api_key = secret_drugs.FDA_API_KEY
        fda_search_drug = "&search=patient.reaction.reactionmeddrapt:" + user_reaction
        limit = '&limit=1000'

        drugs_output = requests.get(fda_url_base + api_key + fda_search_drug + limit)
        drug_results = json.loads(drugs_output.text)
        try:
            drugs = drug_results['results']
            add_to_cache(user_reaction, drug_results)

            drugs_dict = {}
            for i in range(len(drugs)):
                for x in range(len(drugs[i]['patient']['drug'])):
                    found_drug = drugs[i]['patient']['drug'][x]['medicinalproduct'].replace('  ','')
                    if found_drug not in drugs_dict:
                        drugs_dict[found_drug] = 1
                    else:
                        drugs_dict[found_drug] += 1
                    ### PICK UP FROM HERE ### NOT FINISHSED ###

            drugsDict = dict(sorted(drugs_dict.items(), key=lambda kv: kv[1], reverse=True))
        except:
            print('Reaction not found in FDA database. Please try another search.')
            return None

    return drugsDict


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
        json.dump(json_cache, cache, indent=2)


# Initializing setup of cache
json_cache = {}
path = 'drugs_cache.json'

# if the cache file exist, read from that file
if os.path.isfile(path):
    with open('drugs_cache.json') as f:
        json_cache = json.load(f)


if __name__ == "__main__":
    # interactive search should go here
    drug_test = find_by_reaction('vomiting')
    print(drug_test)

    while True:
        drug_search = input("Please enter the name of a drug to search: ")
        test = find_by_drug(drug_search)
        # if 'test' is None, allow the user to search again.
        while test is None:
            drug_search = input("Please enter the name of a drug to search: ")
            test = find_by_drug(drug_search)


        # Have a way to present as chart here (create functions?)
        print(test)

        # For Reddit section
        more_info = input("Would you like to find out more info about this drug (y/n)? ")
        exit()