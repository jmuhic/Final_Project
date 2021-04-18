import requests
import json
import os
import webbrowser
import secret_drugs
import sqlite3
import plotly



def find_by_drug(drug_name):
    '''
    Returns a list of rections reported to the FDA
    for the drug entered by the user.
    Will return data from cache, if found.  Otherwise,
    will use FDA API to retrieve the information.

    Parameters:
    -----------
    drug_name: string
        name of drug entered by user

    Returns:
    --------
    results_list: list
        List of tuples containing the FDA Report ID,
        drug name of user's search,
        and the associated reaction reported.
    '''

    drug_dict = {}
    drug_dict = check_cache(drug_name)

    if drug_dict:
        reactions = drug_dict['results']
        results_list = results_loop_drug(reactions, drug_name)

        # results_list = []
        # reactions = drug_dict['results']
        # for i in range(len(reactions)):
        #     for x in range(len(reactions[i]['patient']['reaction'])):
        #         drug_reaction = reactions[i]['patient']['reaction'][x]['reactionmeddrapt']
        #         report_id = reactions[i]['safetyreportid']
        #         results_list.append((report_id, drug_name, drug_reaction))

    elif drug_dict is None:
        fda_url_base = "https://api.fda.gov/drug/event.json?api_key="
        api_key = secret_drugs.FDA_API_KEY
        limit = '&limit=1000'

        # More generalized search appears to be most effective for brand/generic/substance_name
        output = requests.get(fda_url_base + api_key + '&search=' + drug_name + limit)
        reaction_results = json.loads(output.text)
        try:
            reactions = reaction_results['results']
            add_to_cache(drug_name, reaction_results)

        # Building a dictionary to list reporting reactions and number of occurrences
            results_list = results_loop_drug(reactions, drug_name)
            # results_list = []
            # for i in range(len(reactions)):
            #     for x in range(len(reactions[i]['patient']['reaction'])):
            #         drug_reaction = reactions[i]['patient']['reaction'][x]['reactionmeddrapt']
            #         report_id = reactions[i]['safetyreportid']
            #         results_list.append((report_id, drug_name, drug_reaction))

        except:
            print('Drug not found in FDA database. Please try another search.')
            return None

    return results_list



def find_by_reaction(user_reaction):
    '''
    Returns a list of drugs associated with reaction
    entered in the user search which has been reported
    to the FDA.
    Will return data from cache, if found.  Otherwise,
    will use FDA API to retrieve the information.

    Parameters:
    -----------
    user_reaction: string
        name of reaction entered by user

    Returns:
    --------
    results_list: list
        List of tuples containing the FDA Report ID,
        the drug associated with the reaction reported,
        and the reaction name of user's search.
    '''

    # Can use the same base as 'find_my_drug' probably, but search
    # for different values in 'output'
    reaction_dict = {}
    reaction_dict = check_cache(user_reaction)

    if reaction_dict:
        drugs = reaction_dict['results']
        results_list = results_loop_reactions(drugs, user_reaction)
        # results_list = []
        # drugs = reaction_dict['results']
        # for i in range(len(drugs)):
        #     for x in range(len(drugs[i]['patient']['drug'])):
        #         found_drug = drugs[i]['patient']['drug'][x]['medicinalproduct'].replace('  ','')
        #         report_id = drugs[i]['safetyreportid']
        #         results_list.append((report_id, found_drug, user_reaction))

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

            results_list = results_loop_reactions(drugs, user_reaction)
            # results_list = []
            # for i in range(len(drugs)):
            #     for x in range(len(drugs[i]['patient']['drug'])):
            #         found_drug = drugs[i]['patient']['drug'][x]['medicinalproduct'].replace('  ','')
            #         report_id = drugs[i]['safetyreportid']
            #         results_list.append((report_id, found_drug, user_reaction))

        except:
            print('Reaction not found in FDA database. Please try another search.')
            return None

    return results_list

def results_loop_drug(raw_data, drug_name):
    '''Takes the raw results from the FDA API
    and creates a list of desired values:
    report_id, drug, reaction

    Parameters:
    -----------
    raw_results: list
        raw results returned from FDA for drug searched

    Returns:
    --------
    results_list: list
        List of tuples containing the FDA Report ID,
        drug name of user's search,
        and the associated reaction reported.

    '''
    results_list = []
    for i in range(len(raw_data)):
        for x in range(len(raw_data[i]['patient']['reaction'])):
            drug_reaction = raw_data[i]['patient']['reaction'][x]['reactionmeddrapt']
            report_id = raw_data[i]['safetyreportid']
            results_list.append((report_id, drug_name.upper(), drug_reaction))

    return results_list

def results_loop_reactions(raw_data, user_reaction):
    '''Takes the raw results from the FDA API
    and creates a list of desired values:
    report_id, drug, reaction

    Parameters:
    -----------
    raw_results: list
        raw results returned from FDA for reaction searched

    Returns:
    --------
    results_list: list
        List of tuples containing the FDA Report ID,
        the drug associated with the reaction reported
        and reaction name of user's search.

    '''
    results_list = []
    for i in range(len(raw_data)):
        for x in range(len(raw_data[i]['patient']['drug'])):
            found_drug = raw_data[i]['patient']['drug'][x]['medicinalproduct'].replace('  ','')
            report_id = raw_data[i]['safetyreportid']
            results_list.append((report_id, found_drug.upper(), user_reaction))

    return results_list


def total_reaction_by_drug(drug_name):
    '''
    Returns a summarized list of rections reported to the FDA
    for the drug entered by the user.
    Will return data from cache, if found.  Otherwise,
    will use FDA API to retrieve the information.

    Parameters:
    -----------
    drug_name: string
        name of drug entered by user

    Returns: 
    --------
    None (writes results to table in DB)
    '''
    drug_name = drug_name.upper()
    json_dict = {}
    json_dict = check_summary_cache(drug_name)

    if json_dict:
        tot_reactions = json_dict['results']
        summary_list = []
        for i in range(len(tot_reactions)):
            reaction = tot_reactions[i]['term']
            count = tot_reactions[i]['count']
            summary_list.append((drug_name, reaction, count))

    elif json_dict is None:
        summary_url_base = "https://api.fda.gov/drug/event.json?api_key="
        api_key = secret_drugs.FDA_API_KEY
        descrip = '&count=patient.reaction.reactionmeddrapt.exact&search=patient.drug.medicinalproduct.exact:'

        # Getting data from FDA API Call
        # Call returns the top 100 reactions reported to the FDA
        output = requests.get(summary_url_base + api_key + descrip + drug_name)
        json_dict = json.loads(output.text)

        try:
            tot_reactions = json_dict['results']
            add_to_summary_cache(drug_name, json_dict)

        # Building a dictionary to list reporting reactions and number of occurrences
            summary_list = []
            for i in range(len(tot_reactions)):
                reaction = tot_reactions[i]['term']
                count = tot_reactions[i]['count']
                summary_list.append((drug_name, reaction, count))
            # results_list = []
            # for i in range(len(reactions)):
            #     for x in range(len(reactions[i]['patient']['reaction'])):
            #         drug_reaction = reactions[i]['patient']['reaction'][x]['reactionmeddrapt']
            #         report_id = reactions[i]['safetyreportid']
            #         results_list.append((report_id, drug_name, drug_reaction))
        except:
            print('Drug not found in FDA database. Please try another search.')
            return None

    write_Reaction_DB(summary_list)


def total_drugs_by_reaction(reaction):
    '''
    Returns a summarized list of drugs by count for the
    reaction entered by the user.
    Will return data from cache, if found.  Otherwise,
    will use FDA API to retrieve the information.

    Parameters:
    -----------
    reaction_name: string
        name of reaction entered by user

    Returns:
    --------
    None (writes results to table in DB)
    '''
    reaction = reaction.upper()
    json_dict = {}
    json_dict = check_summary_cache(reaction)

    if json_dict:
        tot_drugs = json_dict['results']
        summary_list = []
        for i in range(len(tot_drugs)):
            drug_name = tot_drugs[i]['term']
            count = tot_drugs[i]['count']
            summary_list.append((drug_name, reaction, count))

    elif json_dict is None:
        summary_url_base = "https://api.fda.gov/drug/event.json?api_key="
        api_key = secret_drugs.FDA_API_KEY
        descrip = '&count=patient.drug.medicinalproduct.exact&search=patient.reaction.reactionmeddrapt.exact:'

        # Getting data from FDA API Call
        # Call returns the top 100 instances reported to the FDA
        output = requests.get(summary_url_base + api_key + descrip + reaction)
        json_dict = json.loads(output.text)

        try:
            tot_drugs = json_dict['results']
            add_to_summary_cache(reaction, json_dict)

        # Building a dictionary to list reporting reactions and number of occurrences
            summary_list = []
            for i in range(len(tot_drugs)):
                drug_name = tot_drugs[i]['term']
                count = tot_drugs[i]['count']
                summary_list.append((drug_name, reaction, count))
            # results_list = []
            # for i in range(len(reactions)):
            #     for x in range(len(reactions[i]['patient']['reaction'])):
            #         drug_reaction = reactions[i]['patient']['reaction'][x]['reactionmeddrapt']
            #         report_id = reactions[i]['safetyreportid']
            #         results_list.append((report_id, drug_name, drug_reaction))
        except:
            print('Drug not found in FDA database. Please try another search.')
            return None

    write_Drug_DB(summary_list)

def create_database():
    '''
    Creates the database and tables that will be used to store
    the results from the user's search(es).  If the tables/database
    already exists, there will be no update.
    There are five tables:
    (1) Drugs - table of all drugs searched by user
    (2) Reactions - table of all reactions searched by user
    (3) Drug_Reactions - table of drugs and associated reactions
        in addition to the FDA's report id for the drug/reaction combo
    (4) Reactions_per_Drug - table of drugs that list the number of times
        a reaction has been reported for a specified drug
    (5) Drug_per_Reaction - table that lists the number of times a Drug
        has been reported for a specified Reaction

    Parameters:
    -----------
    None

    Returns:
    --------
    None
    '''

    # Connect to database
    conn = sqlite3.connect('FDA_DRUGS.db')

    # Create DB cursor
    cur = conn.cursor()

    ### CREATION OF THREE TABLES IN DB (IF NOT EXIST) ###
    # Create the Drugs + Reactions table if does not already exist
    cur.execute('''
    CREATE TABLE IF NOT EXISTS "Drug_Reactions" (
	"ReportID"	INTEGER NOT NULL,
	"Drugs"	TEXT NOT NULL,
	"Reactions"	TEXT NOT NULL,
    UNIQUE (ReportID, Drugs, Reactions) ON CONFLICT IGNORE
)
    '''
    )

    # Create the Drugs List table if does not already exist
    cur.execute('''
    CREATE TABLE IF NOT EXISTS "Drugs" (
	"Drug_Name"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("Drug_Name")
    )
    '''
    )

    # Create the Reaction List table if does not already exist
    cur.execute('''
    CREATE TABLE IF NOT EXISTS "Reactions" (
	"Reaction_Type"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("Reaction_Type")
    )
    '''
    )

    # Create the Reaction Summary table if does not already exist
    # List count of reactions reported for a specified drug
    cur.execute('''
    CREATE TABLE IF NOT EXISTS "Reactions_per_Drug" (
	"Drug"	TEXT NOT NULL,
	"Reaction"	TEXT NOT NULL,
	"Reaction_Count"	INTEGER NOT NULL
    )
    '''
    )

    # Create the Drug Summary table if does not already exist
    # List count of Drugs reported for a specified Reaction
    cur.execute('''
    CREATE TABLE IF NOT EXISTS "Drug_per_Reaction" (
	"Reaction"	TEXT NOT NULL,
	"Drug"	TEXT NOT NULL,
	"Drug_Count"	INTEGER NOT NULL
    )
    '''
    )

def write_Reaction_DB(summary_list):
    '''
    Writes to the database the results returned for the
    number of Reactions reported for a particular Drug

    Parameters:
    -----------
    summary_list: list
        The list of results returned with the count of reactions
        for a specified drug.

    Returns:
    --------
    None
    '''
    #create_database()

    # Re-connect to database
    conn = sqlite3.connect('FDA_DRUGS.db')

    # Re-create DB cursor
    cur = conn.cursor()

    for i in range(len(summary_list)):
        cur.execute(f"INSERT OR IGNORE INTO Reactions_per_Drug VALUES\
            ('{summary_list[i][0]}', '{summary_list[i][1]}',\
                '{summary_list[i][2]}')")
    conn.commit()

    # Close the connection to the database
    conn.close()

def write_Drug_DB(summary_list):
    '''
    Writes to the database the results returned for the
    number of times a Drug was reported for a particular Reaction

    Parameters:
    -----------
    summary_list: list
        The list of results returned with the report count of a Drug
        reported for a specified Reaction.

    Returns:
    --------
    None
    '''
    #create_database()

    # Re-connect to database
    conn = sqlite3.connect('FDA_DRUGS.db')

    # Re-create DB cursor
    cur = conn.cursor()

    for i in range(len(summary_list)):
        cur.execute(f"INSERT OR IGNORE INTO Drug_per_Reaction VALUES\
            ('{summary_list[i][1]}', '{summary_list[i][0]}',\
                '{summary_list[i][2]}')")
    conn.commit()

    # Close the connection to the database
    conn.close()

def write_to_DB(user_search, search_results, search_type):
    '''
    Writes to the database the results that were returned
    based on the user's search.  List of results containing
    also the Report ID will be written to the Drugs_Reaction table.
    If the user searched for a reaction, then that reaction name
    will be added to the Reaction table.  If the user searched for a
    drug, then that drug will be added to the Drug table.

    Parameters:
    -----------
    user_search: string
        name of the drug or reaction entered by the user

    search_results: list
        results returned from the FDA based on the drug name
        or reaction entered by the user

    search_type: string
        will identify if the search was by 'reaction' or 'drug'.

    Returns:
    --------
    None
    '''
    #create_database()

    # Re-connect to database
    conn = sqlite3.connect('FDA_DRUGS.db')

    # Re-create DB cursor
    cur = conn.cursor()

    if search_type == 'drug':
        cur.execute(f"INSERT OR IGNORE INTO Drugs VALUES ('{user_search}')")
        for i in range(len(search_results)):
            cur.execute(f"INSERT OR IGNORE INTO Drug_Reactions VALUES\
                ('{search_results[i][0]}', '{search_results[i][1]}',\
                    '{search_results[i][2]}')")
        conn.commit()
    elif search_type == 'reaction':
        cur.execute(f"INSERT OR IGNORE INTO Reactions VALUES ('{user_search}')")
        for i in range(len(search_results)):
            cur.execute(f"INSERT OR IGNORE INTO Drug_Reactions VALUES\
                ('{search_results[i][0]}', '{search_results[i][1]}',\
                    '{search_results[i][2]}')")
        conn.commit()

    # Close the connection to the database
    conn.close()


def bar_chart(drug_name=None, reaction_name=None):
    ''' Read information from the database to build a bar chart
    which will display the top ten results based on user request.
    '''

    ### HERE IS A SAMPLE OF THE QUERY USED TO TEST ###
    # SELECT Reactions, Count(*) AS "Count"
    # FROM Drug_Reactions
    # WHERE Drugs LIKE "%klonopi%"
    # GROUP BY Reactions
    # ORDER BY Count DESC


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
        return json_cache[key]
    else:
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


def check_summary_cache(key):
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
    if key in json_summary_cache:
        return json_summary_cache[key]
    else:
        return None

def add_to_summary_cache(key, value):
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
    json_summary_cache[key] = value

    # writing new key,value pair to cache file
    with open("summary_cache.json", "w") as summary_cache:
        json.dump(json_summary_cache, summary_cache, indent=2)


def create_table(fda_results, search_type, user_search):
    '''
    Will create a new table or write to an existing
    table in the database which is use to store the
    results retrieved from user's FDA search.

    Parameters:
    -----------
    fda_results: dictionary
        dictionary of results from FDA search
        (either by drug or reaction).

    search_type: string
        Indicates whether the dictionary passed into
        the function is for drugs or reaction table.
        (e.g. 'drug' or 'reaction')

    user_search: string
        The search value entered by the user.
        Can be the name of a drug or a reaction.
        (e.g. 'Celebrex' or 'vomiting')

    Returns:
    --------
    None
    '''
    conn = sqlite3.connect('test.db')
    try:
        conn.execute('''
        CREATE TABLE "Reactions_by_Drug" (
            "Drug_Name"	TEXT UNIQUE,
            "Adverse_Reaction"	TEXT NOT NULL,
            "Count_Reaction_Reported"	INTEGER NOT NULL,
            PRIMARY KEY("Drug_Name")
            )
        '''
        )
    except:
        pass

    conn.close()

# Initializing setup of cache
json_cache = {}
path = 'drugs_cache.json'

json_summary_cache = {}
summary_path = 'summary_cache.json'

# if the cache file exist, read from that file
if os.path.isfile(path):
    with open('drugs_cache_redo.json') as f:
        json_cache = json.load(f)

if os.path.isfile(summary_path):
    with open('summary_cache.json') as sum_f:
        json_summary_cache = json.load(sum_f)


if __name__ == "__main__":
    # # interactive search should go here
    #drug_test = find_by_reaction('headache')
    #drug_test = drug_test.capitalize()
    #print(drug_test)

    #write_to_DB('headache', drug_test, 'reaction')

    # while True:
    #     drug_search = input("Please enter the name of a drug to search: ")
    #     drug_search = drug_search.upper()
    #     test = find_by_drug(drug_search)
    #     # if 'test' is None, allow the user to search again.
    #     while test is None:
    #         drug_search = input("Please enter the name of a drug to search: ")
    #         drug_search = drug_search.upper()
    #         test = find_by_drug(drug_search)

    # #     # Have a way to present as chart here (create functions?)
    #     print(test)

    #     write_to_DB(drug_search, test, 'drug')

        # # For Reddit section
        # more_info = input("Would you like to find out more info about this drug (y/n)? ")
    create_database()
    #total_reaction_by_drug("Tylenol")
    total_drugs_by_reaction("cough")
    exit()