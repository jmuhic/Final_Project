import requests
import json
import os
import webbrowser
import secret_drugs
import sqlite3
import plotly
import plotly.graph_objects as go
import plotly.express as px
import numpy
from flask import Flask
from flask import request
import logging
import requests.auth
import urllib
import urllib.parse
import click

CLIENT_ID = secret_drugs.REDDIT_CLIENT_ID
CLIENT_SECRET = secret_drugs.REDDIT_CLIENT_SECRET
REDIRECT_URI = secret_drugs.REDIRECT_URI
REDDIT_USERNAME = secret_drugs.REDDIT_USERNAME
REDDIT_PASSWORD = secret_drugs.REDDIT_PASSWORD

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

    Returns: (NONE)
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

    if results_list:
        write_to_DB(drug_name, results_list, 'drug')
        total_reaction_by_drug(drug_name)

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

    Returns: (NONE)
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
    
    if results_list:
        write_to_DB(user_reaction, results_list, 'reaction')
        total_drugs_by_reaction(user_reaction)

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
        try:
            age = raw_data[i]['patient']['patientonsetage']
        except:
            age = 0

        try:
            gender = raw_data[i]['patient']['patientsex']
        except:
            gender = 0

        for x in range(len(raw_data[i]['patient']['reaction'])):
            drug_reaction = raw_data[i]['patient']['reaction'][x]['reactionmeddrapt']
            report_id = raw_data[i]['safetyreportid']
            results_list.append((report_id, drug_name.upper(), drug_reaction, age, gender))

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
        try:
            age = raw_data[i]['patient']['patientonsetage']
        except:
            age = 0

        try:
            gender = raw_data[i]['patient']['patientsex']
        except:
            gender = 0

        for x in range(len(raw_data[i]['patient']['drug'])):
            found_drug = raw_data[i]['patient']['drug'][x]['medicinalproduct'].replace('  ','')
            report_id = raw_data[i]['safetyreportid']
            results_list.append((report_id, found_drug.upper(), user_reaction, age, gender))

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

    if summary_list:
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

    if summary_list:
        write_Drug_DB(summary_list)


def create_database():
    '''
    Creates the database and tables that will be used to store
    the results from the user's search(es).  If the tables/database
    already exists, there will be no update.
    There are five tables:
    (1) Drugs - table of all drugs searched by user
    (2) Reactions - table of all reactions searched by user
    (3) Report_Summary - table of drugs and associated reactions
        in addition to the FDA's report id for the drug/reaction combo
        listing Report ID, Age, and Gender
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
    # Create the Report Summary table if does not already exist
    cur.execute('''
    CREATE TABLE IF NOT EXISTS "Report_Summary" (
	"ReportID"	INTEGER NOT NULL,
	"Drugs"	TEXT NOT NULL,
	"Reactions"	TEXT NOT NULL,
    "Age" INTEGER,
    "Gender" INTEGER,
    UNIQUE (ReportID, Drugs, Reactions, Age, Gender) ON CONFLICT IGNORE
)
    '''
    )

    # Create the Drugs List table if does not already exist
    cur.execute('''
    CREATE TABLE IF NOT EXISTS "Drugs" (
	"Drugs"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("Drugs")
    )
    '''
    )

    # Create the Reaction List table if does not already exist
    cur.execute('''
    CREATE TABLE IF NOT EXISTS "Reactions" (
	"Reactions"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("Reactions")
    )
    '''
    )

    # Create the Reaction Summary table if does not already exist
    # List count of reactions reported for a specified drug
    cur.execute('''
    CREATE TABLE IF NOT EXISTS "Reactions_per_Drug" (
	"Drugs"	TEXT NOT NULL,
	"Reactions"	TEXT NOT NULL,
	"Reaction_Count"	INTEGER NOT NULL
    )
    '''
    )

    # Create the Drug Summary table if does not already exist
    # List count of Drugs reported for a specified Reaction
    cur.execute('''
    CREATE TABLE IF NOT EXISTS "Drug_per_Reaction" (
	"Reactions"	TEXT NOT NULL,
	"Drugs"	TEXT NOT NULL,
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
            cur.execute(f"INSERT OR IGNORE INTO Report_Summary VALUES\
                ('{search_results[i][0]}', '{search_results[i][1]}',\
                    '{search_results[i][2]}', '{search_results[i][3]}',\
                        '{search_results[i][4]}')")
        conn.commit()
    elif search_type == 'reaction':
        cur.execute(f"INSERT OR IGNORE INTO Reactions VALUES ('{user_search}')")
        for i in range(len(search_results)):
            cur.execute(f"INSERT OR IGNORE INTO Report_Summary VALUES\
                ('{search_results[i][0]}', '{search_results[i][1]}',\
                    '{search_results[i][2]}', '{search_results[i][3]}',\
                        '{search_results[i][4]}')")
        conn.commit()

    # Close the connection to the database
    conn.close()


def bar_chart(drug_name=None, reaction_name=None):
    ''' Read information from the database to build a bar chart
    which will display the top ten results for either top Reactions reported
    or top Drugs per Reaction based on user request.

    Parameters:
    -----------
    drug_name: string
        name of the drug entered by the user
        If search was for a reaction, default is None

    reaction_name: string
        name of the reaction entered by the user
        If search was for a drug, default is None

    Returns:
    --------
    None
    '''

    xvals = []
    yvals = []

    # retrieve top ten results of reactions per drug
    if drug_name:
        con = sqlite3.connect("FDA_DRUGS.db")
        cur = con.cursor()
        query = """
            SELECT Reactions, Reaction_Count
            FROM Reactions_per_Drug
            WHERE Drugs = ?
            LIMIT 10
            """
        result = cur.execute(query, (drug_name,)).fetchall()

        # build bar chart from retrieved DB data (plotly)
        for i in range(len(result)):
            xvals.append(result[i][0])
            yvals.append(result[i][1])

        bar_data =go.Bar(x=xvals, y=yvals)
        #basic_layout = go.Layout(title="Top Reactions per Drug")
        basic_layout = go.Layout(title=f"Top 10 Reactions for {drug_name}")
        fig = go.Figure(data=bar_data, layout=basic_layout)
        fig.show()

    if reaction_name:
        con = sqlite3.connect("FDA_DRUGS.db")
        cur = con.cursor()
        query = """
            SELECT Drugs, Drug_Count
            FROM Drug_per_Reaction
            WHERE Reactions = ?
            LIMIT 10
            """
        result = cur.execute(query, (reaction_name,)).fetchall()

        # build bar chart from retrieved DB data (plotly)
        for i in range(len(result)):
            xvals.append(result[i][0])
            yvals.append(result[i][1])

        bar_data =go.Bar(x=xvals, y=yvals)
        #basic_layout = go.Layout(title="Top Reactions per Drug")
        basic_layout = go.Layout(title=f"Top 10 Reported Drugs for {reaction_name}")
        fig = go.Figure(data=bar_data, layout=basic_layout)
        fig.show()

        con.close()


def line_chart(drug_name=None, reaction_name=None):
    ''' Read information from the database to build a line chart
    which will display the top ten results for either top Reactions reported
    or top Drugs per Reaction based on user request.

    Parameters:
    -----------
    drug_name: string
        name of the drug entered by the user
        If search was for a reaction, default is None

    reaction_name: string
        name of the reaction entered by the user
        If search was for a drug, default is None

    Returns:
    --------
    None
    '''

    xvals = []
    yvals = []

    # retrieve top ten results of reactions per drug
    # if user initiated a search to find the most reported reactions for a drug
    if drug_name:
        con = sqlite3.connect("FDA_DRUGS.db")
        cur = con.cursor()
        query = """
            SELECT Reactions, Reaction_Count
            FROM Reactions_per_Drug
            WHERE Drugs = ?
            LIMIT 10
            """
        result = cur.execute(query, (drug_name,)).fetchall()

        # build bar chart from retrieved DB data (plotly)
        for i in range(len(result)):
            xvals.append(result[i][0])
            yvals.append(result[i][1])

        bar_data =go.Scatter(x=xvals, y=yvals)
        #basic_layout = go.Layout(title="Top Reactions per Drug")
        basic_layout = go.Layout(title=f"Top 10 Reactions for {drug_name}")
        fig = go.Figure(data=bar_data, layout=basic_layout)
        fig.show()
 
    # retrieve top ten most commonly reported drug for a reaction
    # if user initiated a search to find most reported drugs for a reaction
    if reaction_name:
        con = sqlite3.connect("FDA_DRUGS.db")
        cur = con.cursor()
        query = """
            SELECT Drugs, Drug_Count
            FROM Drug_per_Reaction
            WHERE Reactions = ?
            LIMIT 10
            """
        result = cur.execute(query, (reaction_name,)).fetchall()

        # build (scatter)line chart from retrieved DB data (plotly)
        for i in range(len(result)):
            xvals.append(result[i][0])
            yvals.append(result[i][1])

        bar_data =go.Scatter(x=xvals, y=yvals)
        basic_layout = go.Layout(title=f"Top 10 Reported Drugs for {reaction_name}")
        fig = go.Figure(data=bar_data, layout=basic_layout)
        fig.show()

        con.close()

def sample_reportids(drug_name=None, reaction_name=None):
    ''' Will present a list of report ids as samples which the user can choose
    to request on his or her own through the Freedom of Information Act (FOIA).

    Parameters:
    -----------
    drug_name: string
        name of the drug entered by the user
        If search was for a reaction, default is None

    reaction_name: string
        name of the reaction entered by the user
        If search was for a drug, default is None

    Returns:
    --------
    None
    '''

    if drug_name:
        con = sqlite3.connect("FDA_DRUGS.db")
        cur = con.cursor()
        query = """
            SELECT ReportID
            FROM Report_Summary
            WHERE Drugs = ?
            GROUP BY ReportID
            LIMIT 10
            """
        result = cur.execute(query, (drug_name,)).fetchall()

        print(f"\nSample List of Reports for {drug_name}.  Can be retrieved through FOIA request.")
        print("-" * 79)
        for i in range(len(result)):
            print(f"{i + 1}. {result[i][0]}")

    if reaction_name:
        con = sqlite3.connect("FDA_DRUGS.db")
        cur = con.cursor()
        query = """
            SELECT ReportID
            FROM Report_Summary
            WHERE Reactions = ?
            GROUP BY ReportID
            LIMIT 10
            """
        result = cur.execute(query, (reaction_name.capitalize(),)).fetchall()

        print(f"\nSample List of Reports for {reaction_name}.  Can be retrieved through FOIA request.")
        print("-" * 79)
        for i in range(len(result)):
            print(f"{i + 1}. {result[i][0]}")

    return result


def gender_stats(drug_name=None, reaction_name=None):
    ''' Will present a pie chart displaying the gender distribution
    related the results returned for a Drug or Reaction.

    Parameters:
    -----------
    drug_name: string
        name of the drug entered by the user
        If search was for a reaction, default is None

    reaction_name: string
        name of the reaction entered by the user
        If search was for a drug, default is None

    Returns:
    --------
    None
    '''
    gender = []
    gender_count = []
    gender_result = []

    if drug_name:
        con = sqlite3.connect("FDA_DRUGS.db")
        cur = con.cursor()
        query = """
            SELECT Gender, COUNT(*) AS 'num'
            FROM Report_Summary
            WHERE Drugs = ?
            GROUP BY Gender
            """
        result = cur.execute(query, (drug_name,)).fetchall()

        # Changing numeric values to Gender Names for pie chart
        for p in range(len(result)):
            if result[p][0] == 0:
                gender_result.append(('Unknown',result[p][1]))
            elif result[p][0] == 1:
                gender_result.append(('Male',result[p][1]))
            elif result[p][0] == 2:
                gender_result.append(('Female',result[p][1]))

        for i in range(len(gender_result)):
            gender.append(gender_result[i][0])
            gender_count.append(gender_result[i][1])
        fig = px.pie(values=gender_count, names=gender,\
            title=f"Gender Distribution for Reports related to {drug_name}")
        fig.show()


    if reaction_name:
        reaction_name = reaction_name.capitalize()
        con = sqlite3.connect("FDA_DRUGS.db")
        cur = con.cursor()
        query = """
            SELECT Gender, COUNT(*) AS 'num'
            FROM Report_Summary
            WHERE Reactions = ?
            GROUP BY Gender
            """
        result = cur.execute(query, (reaction_name,)).fetchall()

        # Changing numeric values to Gender Names for pie chart
        for p in range(len(result)):
            if result[p][0] == 0:
                gender_result.append(('Unknown',result[p][1]))
            elif result[p][0] == 1:
                gender_result.append(('Male',result[p][1]))
            elif result[p][0] == 2:
                gender_result.append(('Female',result[p][1]))

        for i in range(len(gender_result)):
            gender.append(gender_result[i][0])
            gender_count.append(gender_result[i][1])
        fig = px.pie(values=gender_count, names=gender,\
            title=f"Gender Distribution for Reports related to {reaction_name.upper()}")
        fig.show()


    return result

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


app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
log.disabled = True
oauth_state=''
oauth_code=''

@app.route('/')
def get_auth_parameters():
    global oauth_state
    global oauth_code
    oauth_state = request.args.get('state')
    oauth_code = request.args.get('code')

    func = request.environ.get('werkzeug.server.shutdown')
    func()
    return '<script>window.onload=window.close()</script>'

def make_authorization_url():
	# Generate a random string for the state parameter
	# Save it for use later to prevent xsrf attacks
	from uuid import uuid4
	state = str(uuid4())
	save_created_state(state)
	params = {"client_id": CLIENT_ID,
			  "response_type": "code",
			  "state": state,
			  "redirect_uri": REDIRECT_URI,
			  "duration": "permanent",
			  "scope": "identity,edit,flair,history,modconfig,modflair,modlog,modposts,modwiki,mysubreddits,privatemessages,read,report,save,submit,subscribe,vote,wikiedit,wikiread"}
	import urllib
	url = "https://ssl.reddit.com/api/v1/authorize?" + urllib.parse.urlencode(params)
	return url

# Left as an exercise to the reader.
# You may want to store valid states in a database or memcache,
# or perhaps cryptographically sign them and verify upon retrieval.
# I chose not to use this
def save_created_state(state):
	pass

def is_valid_state(state):
	return True

# Used these functions to suppress warning messages from being displayed to the user
def secho(text, file=None, nl=None, err=None, color=None, **styles):
   pass

def echo(text, file=None, nl=None, err=None, color=None, **styles):
   pass

click.echo = echo
click.secho = secho

def init_tokens_for_Reddit():
    '''Initial creation of tokens for access to
    the Reddit application

    Parameters:
    -----------
    refresh_token: string
        token provided by Reddit OATH to refresh the
        access token

    Returns:
    --------
    tokens: tuple
        tuple containing both the access_token and
        refresh_token retrieved

    '''
    input("test")
    webbrowser.open(make_authorization_url())
    app.run(port=8080)
    print(oauth_state)
    print(oauth_code)

    client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    post_data = {"grant_type": "authorization_code", "code": oauth_code, "redirect_uri": REDIRECT_URI}
    headers = {"User-Agent": "ChangeMeClient/0.1 by bluewolfhi1817"}
    response = requests.post("https://ssl.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
    output = response.json()

    access_token = output['access_token']
    refresh_token = output['refresh_token']
    tokens = (access_token, refresh_token)
    print(output)

    return tokens

def token_refresh(refresh_token):
    '''Refreshing the Reddit token after it expires.

    Parameters:
    -----------
    refresh_token: string
        token provided by Reddit OATH to refresh the
        access token

    Returns:
    --------
    access_token: string
        the new access token to be used for Reddit access
    '''
    client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    post_data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    headers = {"User-Agent": f"ChangeMeClient/0.1 by {REDDIT_USERNAME}"}
    response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
    output = response.json()
    access_token = output['access_token']
    print(output)

    return access_token

def for_Reddit_retrieve(access_token, drug_name):
    '''Refreshing the Reddit token after it expires.

    Parameters:
    -----------
    access_token: string
        access token required to retrieve information from
        the Reddit application

    drug_search: string
        the name of the drug which the user searched and is
        attempting to find more information on Reddit

    Returns:
    --------
    URL_list: list
        list of Titles and URLs related to the user's search
    '''

    url_list = []
    title_list = []

    headers = {"Authorization": f"bearer {access_token}", "User-Agent": f"ChangeMeClient/0.1 by {REDDIT_USERNAME}"}

    url_search = "https://oauth.reddit.com/search.json?limit=100&t=month&type=link&q="
    url_end = "+AND+reaction"

    response = requests.get(url_search + drug_name + url_end, headers=headers)

    output = response.json()

    for i in range(10):
        title_list.append(output['data']['children'][i]['data']['title'])
        url_list.append(output['data']['children'][i]['data']['url'])


    response_Dict = {
        "Title": title_list,
        "URL": url_list
    }

    return response_Dict


# Initializing setup of cache
json_cache = {}
path = 'drugs_cache.json'

json_summary_cache = {}
summary_path = 'summary_cache.json'

# if the cache file exist, read from that file
if os.path.isfile(path):
    with open('drugs_cache.json') as f:
        json_cache = json.load(f)

if os.path.isfile(summary_path):
    with open('summary_cache.json') as sum_f:
        json_summary_cache = json.load(sum_f)


if __name__ == "__main__":
    # First thing will be to create the DB to store results
    create_database()

    # drug_name = None
    # reaction_name = None


    #drug_name = 'AMLODIPINE'
    # reaction_name = 'COUGH'
    # bar_chart(drug_name=drug_name, reaction_name=reaction_name)
    # line_chart(drug_name=drug_name, reaction_name=reaction_name)
    #results = sample_reportids(drug_name=drug_name, reaction_name=reaction_name)
    # results = gender_stats(drug_name=drug_name, reaction_name=reaction_name)
    # print(results)

    ### interactive search should go here ###
    # while True:
    #     reaction_search = input("Please enter a reaction to search: ")
    #     reaction_search = reaction_search.capitalize()
    #     drug_test = find_by_reaction(reaction_search)
    #     print(drug_test)
    #     exit()


    # while True:
    #     drug_search = input("Please enter the name of a drug to search: ")
    #     drug_search = drug_search.upper()
    #     test = find_by_drug(drug_search)
    #     # if 'test' is None, allow the user to search again.
    #     # while test is None:
    #     #     drug_search = input("Please enter the name of a drug to search: ")
    #     #     drug_search = drug_search.upper()
    #     #     test = find_by_drug(drug_search)
    #     #     #find_by_drug(drug_search)
    #     print(test)
    #     exit()


        # #     # Have a way to present as chart/graphic here (create functions?)

    #     write_to_DB(drug_search, test, 'drug')

    ### For Reddit section ###
        # more_info = input("Would you like to find out more info about this drug (y/n)? ")

    temp = init_tokens_for_Reddit()
    access_token = temp[0]
    refresh_token = temp[1]
    print(temp)

    access_token2 = token_refresh(refresh_token)
    print(access_token2)

    drug_name = 'ibuprofen'
    temp3 = for_Reddit_retrieve(access_token2, drug_name)
    print(temp3)

    exit()