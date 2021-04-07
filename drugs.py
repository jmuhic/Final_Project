import requests
import json
import webbrowser
import secret_drugs

def find_adverse_reactions(drug_name):
    fda_url_base = "https://api.fda.gov/drug/event.json?"
    api_key = FDA_API_KEY
    
    '''
    search by either brand name first, if not found, then search generic.
    if nothing found, then print apologies and ask to try another drug search
    #fda_url_search = 
    #https://api.fda.gov/drug/event.json?search=patient.drug.openfda.brand_name:%22BONIVA%22
    #search=patient.drug.openfda.generic_name:"FOO+BAR"
    '''
    pass



if __name__ == "__main__":
    # interactive search should go here
    pass